from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fc_pipeline_v2.config import load_config, resolve_path


def infer_subject_and_hc(file_path: Path) -> tuple[str, str]:
    match = re.search(r"(?P<subject>\d{3,}).*?(?P<hc>HC\d+)", file_path.stem, flags=re.IGNORECASE)
    if not match:
        return "", ""
    return match.group("subject"), match.group("hc").upper()


def read_fif(file_path: Path) -> Any:
    import mne

    try:
        return mne.io.read_raw_fif(file_path, preload=False, verbose="ERROR")
    except Exception as raw_error:
        try:
            return mne.read_epochs(file_path, preload=False, verbose="ERROR")
        except Exception as epochs_error:
            raise RuntimeError(
                f"Could not read {file_path} as MNE Raw or Epochs. "
                f"Raw error: {raw_error}; Epochs error: {epochs_error}"
            ) from epochs_error


def count_annotations(eeg: Any, pattern: str) -> int:
    annotations = getattr(eeg, "annotations", None)
    if annotations is None:
        return 0
    return sum(1 for desc in annotations.description if pattern.lower() in str(desc).lower())


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    if not rows:
        return
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lightweight QC for montage-aligned FIF files before source localization."
    )
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    block_dir = resolve_path(config, config["paths"]["block_data_dir"])
    check_cfg = config.get("montage_check", {})
    aligned_dir = block_dir / str(check_cfg.get("montage_aligned_subdir", "montage_aligned"))
    files = sorted(aligned_dir.glob("*_montage_raw.fif")) + sorted(aligned_dir.glob("*_montage-epo.fif"))
    if not files:
        raise FileNotFoundError(f"No montage-aligned FIF files found in {aligned_dir}")

    non_source_channels = {
        "GND",
        "LHEye",
        "RHEye",
        "RVEye",
        "Lneck",
        "Rneck",
    }

    rows: list[dict[str, Any]] = []
    for file_path in files:
        eeg = read_fif(file_path)
        info = eeg.info
        subject, hc_label = infer_subject_and_hc(file_path)
        channel_names = list(info["ch_names"])
        # This is only a QC count. It does not remove channels; the source
        # localization script handles removal if the lab confirms it.
        data_channels = [name for name in channel_names if name not in non_source_channels]
        present_non_source = [name for name in channel_names if name in non_source_channels]
        loc_available = 0
        for ch in info["chs"]:
            loc = ch.get("loc")
            if loc is not None and len(loc) >= 3 and not all(float(value) == 0.0 for value in loc[:3]):
                loc_available += 1

        row = {
            "file": str(file_path),
            "subject": subject,
            "hc_label": hc_label,
            "mne_type": type(eeg).__name__,
            "sfreq": float(info["sfreq"]),
            "n_channels_total": len(channel_names),
            "n_probable_source_channels": len(data_channels),
            "n_non_source_channels_present": len(present_non_source),
            "non_source_channels_present": ";".join(present_non_source),
            "n_channels_with_nonzero_location": loc_available,
            "n_bad_channels_marked": len(info.get("bads", [])),
            "bad_channels_marked": ";".join(info.get("bads", [])),
            "n_boundary_annotations": count_annotations(eeg, "boundary"),
            "first_channels": ";".join(channel_names[:10]),
        }
        rows.append(row)
        print(
            f"{file_path.name}: sfreq={row['sfreq']}, total={row['n_channels_total']}, "
            f"source_like={row['n_probable_source_channels']}, "
            f"non_source={row['non_source_channels_present'] or 'none'}, "
            f"locations={row['n_channels_with_nonzero_location']}, "
            f"boundaries={row['n_boundary_annotations']}, bads={row['n_bad_channels_marked']}"
        )

    output_path = aligned_dir / "aligned_fif_qc.csv"
    write_csv(rows, output_path)
    print(f"Done. QC report saved to {output_path}")


if __name__ == "__main__":
    main()
