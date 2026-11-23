# PCD analysis: provided Clean BP and raw EEG reprocessing

## Current project status — 2026-11-23

**PCD: preprocessing/manual review and FC matrix calculations are complete for 33 participants across all four HC blocks (132 blocks). Group figures, QC summaries and the results-sharing package are complete.**

**TCP: awaiting continuation of review under the current protocol.** Previously computed TCP matrices remain available, but their existence does not establish completion of the current channel/interval/ICA review protocol. Next work is TCP review, with channel decisions confirmed before interval screening and component review. No new TCP review was started by this status update.

This is the current project status; dated completion statements below about earlier TCP computations describe historical runs, not completion of the forthcoming protocol-aligned review.


## Final reviewed PCD cohort and recording selection (2026-11-23)

Processing and FC matrix calculations are complete for 33 participants, each with all four HC blocks (132 block results). The final cohort excludes PCD103, PCD104, PCD107, PCD202 and PCD210 according to confirmed study notes; PCD211 was excluded by user decision because only HC1 is available. No local raw recordings were found for PCD108; this is a data-availability limitation, not an EEG-quality exclusion. None of these seven IDs is included in the final 33.

Two recordings contributed to one block for three included participants: PCD101 HC4, PCD102 HC1 and PCD208 HC4. All three combination decisions were approved and implemented; they are not pending or provisional processing decisions. Each acquisition was processed separately with boundaries preserved, and valid observations were pooled to calculate one matrix per block and frequency band. Recording gaps contributed no observations. Each participant counts once. PCD101 run01 has an incomplete TTL time code, limiting verification of timing continuity; this evidence limitation remains documented despite the completed combination. PCD109 HC4 used only the second recording (HC4_2), with no combination.

Historical 34-participant Clean BP summaries describe an earlier cohort/version and are not the current reviewed cohort. PCD119, PCD206 and PCD218 have historical quality notes but were reviewed and are included; completion does not erase their QC history.


> **Archive relocation (2026-11-21):** Historical PCD Clean BP inputs/results and TCP `corrected` were moved to [the legacy archive](../../../archives/legacy_results_20261121/README.md). Historical paths below describe the original run layout; restore instructions and exact mappings are in that archive. Current reviewed PCD and TCP `tcp_rank_harmonized` results remain local.


This workspace is now `auto_fc_pipeline_v2/output/PCD_output/`. The historical `inputs/`, `rank_corrected/` and 35 plain-ID participant output folders were archived on November 21; current reviewed `outputs/PCDxxx_epoch_union_*` folders remain local. Raw-reviewed run folders and historical Clean BP results remain distinct. Main TCP outputs and cross-study summaries are in [TCP_output](../TCP_output/README.md).

For recordings reprocessed from raw EEG, see the [split-half FC diagnostic record](raw_review_fc_diagnostics.md).

## Current cohort policy (updated 2026-11-21)

Use [participant_policy.json](participant_policy.json) and [effective_input_manifest.json](effective_input_manifest.json) for current inclusion decisions. The team confirmed that the exclusion notes in the Perturbation Summary worksheet of [Subject Level Data Organizing.xlsx](../../../references/Subject%20Level%20Data%20Organizing.xlsx) apply to the current HC analysis. Accordingly, we skip PCD103, PCD104, PCD107, PCD202 and PCD210. For PCD202, all four trials have `wrong order` in E74:E77 and `exclude` in F74:F77. PCD119/206/218 remain quality-review cases, not automatic exclusions or approvals. The original input manifest and historical outputs are preserved. The current complete four-HC analysis cohort is 33 participants after skipping HC1-only PCD211; PCD208 HC4 combining was approved on November 18. Both raw acquisitions were reviewed separately and pooled with a 47.455 s gap recorded as metadata. Channel/interval/ICA reviews, four-block FC and split-half diagnostics are complete. Historical Clean BP alternatives remain held and are not substituted for the raw workflow. See the run-selection section below.

The filtered historical QC view is [selected_cohort](rank_corrected/qc_validation/selected_cohort), not a completed harmonized analysis. See the [main v2 README](../../readme.md) for shared TCP/PCD numerical code, the centered projection correction, TCP404 sequencing, and participant identity decisions. Re-running the historical PCD runner skips historical completed entries; it does not certify that their projection-policy version matches a new run. The [compatibility audit](rank_corrected/projection_compatibility.json) records input/covariance differences separately.

