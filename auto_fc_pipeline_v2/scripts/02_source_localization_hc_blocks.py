from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fc_pipeline_v2.config import load_config, resolve_path
from fc_pipeline_v2.output_paths import corrected_output_root, ensure_participant_output_paths


def infer_subject_id(file_path: Path, subject_regex: str) -> str:
    match = re.search(subject_regex, file_path.stem)
    if not match:
        raise ValueError(f"Could not infer subject id from {file_path.name!r}")
    return match.group(1)


def infer_block_name(file_path: Path, block_patterns: dict[str, list[str]]) -> str:
    stem_lower = file_path.stem.lower()
    for block_name, patterns in block_patterns.items():
        for pattern in patterns:
            if pattern.lower() in stem_lower:
                return block_name
    raise ValueError(f"Could not infer block type from {file_path.name!r}")


def infer_hc_label(file_path: Path) -> str:
    match = re.search(r"HC\d+", file_path.stem, flags=re.IGNORECASE)
    return match.group(0).upper() if match else ""


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    if not rows:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def resolve_subjects_dir(config: dict[str, Any], mne) -> Path:
    configured = str(config["paths"].get("subjects_dir", "")).strip()
    if configured and not configured.lower().startswith("todo"):
        subjects_dir = resolve_path(config, configured)
        subjects_dir.mkdir(parents=True, exist_ok=True)
        return subjects_dir

    fs_dir = Path(mne.datasets.fetch_fsaverage(verbose=True))
    return fs_dir.parent


def read_raw_block(file_path: Path, exclude_channels: list[str], set_average_ref: bool):
    import mne

    raw = mne.io.read_raw_fif(file_path, preload=True, verbose="ERROR")
    # Eye/neck/ground channels are useful for QC, but should not be used as
    # brain-source EEG channels in the inverse solution
    drop_existing = [ch for ch in exclude_channels if ch in raw.ch_names]
    if drop_existing:
        raw.drop_channels(drop_existing)
    raw.pick_types(meg=False, eeg=True, eog=False, stim=False, exclude=[])
    if set_average_ref:
        raw.set_eeg_reference("average", projection=True, verbose="ERROR")
        raw.apply_proj()
    return raw


