"""Project cleaned HC EEG to signed 14-ROI source signals in bounded chunks."""
from __future__ import annotations

import argparse
import functools
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fc_pipeline_v2.config import load_config, resolve_path
from fc_pipeline_v2.corrected import NETWORK_ORDER, continuous_segments
from fc_pipeline_v2.output_paths import corrected_output_root, ensure_participant_output_paths


def build_network_rois(mne, subjects_dir: Path, parc: str):
    labels = mne.read_labels_from_annot(
        "fsaverage", parc=parc, subjects_dir=str(subjects_dir)
    )
    labels = [
        label
        for label in labels
        if not label.name.startswith("Background")
        and "unknown" not in label.name.lower()
    ]
    groups = {}
    for label in labels:
        parts = label.name.split("_")
        groups.setdefault((parts[1], parts[2]), []).append(label)

    rois = []
    for hemi in ["LH", "RH"]:
        for network in NETWORK_ORDER:
            members = groups[(hemi, network)]
            roi = functools.reduce(lambda left, right: left + right, members)
            roi.name = f"{hemi}_{network}"
            rois.append(roi)
    return rois


def infer_subject(path: Path) -> str:
    match = re.match(r"(.+?)_HC\d+_", path.name, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Cannot infer subject from {path.name}")
    return match.group(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--subject", help="Optional participant filter, e.g. 101")
    parser.add_argument("--include-parcels", action="store_true", help="Also extract signed Schaefer-100 signals from the same inverse chunks")
    parser.add_argument(
        "--chunk-seconds",
        type=float,
        default=2.0,
        help="Bounded inverse-projection chunk size; 2 s uses about 0.35 GB for ico5.",
    )
    args = parser.parse_args()
    if not np.isfinite(args.chunk_seconds) or args.chunk_seconds <= 0:
        parser.error('--chunk-seconds must be positive and finite')

    import mne
    from mne.minimum_norm import (
        apply_inverse_raw,
        prepare_inverse_operator,
        read_inverse_operator,
    )

    cfg = load_config(args.config)
    source_cfg = cfg["source_localization"]
    subjects_dir = resolve_path(cfg, cfg["paths"]["subjects_dir"])
    root = corrected_output_root(cfg)

    parc = cfg["parcel_extraction"].get(
        "parc", "Schaefer2018_100Parcels_7Networks_order"
    )
    rois = build_network_rois(mne, subjects_dir, parc)
    roi_names = np.array([roi.name for roi in rois])
    parcels = []
    if args.include_parcels:
        parcels = [label for label in mne.read_labels_from_annot(
            "fsaverage", parc=parc, subjects_dir=str(subjects_dir))
            if not label.name.startswith("Background") and "unknown" not in label.name.lower()]
        parcels.sort(key=lambda label: (label.name.split('_')[1],
                     NETWORK_ORDER.index(label.name.split('_')[2]), label.name))
        if len(parcels) != 100:
            raise ValueError(f"Expected 100 parcels, got {len(parcels)}")
    pattern = str(source_cfg.get("input_glob", "*_montage_raw.fif"))
    if args.subject:
        files = sorted(ensure_participant_output_paths(cfg, args.subject)["montage_aligned"].glob(pattern))
    else:
        files = sorted(root.glob(f"*/01_block_level_eeg/montage_aligned/{pattern}"))
    if not files:
        requested = f" for participant {args.subject}" if args.subject else ""
        raise FileNotFoundError(f"No matching montage-aligned FIF files found{requested} under {root}")

    method = str(source_cfg.get("method", "eLORETA"))
    lambda2 = 1.0 / float(source_cfg.get("snr", 3.0)) ** 2
    exclude_channels = list(source_cfg.get("exclude_channels", []))

    prepared_by_subject = {}
    for file_path in files:
        subject = infer_subject(file_path)
        paths = ensure_participant_output_paths(cfg, subject)
        inverse_path = paths["source_model"] / f"{subject}_common_inverse_operator.fif"
        if not inverse_path.exists():
            raise FileNotFoundError(
                f"Missing {inverse_path}; run step 02 far enough to create the common inverse."
            )
        if subject not in prepared_by_subject:
            inverse = read_inverse_operator(inverse_path)
            prepared_by_subject[subject] = prepare_inverse_operator(
                inverse, nave=1, lambda2=lambda2, method=method
            )
        inverse = prepared_by_subject[subject]

        raw = mne.io.read_raw_fif(file_path, preload=True, verbose="ERROR")
        drop_existing = [name for name in exclude_channels if name in raw.ch_names]
        if drop_existing:
            raw.drop_channels(drop_existing)
        raw.pick(picks="eeg", exclude=[])
        if bool(source_cfg.get("set_average_reference_projection", True)):
            raw.set_eeg_reference("average", projection=True, verbose="ERROR")
            raw.apply_proj(verbose="ERROR")

        if source_cfg.get('rank_policy')=='data_relative':
            from fc_pipeline_v2.signal_rank import project_numerical_residue
            rank_audit=project_numerical_residue(raw,float(source_cfg.get('rank_relative_tolerance',1e-6)))
            print(f'{subject}: input rank={rank_audit["rank"]}; numerical residue removed={rank_audit["relative_change"]:.3g}',flush=True)

        chunk_samples = max(1, int(round(args.chunk_seconds * raw.info["sfreq"])))
        chunks = []
        parcel_chunks = []
        for start in range(0, raw.n_times, chunk_samples):
            stop = min(raw.n_times, start + chunk_samples)
            stc = apply_inverse_raw(
                raw,
                inverse,
                lambda2,
                method=method,
                pick_ori="normal",
                start=start,
                stop=stop,
                prepared=True,
                verbose="ERROR",
            )
            chunks.append(
                mne.extract_label_time_course(
                    stc, rois, inverse["src"], mode="mean_flip", verbose="ERROR"
                ).astype(np.float32)
            )
            if parcels:
                parcel_chunks.append(mne.extract_label_time_course(
                    stc, parcels, inverse["src"], mode="mean_flip",
                    verbose="ERROR").astype(np.float32))
        signed_tc14 = np.concatenate(chunks, axis=1)
        if signed_tc14.shape != (14, raw.n_times):
            raise ValueError(
                f"Unexpected 14-ROI shape {signed_tc14.shape}; expected (14, {raw.n_times})"
            )

        valid = np.isfinite(raw.get_data(reject_by_annotation="NaN")).all(axis=0)
        boundaries = np.zeros(raw.n_times, dtype=bool)
        boundaries[0] = True
        for onset, description in zip(raw.annotations.onset, raw.annotations.description):
            if "boundary" in str(description).lower() or str(description).lower().startswith("edge"):
                index = int(round((onset - raw.first_time) * raw.info["sfreq"]))
                if 0 <= index < raw.n_times:
                    boundaries[index] = True
        starts, stops = continuous_segments(valid, boundaries)

        stem = file_path.name.replace("_montage_raw.fif", "")
        target = paths["roi_timeseries"] / f"{stem}_signed_rois14.npz"
        np.savez_compressed(
            target,
            signed_tc14=signed_tc14,
            roi_names=roi_names,
            sfreq=float(raw.info["sfreq"]),
            segment_starts=starts,
            segment_stops=stops,
            pick_ori="normal",
            inverse_file=str(inverse_path),
            source_file=str(file_path),
        )
        if parcels:
            np.savez_compressed(
                paths["roi_timeseries"] / f"{stem}_signed_parcels.npz",
                signed_tc100=np.concatenate(parcel_chunks, axis=1),
                parcel_names=np.array([label.name for label in parcels]),
                parcel_network=np.array([label.name.split('_')[2] for label in parcels]),
                signed_tc14=signed_tc14, roi_names=roi_names,
                sfreq=float(raw.info["sfreq"]), segment_starts=starts,
                segment_stops=stops, pick_ori="normal",
                inverse_file=str(inverse_path), source_file=str(file_path))
        print(
            f"Saved {target.name}: {signed_tc14.shape[1] / raw.info['sfreq']:.1f} s, "
            f"{len(starts)} clean segment(s)"
        )


if __name__ == "__main__":
    main()
