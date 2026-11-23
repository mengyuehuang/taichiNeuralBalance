# v2 directory migration and v1 recheck — 2026-11-18

Authorized mapping, relative to v2:

- `extra_data_pipeline/` -> `PCD_output/`.
- `outputs/` -> `TCP_output/`.

Internal participant/run `outputs/` directories keep their names. Directory depth is unchanged. The original top-level output package includes shared diagnostics as well as TCP results; all were moved intact.

All 13,160 files matched their original SHA-256 hashes after moving and before editing references. `move_inventory.json` records both locations and hashes. `edits.json` records 747 reference updates (10 Python scripts, 172 JSON files, 380 CSV manifests/plans, 176 logs and accompanying documentation/ignore rules). No numerical matrix CSV was edited. No EEG, ICA weights or FC arrays were rewritten, and processing was not rerun. Original source-code hashes stored in historical scientific provenance remain historical; migration before/after hashes explain path-only code changes.

Validation: changed Python and JSON parse successfully; actual referenced moved files/directories are checked in JSON and CSV; both v2 command-line entry points start; 13 existing cohort-policy/review-interface/corrected-workflow tests pass. Operational references to old v1/v2 directories are absent from the final scan. Historical maintenance manifests deliberately retain old paths.

The v1 recheck confirmed 8 relocated script-root calculations, the default TCP output configuration, and both PCD channel/interval review entry points. Its old directories are absent. Details are in `v1_recheck.json`.

Temporary staging copies are removed after verification; manifests and scripts remain as an audit. Do not rerun these one-time migration scripts as production steps. References to staging files in `edits.json` are historical. The separate earlier v1 migration audit is preserved.
