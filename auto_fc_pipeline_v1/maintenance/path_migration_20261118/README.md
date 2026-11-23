# Output directory migration — 2026-11-18

Authorized mapping, relative to `auto_fc_pipeline_v1`:

- `extra_review/` moved intact to `outputs/PCD_output/`.
- `outputs/v1_preica_test/` moved intact to `outputs/TCP_output/`.

The PCD workspace also contains shared review tooling and historical TCP review records. These were preserved in place within the moved package, not reclassified as PCD data.

All 4,625 moved files matched their pre-move SHA-256 hashes before reference edits. The two source directories no longer exist. `move_inventory.json` records the original and destination paths and hashes. `edits.json` records 1,061 text updates with before/after hashes. Script project-root calculations and relative Markdown links were adjusted for the additional directory level. Git ignore exceptions keep relocated source code visible while generated data remains ignored.

72 Excel workbooks contained the former directory only in `xl/workbook.xml` saved-location metadata (`absPath`). That metadata now names the actual destination directory. Every other ZIP member, including sheets, styles, notes, formulas and relationships, was checked byte-for-byte unchanged. The metadata audit includes the original workbook XML for recovery. No EEG, ICA weights, component classifications, manual decisions or FC numerical data were changed.

Validation includes Python syntax and JSON parsing for changed source/config files, scanning for stale paths outside this historical migration audit, and read-only entry-point checks. Archived/deleted intermediate paths may remain nonexistent by design; the earlier cleanup documentation still applies.

Final checks found all 3,758 referenced moved files at their new locations. Read-only `--help` checks passed for channel review, PCD interval review and TCP rank-harmonized processing. No processing was rerun.

Temporary staged text copies were removed after verification. Manifests and metadata recovery records remain as a small migration audit, not an additional copy of the EEG dataset. Scripts here are one-time maintenance records, not production processing steps; staging paths in `edits.json` are historical.
