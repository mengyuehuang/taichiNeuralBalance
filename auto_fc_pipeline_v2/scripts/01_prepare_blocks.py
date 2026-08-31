from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from fc_pipeline_v2.config import load_config, resolve_path
from fc_pipeline_v2.io import (
    find_files,
    infer_block_name,
    infer_subject_id,
    read_backprojected_eeglab_set,
    summarize_mne_object,
)


def infer_hc_label(file_path: Path) -> str:
    match = re.search(r"HC\d+", file_path.stem, flags=re.IGNORECASE)
    return match.group(0).upper() if match else "unknown_hc"


def get_boundary_rows(eeg: Any, *, source_file: Path, subject: str, block: str) -> list[dict[str, Any]]:
    # Boundary annotations mark possible discontinuities. We report them before
    # any filtering so we do not accidentally filter across a break in the data.
    rows: list[dict[str, Any]] = []
    annotations = getattr(eeg, "annotations", None)
    if annotations is None:
        return rows

    for onset, duration, description in zip(
        annotations.onset,
        annotations.duration,
        annotations.description,
        strict=False,
    ):
        desc = str(description)
        if "boundary" not in desc.lower():
            continue
        rows.append(
            {
                "source_file": str(source_file),
                "subject": subject,
                "block": block,
                "onset_seconds": float(onset),
                "duration_seconds": float(duration),
                "description": desc,
            }
        )
    return rows


def save_eeg_object(eeg: Any, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(eeg, "events"):
        eeg.save(output_path, overwrite=True)
    else:
        eeg.save(output_path, overwrite=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Read cleaned/backprojected EEGLAB files, report discontinuity "
            "markers, and export block-level files for later source localization."
        )
    )
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    input_dir = resolve_path(config, config["paths"]["backprojected_dir"])
    block_dir = resolve_path(config, config["paths"]["block_data_dir"])
    block_dir.mkdir(parents=True, exist_ok=True)

    files = find_files(input_dir, config["inputs"]["backprojected_glob"])
    if not files:
        raise FileNotFoundError(f"No backprojected files found in {input_dir}")

    prep_cfg = config.get("prepare_blocks", {})
    export_fif = bool(prep_cfg.get("export_fif", True))
    boundary_policy = str(prep_cfg.get("boundary_policy", "report_only"))

    manifest_rows: list[dict[str, Any]] = []
    boundary_rows: list[dict[str, Any]] = []

    for file_path in files:
        subject = infer_subject_id(file_path, config["naming"]["subject_regex"])
        block = infer_block_name(file_path, config["naming"]["block_patterns"])
        hc_label = infer_hc_label(file_path)
        print(f"Reading subject={subject}, block={block}, file={file_path.name}")

        eeg = read_backprojected_eeglab_set(file_path)
        summary = summarize_mne_object(eeg)
        current_boundary_rows = get_boundary_rows(eeg, source_file=file_path, subject=subject, block=block)
        boundary_rows.extend(current_boundary_rows)

        # Keep this step format-only: save MNE-readable files, but do not
        # filter, epoch, or source-localize yet.
        output_file = ""
        if export_fif:
            if "Epochs" in summary["type"]:
                output_path = block_dir / f"{subject}_{hc_label}_{block}-epo.fif"
            else:
                output_path = block_dir / f"{subject}_{hc_label}_{block}_raw.fif"
            save_eeg_object(eeg, output_path)
            output_file = str(output_path)

        if current_boundary_rows and boundary_policy == "error":
            raise RuntimeError(
                f"{file_path.name} contains {len(current_boundary_rows)} boundary annotations. "
                "Set prepare_blocks.boundary_policy to report_only if this is expected."
            )

        manifest_rows.append(
            {
                "source_file": str(file_path),
                "subject": subject,
                "hc_label": hc_label,
                "block": block,
                "mne_type": summary["type"],
                "sfreq": summary["sfreq"],
                "n_channels": summary["n_channels"],
                "n_times": summary.get("n_times", ""),
                "duration_seconds": summary.get("duration_seconds", ""),
                "n_epochs": summary.get("n_epochs", ""),
                "n_bad_channels_marked": len(summary["bads"]),
                "bad_channels_marked": ";".join(summary["bads"]),
                "boundary_count": len(current_boundary_rows),
                "exported_file": output_file,
            }
        )
        print(
            f"  type={summary['type']} sfreq={summary['sfreq']} "
            f"channels={summary['n_channels']} boundaries={len(current_boundary_rows)}"
        )

    manifest_path = block_dir / "block_manifest.csv"
    pd.DataFrame(manifest_rows).to_csv(manifest_path, index=False)

    boundary_path = block_dir / "boundary_events.csv"
    pd.DataFrame(boundary_rows).to_csv(boundary_path, index=False)

    print(f"Done. Manifest saved to {manifest_path}")
    print(f"Boundary report saved to {boundary_path}")
    if boundary_rows:
        print(
            "Boundary annotations were found. Do not band-pass filter across those "
            "points unless the team agrees on the discontinuity handling plan."
        )


if __name__ == "__main__":
    main()
