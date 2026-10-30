"""Compute whole-recording symmetric 14-ROI HC connectivity matrices."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fc_pipeline_v2.config import load_config
from fc_pipeline_v2.connectivity import fisher_r_to_z
from fc_pipeline_v2.corrected import NETWORK_ORDER, network_features, prepare_segments, symmetric_fc
from fc_pipeline_v2.output_paths import corrected_output_root, ensure_participant_output_paths


def identity(path: Path):
    match = re.match(r"(.+?)_(HC\d+)_(perturbation|non_perturbation)_signed_rois14", path.stem)
    if not match:
        raise ValueError(f"Cannot parse {path.name}")
    return match.groups()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--subject", help="Optional participant filter, e.g. 101")
    args = parser.parse_args()

    cfg = load_config(args.config)
    root = corrected_output_root(cfg)
    if args.subject:
        files = sorted(ensure_participant_output_paths(cfg, args.subject)["roi_timeseries"].glob("*_signed_rois14.npz"))
    else:
        files = sorted(root.glob("*/03_roi_timeseries/*_signed_rois14.npz"))
    if not files:
        requested = f" for participant {args.subject}" if args.subject else ""
        raise FileNotFoundError(f"No 14-ROI inputs found{requested} under {root}")

    settings = cfg.get("corrected_fc", {})
    bands = {"broadband": None, **cfg.get("frequency_bands", {})}
    envelope_hz = float(settings.get("symmetric_envelope_hz", 10))
    rows_by_subject = {}
    plot_records = []
    for file_path in files:
        subject, hc, condition = identity(file_path)
        output = ensure_participant_output_paths(cfg, subject)["matrices"]
        group = next(
            (name for name, ids in cfg.get("groups", {}).items() if subject in ids),
            "unknown",
        )
        with np.load(file_path) as data:
            signals = data["signed_tc14"]
            sfreq = float(data["sfreq"])
            starts = data["segment_starts"]
            stops = data["segment_stops"]
            roi_names = data["roi_names"]
        for band_name, limits in bands.items():
            trim = 0 if limits is None else float(cfg["filtering"]["edge_trim_seconds"])
            parts = prepare_segments(
                signals,
                starts,
                stops,
                sfreq,
                limits,
                trim,
                int(cfg["filtering"]["order"]),
            )
            block = max(1, int(round(sfreq / envelope_hz)))
            parts = [part for part in parts if part.shape[1] >= block]
            if not parts:
                raise ValueError(
                    f"No segment long enough for {band_name} envelope smoothing in {file_path.name}"
                )
            matrix, residual = symmetric_fc(parts, sfreq=sfreq, envelope_hz=envelope_hz)
            if (
                not np.isfinite(matrix).all()
                or not np.allclose(matrix, matrix.T, atol=1e-6)
                or not np.allclose(np.diag(matrix), 1, atol=1e-6)
            ):
                raise ValueError(f"Invalid 14-ROI matrix for {file_path.name} {band_name}")
            fisher_z = fisher_r_to_z(matrix)
            stem = f"{subject}_{hc}_{condition}_{band_name}_fc14"
            np.savez_compressed(
                output / f"{stem}.npz",
                fc14_signed=matrix,
                fc14_fisher_z=fisher_z,
                roi_names=roi_names,
                sfreq=sfreq,
                envelope_hz_target=envelope_hz,
                envelope_method="mne_fft_resample_per_segment",
                input_timeseries_file=str(file_path),
                n_segments=len(parts),
                clean_seconds_used=sum(part.shape[1] for part in parts) / sfreq,
                orthogonality_residual=residual,
            )
            pd.DataFrame(matrix, index=roi_names, columns=roi_names).to_csv(
                output / f"{stem}_r.csv"
            )
            pd.DataFrame(fisher_z, index=roi_names, columns=roi_names).to_csv(
                output / f"{stem}_fisher_z.csv"
            )
            rows_by_subject.setdefault(subject, []).append(
                {
                    "subject": subject,
                    "group": group,
                    "hc": hc,
                    "condition": condition,
                    "band": band_name,
                    "envelope_hz_target": envelope_hz,
                    "envelope_method": "mne_fft_resample_per_segment",
                    "clean_seconds_used": sum(part.shape[1] for part in parts) / sfreq,
                    "n_segments": len(parts),
                    "orthogonality_residual": residual,
                    **network_features(matrix, np.array(NETWORK_ORDER * 2)),
                }
            )
            plot_records.append(
                {
                    "subject": subject,
                    "hc": hc,
                    "band": band_name,
                    "matrix": matrix,
                    "roi_names": roi_names,
                }
            )
            print(f"Saved {stem}: symmetric 14x14 FC")
    for subject, rows in rows_by_subject.items():
        paths = ensure_participant_output_paths(cfg, subject)
        table_path = paths["tables"] / f"{subject}_recording_network_features_fisher_z.csv"
        pd.DataFrame(rows).to_csv(table_path, index=False)
        selected = [record for record in plot_records if record["subject"] == subject]
        plot_participant_summaries(selected, paths["figures"])
        print(f"Done. Participant {subject} results saved to {paths['static_fc']}")


def plot_participant_summaries(records, output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    bands = ["broadband", "alpha", "beta"]
    hcs = ["HC1", "HC2", "HC3", "HC4"]
    for subject in sorted({record["subject"] for record in records}):
        selected = [record for record in records if record["subject"] == subject]
        lookup = {(record["hc"], record["band"]): record for record in selected}
        if not all((hc, band) in lookup for hc in hcs for band in bands):
            continue
        roi_names = lookup[(hcs[0], bands[0])]["roi_names"]
        short_names = [
            name.replace("LH_", "L-").replace("RH_", "R-")
            for name in roi_names
        ]
        limits = {}
        off_diagonal = ~np.eye(14, dtype=bool)
        for band in bands:
            values = np.concatenate(
                [np.abs(lookup[(hc, band)]["matrix"][off_diagonal]) for hc in hcs]
            )
            limits[band] = max(0.1, float(np.percentile(values, 99)))

        fig, axes = plt.subplots(4, 3, figsize=(13, 15), constrained_layout=True)
        images = {}
        for row, hc in enumerate(hcs):
            for col, band in enumerate(bands):
                ax = axes[row, col]
                matrix = lookup[(hc, band)]["matrix"].copy()
                np.fill_diagonal(matrix, np.nan)
                images[band] = ax.imshow(
                    matrix,
                    cmap="RdBu_r",
                    vmin=-limits[band],
                    vmax=limits[band],
                    interpolation="nearest",
                )
                ax.axhline(6.5, color="black", linewidth=1.2)
                ax.axvline(6.5, color="black", linewidth=1.2)
                if row == 0:
                    ax.set_title(f"{band.capitalize()} (r, +/-{limits[band]:.2f})")
                if col == 0:
                    ax.set_ylabel(hc, fontsize=11, fontweight="bold")
                if row == len(hcs) - 1:
                    ax.set_xticks(range(14), short_names, rotation=90, fontsize=7)
                else:
                    ax.set_xticks([])
                if col == 0:
                    ax.set_yticks(range(14), short_names, fontsize=7)
                else:
                    ax.set_yticks([])
        for col, band in enumerate(bands):
            fig.colorbar(images[band], ax=axes[:, col], shrink=0.72, label="Envelope correlation (r)")
        fig.suptitle(
            f"Participant {subject}: symmetric 14-ROI functional connectivity",
            fontsize=15,
            fontweight="bold",
        )
        target = output / f"{subject}_fc14_summary.png"
        fig.savefig(target, dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved {target.name}")


if __name__ == "__main__":
    main()