This independent run reads `data/VRHCT_CleanData-selected/Clean BP` directly.
It does not use the experimental backprojections produced under v1.
Clean BP signals are converted from EEGLAB SET/FDT to FIF without another ICA
application or upstream filtering. The provided MATLAB 63-channel positional labels
are assigned and eye/neck/ground channels are typed before source modeling.

Run from the project root:

```powershell
python auto_fc_pipeline_v2/output/PCD_output/run_clean_bp.py
```

Use `--subject PCD105` for one participant. A repeat invocation skips participants
recorded as completed. Do not change inputs or settings while reusing completion
records; use a separate output location for a different analysis.

- `input_manifest.csv`: selected inputs and explicit holds.
- `config.clean_bp.json`: local v2 paths and PCD group assignments.
- `inputs/`: format-converted provided Clean BP inputs.
- `outputs/PCD105/`, etc.: standard v2 participant results.
- `logs/`: participant execution logs.
- `run_status.json`: completion, failures and route limitations.

PCD103 remains on hold because the supplied subject summary marks it excluded.
Both historical PCD208 HC4 Clean BP alternatives remain held in this legacy input route; the separate raw workflow now selects both acquisitions for reviewed combination;
the remaining three unique blocks can run. Participants with partial recordings
are processed as partial, not presented as complete four-block participants.

The symmetric 14-ROI route requires full signal rank. Where any supplied Clean BP
has fewer than 14 retained ICA components, the batch runs only the existing
pairwise 100-parcel route and records the 14-ROI limitation. A numerical rank
failure on the 14-ROI route is also recorded, without disabling rank checks.
The 100-parcel route remains exploratory QC and is not a replacement estimator
for symmetric 14-ROI results. Successful execution is not scientific validation.

The original v2 scripts retain their band-specific analysis filtering and
boundary handling. No reconstruction of missing artifact annotations is inferred
from the provided files. Existing TCP/TCOA results remain in their original output
directory and are not pooled by this run.

## PCD211 skipped: HC1-only data (2026-11-21)

PCD211 is skipped for the current final matrix analysis by user decision on November 21, 2026. Only HC1 is available, so its available-condition structure does not match the complete HC1-HC4 structure used for the other included participants. This is a completeness/analysis-structure exclusion, not an EEG-quality exclusion or a file-format error. Existing source data and historical outputs are preserved.

## Raw HC run selection and pooling

