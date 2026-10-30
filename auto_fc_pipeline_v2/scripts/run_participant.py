"""Run the complete corrected v2 workflow for one participant."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fc_pipeline_v2.config import load_config, resolve_path
DEFAULT_CONFIG = ROOT / "config.hc_corrected.example.json"
DEFAULT_V1_CONFIG = ROOT.parent / "auto_fc_pipeline_v1" / "config.local.json"


def v1_output_path(config_path: Path, settings: dict) -> Path:
    output = Path(settings['paths']['output_dir']).expanduser()
    parent = config_path.resolve().parent
    base = parent.parent if parent.name == 'auto_fc_pipeline' else parent
    return (output if output.is_absolute() else base / output).resolve()


def backprojection_is_current(preica_file: Path, v1_output: Path, cleaned_suffix: str) -> bool:
    block_id = preica_file.name.removesuffix("_preica_raw.fif")
    subject = block_id.split("_", 1)[0]
    dependencies = [
        preica_file,
        v1_output / "ICA" / f"{block_id}-ica.fif",
        v1_output / "ICA_Review" / subject / f"{block_id}_ica_review.csv",
    ]
    workbook = dependencies[-1].with_suffix('.xlsx')
    if workbook.exists():
        dependencies.append(workbook)
    output = v1_output / "Backprojected" / f"{block_id}{cleaned_suffix}"
    if not output.exists() or any(not path.exists() for path in dependencies):
        return False
    return output.stat().st_mtime >= max(path.stat().st_mtime for path in dependencies)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subject", help="Participant id, for example 101")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--v1-config", default=str(DEFAULT_V1_CONFIG))
    parser.add_argument("--chunk-seconds", type=float, default=2.0)
    parser.add_argument("--route", choices=["14", "100", "both"], default="both",
                        help="Default: primary 14-ROI plus secondary pairwise-100 QC")
    parser.add_argument(
        "--start-at",
        type=int,
        choices=range(0, 6),
        default=0,
        metavar="STEP",
        help="Resume at step 0-5; step 0 creates reviewed v1 backprojected files.",
    )
    args = parser.parse_args()
    if args.subject.startswith('PCD'):
        from fc_pipeline_v2.cohort_policy import is_excluded
        if is_excluded(args.subject):
            raise SystemExit(f'{args.subject}: excluded by documented cohort policy; historical outputs preserved.')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.subject):
        parser.error('subject must be an ID, not a path or regular expression')

    config = str(Path(args.config).expanduser().resolve())
    v1_config = str(Path(args.v1_config).expanduser().resolve())
    required = ["numpy", "pandas", "scipy", "mne", "matplotlib"]
    if args.start_at <= 4:
        required.extend(["mne", "nibabel"])
    if args.start_at == 0:
        required.append('openpyxl')
    missing = [name for name in required if importlib.util.find_spec(name) is None]
    if missing:
        requirements = ROOT / "requirements-colab.txt"
        raise SystemExit(
            "The selected Python environment is missing: "
            + ", ".join(missing)
            + f"\nPython: {sys.executable}"
            + f"\nInstall the v2 dependencies with:\n{sys.executable} -m pip install -r {requirements}"
        )

    print(f"Python: {sys.executable}")
    mne_home = ROOT.parent / ".mne_fake_home"
    mne_home.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["PYTHONUNBUFFERED"] = "1"
    environment.setdefault("_MNE_FAKE_HOME_DIR", str(mne_home))
    environment.setdefault("NUMBA_CACHE_DIR", str(ROOT.parent / ".numba_cache"))
    Path(environment["NUMBA_CACHE_DIR"]).mkdir(parents=True, exist_ok=True)
    cfg = load_config(config)
    if args.start_at == 0:
        with Path(v1_config).open("r", encoding="utf-8") as handle:
            v1_settings = json.load(handle)
        v1_output = v1_output_path(Path(v1_config), v1_settings)
        if resolve_path(cfg, cfg['paths']['backprojected_dir']) != v1_output / 'Backprojected':
            raise SystemExit('v1 output_dir/Backprojected and v2 backprojected_dir differ. '
                             'Align the configs before running; no files were changed.')
        preica = v1_output / "PreICA"
        backprojected = v1_output / "Backprojected"
        suffix = str(v1_settings['naming']['preica_suffix'])
        if suffix != '_preica_raw.fif':
            raise SystemExit('The HC runner requires preica_suffix=_preica_raw.fif.')
        expected = sorted(preica.glob(f"{args.subject}_HC*{suffix}"))
        if not expected:
            raise SystemExit(
                f"No v1 PreICA HC files found for participant {args.subject} in {preica}"
            )
        cleaned_suffix = str(v1_settings.get("naming", {}).get("cleaned_suffix", "_backproject_raw.fif"))
        if (cfg['inputs'].get('backprojected_format') != 'mne_raw_fif'
                or cfg['inputs']['backprojected_glob'] != f'*{cleaned_suffix}'):
            raise SystemExit('v2 input format/glob must match the v1 Backprojected FIF suffix.')
        current = all(backprojection_is_current(path, v1_output, cleaned_suffix) for path in expected)
        if current:
            print(f"\n[0/5] reviewed v1 backprojection: all {len(expected)} HC file(s) are current, skipping")
        else:
            print(
                "\n[0/5] create/update reviewed v1 backprojected HC files "
                "(saved ICA plus current manual review CSV)",
                flush=True,
            )
            v1_script = ROOT.parent / "auto_fc_pipeline_v1" / "scripts" / "04_run_ica.py"
            subprocess.run(
                [
                    sys.executable,
                    str(v1_script),
                    "--config",
                    v1_config,
                    "--backproject-only",
                    "--include-regex",
                    rf"^{re.escape(args.subject)}_HC\d+$",
                ],
                cwd=ROOT.parent,
                env=environment,
                check=True,
            )

    common = ["--config", config, "--subject", args.subject]
    steps = [
        ("prepare cleaned HC blocks", "01_prepare_blocks.py", common),
        ("align montage and channels", "02_check_montage_and_channels.py", common),
        (
            "build common source inverse",
            "02_source_localization_hc_blocks.py",
            [*common, "--run", "--inverse-only"],
        ),
        (
            "extract signed source time series",
            "03_extract_14roi_timeseries.py",
            [*common, "--chunk-seconds", str(args.chunk_seconds),
             *(["--include-parcels"] if args.route != "14" else [])],
        ),
        ("calculate 14-ROI connectivity", "04_whole_recording_fc14.py", common),
    ]

    started = time.perf_counter()
    for number, (label, script, arguments) in enumerate(steps, start=1):
        if number < args.start_at:
            continue
        if number == 5 and args.route == "100":
            continue
        command = [sys.executable, str(ROOT / "scripts" / script), *arguments]
        print(f"\n[{number}/5] {label}", flush=True)
        subprocess.run(command, cwd=ROOT.parent, env=environment, check=True)

    if args.route != "14":
        print("\n[5/5] calculate secondary pairwise-100 connectivity and QC", flush=True)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "04_whole_recording_fc.py"),
                        *common], cwd=ROOT.parent, env=environment, check=True)

    elapsed = time.perf_counter() - started
    sys.path.insert(0, str(ROOT / "src"))
    from fc_pipeline_v2.output_paths import participant_output_paths
    output = participant_output_paths(load_config(config), args.subject)["root"]
    print(f"\nCompleted participant {args.subject} in {elapsed / 60:.1f} min")
    print(f"Outputs: {output}")


if __name__ == "__main__":
    main()
