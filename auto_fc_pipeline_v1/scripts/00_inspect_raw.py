from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from fc_pipeline.config import load_config, resolve_path


TASK_RE = re.compile(r"^TCOA_(?P<subject>\d+)_(?P<task>.+)$", re.IGNORECASE)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect BrainVision raw files before running preprocessing."
    )
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search raw_data_dir recursively for .vhdr files.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    raw_dir = resolve_path(config, config["paths"]["raw_data_dir"])
    output_root = resolve_path(config, config["paths"]["output_dir"])
    output_root.mkdir(parents=True, exist_ok=True)

    pattern = "**/*.vhdr" if args.recursive else config["raw"].get("file_glob", "*.vhdr")
    vhdr_files = sorted(raw_dir.glob(pattern))
    if not vhdr_files:
        raise FileNotFoundError(f"No .vhdr files found in {raw_dir} using {pattern!r}")

    rows = [inspect_vhdr(path) for path in vhdr_files]
    inventory = pd.DataFrame(rows)
    inventory_path = output_root / "raw_inventory.csv"
    inventory.to_csv(inventory_path, index=False)

    hc_summary = build_hc_summary(inventory)
    hc_path = output_root / "hc_block_summary.csv"
    hc_summary.to_csv(hc_path, index=False)

    print(f"Found {len(inventory)} BrainVision header files.")
    print_group_summary(inventory)
    print("\nHC block summary:")
    for _, row in hc_summary.iterrows():
        status = "complete" if row["has_all_hc"] else f"missing {row['missing_hc']}"
        print(f"  {row['subject']}: {status}; tasks={row['tasks']}")
    print(f"\nRaw inventory saved to: {inventory_path}")
    print(f"HC summary saved to: {hc_path}")


def inspect_vhdr(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    values = parse_key_values(text)
    channel_labels = parse_channel_labels(text)
    match = TASK_RE.match(path.stem)
    subject = match.group("subject") if match else ""
    task = match.group("task").upper() if match else path.stem
    sampling_interval_us = float(values.get("SamplingInterval", "nan"))
    sfreq = 1_000_000.0 / sampling_interval_us
    eeg_size = path.with_suffix(".eeg").stat().st_size if path.with_suffix(".eeg").exists() else 0

    return {
        "subject": subject,
        "task": task,
        "vhdr_file": str(path),
        "data_file": values.get("DataFile", ""),
        "marker_file": values.get("MarkerFile", ""),
        "n_channels": int(values.get("NumberOfChannels", 0)),
        "sampling_interval_us": sampling_interval_us,
        "sfreq_hz": sfreq,
        "duration_seconds_est": eeg_size / (int(values.get("NumberOfChannels", 1)) * 2 * sfreq),
        "channel_21_label": channel_labels.get(21, ""),
        "aux_channels": ";".join(
            label for idx, label in channel_labels.items() if label.lower().startswith("aux")
        ),
        "first_channels": ";".join(channel_labels[idx] for idx in sorted(channel_labels)[:12]),
        "last_channels": ";".join(channel_labels[idx] for idx in sorted(channel_labels)[-8:]),
    }


def parse_key_values(lines: list[str]) -> dict[str, str]:
    values = {}
    for line in lines:
        if "=" in line and not line.startswith("Ch"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def parse_channel_labels(lines: list[str]) -> dict[int, str]:
    labels = {}
    for line in lines:
        match = re.match(r"^Ch(?P<idx>\d+)=(?P<label>[^,]*)", line)
        if match:
            labels[int(match.group("idx"))] = match.group("label")
    return labels


def build_hc_summary(inventory: pd.DataFrame) -> pd.DataFrame:
    expected = {"HC1", "HC2", "HC3", "HC4"}
    rows = []
    for subject, group in inventory.groupby("subject"):
        tasks = sorted(set(group["task"]))
        missing = sorted(expected - set(tasks))
        rows.append(
            {
                "subject": subject,
                "has_all_hc": not missing,
                "missing_hc": ",".join(missing),
                "tasks": ",".join(tasks),
            }
        )
    return pd.DataFrame(rows).sort_values("subject")


def print_group_summary(inventory: pd.DataFrame) -> None:
    grouped = (
        inventory.groupby(["n_channels", "sampling_interval_us", "sfreq_hz"])
        .size()
        .reset_index(name="count")
    )
    print("\nFormat summary:")
    for _, row in grouped.iterrows():
        print(
            "  "
            f"{int(row['count'])} files: "
            f"{int(row['n_channels'])} channels, "
            f"SamplingInterval={row['sampling_interval_us']:.0f} us, "
            f"sfreq={row['sfreq_hz']:.1f} Hz"
        )


if __name__ == "__main__":
    main()
