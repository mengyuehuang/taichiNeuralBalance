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


def normalize_name(name: str) -> str:
    return name.strip().lower()


def parse_numeric_channel(name: str, prefix: str) -> int | None:
    match = re.fullmatch(rf"{re.escape(prefix)}(\d+)", name.strip(), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def build_numeric_channel_mapping(
    raw_names: list[str],
    montage_names: list[str],
    *,
    prefix: str,
    skipped_numbers: set[int],
) -> dict[str, str]:
    # The sample files arrive as Ch1, Ch2, ..., Ch64 with Ch21 skipped.
    # The old MATLAB code maps those numeric channels to montage labels by
    # order, so we reproduce that mapping here before setting the montage.
    mapping: dict[str, str] = {}
    ordered_raw_names = []
    for name in raw_names:
        number = parse_numeric_channel(name, prefix)
        if number is None:
            return {}
        ordered_raw_names.append((number, name))

    expected_numbers = [number for number in range(1, max(number for number, _ in ordered_raw_names) + 1)]
    expected_numbers = [number for number in expected_numbers if number not in skipped_numbers]
    actual_numbers = [number for number, _ in ordered_raw_names]
    if actual_numbers != expected_numbers:
        return {}
    if len(raw_names) != len(montage_names):
        return {}

    for (_, raw_name), montage_name in zip(ordered_raw_names, montage_names, strict=True):
        mapping[raw_name] = montage_name
    return mapping


def compare_channels(raw_names: list[str], montage_names: list[str], ignore_channels: set[str]) -> dict[str, Any]:
    ignored_norm = {normalize_name(name) for name in ignore_channels}
    raw_lookup = {normalize_name(name): name for name in raw_names if normalize_name(name) not in ignored_norm}
    montage_lookup = {normalize_name(name): name for name in montage_names if normalize_name(name) not in ignored_norm}

    raw_norm = set(raw_lookup)
    montage_norm = set(montage_lookup)
    matched_norm = raw_norm & montage_norm

    return {
        "matched_channels": sorted(raw_lookup[name] for name in matched_norm),
        "missing_from_montage": sorted(raw_lookup[name] for name in raw_norm - montage_norm),
        "extra_in_montage": sorted(montage_lookup[name] for name in montage_norm - raw_norm),
    }


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    if not rows:
        return
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check whether exported block FIF channel names match the custom .sfp montage."
    )
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    block_dir = resolve_path(config, config["paths"]["block_data_dir"])
    montage_path = resolve_path(config, config["paths"]["montage_path"])
    report_path = block_dir / "montage_channel_check.csv"

    check_cfg = config.get("montage_check", {})
    block_glob = str(check_cfg.get("block_file_glob", "*.fif"))
    ignore_channels = set(check_cfg.get("ignore_channels", []))
    should_rename_numeric = bool(check_cfg.get("rename_numeric_channels_from_montage_order", True))
    numeric_prefix = str(check_cfg.get("numeric_channel_prefix", "Ch"))
    skipped_numbers = {int(value) for value in check_cfg.get("skip_numeric_channels", [])}
    write_aligned = bool(check_cfg.get("write_montage_aligned_fif", True))
    aligned_dir = block_dir / str(check_cfg.get("montage_aligned_subdir", "montage_aligned"))
    if write_aligned:
        aligned_dir.mkdir(parents=True, exist_ok=True)

    import mne

    montage = mne.channels.read_custom_montage(montage_path)
    montage_names = list(montage.ch_names)
    files = sorted(block_dir.glob(block_glob))
    if not files:
        raise FileNotFoundError(f"No FIF files found in {block_dir} with pattern {block_glob!r}")

    rows: list[dict[str, Any]] = []
    for file_path in files:
        eeg = read_fif(file_path)
        original_names = list(eeg.info["ch_names"])
        original_comparison = compare_channels(original_names, montage_names, ignore_channels)

        rename_status = "not_requested"
        rename_mapping = {}
        if should_rename_numeric and original_comparison["missing_from_montage"]:
            # If nothing matches the montage, try the known Ch# -> montage-order
            # conversion before calling this a failed montage.
            rename_mapping = build_numeric_channel_mapping(
                original_names,
                montage_names,
                prefix=numeric_prefix,
                skipped_numbers=skipped_numbers,
            )
            if rename_mapping:
                eeg.rename_channels(rename_mapping)
                rename_status = "renamed_from_numeric_order"
            else:
                rename_status = "numeric_mapping_not_available"

        final_names = list(eeg.info["ch_names"])
        comparison = compare_channels(final_names, montage_names, ignore_channels)

        status = "ok"
        if comparison["missing_from_montage"]:
            status = "missing_montage_channels"

        output_file = ""
        montage_status = "not_set"
        if not comparison["missing_from_montage"]:
            # Save a clean copy for source localization so downstream scripts do
            # not need to repeat the channel rename/montage work.
            eeg.set_montage(montage, match_case=False, on_missing="raise")
            montage_status = "set"
            if write_aligned:
                suffix = "-epo.fif" if "Epochs" in type(eeg).__name__ else "_raw.fif"
                aligned_output_path = aligned_dir / file_path.name.replace(suffix, f"_montage{suffix}")
                eeg.save(aligned_output_path, overwrite=True)
                output_file = str(aligned_output_path)

        rows.append(
            {
                "file": str(file_path),
                "status": status,
                "rename_status": rename_status,
                "montage_status": montage_status,
                "n_data_channels": len(final_names),
                "n_montage_channels": len(montage_names),
                "n_original_matched": len(original_comparison["matched_channels"]),
                "n_original_missing_from_montage": len(original_comparison["missing_from_montage"]),
                "n_matched": len(comparison["matched_channels"]),
                "n_missing_from_montage": len(comparison["missing_from_montage"]),
                "n_extra_in_montage": len(comparison["extra_in_montage"]),
                "n_renamed_channels": len(rename_mapping),
                "missing_from_montage": ";".join(comparison["missing_from_montage"]),
                "extra_in_montage": ";".join(comparison["extra_in_montage"]),
                "exported_montage_aligned_file": output_file,
            }
        )
        print(
            f"{file_path.name}: status={status}, rename={rename_status}, "
            f"matched={len(comparison['matched_channels'])}, "
            f"missing={len(comparison['missing_from_montage'])}, extra={len(comparison['extra_in_montage'])}"
        )

    write_csv(rows, report_path)
    print(f"Done. Montage/channel report saved to {report_path}")


if __name__ == "__main__":
    main()
