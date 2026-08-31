from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd

from fc_pipeline_v2.config import load_config, resolve_path
from fc_pipeline_v2.connectivity import compute_static_amplitude_connectivity
from fc_pipeline_v2.io import find_files, infer_block_name, infer_hc_label, infer_subject_id, load_parcel_timeseries


def save_matrix(matrix: np.ndarray, output_base: Path, save_npy: bool, save_csv: bool) -> None:
    if save_npy:
        np.save(output_base.with_suffix(".npy"), matrix)
    if save_csv:
        pd.DataFrame(matrix).to_csv(output_base.with_suffix(".csv"), index=False, header=False)


def saved_paths(output_base: Path, save_npy: bool, save_csv: bool) -> str:
    paths = []
    if save_npy:
        paths.append(str(output_base.with_suffix(".npy")))
    if save_csv:
        paths.append(str(output_base.with_suffix(".csv")))
    return ";".join(paths)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute alpha/beta static amplitude-envelope connectivity.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    ts_dir = resolve_path(config, config["paths"]["parcel_timeseries_dir"])
    output_dir = resolve_path(config, config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    files = find_files(ts_dir, config["inputs"]["parcel_timeseries_glob"])
    if not files:
        raise FileNotFoundError(f"No parcel time-series files found in {ts_dir}")

    conn_cfg = config["connectivity"]
    filt_cfg = config["filtering"]
    ts_cfg = config["timeseries"]
    sfreq = float(ts_cfg["sfreq"])

    rows = []
    for file_path in files:
        subject = infer_subject_id(file_path, config["naming"]["subject_regex"])
        block = infer_block_name(file_path, config["naming"]["block_patterns"])
        hc_label = infer_hc_label(file_path)
        # Keep HC1/HC2/HC3/HC4 in the output name so two blocks with the same
        # condition label do not overwrite each other.
        block_instance = hc_label or block
        signed_ts = load_parcel_timeseries(file_path, ts_cfg)
        print(f"Processing subject={subject}, block={block}, instance={block_instance}, shape={signed_ts.shape}")

        for band_name, band_limits in config["frequency_bands"].items():
            # This starts after source localization/parcel extraction. The input
            # should already be signed parcel time series, not raw EEG.
            r, z = compute_static_amplitude_connectivity(
                signed_parcels_by_time=signed_ts,
                sfreq=sfreq,
                band=(float(band_limits[0]), float(band_limits[1])),
                filter_order=int(filt_cfg["order"]),
                edge_trim_seconds=float(filt_cfg["edge_trim_seconds"]),
                orthogonalization=conn_cfg["orthogonalization"],
                apply_absolute_value=bool(conn_cfg["apply_absolute_value"]),
            )

            stem = f"{subject}_{block_instance}_{block}_{band_name}"
            r_base = output_dir / f"{stem}_r"
            z_base = output_dir / f"{stem}_fisher_z"
            save_matrix(r, r_base, conn_cfg["save_npy"], conn_cfg["save_csv"])
            save_matrix(z, z_base, conn_cfg["save_npy"], conn_cfg["save_csv"])
            rows.append(
                {
                    "subject": subject,
                    "block_instance": block_instance,
                    "block": block,
                    "band": band_name,
                    "input_file": str(file_path),
                    "r_matrix_files": saved_paths(r_base, conn_cfg["save_npy"], conn_cfg["save_csv"]),
                    "fisher_z_matrix_files": saved_paths(z_base, conn_cfg["save_npy"], conn_cfg["save_csv"]),
                    "n_parcels": r.shape[0],
                    "sfreq": sfreq,
                }
            )
            print(f"Saved {stem}: r and Fisher-z")

    pd.DataFrame(rows).to_csv(output_dir / "manifest.csv", index=False)
    print(f"Done. Manifest saved to {output_dir / 'manifest.csv'}")


if __name__ == "__main__":
    main()
