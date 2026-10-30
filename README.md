# Tai Chi / Height Control EEG pipelines

Python/MNE research workflow. v1 handles preprocessing, ICA review and cleaned channel-space backprojection (BP). v2 handles source reconstruction, signed time series, functional connectivity (FC), and QC.

- [v1 instructions](auto_fc_pipeline_v1/README.md)
- [Extra pre-ICA review](auto_fc_pipeline_v1/extra_review/README.md), including the [TCP404 HC4 case](auto_fc_pipeline_v1/extra_review/manual_preica_review_404/README.md)
- [v2 instructions and identity limitations](auto_fc_pipeline_v2/readme.md)
- [PCD Clean BP route](auto_fc_pipeline_v2/extra_data_pipeline/README.md)

## Features in this update (pending push)

- Added an isolated extra pre-ICA review workflow with an interactive waveform viewer, saved human interval decisions, and ICA comparison/topography exports.
- Added shared rank-aware source reconstruction for TCP and PCD, including centered numerical-residue projection and explicit input/output rank checks.
- Added guarded participant/batch runners, resumable progress records, and isolated output versions; the current TCP batch includes the reviewed case previously held from analysis.
- Added waveform/spectrum QC, split-half FC checks, threshold sensitivity analysis, cohort exclusion rules, and regression tests.
- Updated documentation, result paths and Git exclusions. Raw data, references, local configurations and generated results are distributed separately.

## Potential next step: reproduce extra pre-ICA review

Apply the extra time-interval/channel review to the prioritized suspicious recordings before ICA. Review proposed exclusions, refit ICA in isolated output folders, manually review the new components, then regenerate affected BP and v2 matrices. Compare with the existing outputs using consistent QC; do not assume that improved-looking topographies alone establish better results. The five-block pilot is experimental and has not replaced production outputs. Expansion to the additional dataset depends on confirming the updated preprocessing protocol.

## Current results

TCP rank harmonization is complete for **18 participants / 72 HC blocks**, including TCP404. Both routes contain **216 matrices** each. Numerical checks passed; updated waveform/stability QC and combined group summaries remain outstanding. Completion is not formal statistical approval.

PCD has 35 historical rank-corrected participant outputs; the documented inclusion policy leaves **34 selected participants / 131 available blocks** after removing PCD107 from that historical set. Other explicit exclusions were already absent from the computed cohort. PCD119/206/218 remain quality-review cases. Do not count historical excluded files as current eligible results. Identity overlap still requires confirmation.

## Canonical local paths

| Purpose | Path from repository root |
| --- | --- |
| Raw TCP data | `data/TCP_EEG_sync-selected/` |
| Raw/provided PCD archive | `data/VRHCT_CleanData-selected/` |
| Production v1 reviews, ICA, BP | `auto_fc_pipeline_v1/outputs/v1_preica_test/` |
| Isolated extra-review experiments | `auto_fc_pipeline_v1/extra_review/outputs/` |
| TCP404 review evidence and snapshots | `auto_fc_pipeline_v1/extra_review/manual_preica_review_404/outputs/` |
| Completed harmonized TCP FC | `auto_fc_pipeline_v2/outputs/tcp_rank_harmonized/outputs/<id>/` |
| Historical PCD rank-corrected FC | `auto_fc_pipeline_v2/extra_data_pipeline/rank_corrected/outputs/PCD<id>/` |
| Filtered historical QC view | `auto_fc_pipeline_v2/extra_data_pipeline/rank_corrected/qc_validation/selected_cohort/` |
| Older TCP FC (historical only) | `auto_fc_pipeline_v2/outputs/corrected/` |
| New runs using the v2 example config | `auto_fc_pipeline_v2/outputs/new_rank_corrected_runs/` |

The five extra-review pilot ICA fits do not replace production BP or FC until their manual reviews and backprojection are finalized. The historical QC view has not been recomputed against the harmonized TCP output.

## Setup and entry points

Use an EEG Python environment with the dependencies in each pipeline's `requirements-colab.txt`. Run commands from this repository root. Copy v1 `config.example.json` to `config.local.json` and set local raw/output/montage paths. Local configs, references and data are intentionally absent from Git; restore them separately before analysis.

```powershell
python auto_fc_pipeline_v2/scripts/run_participant.py 101 --config auto_fc_pipeline_v2/config.hc_corrected.example.json
```

The v2 example enables the corrected data-relative rank policy. Its fresh output directory protects both historical and completed harmonized results. Copy it to a local config for different paths. Relative paths in configs directly inside `auto_fc_pipeline_v2` resolve from the repository root; configs elsewhere currently use their containing directory. Generated run configs use absolute paths and must be regenerated after relocating the project.

The case-specific `scripts/run_tcp_rank_harmonized.py --run` is a guarded resume tool for the existing local cohort and requires the previous TCP outputs/configs. It is not a fresh-clone setup command. Source code hashes protect its existing run from resuming with different numerical code.

HC1/HC4 are non-perturbation; HC2/HC3 are perturbation. The 14-ROI symmetric and 100-parcel pairwise estimators are different methods. The latter remains a visualization/QC route. Current HC data are not the reference EC/EO dataset.

## Git versus Google Drive

**Git:** Python source, HTML viewer templates, tests, dependency lists, example configs, cohort policy and README files. The participant policy is a processing rule with workbook provenance, not a generated result.

**Local / separate Drive:** raw data, `references/`, all `outputs/`, PCD `inputs/`, `validation/`, `qc_validation/`, logs, run status, generated manifests/configs, arrays, images and review workbooks. `.gitignore` covers these even when nested. Ignoring never deletes local files. Output links in READMEs work only after the separate result archive is restored.

For result review, upload each included participant's complete `04_static_fc/` folder with its participant and study/version folders intact, plus the relevant README, actual run config, cohort policy, status and source-rank audit. Keep the complete outputs and manual decisions in the separate archive for reproducibility. Do not upload only PNGs or mix TCP and PCD numeric IDs. PCD exclusions apply even when their historical result files exist.

Before committing, inspect `git status --short` and `git diff --cached --name-only`. No Git push or Drive upload is performed automatically.
