from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import mne
import pandas as pd
from mne.preprocessing import ICA

from fc_pipeline.config import load_config, resolve_path
from fc_pipeline.io import infer_subject_id


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run ICA on preICA files and export component-review files."
    )
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    parser.add_argument(
        "--apply-auto",
        action="store_true",
        help="Apply automatically suggested artifact IC exclusions without a reviewed CSV.",
    )
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help="Redraw ICA review figures from saved ICA files without updating review CSVs.",
    )
    parser.add_argument(
        "--include-regex",
        help="Only process preICA files whose inferred subject/block id matches this regex, e.g. '^105_HC'.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    output_root = resolve_path(config, config["paths"]["output_dir"])
    preica_dir = output_root / "PreICA"
    ica_dir = output_root / "ICA"
    review_dir = output_root / "ICA_Review"
    cleaned_dir = output_root / "Backprojected"
    figure_dir = output_root / "ICA_Figures"
    for path in [ica_dir, review_dir, cleaned_dir, figure_dir]:
        path.mkdir(parents=True, exist_ok=True)

    ica_config = config["ica"]
    preica_files = sorted(preica_dir.glob(f"*{config['naming']['preica_suffix']}"))
    if not preica_files:
        raise FileNotFoundError(f"No preICA FIF files found in {preica_dir}")

    for preica_file in preica_files:
        subject_id = infer_subject_id(preica_file, config["naming"]["subject_regex"])
        if args.include_regex and not re.search(args.include_regex, subject_id):
            continue
        print(f"\nRunning ICA for {subject_id}: {preica_file.name}")

        raw = mne.io.read_raw_fif(preica_file, preload=True)
        if ica_config.get("set_average_reference_before_ica", False):
            # ICLabel expects common-average referenced EEG. This also follows
            # the current lab guidance for the Tai Chi preprocessing path.
            raw.set_eeg_reference("average", projection=False)

        picks = mne.pick_types(raw.info, eeg=True, eog=False, emg=False, misc=False)
        picks = [
            pick
            for pick in picks
            if raw.ch_names[pick] not in set(ica_config.get("exclude_channels", []))
        ]

        ica_path = ica_dir / f"{subject_id}-ica.fif"
        if args.figures_only:
            if not ica_path.exists():
                raise FileNotFoundError(f"No saved ICA file found for {subject_id}: {ica_path}")
            ica = mne.preprocessing.read_ica(ica_path)
            save_ica_figures(raw, ica, figure_dir, subject_id)
            print(f"Saved ICA review figures from existing ICA: {subject_id}")
            continue

        # This mirrors Yang's intent: fit ICA on cleaned preICA data while
        # ignoring chunks annotated as BAD during the 1-second QC step.
        ica = fit_ica_with_retry(raw, picks, ica_config)

        ica.save(ica_path, overwrite=True)
        print(f"Saved ICA solution: {ica_path}")

        labels, probabilities = label_ica_components(raw, ica)
        subject_review_dir = participant_output_dir(review_dir, subject_id)
        subject_review_dir.mkdir(parents=True, exist_ok=True)
        review_path = subject_review_dir / f"{subject_id}_ica_review.csv"
        old_review_path = review_dir / f"{subject_id}_ica_review.csv"
        review_table = build_review_table(labels, probabilities, ica_config)
        if review_path.exists():
            review_table = merge_existing_review(review_table, review_path)
        elif old_review_path.exists():
            review_table = merge_existing_review(review_table, old_review_path)
        try:
            review_table.to_csv(review_path, index=False)
            print(f"Saved ICA review table: {review_path}")
        except PermissionError:
            print(f"Review table is open or locked; keeping existing file: {review_path}")

        save_ica_figures(raw, ica, figure_dir, subject_id)

        reviewed_exclude = exclusions_from_review(review_table)
        if reviewed_exclude:
            exclusion_source = "reviewed_exclude"
            exclude = reviewed_exclude
        elif args.apply_auto or ica_config.get("apply_without_review", False):
            exclusion_source = "auto_exclude"
            exclude = review_table.loc[review_table["auto_exclude"], "component"].astype(int).tolist()
        else:
            print("No reviewed exclusions found. Skipping backprojection for this file.")
            print("Review the CSV, set any review_exclude1/2/3=true for bad ICs, then rerun this script.")
            continue

        # MNE's ICA.apply removes the selected ICs and projects the remaining
        # components back to channel space, equivalent to Yang's pop_subcomp step.
        ica.exclude = exclude
        cleaned = ica.apply(raw.copy())
        cleaned_path = cleaned_dir / f"{subject_id}{config['naming']['cleaned_suffix']}"
        cleaned.save(cleaned_path, overwrite=True)
        print(f"Applied {exclusion_source} IC exclusions {exclude}")
        print(f"Saved backprojected cleaned raw: {cleaned_path}")


def label_ica_components(raw: mne.io.BaseRaw, ica: ICA) -> tuple[list[str], list[float]]:
    """Use ICLabel if installed; otherwise leave labels blank for manual review."""
    try:
        from mne_icalabel import label_components
    except ImportError:
        n_components = len(ica.get_components().T)
        return ["manual_review_needed"] * n_components, [float("nan")] * n_components

    result = label_components(raw, ica, method="iclabel")
    return list(result["labels"]), [float(prob) for prob in result["y_pred_proba"]]


def fit_ica_with_retry(raw: mne.io.BaseRaw, picks: list[int], ica_config: dict) -> ICA:
    """Fit ICA, retrying with a higher variance threshold if too few ICs result."""
    primary_n_components = ica_config.get("n_components", 0.99)
    retry_n_components = ica_config.get("n_components_retry", 0.999)
    min_components = int(ica_config.get("min_components_before_retry", 0))

    try:
        ica = fit_single_ica(raw, picks, ica_config, primary_n_components)
    except RuntimeError as exc:
        if not retry_n_components or "threshold results in 1 component" not in str(exc):
            raise
        print(
            f"ICA failed with n_components={primary_n_components}; "
            f"retrying with n_components={retry_n_components}."
        )
        ica = fit_single_ica(raw, picks, ica_config, retry_n_components)

    n_components = int(getattr(ica, "n_components_", 0) or 0)
    if min_components and retry_n_components and n_components < min_components:
        print(
            f"Only {n_components} ICA components selected; "
            f"retrying with n_components={retry_n_components}."
        )
        ica = fit_single_ica(raw, picks, ica_config, retry_n_components)
    return ica


def fit_single_ica(
    raw: mne.io.BaseRaw,
    picks: list[int],
    ica_config: dict,
    n_components: float | int,
) -> ICA:
    ica = ICA(
        n_components=n_components,
        method=ica_config.get("method", "infomax"),
        fit_params=ica_config.get("fit_params", {"extended": True}),
        random_state=ica_config.get("random_state", 97),
        max_iter="auto",
    )
    ica.fit(
        raw,
        picks=picks,
        decim=ica_config.get("decim", 3),
        reject_by_annotation=True,
    )
    return ica


def build_review_table(
    labels: list[str],
    probabilities: list[float],
    ica_config: dict,
) -> pd.DataFrame:
    auto_artifact_labels = {label.lower() for label in ica_config.get("auto_artifact_labels", [])}
    rows = []
    for component, (label, probability) in enumerate(zip(labels, probabilities)):
        rows.append(
            {
                "component": component,
                "iclabel": label,
                "iclabel_probability": probability,
                "auto_exclude": str(label).lower() in auto_artifact_labels,
                "review_exclude1": "",
                "reviewer1": "",
                "reviewer1_note": "",
                "review_exclude2": "",
                "reviewer2": "",
                "reviewer2_note": "",
                "review_exclude3": "",
                "reviewer3": "",
                "reviewer3_note": "",
            }
        )
    return pd.DataFrame(rows)


def merge_existing_review(new_table: pd.DataFrame, review_path: Path) -> pd.DataFrame:
    existing = pd.read_csv(review_path)
    legacy_cols = {
        "reviewed_exclude": "review_exclude1",
        "review_notes": "reviewer1_note",
    }
    existing = existing.rename(columns=legacy_cols)
    keep_cols = [
        "component",
        "review_exclude1",
        "reviewer1",
        "reviewer1_note",
        "review_exclude2",
        "reviewer2",
        "reviewer2_note",
        "review_exclude3",
        "reviewer3",
        "reviewer3_note",
    ]
    existing = existing[[col for col in keep_cols if col in existing.columns]]
    if existing.empty:
        return new_table

    merged = new_table.merge(existing, on="component", how="left", suffixes=("", "_old"))
    for col in keep_cols:
        if col == "component":
            continue
        old_col = f"{col}_old"
        if old_col in merged:
            merged[col] = merged[old_col].combine_first(merged[col])
            merged = merged.drop(columns=[old_col])
    return merged


def exclusions_from_review(review_table: pd.DataFrame) -> list[int]:
    review_cols = [f"review_exclude{idx}" for idx in range(1, 4)]
    present_cols = [col for col in review_cols if col in review_table]
    if not present_cols:
        return []

    # Treat an IC as reviewed for removal if any reviewer marks their
    # review_exclude column true. Leave all cells blank until a human has checked.
    reviewed = pd.Series(False, index=review_table.index)
    for col in present_cols:
        reviewed = reviewed | review_table[col].astype(str).str.lower().isin({"true", "1", "yes", "y"})
    return review_table.loc[reviewed, "component"].astype(int).tolist()


def save_ica_figures(raw: mne.io.BaseRaw, ica: ICA, figure_dir: Path, subject_id: str) -> None:
    output_dir = figure_output_dir(figure_dir, subject_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        component_fig = ica.plot_components(show=False)
        if isinstance(component_fig, list):
            for idx, fig in enumerate(component_fig):
                fig.savefig(output_dir / f"ica_components_{idx + 1}.png", dpi=150)
                close_figure(fig)
        else:
            component_fig.savefig(output_dir / "ica_components.png", dpi=150)
            close_figure(component_fig)
    except Exception as exc:  # Plotting is useful but should not kill the run.
        print(f"Could not save ICA component topography figure: {exc}")

    try:
        save_clean_source_trace_figures(raw, ica, output_dir, subject_id)
    except Exception as exc:
        print(f"Could not save ICA source time-course figure: {exc}")

    try:
        save_source_psd_figure(raw, ica, output_dir, subject_id)
    except Exception as exc:
        print(f"Could not save ICA source PSD figure: {exc}")


def participant_block_output_dir(root_dir: Path, subject_id: str) -> Path:
    """Store review artifacts as <root>/<participant>/<block>/... when possible."""
    parts = subject_id.split("_", 1)
    if len(parts) == 2 and parts[1].upper().startswith("HC"):
        return root_dir / parts[0] / parts[1]
    return root_dir / subject_id


def participant_output_dir(root_dir: Path, subject_id: str) -> Path:
    """Store one-file-per-block review tables as <root>/<participant>/..."""
    return root_dir / subject_id.split("_", 1)[0]


def figure_output_dir(figure_dir: Path, subject_id: str) -> Path:
    return participant_block_output_dir(figure_dir, subject_id)


def save_clean_source_trace_figures(
    raw: mne.io.BaseRaw,
    ica: ICA,
    figure_dir: Path,
    subject_id: str,
    seconds_to_show: float = 10.0,
) -> None:
    """Save readable 0-10 s ICA source-trace pages for manual review."""
    import math

    import matplotlib.pyplot as plt
    import numpy as np

    sources = ica.get_sources(raw)
    data = sources.get_data()
    sfreq = raw.info["sfreq"]
    stop_sample = min(data.shape[1], int(seconds_to_show * sfreq))
    data = data[:, :stop_sample]
    times = np.arange(stop_sample) / sfreq
    n_components = data.shape[0]
    n_pages = 2
    components_per_page = math.ceil(n_components / n_pages)

    for page_idx in range(n_pages):
        start = page_idx * components_per_page
        stop = min(start + components_per_page, n_components)
        if start >= stop:
            continue

        page_data = data[start:stop]
        page_components = list(range(start, stop))
        offsets = np.arange(len(page_components))[::-1] * 4.0
        fig_height = max(7.0, 0.55 * len(page_components))
        fig, axis = plt.subplots(figsize=(16, fig_height), constrained_layout=True)

        for local_idx, (component_idx, trace) in enumerate(zip(page_components, page_data)):
            q25, q75 = np.nanpercentile(trace, [25, 75])
            scale = np.nanstd(trace)
            if scale > 0:
                trace = trace / scale
                q25 = q25 / scale
                q75 = q75 / scale
            baseline = offsets[local_idx]
            axis.axhspan(
                baseline + q25,
                baseline + q75,
                color="#90caf9",
                alpha=0.14,
                linewidth=0,
            )
            axis.axhline(baseline, color="0.72", linewidth=0.45)
            axis.plot(times, trace + baseline, color="black", linewidth=0.65)

        for annotation in raw.annotations:
            description = str(annotation["description"])
            if not description.upper().startswith("BAD"):
                continue
            onset = float(annotation["onset"])
            duration = float(annotation["duration"])
            if onset > seconds_to_show:
                continue
            axis.axvspan(onset, min(onset + duration, seconds_to_show), color="#e57373", alpha=0.18)

        axis.set_yticks(offsets)
        axis.set_yticklabels([f"IC {idx}" for idx in page_components], fontsize=8)
        axis.set_xlabel("Time (s)")
        axis.set_ylabel("ICA activation, scaled by each IC standard deviation")
        axis.set_title(
            f"{subject_id} ICA source traces, first {seconds_to_show:g} seconds "
            f"(page {page_idx + 1}/{n_pages})"
        )
        axis.set_xlim(times[0], times[-1])
        axis.grid(axis="x", color="0.85", linewidth=0.5)
        fig.savefig(figure_dir / f"ica_sources_{page_idx + 1}.png", dpi=150)
        plt.close(fig)


def close_figure(fig: object) -> None:
    import matplotlib.pyplot as plt

    plt.close(fig)


def save_source_psd_figure(
    raw: mne.io.BaseRaw,
    ica: ICA,
    figure_dir: Path,
    subject_id: str,
    fmin: float = 1.0,
    fmax: float = 80.0,
) -> None:
    """Save a compact PSD grid for the ICA component activations."""
    import math

    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.signal import welch

    sources = ica.get_sources(raw)
    data = sources.get_data(reject_by_annotation="NaN")
    sfreq = raw.info["sfreq"]
    n_components = data.shape[0]
    n_cols = 4
    n_rows = math.ceil(n_components / n_cols)
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(14, max(8.0, 2.0 * n_rows)),
        sharex=True,
        constrained_layout=True,
    )
    axes = np.atleast_1d(axes).ravel()

    for component_idx, axis in enumerate(axes):
        if component_idx >= n_components:
            axis.axis("off")
            continue

        trace = data[component_idx]
        trace = trace[np.isfinite(trace)]
        if trace.size < 2:
            axis.set_title(f"IC {component_idx}: no data", fontsize=8)
            axis.axis("off")
            continue

        freqs, psd = welch(
            trace,
            fs=sfreq,
            nperseg=min(int(2 * sfreq), trace.size),
            noverlap=min(int(sfreq), max(trace.size - 1, 0)),
        )
        keep = (freqs >= fmin) & (freqs <= fmax)
        power = 10 * np.log10(psd[keep] + np.finfo(float).eps)
        axis.plot(freqs[keep], power, color="#b71c1c", linewidth=0.9)
        axis.axvspan(8, 12, color="#64b5f6", alpha=0.16)
        axis.axvspan(13, 30, color="#81c784", alpha=0.12)
        axis.axvline(60, color="0.35", linewidth=0.7, linestyle="--")
        axis.set_title(f"IC {component_idx}", fontsize=8)
        axis.tick_params(labelsize=7)
        axis.grid(color="0.9", linewidth=0.5)

    fig.suptitle(f"{subject_id} ICA component PSD, {fmin:g}-{fmax:g} Hz", fontsize=12)
    fig.supxlabel("Frequency (Hz)", fontsize=10)
    fig.supylabel("Power (dB)", fontsize=10)
    fig.savefig(figure_dir / "ica_psd.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
