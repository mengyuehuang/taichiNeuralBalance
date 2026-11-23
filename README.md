# Tai Chi / Height Control EEG pipelines

## Current project status — 2026-11-23

**PCD: preprocessing/manual review and FC matrix calculations are complete for 33 participants across all four HC blocks (132 blocks). Group figures, QC summaries and the results-sharing package are complete.**

**TCP: awaiting continuation of review under the current protocol.** Previously computed TCP matrices remain available, but their existence does not establish completion of the current channel/interval/ICA review protocol. Next work is TCP review, with channel decisions confirmed before interval screening and component review. No new TCP review was started by this status update.

This is the current project status; dated completion statements below about earlier TCP computations describe historical runs, not completion of the forthcoming protocol-aligned review.


## Final reviewed PCD cohort and recording selection (2026-11-23)

Processing and FC matrix calculations are complete for 33 participants, each with all four HC blocks (132 block results). The final cohort excludes PCD103, PCD104, PCD107, PCD202 and PCD210 according to confirmed study notes; PCD211 was excluded by user decision because only HC1 is available. No local raw recordings were found for PCD108; this is a data-availability limitation, not an EEG-quality exclusion. None of these seven IDs is included in the final 33.

Two recordings contributed to one block for three included participants: PCD101 HC4, PCD102 HC1 and PCD208 HC4. All three combination decisions were approved and implemented; they are not pending or provisional processing decisions. Each acquisition was processed separately with boundaries preserved, and valid observations were pooled to calculate one matrix per block and frequency band. Recording gaps contributed no observations. Each participant counts once. PCD101 run01 has an incomplete TTL time code, limiting verification of timing continuity; this evidence limitation remains documented despite the completed combination. PCD109 HC4 used only the second recording (HC4_2), with no combination.

Historical 34-participant Clean BP summaries describe an earlier cohort/version and are not the current reviewed cohort. PCD119, PCD206 and PCD218 have historical quality notes but were reviewed and are included; completion does not erase their QC history.


Repository housekeeping: keep v2's reusable code in `auto_fc_pipeline_v2/shared_code/` and cohort data/results in their respective output workspaces. Put temporary work in a dedicated temporary directory, never loose at the project root. Delete one-off validation/migration scripts and staging files after completion; preserve maintained tests, production code, manual review decisions and concise audit results.

Python/MNE research workflow. v1 handles preprocessing, ICA review and cleaned channel-space backprojection (BP). v2 handles source reconstruction, signed time series, functional connectivity (FC), and QC.

- [v1 instructions](auto_fc_pipeline_v1/README.md)
- [Extra pre-ICA review](auto_fc_pipeline_v1/outputs/PCD_output/README.md), including the [TCP404 HC4 case](auto_fc_pipeline_v1/outputs/PCD_output/manual_preica_review_404/README.md)
- [v2 instructions and identity limitations](auto_fc_pipeline_v2/readme.md)
- [PCD Clean BP route](auto_fc_pipeline_v2/output/PCD_output/README.md)

## Features in this update (pending push)

- Added an isolated extra pre-ICA review workflow with an interactive waveform viewer, saved human interval decisions, and ICA comparison/topography exports.
- Added shared rank-aware source reconstruction for TCP and PCD, including centered numerical-residue projection and explicit input/output rank checks.
- Added guarded participant/batch runners, resumable progress records, and isolated output versions; the current TCP batch includes the reviewed case previously held from analysis.
- Added waveform/spectrum QC, split-half FC checks, threshold sensitivity analysis, cohort exclusion rules, and regression tests.
- Updated documentation, result paths and Git exclusions. Raw data, references, local configurations and generated results are distributed separately.

## Raw EEG review and next steps

