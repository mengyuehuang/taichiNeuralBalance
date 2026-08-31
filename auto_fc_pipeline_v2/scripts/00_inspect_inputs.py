from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fc_pipeline_v2.config import load_config, resolve_path
from fc_pipeline_v2.io import (
    find_files,
    infer_block_name,
    infer_subject_id,
    read_backprojected_eeglab_set,
    summarize_mne_object,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="List candidate backprojected files and infer subject/block labels.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--read-eeglab", action="store_true", help="Try reading each .set file with MNE and print basic metadata.")
    args = parser.parse_args()

    config = load_config(args.config)
    input_dir = resolve_path(config, config["paths"]["backprojected_dir"])
    files = find_files(input_dir, config["inputs"]["backprojected_glob"])
    print(f"Found {len(files)} candidate files in {input_dir}")

    for file_path in files:
        try:
            subject = infer_subject_id(file_path, config["naming"]["subject_regex"])
        except ValueError as exc:
            subject = f"UNRESOLVED ({exc})"
        try:
            block = infer_block_name(file_path, config["naming"]["block_patterns"])
        except ValueError as exc:
            block = f"UNRESOLVED ({exc})"
        print(f"{file_path.name}\tsubject={subject}\tblock={block}")
        if args.read_eeglab and file_path.suffix.lower() == ".set":
            eeg = read_backprojected_eeglab_set(file_path)
            summary = summarize_mne_object(eeg)
            print(
                f"  type={summary['type']} sfreq={summary['sfreq']} "
                f"n_channels={summary['n_channels']} "
                f"n_times={summary.get('n_times', 'NA')} "
                f"n_epochs={summary.get('n_epochs', 'NA')}"
            )


if __name__ == "__main__":
    main()
