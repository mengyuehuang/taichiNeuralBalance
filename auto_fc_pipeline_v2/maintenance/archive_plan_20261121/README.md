# Legacy archive register — 2026-11-21

Status: 38 directories / 6,997 files moved and verified locally; 48.82 GiB. ZIP creation, cloud upload and cloud verification have not been verified by this task. This register remains outside the archive after offload. Do not interpret archive relocation as confirmed cloud backup.

## Archived categories

- PCD `inputs`: converted provided-Clean-BP FIF inputs for the historical workflow, not original raw EEG.
- PCD `rank_corrected`: historical Clean BP source/FC results, QC, logs and configurations.
- PCD `outputs/PCDxxx`: 35 historical plain-ID participant output directories, not current `PCDxxx_epoch_union_*` results.
- TCP `corrected`: older TCP source/FC results, including legacy forward models.

## What still needs these files?

Current reviewed PCD matrices, group plots and the saved new/old comparison do not require restoring this archive. The comparison script uses 262 hash-verified historical alpha/beta matrix copies (approximately 61 MiB) kept in `group_fc_display/comparison_old_new/legacy_matrix_inputs`.

Existing TCP `tcp_rank_harmonized` results remain local and readable. Re-running the historical TCP harmonized batch entry point can require archived PCD configuration and TCP forward-model inputs. Historical Clean BP processing, old-result audit/reproduction and inspection of archived intermediate signals also require restoration. These are archived dependencies, not universally unused or disposable files. Legacy entry points stop with a restoration message rather than silently recreating an old output tree.

Raw source data, references, v1 PreICA/ICA/backprojection/review records, current reviewed PCD runs, current TCP results, source templates and presentation figures remain local. No processing or matrix values were changed by this documentation update.

## Recovery

Restore only the mapped directories to their original paths; do not overwrite a whole current outputs directory. Historical configs/provenance intentionally retain original paths. Use the archive's file inventory and relocation verification for file-level records. Verify ZIP integrity and completed cloud upload before deleting local archived data. The current archive contents were not edited during this update, to avoid interfering with an in-progress ZIP.

## Exact directory mappings

| Original path (relative to taichi) | Archive path (relative to taichi) |
|---|---|
| `auto_fc_pipeline_v2/output/PCD_output/rank_corrected` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/rank_corrected` |
| `auto_fc_pipeline_v2/output/PCD_output/inputs` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/inputs` |
| `auto_fc_pipeline_v2/output/TCP_output/corrected` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/TCP_output/corrected` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD101` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD101` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD102` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD102` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD105` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD105` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD106` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD106` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD107` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD107` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD109` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD109` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD110` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD110` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD111` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD111` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD112` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD112` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD113` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD113` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD114` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD114` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD115` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD115` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD116` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD116` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD117` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD117` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD118` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD118` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD119` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD119` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD120` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD120` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD201` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD201` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD203` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD203` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD204` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD204` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD205` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD205` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD206` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD206` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD207` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD207` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD208` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD208` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD209` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD209` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD211` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD211` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD212` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD212` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD213` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD213` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD214` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD214` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD215` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD215` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD216` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD216` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD217` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD217` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD218` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD218` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD219` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD219` |
| `auto_fc_pipeline_v2/output/PCD_output/outputs/PCD220` | `archives/legacy_results_20261121/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD220` |

## Cloud offload and local deletion — 2026-11-22

User confirmed the upload completed and authorized deletion. The local legacy_results_20261121 directory and ZIP were deleted. Observed disk free-space increase: 94.00 GiB. Before deletion, ZIP entries covered all 6,997 inventoried data files at expected uncompressed sizes; full CRC and remote cloud integrity were not independently checked. Exact mappings, the copied archived file inventory and offload_20261122.json remain in the local maintenance register. Download and extract the cloud archive before restoring historical paths. Current reviewed PCD, current TCP and local report comparisons remain available.
