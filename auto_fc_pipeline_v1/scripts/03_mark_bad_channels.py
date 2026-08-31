from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import mne
import pandas as pd

from fc_pipeline.config import load_config, resolve_path
from fc_pipeline.io import infer_subject_id


def parse_bad_channels(value: object) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return []
    parsed = ast.literal_eval(value)
    return [str(ch) for ch in parsed]


def main() -> None:
    parser = argparse.ArgumentParser(description="Mark bad channels from bad_channels.csv and save FIF files.")
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    args = parser.parse_args()

    config = load_config(args.config)
    output_root = resolve_path(config, config["paths"]["output_dir"])
    filtered_dir = output_root / "Filtered"
    marked_dir = output_root / "Bad_Channels_Marked"
    marked_dir.mkdir(parents=True, exist_ok=True)

    bad_csv = output_root / "bad_channels.csv"
    bad_df = pd.read_csv(bad_csv)
    bad_map = {
        str(row["Subject"]): parse_bad_channels(row["Bad Channels"])
        for _, row in bad_df.iterrows()
    }

    for fif_file in sorted(filtered_dir.glob("*.fif")):
        subject_id = infer_subject_id(fif_file, config["naming"]["subject_regex"])
        raw = mne.io.read_raw_fif(fif_file, preload=True)
        raw.info["bads"] = [ch for ch in bad_map.get(subject_id, []) if ch in raw.ch_names]
        output_path = marked_dir / f"{subject_id}_badchannels_raw.fif"
        raw.save(output_path, overwrite=True)
        print(f"{subject_id}: marked {raw.info['bads']} -> {output_path}")


if __name__ == "__main__":
    main()

