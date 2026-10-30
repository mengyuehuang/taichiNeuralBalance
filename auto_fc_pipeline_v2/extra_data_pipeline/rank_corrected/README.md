# Rank-corrected provided Clean BP analysis

This run preserves provided Clean BP files and saved ICA inclusion/exclusion
decisions. The original results in `../outputs` are provisional; this directory
contains separate recomputed results with additional numerical checks.

The rank policy uses a relative singular-value threshold of 1e-6. Each HC block
is projected onto its measured signal subspace to remove storage-rounding
residue. A relative signal change above 1e-5 stops processing for review. The
common inverse uses the pooled participant data rank, not the minimum rank of
the separately cleaned HC blocks. The same numerical projection is applied
before covariance estimation and before source time-series extraction.

Existing forward models are reused because electrode geometry is unchanged;
covariance, inverse models, source signals and connectivity are recomputed.
No ICA is refitted. The original files and original analysis outputs remain.

Progress: `run_status.json`; detailed logs: `logs/PCD107.log`, etc.
Results: `outputs/PCD101/`, etc. Per-participant source-model directories contain
`signal_rank_audit.json` with the measured ranks and relative signal changes.

PCD107 was the historical pilot but is now excluded by the documented policy. Its output is retained only for provenance. The current selected cohort has 34 participants; see [cohort policy and current instructions](../README.md). Failed checks remain failures, not usable results.
Successful execution still requires signal-quality and study-level validation.

This directory contains local run artifacts. Only this README belongs in Git; outputs, QC, logs, generated config, compatibility reports and status are archived separately. Historical PCD results predate `centered_preserve_mean_v2`; see the main v2 README for the measured compatibility differences.
