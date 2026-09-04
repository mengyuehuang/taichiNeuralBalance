from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

NUMBA_CACHE_DIR = ROOT.parent / ".numba_cache"
NUMBA_CACHE_DIR.mkdir(exist_ok=True)
os.environ.setdefault("NUMBA_CACHE_DIR", str(NUMBA_CACHE_DIR))
MNE_FAKE_HOME = ROOT.parent / ".mne_fake_home"
MNE_FAKE_HOME.mkdir(exist_ok=True)
os.environ.setdefault("_MNE_FAKE_HOME_DIR", str(MNE_FAKE_HOME))

from fc_pipeline.config import load_config, resolve_path
from fc_pipeline.io import drop_configured_channels, find_raw_files, infer_subject_id, read_raw
from fc_pipeline.montage import apply_hernandez_montage
from fc_pipeline.preica import annotate_noisy_fixed_chunks


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Yang-inspired pre-ICA preprocessing: load raw EEG, montage, filter, mark noisy 1-sec chunks."
    )
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    args = parser.parse_args()

    config = load_config(args.config)
    raw_dir = resolve_path(config, config["paths"]["raw_data_dir"])
    output_root = resolve_path(config, config["paths"]["output_dir"])
    filtered_dir = output_root / "Filtered"
    preica_dir = output_root / "PreICA"
    qc_dir = output_root / "PreICA_QC"
    montage_path = resolve_path(config, config["paths"]["montage_path"])
    filtered_dir.mkdir(parents=True, exist_ok=True)
    preica_dir.mkdir(parents=True, exist_ok=True)
    qc_dir.mkdir(parents=True, exist_ok=True)

    raw_files = find_raw_files(raw_dir, config["raw"]["file_glob"])
    print(f"Files to process: {len(raw_files)}")
    if not raw_files:
        raise FileNotFoundError(f"No files found in {raw_dir} matching {config['raw']['file_glob']!r}")

    for raw_file in raw_files:
        subject_id = infer_subject_id(raw_file, config["naming"]["subject_regex"])
        print(f"\nProcessing {subject_id}: {raw_file}")

        raw = read_raw(raw_file, config["raw"]["file_format"], preload=config["raw"].get("preload", True))
        drop_configured_channels(raw, config["raw"])
        apply_hernandez_montage(raw, montage_path, config["channels"])

        # Yang filters before ICA. We keep the same default band in config:
        # 1 Hz high-pass, 55 Hz low-pass, and 60 Hz line-noise removal.
        filtering = config["filtering"]
        raw.filter(l_freq=filtering.get("l_freq"), h_freq=filtering.get("h_freq"))
        notch_freqs = filtering.get("notch_freqs", [])
        if notch_freqs:
            raw.notch_filter(freqs=notch_freqs)

        filtered_path = filtered_dir / f"{subject_id}{config['naming']['filtered_suffix']}"
        raw.save(filtered_path, overwrite=True)
        print(f"Saved filtered raw: {filtered_path}")

        # Yang creates 1-second epochs to find noisy periods before ICA. Here we
        # annotate suspicious chunks instead of silently concatenating around
        # deleted pieces, because later FC analysis needs discontinuities handled
        # explicitly.
        if config.get("preica_qc", {}).get("enabled", True):
            qc_result = annotate_noisy_fixed_chunks(raw, config["preica_qc"])
            if len(qc_result.annotations):
                raw.set_annotations(raw.annotations + qc_result.annotations)
            qc_path = qc_dir / f"{subject_id}_preica_chunk_qc.csv"
            qc_result.report.to_csv(qc_path, index=False)
            print(f"Saved pre-ICA chunk QC: {qc_path}")
            print(f"Auto-marked noisy chunks: {len(qc_result.annotations)}")

        preica_path = preica_dir / f"{subject_id}{config['naming']['preica_suffix']}"
        raw.save(preica_path, overwrite=True)
        print(f"Saved preICA raw with annotations: {preica_path}")

    print("\nPreprocessing complete.")


if __name__ == "__main__":
    main()