November 11, 2026. The decisions below apply to raw EEG reprocessing. Historical PCD101 HC4 and PCD102 HC1 matrices used run01 alone. Both combined versions completed November 12. See the [matched comparisons and stability findings](raw_review_fc_diagnostics.md#november-12-combined-runs).

| Block | Run selection | Timing evidence |
| --- | --- | --- |
| PCD101 HC4 | Approved and completed: combine run01 (56.06 s) and run02 (266.10 s) as two segments of HC4. Record a 209.00 s gap. | The last eight TTL values in run01 decode to a possible Vizard time of 14.72 s. The file ends before the marker needed to verify it. If valid, the Vizard times of the two pulse groups differ by 219.03 s, versus approximately 217.94 s on the EEG acquisition clock. This supports continuity. The corresponding Vizard trial002 log could verify the run01 timestamp. |
| PCD102 HC1 | Combine `height_1` (62.15 s) and `height_1_1` (125.30 s) as two segments of HC1. Record a 106.94 s gap. | Both runs contain decodable TTL groups. Their fitted Vizard start times differ by 169.085 s, compared with 169.093 s between EEG recording starts. The 49.15 s retained and the stability flag reported below describe the first run alone. |
| PCD109 HC4 | Use `PCD2018_109_day2_height_control_4_2` alone (271.30 s). | The study workbook records 25 s for HC4_1 and says it was skipped for backprojection. Only HC4_2 raw EEG is available locally. The aligned review folder named `run01` points to that same HC4_2 file. |

### PCD208 HC4 timing review — November 18

Combining was approved on November 18: use both `PCD_208_2_anxiety4` (181.05 s) and `PCD_208_2_anxiety4_2` (60.60 s). The fitted Vizard start-time difference is 228.496959 s versus 228.505 s between EEG acquisition starts (8.041 ms discrepancy). There is a 47.455 s recording gap and 241.65 s of recorded data before QC. Fits use 26 and 9 complete TTL groups with maximum residuals below 0.53 ms. The supplied `HC_timing/208_4.csv` independently agrees with run02 timing within 1.14 ms. Timing supports continuation rather than a clock reset, as in the PCD102 case. Both raw entry points were promoted to `outputs/pcd_aligned/raw/PCD208/HC4/run01` and `run02`. Their approved `run_selection.json` records run order, gap, timing evidence and processing boundaries; `raw_naming_manifest.csv` marks both selected for combination. The channel-review runner resolves both acquisitions explicitly. Channel, interval and IC reviews were subsequently completed, followed by pooled HC4 FC calculation. Historical Clean BP manifest selections are unchanged. See the [full timing evidence](../../../auto_fc_pipeline_v1/outputs/PCD_output/outputs/pcd208_review/HC4_timing_review/README.md).

### Processing steps for combined runs

1. Track the original filename, run ID, acquisition start, duration, TTL timing evidence and QC decisions for each run. Review channels and intervals under the v1 protocol. Keep each retained continuous interval associated with its source run.
2. Align the reviewed EEG inputs on the same channels, order, reference and sampling rate for the participant's common inverse. Extract signals for the same atlas regions. Verify ROI or parcel labels and order, frequency band and envelope sampling rate before pooling.
3. Represent each combined HC as one block with an explicit boundary between runs. Store elapsed gap duration as timing metadata and give the gap zero observations. Filter, trim edges and compute Hilbert envelopes within each continuous segment, respecting the run boundary even if both sides pass QC.
4. For each band, pool valid envelope observations in acquisition order, with one column per region and one row per time point. On the 14-ROI route, apply the existing joint symmetric correction to the valid signals and compute the envelopes segment by segment. Correlate the pooled envelope columns to populate one FC matrix for the block. On the 100-parcel route, pool within each direction of pairwise correction before averaging the two directional correlations. Each run contributes its valid observations. Count the combined HC once in participant and group summaries.
5. Rebuild the affected participant's common inverse and downstream matrices. Record retained seconds per run and repeat the rank and chronological split-half FC checks on the combined block. Keep the run01-only QC identifiable for comparison.

## PCD102 HC1 quality review flag (raw reprocessing, run01)

For PCD105 HC3 preprocessing and its C3 channel exclusion, see the [v1 recording-specific decision](../../../auto_fc_pipeline_v1/outputs/PCD_output/README.md#pcd105-hc3-recording-specific-c3-exclusion).

The updated four-block common inverse uses 56 shared EEG channels after the HC4 O1 exclusion. HC1 reached ROI rank 14/14 with 49.15 s retained. Its centered split-half correlations were -0.115 for broadband, 0.013 for alpha and 0.201 for beta. Keep the HC1 review flag for statistical inclusion. See the [current QC metrics](outputs/raw_pilot_PCD102_four_blocks_HC4_O1_excluded/quality_review/split_stability.csv) and [diagnostic history](raw_review_fc_diagnostics.md).

## PCD105 four-block raw reprocessing, November 4, 2026

Existing reviewed ICA fits and component decisions are retained. F2 retention in HC2/HC3 was explicitly confirmed on this date; no earlier approval is implied. HC1–HC3 exclude C3 upstream, and HC4 excludes C3/F2. For one participant-level common inverse, all four blocks use the 55 shared EEG channels, excluding C3/F2 downstream and applying the same average-reference policy. This does not refit the HC2/HC3 ICA. Source inputs are copied unchanged with SHA-256 provenance.

The current run is [raw_pilot_PCD105_four_blocks](outputs/raw_pilot_PCD105_four_blocks). The input provenance, config, run status and log are saved there. Common-inverse FC and split-half QC are complete (24 validated matrices; all four ROI ranks 14/14). See the [completion report](outputs/raw_pilot_PCD105_four_blocks/README.md) and [QC metrics](outputs/raw_pilot_PCD105_four_blocks/quality_review/split_stability.csv). All four 14-ROI alpha results have low split-half stability (r=0.16–0.20). HC3 Fp1 has an accepted-window amplitude flag near 16.5–17.5 s. These are review flags, not automatic upstream exclusions or statistical approval. The waveform/PSD QC now reads the configured downstream channel exclusions and reference, so it assesses the same sensor channel set as the source model.


## PCD208 reviewed raw results - 2026-11-18

PCD208 completed 2026-11-18: five reviewed acquisitions form four HC results. All 57 EEG channels retained. Valid HC1-HC4 durations: 284.5, 276.5, 277.5, 228 s. Reviewed ICs retained: HC1 9/16, HC2 11/24, HC3 15/29, HC4 run01 10/21 and run02 11/17. Both HC4 runs were processed separately before downstream pooling (170 + 58 valid seconds); the 47.455 s physical gap contributes no observations. Stored boundary at 181.05 s verified in the extracted segment metadata. All four signed 14-ROI time series have rank 14/14 at relative tolerance 1e-6. All 24 FC matrices passed dimension, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 4/12 block-band pairs on the 14-ROI route and 4/12 on the 100-parcel route. Minimum full-versus-saved edge correlation 0.99986510. These exploratory stability checks measure relative edge-pattern agreement, not directionality, and are not automatic participant exclusion.

[Current run and provenance](outputs/PCD208_epoch_union_20261118/README.md). Historical Clean BP results are unchanged.


## PCD209 four-block results - 2026-11-19

PCD209 completed manual ICA review and four-block common-inverse FC. Fp1 excluded in every block; other 56 EEG channels retained. Valid HC1-HC4 durations: 293.50, 281.65, 281.25, 286.90 seconds. Retained IC counts: 20/42, 20/38, 25/37, 23/39. All four signed 14-ROI time series have rank 14/14 at relative tolerance 1e-6. All 24 FC matrices passed dimension, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 1/12 block-band pairs on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-versus-saved edge correlation: 0.99969963. Limited split-half agreement is an exploratory QC flag, not rank deficiency or automatic participant exclusion.

[Current results and provenance](outputs/PCD209_epoch_union_20261119/README.md).


## PCD212 four-block results completed - 2026-11-19

All four blocks excluded AFz and used 56 EEG channels. Reviewed valid durations:369,286.50,292,286.85 seconds; retained IC counts:11,14,16,16. All four signed 14-ROI time series reached rank14/14 at relative tolerance1e-6. All24 FC matrices passed shape,finite off-diagonal,symmetry and correlation-range checks. Centered split-half r>=0.5: 5/12 on the14-ROI route and 5/12 on the100-parcel route. Minimum full-recording-versus-saved edge correlation:0.99994140. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

Results: auto_fc_pipeline_v2/output/PCD_output/outputs/PCD212_epoch_union_20261119/README.md


## PCD213 four-block results completed - 2026-11-19

All four blocks excluded AFz and used 56 EEG channels. Reviewed valid durations: 303, 310.50, 283 and 295.50 seconds; retained IC counts: 8, 8, 8 and 6. Signed 14-ROI ranks (HC1-HC4): 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 1/12 on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-recording-versus-saved edge correlation: 0.99957239. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

Results: C:/Users/98768/Desktop/taichi/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD213_epoch_union_20261119/README.md

## PCD214 four-block results completed - 2026-11-19

All four blocks retained 57 EEG channels. Valid durations HC1-HC4: 308.50, 266.00, 289.00 and 263.50 seconds; retained IC counts: 9, 8, 8 and 7. Signed 14-ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 3/12 on the 14-ROI route and 7/12 on the 100-parcel route. Minimum full-recording-versus-saved edge correlation: 0.99992535. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

Results: C:/Users/98768/Desktop/taichi/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD214_epoch_union_20261119/README.md


## PCD215 four-block results completed - 2026-11-20

All four blocks exclude Fp1 and retain 56 EEG channels. Valid durations HC1-HC4: 293.25, 248.90, 268.65 and 282.90 seconds. Retained IC counts: 4, 3, 5 and 5. Signed ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 3/12 on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-recording-versus-saved edge correlation: 0.99989116. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

Results: C:/Users/98768/Desktop/taichi/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD215_epoch_union_20261120/README.md


## PCD216 four-block results completed - 2026-11-20

All four blocks exclude F1 and retain 56 EEG channels. Valid durations HC1–HC4: 278.50, 276.00, 281.00 and 271.00 seconds. Retained IC counts: 4, 3, 4 and 6. Signed ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 3/12 on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-recording-versus-saved edge correlation: 0.99990393. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

Results: C:/Users/98768/Desktop/taichi/auto_fc_pipeline_v2/output/PCD_output/outputs/PCD216_epoch_union_20261120/README.md


## PCD217 four-block results completed - 2026-11-20

All four blocks exclude P7 and retain 56 EEG channels. Valid durations HC1-HC4: 219.50, 324.00, 303.00 and 296.00 seconds. Retained IC counts: 8, 6, 7 and 5. Signed ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 0/12 on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-recording-versus-saved edge correlation: 0.99979477. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

[Full results](outputs/PCD217_epoch_union_20261120/README.md)


### PCD218 four-block results (November 21, 2026)

All four blocks retain 57 EEG channels. Valid durations HC1-HC4: 364.50, 278.50, 265.00 and 240.50 seconds. Retained IC counts: 1, 3, 3 and 5. Signed 14-ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 1/12 on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-versus-saved edge correlation: 0.99959282. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

[Full results](outputs/PCD218_epoch_union_20261121/README.md)


### PCD219 four-block results (November 21, 2026)

All four blocks retain 57 EEG channels. Valid durations HC1-HC4: 307.00, 262.30, 436.00 and 269.50 seconds. Retained IC counts: 6, 2, 5 and 5. Signed 14-ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 0/12 on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-versus-saved edge correlation: 0.99969933. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

[Full results](outputs/PCD219_epoch_union_20261121/README.md)


### PCD220 four-block results (November 21, 2026)

All four blocks retain 57 EEG channels. Retained durations HC1–HC4: 253.50, 245.60, 242.85 and 304.00 seconds. Retained IC counts: 14, 19, 13 and 16. Signed 14-ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >= 0.5: 5/12 on the 14-ROI route and 2/12 on the 100-parcel route. Minimum full-versus-saved edge correlation: 0.99987000. Split-half agreement compares connection patterns from the chronological halves of retained data within each HC; it is exploratory QC, not a rank test or automatic exclusion. The rank above concerns signed ROI time series, not FC matrix rank.

[Full results](outputs/PCD220_epoch_union_20261121/README.md)


## Reviewed 33-participant group display (2026-11-21)

[Current group figures and method](group_fc_display/README.md) use the completed raw-review results for 33 participants, excluding HC1-only PCD211. The replacement `shared_code/scripts/refresh_fc_display.py` adapts reference Step0b cell 0b.6 directly: Fisher z per HC, equal HC1-HC4 mean within participant, reference double-centering, then equal participant mean. Alpha and beta are separate panels, with a shared data-derived symmetric 99th-percentile color scale, not fixed -1/+1. Pairwise-corrected and uncorrected comparison figures, numeric matrices and input hashes are saved. Independent execution of the reference functions reproduced all four exported matrices. These are all-HC descriptive figures, not perturbation contrasts.

## Archive availability and dependencies (2026-11-21)

See the [persistent archive register](../../maintenance/archive_plan_20261121/README.md) for all 38 directory mappings and recovery dependencies. Current reviewed PCD, completed TCP and report comparisons remain local. Archived files are unnecessary for reading these current results, but can be required for historical reruns/audits. ZIP/cloud completion has not been verified. The register is kept outside the archive so it remains available after cloud offload.

## Cloud offload and local deletion — 2026-11-22

User confirmed the upload completed and authorized deletion. The local legacy_results_20261121 directory and ZIP were deleted. Observed disk free-space increase: 94.00 GiB. Before deletion, ZIP entries covered all 6,997 inventoried data files at expected uncompressed sizes; full CRC and remote cloud integrity were not independently checked. Exact mappings, the copied archived file inventory and offload_20261122.json remain in the local maintenance register. Download and extract the cloud archive before restoring historical paths. Current reviewed PCD, current TCP and local report comparisons remain available.
