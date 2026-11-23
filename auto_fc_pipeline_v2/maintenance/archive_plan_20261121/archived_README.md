# Legacy result archive — November 21, 2026

This folder contains 38 moved directories, 6,997 files, approximately 48.82 GiB. Nothing was deleted. Folder hierarchy is preserved relative to the taichi project root.

Included: PCD converted provided-Clean-BP inputs; PCD rank_corrected; 35 historical PCD plain-ID output directories; TCP historical corrected. Excluded: reviewed PCD epoch_union results, current TCP tcp_rank_harmonized, all v1 records, raw data, references, shared source templates and presentation comparisons.

## ZIP / Google Drive

Zip this entire `legacy_results_20261121` folder. Moving folders on the same drive does not free space. Creating a ZIP needs additional disk space until originals are removed. Compression size is not yet measured. Verify ZIP integrity and that the cloud upload is complete before deleting either local folder or ZIP. No local archive has been deleted or uploaded by this task.

## Restore

Extract the archive outside the project first. Each top-level `auto_fc_pipeline_v2/...` subtree maps directly to the same path beneath the taichi root. Use `move_manifest.json` for exact old/new mappings and `file_inventory.json` for every original file's byte size and modification timestamp. Restore missing directories only; never overwrite newer output folders wholesale. Restore all archived original paths before executing historical runners or audits. Existing generated configs, logs and provenance intentionally retain original paths and hashes; they were not rewritten as if recomputed.

## Local reporting dependencies

Current new/old comparison images, metrics and numeric summaries remain under `auto_fc_pipeline_v2/output/PCD_output/group_fc_display`. Approximately 61 MiB of old alpha/beta input matrices were copied and SHA-256 verified into `comparison_old_new/legacy_matrix_inputs`; the comparison script now reads these local copies. Thus the comparison can be regenerated after cloud offload. Current TCP results remain local; the historical harmonized batch runner requires restoration of its legacy forward-model/config dependencies before rerunning. New numerical workflows should use separate output versions.

The source-directory relocation was checked against all 6,997 inventory entries: byte sizes and modification timestamps unchanged. This is a relocation check, not a substitute for ZIP/cloud integrity verification.