PCD raw reprocessing is complete for the final 33-participant cohort. The following describes the earlier refit history. The epoch-policy comparison of 17 previously fitted PCD blocks identified 15 ICA refits and two reusable fits for the inputs compared. All 15 ICA refits and their component reviews are complete. This comparison covered run01 alone for PCD101 HC4 and PCD102 HC1. The later [multi-run decisions and pooling plan](auto_fc_pipeline_v2/output/PCD_output/README.md#raw-hc-run-selection-and-pooling) were applied to both participants. See the [November 12 comparison](auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#november-12-combined-runs) for the remaining stability flags. Audit the 72 TCP blocks against the same upstream policy before deciding which fits to repeat. The five-block TCP pilot remains experimental.

## Current results

TCP rank harmonization is complete for **18 participants / 72 HC blocks**, including TCP404. Both routes contain **216 matrices** each. Numerical checks passed; updated waveform/stability QC and combined group summaries remain outstanding. Completion is not formal statistical approval.

PCD has 35 historical rank-corrected participant outputs; the documented inclusion policy leaves **34 selected participants / 131 available blocks** after removing PCD107 from that historical set. Other explicit exclusions were already absent from the computed cohort. PCD119/206/218 remain quality-review cases. Do not count historical excluded files as current eligible results. PCD101, PCD203, and PCD213 are confirmed to be three distinct participants. Count each separately despite the shared GLOBAL_ID 1012 in the master sheet. Keep study-qualified IDs when comparing TCP and PCD.

## Canonical local paths

| Purpose | Path from repository root |
| --- | --- |
| Raw TCP data | `data/TCP_EEG_sync-selected/` |
| Raw/provided PCD archive | `data/VRHCT_CleanData-selected/` |
| Production v1 reviews, ICA, BP | `auto_fc_pipeline_v1/outputs/TCP_output/` |
| Isolated extra-review experiments | `auto_fc_pipeline_v1/outputs/PCD_output/outputs/` |
| TCP404 review evidence and snapshots | `auto_fc_pipeline_v1/outputs/PCD_output/manual_preica_review_404/outputs/` |
| Completed harmonized TCP FC | `auto_fc_pipeline_v2/output/TCP_output/tcp_rank_harmonized/outputs/<id>/` |
| Historical PCD rank-corrected FC | `auto_fc_pipeline_v2/output/PCD_output/rank_corrected/outputs/PCD<id>/` |
| Filtered historical QC view | `auto_fc_pipeline_v2/output/PCD_output/rank_corrected/qc_validation/selected_cohort/` |
| Older TCP FC (historical only) | `auto_fc_pipeline_v2/output/TCP_output/corrected/` |
| New runs using the v2 example config | `auto_fc_pipeline_v2/output/TCP_output/new_rank_corrected_runs/` |

The five extra-review pilot ICA fits do not replace production BP or FC until their manual reviews and backprojection are finalized. The historical QC view has not been recomputed against the harmonized TCP output.

## Setup and entry points

Use an EEG Python environment with the dependencies in each pipeline's `requirements-colab.txt`. Run commands from this repository root. Copy v1 `config.example.json` to `config.local.json` and set local raw/output/montage paths. Local configs, references and data are intentionally absent from Git; restore them separately before analysis.

```powershell
python auto_fc_pipeline_v2/shared_code/scripts/run_participant.py 101 --config auto_fc_pipeline_v2/config.hc_corrected.example.json
```

The v2 example enables the corrected data-relative rank policy. Its fresh output directory protects both historical and completed harmonized results. Copy it to a local config for different paths. Relative paths in configs directly inside `auto_fc_pipeline_v2` resolve from the repository root; configs elsewhere currently use their containing directory. Generated run configs use absolute paths and must be regenerated after relocating the project.

The case-specific `scripts/run_tcp_rank_harmonized.py --run` is a guarded resume tool for the existing local cohort and requires the previous TCP outputs/configs. It is not a fresh-clone setup command. Source code hashes protect its existing run from resuming with different numerical code.

HC1/HC4 are non-perturbation; HC2/HC3 are perturbation. The 14-ROI symmetric and 100-parcel pairwise estimators are different methods. The latter remains a visualization/QC route. Current HC data are not the reference EC/EO dataset.

## Git versus Google Drive

**Git:** Python source, HTML viewer templates, tests, dependency lists, example configs, cohort policy and README files. The participant policy is a processing rule with workbook provenance, not a generated result.

**Local / separate Drive:** raw data, `references/`, all `outputs/`, PCD `inputs/`, `validation/`, `qc_validation/`, logs, run status, generated manifests/configs, arrays, images and review workbooks. `.gitignore` covers these even when nested. Ignoring never deletes local files. Output links in READMEs work only after the separate result archive is restored.

For result review, upload each included participant's complete `04_static_fc/` folder with its participant and study/version folders intact, plus the relevant README, actual run config, cohort policy, status and source-rank audit. Keep the complete outputs and manual decisions in the separate archive for reproducibility. Do not upload only PNGs or mix TCP and PCD numeric IDs. PCD exclusions apply even when their historical result files exist.

Before committing, inspect `git status --short` and `git diff --cached --name-only`. No Git push or Drive upload is performed automatically.

Single-block ICA fits store all figures directly in the fit’s `ICA_Figures/` directory. For example, the PCD refit review uses `PCD101/HC1/ICA_Figures/`. Shared output roots containing multiple recordings use `ICA_Figures/<participant>/<HC>/`.

## Reviewed PCD delivery (2026-11-23)

The local Google Drive sharing package is `deliverables/PCD_reviewed_results_20261123.zip` with a SHA-256 sidecar. It includes 33 participants / 132 HC blocks / 792 individual FC NPZ matrices, complete FC exports, group figures, QC records and historical comparison materials. It excludes raw EEG and large processing intermediates, and is not a complete processing backup. Recreate a new version using `python auto_fc_pipeline_v2/shared_code/scripts/export_pcd_results.py --name NEW_DELIVERY_NAME`. The exporter hashes copied files and CRC-tests the ZIP. Upload is manual.

Git ignores delivery/archive folders, generated group reports, PDF/Office exports and machine-specific maintenance JSON inventories. Source scripts, templates, tests and README files remain visible. Git status contains prior directory relocations; include both removed old paths and new source paths when committing the migration. No automatic commit or push was performed.