def prepare_fsaverage_models(subjects_dir: Path, source_cfg: dict[str, Any]):
    import mne

    # These defaults mirror the old Step_2 scripts and current protocol settings.
    subject = str(source_cfg.get("subject", "fsaverage"))
    spacing = str(source_cfg.get("spacing", "ico5"))
    fs_dir = Path(mne.datasets.fetch_fsaverage(subjects_dir=subjects_dir, verbose=True))
    src_file = fs_dir / "bem" / f"{subject}-{spacing.replace('ico', 'ico-')}-src.fif"
    if not src_file.exists():
        src = mne.setup_source_space(subject, spacing=spacing, add_dist=False, subjects_dir=subjects_dir)
        mne.write_source_spaces(src_file, src, overwrite=True)
    else:
        src = mne.read_source_spaces(src_file)

    bem = fs_dir / "bem" / str(source_cfg.get("bem_name", "fsaverage-5120-5120-5120-bem-sol.fif"))
    if not bem.exists():
        raise FileNotFoundError(f"Expected fsaverage BEM file not found: {bem}")
    return src, bem


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Adapted v2 eLORETA source localization for Tai Chi HC block Raw files. "
            "Defaults to dry-run; pass --run to perform the expensive computation."
        )
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--subject", help="Optional subject id filter, e.g. 213")
    parser.add_argument("--run", action="store_true", help="Actually run eLORETA and save source estimates.")
    parser.add_argument(
        "--inverse-only",
        action="store_true",
        help=(
            "Build/save the common participant inverse without allocating a full-resolution "
            "whole-recording STC. Use this before the chunked 14-ROI extraction script."
        ),
    )
    args = parser.parse_args()

    config = load_config(args.config)
    source_cfg = config["source_localization"]
    root = corrected_output_root(config)
    pattern = str(source_cfg.get("input_glob", "*_montage_raw.fif"))
    if args.subject:
        files = sorted(ensure_participant_output_paths(config, args.subject)["montage_aligned"].glob(pattern))
    else:
        files = sorted(root.glob(f"*/01_block_level_eeg/montage_aligned/{pattern}"))
    if not files:
        requested = f" for participant {args.subject}" if args.subject else ""
        raise FileNotFoundError(f"No montage-aligned FIF files found{requested} under {root}")

    grouped: dict[str, list[Path]] = defaultdict(list)
    for file_path in files:
        subject = infer_subject_id(file_path, config["naming"]["subject_regex"])
        if args.subject and subject != args.subject:
            continue
        grouped[subject].append(file_path)

    for subject, subject_files in grouped.items():
        plan_rows = []
        for file_path in subject_files:
            plan_rows.append(
                {
                    "subject": subject,
                    "hc_label": infer_hc_label(file_path),
                    "block": infer_block_name(file_path, config["naming"]["block_patterns"]),
                    "input_file": str(file_path),
                    "will_run": bool(args.run),
                }
            )
        plan_path = ensure_participant_output_paths(config, subject)["source_model"] / "source_localization_plan.csv"
        write_csv(plan_rows, plan_path)
        print(f"Plan saved to {plan_path}")

    print(f"Found {sum(len(v) for v in grouped.values())} files across {len(grouped)} subject(s).")
    if not args.run:
        # Default to dry-run so this script can be tested locally without
        # really launching eLORETA
        print("Dry run only. Re-run with --run --inverse-only, then use chunked extraction locally.")
        return

    import mne
    from mne.minimum_norm import apply_inverse_raw, make_inverse_operator, write_inverse_operator

    subjects_dir = resolve_subjects_dir(config, mne)
    mne.set_config("SUBJECTS_DIR", str(subjects_dir), set_env=True)
    src, bem = prepare_fsaverage_models(subjects_dir, source_cfg)

    method = str(source_cfg.get("method", "eLORETA"))
    snr = float(source_cfg.get("snr", 3.0))
    lambda2 = 1.0 / snr**2
    trans = str(source_cfg.get("trans", "fsaverage"))
    exclude_channels = list(source_cfg.get("exclude_channels", []))
    set_average_ref = bool(source_cfg.get("set_average_reference_projection", True))
    cov_method = source_cfg.get("covariance_method", ["shrunk", "empirical"])

    for subject, subject_files in grouped.items():
        manifest_rows = []
        print(f"Processing subject={subject} with {len(subject_files)} HC block file(s)")
        raws = [read_raw_block(path, exclude_channels, set_average_ref) for path in subject_files]
        explicit_rank=None
        if source_cfg.get('rank_policy')=='data_relative':
            import numpy as np
            import json
            from fc_pipeline_v2.signal_rank import project_numerical_residue,signal_basis
            tolerance=float(source_cfg.get('rank_relative_tolerance',1e-6))
            audit={path.name:project_numerical_residue(raw,tolerance) for path,raw in zip(subject_files,raws)}
            pooled=np.concatenate([raw.get_data()[:,::max(1,raw.n_times//3000)] for raw in raws],axis=1)
            basis,_=signal_basis(pooled,tolerance,max_samples=pooled.shape[1])
            explicit_rank={'eeg':basis.shape[1]}
            audit['pooled_rank']=explicit_rank['eeg']
            (ensure_participant_output_paths(config,subject)['source_model']/'signal_rank_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
        if any(raw.ch_names != raws[0].ch_names or raw.info['sfreq'] != raws[0].info['sfreq']
               or raw.info['bads'] != raws[0].info['bads'] for raw in raws):
            raise ValueError(f'{subject}: HC blocks differ in channels, bad-channel lists or sampling rate; align before using a common inverse')

        # Build one inverse operator per participant, using all available HC
        # blocks for the covariance estimate, then apply it to each block
        common_raw = mne.concatenate_raws([raw.copy() for raw in raws], verbose="ERROR")
        noise_cov = mne.compute_raw_covariance(common_raw, method=cov_method, rank=explicit_rank, verbose=True)
        reuse_root=source_cfg.get('forward_reuse_root')
        existing_forward=Path(reuse_root)/subject/'02_source_model'/f'{subject}_forwardsolution_fsaverage.fif' if reuse_root else None
        if existing_forward is not None and existing_forward.is_file():
            fwd=mne.read_forward_solution(existing_forward,verbose='ERROR')
            if fwd['info']['ch_names']!=raws[0].ch_names:
                raise ValueError('Cached forward channels do not match corrected inputs')
        else:
            fwd = mne.make_forward_solution(
                raws[0].info,
                trans=trans,
                src=src,
                bem=bem,
                eeg=True,
                mindist=float(source_cfg.get("mindist", 5.0)),
                n_jobs=None,
                verbose=True,
            )
        mne.convert_forward_solution(fwd, surf_ori=True, copy=False)
        inv = make_inverse_operator(
            raws[0].info,
            fwd,
            noise_cov,
            fixed=False,
            loose=float(source_cfg.get("loose", 0.2)),
            depth=float(source_cfg.get("depth", 0.8)),
            rank=explicit_rank,
            verbose=True,
        )

        subject_out_dir = ensure_participant_output_paths(config, subject)["source_model"]
        mne.write_forward_solution(subject_out_dir / f"{subject}_forwardsolution_fsaverage.fif", fwd, overwrite=True)
        write_inverse_operator(subject_out_dir / f"{subject}_common_inverse_operator.fif", inv, overwrite=True)

        if args.inverse_only:
            print(
                f"Saved common inverse for {subject}; skipping full-resolution STCs. "
                "Run 03_extract_14roi_timeseries.py next."
            )
            continue

        for raw, file_path in zip(raws, subject_files, strict=True):
            hc_label = infer_hc_label(file_path)
            block = infer_block_name(file_path, config["naming"]["block_patterns"])
            stc = apply_inverse_raw(raw, inv, lambda2, method=method, pick_ori="normal", verbose=True)
            # Separate corrected products from any legacy magnitude estimates.
            stc_base = subject_out_dir / f"{subject}_{hc_label}_{block}_{method}_signed"
            stc.save(stc_base, overwrite=True)
            import numpy as np

            # Keep the original sample grid. Downstream operations must never
            # filter or Hilbert-transform across a rejected interval/boundary.
            valid = np.isfinite(raw.get_data(reject_by_annotation="NaN")).all(axis=0)
            breaks = np.zeros(raw.n_times, dtype=bool)
            breaks[0] = True
            for onset, description in zip(raw.annotations.onset, raw.annotations.description):
                if "boundary" in description.lower() or description.lower().startswith("edge"):
                    index = int(round((onset - raw.first_time) * raw.info["sfreq"]))
                    if 0 <= index < raw.n_times:
                        breaks[index] = True
            np.savez_compressed(
                str(stc_base) + "_metadata.npz", valid_samples=valid, boundary_samples=breaks,
                sfreq=raw.info["sfreq"], pick_ori="normal", source_file=str(file_path),
            )
            manifest_rows.append(
                {
                    "subject": subject,
                    "hc_label": hc_label,
                    "block": block,
                    "input_file": str(file_path),
                    "stc_base": str(stc_base),
                    "method": method,
                    "pick_ori": "normal",
                    "lambda2": lambda2,
                    "n_channels_used": len(raw.ch_names),
                    "sfreq": raw.info["sfreq"],
                }
            )
            print(f"Saved source estimate: {stc_base}")
        if manifest_rows:
            manifest_path = subject_out_dir / "source_estimates_manifest.csv"
            write_csv(manifest_rows, manifest_path)
            print(f"Manifest saved to {manifest_path}")


if __name__ == "__main__":
    main()
