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

import mne
import pandas as pd

from fc_pipeline.config import load_config, resolve_path
from fc_pipeline.io import infer_subject_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect bad channels with MNE LOF and save bad_channels.csv.")
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    args = parser.parse_args()

    config = load_config(args.config)
    filtered_dir = resolve_path(config, config["paths"]["output_dir"]) / "Filtered"
    output_csv = resolve_path(config, config["paths"]["output_dir"]) / "bad_channels.csv"
    exclude = config["channels"].get("bad_detection_exclude", [])

    rows = []
    for fif_file in sorted(filtered_dir.glob("*.fif")):
        subject_id = infer_subject_id(fif_file, config["naming"]["subject_regex"])
        print(f"Detecting bad channels for {subject_id}")
        raw = mne.io.read_raw_fif(fif_file, preload=True)
        picks = mne.pick_channels(raw.ch_names, include=raw.ch_names, exclude=exclude)
        bads = mne.preprocessing.find_bad_channels_lof(raw, picks=picks)
        rows.append({"Subject": subject_id, "Bad Channels": bads})
        print(f"{subject_id}: {bads}")

    pd.DataFrame(rows).to_csv(output_csv, index=False)
    print(f"Saved: {output_csv}")


if __name__ == "__main__":
    main()
