# PCD outputs and shared review tools

## Current project status — 2026-11-23

**PCD: preprocessing/manual review and FC matrix calculations are complete for 33 participants across all four HC blocks (132 blocks). Group figures, QC summaries and the results-sharing package are complete.**

**TCP: awaiting continuation of review under the current protocol.** Previously computed TCP matrices remain available, but their existence does not establish completion of the current channel/interval/ICA review protocol. Next work is TCP review, with channel decisions confirmed before interval screening and component review. No new TCP review was started by this status update.

This is the current project status; dated completion statements below about earlier TCP computations describe historical runs, not completion of the forthcoming protocol-aligned review.


## Final reviewed PCD cohort and recording selection (2026-11-23)

Processing and FC matrix calculations are complete for 33 participants, each with all four HC blocks (132 block results). The final cohort excludes PCD103, PCD104, PCD107, PCD202 and PCD210 according to confirmed study notes; PCD211 was excluded by user decision because only HC1 is available. No local raw recordings were found for PCD108; this is a data-availability limitation, not an EEG-quality exclusion. None of these seven IDs is included in the final 33.

Two recordings contributed to one block for three included participants: PCD101 HC4, PCD102 HC1 and PCD208 HC4. All three combination decisions were approved and implemented; they are not pending or provisional processing decisions. Each acquisition was processed separately with boundaries preserved, and valid observations were pooled to calculate one matrix per block and frequency band. Recording gaps contributed no observations. Each participant counts once. PCD101 run01 has an incomplete TTL time code, limiting verification of timing continuity; this evidence limitation remains documented despite the completed combination. PCD109 HC4 used only the second recording (HC4_2), with no combination.

Historical 34-participant Clean BP summaries describe an earlier cohort/version and are not the current reviewed cohort. PCD119, PCD206 and PCD218 have historical quality notes but were reviewed and are included; completion does not erase their QC history.



## Current IC review priority - clarified 2026-11-20

User clarification: probability >=0.9 automatically accepts only an explicit ICLabel class (brain, muscle artifact, eye blink, heart beat, line noise, channel noise). Other is exempt at every probability and follows the user note. Below 0.9, notes take priority; blank notes agree with the ICLabel default. brain?, brain and unsure retain; not brain, channel, muscle and eye exclude. Resolve ambiguous notes with the user. Match component IDs, never sorted row positions. This clarification is applied to PCD218 HC1 and subsequent reviews; earlier completed results have not been retroactively changed.


Directory organization updated on 2026-11-18. This folder contains the complete former review workspace: PCD participant results are under `outputs/`, shared review scripts under `scripts/`, and templates and the historical TCP404 case under `manual_preica_review_404/`. Historical TCP pilot/screening records and reference tools remain with this workspace; the folder name does not reclassify those records as PCD. Main TCP processing outputs are in [TCP_output](../TCP_output/README.md).

Storage maintenance (2026-11-18): redundant Filtered intermediates with preserved PreICA and completed-PCD reviewer waveform caches were removed. Manual decisions, ICA fits, PreICA and backprojection files remain. Archived reviewers require waveform regeneration to display traces; rerunning pre-PreICA steps requires regenerating Filtered data. See the [exact cleanup scope and audit](maintenance/cleanup_20261118/README.md).

## Raw EEG review protocol for TCP and PCD

Working protocol, November 2026. Apply the same decision rules to each Height Control block in both studies. The current rollout covers PCD first. Cross-study harmonization and protocol approval are pending.

1. Check the recording identity, source files, run selection and participant policy before processing. Preserve the raw data. Track unresolved runs and identity questions separately from quality decisions.
2. On filtered pre-ICA EEG, compare each electrode's one-second peak-to-peak amplitudes with the median of nearby EEG electrodes in the same windows. Record the neighbor names, amplitude ratio and fraction of complete seconds above fivefold. This threshold prompts waveform review. Confirm whether the abnormality persists, is localized, and differs from neighboring activity before marking a channel bad for that block. Document the evidence and decision.
3. Exclude confirmed bad channels from automatic interval screening, the average reference and ICA fitting. Recompute all automatic time flags when the channel list changes. Review the remaining waveforms and record interval boundaries, reasons and retained duration. For a brief disturbance in an otherwise usable channel, review the affected seconds individually.
4. Fit ICA on the retained samples and channels. Review component maps, spectra, time courses and classifier suggestions. Save manual decisions for that specific fit. Resolve explicit reviewer notes against the decision fields before backprojection. Preserve uncertainty and keep previous fits separate.
5. Audit earlier raw runs against the same policy. Reuse verified equivalent inputs and fits. When channels, reference or training samples change, refit ICA, review the new components and regenerate affected outputs, including participant-level common-inverse products. Check the inverse channel list, retained duration, ROI rank, FC matrices, waveforms, spectra and split-half stability. Document unresolved QC flags before group inclusion.

For the current HC analysis, skip PCD103, PCD104, PCD107, PCD202 and PCD210 per the team-confirmed Perturbation Summary exclusion notes.

PCD211 is skipped for the current final matrix analysis by user decision on November 21, 2026. Only HC1 is available, so its available-condition structure does not match the complete HC1-HC4 structure used for the other included participants. This is a completeness/analysis-structure exclusion, not an EEG-quality exclusion or a file-format error. Existing source data and historical outputs are preserved. See the [cohort decision and workbook source](../../../auto_fc_pipeline_v2/output/PCD_output/README.md).

The local raw inventory and the [participant policy](../../../auto_fc_pipeline_v2/output/PCD_output/participant_policy.json) define the review queue. Previously supplied Clean BP results are a separate processing version. Raw-review completion, downstream QC completion and eligibility for group statistics are tracked separately.

Before interval approval, present the proposed block-specific EEG channel list (including an empty exclusion list), supporting measurements and waveforms. Record the explicit channel decision and its scope separately from interval decisions. For retrospective confirmation, record the actual confirmation date.

### Python epoch screen for PCD raw interval review

[PCD109 HC2 reviewer](outputs/pcd109_review/HC2_python_epoch_review/Manual_Review/review.html) · [Per-second flags](outputs/pcd109_review/HC2_python_epoch_review/PreICA_QC/eeglab_epoch_flags.csv)

The PCD interval entry point uses a Python implementation of EEGLAB 2020.0 epoch joint probability and kurtosis (source tag commit `5fe9e2982f350ac90d0b48c2b215ea93b63efd38`). It uses 1000-bin empirical probabilities, per-channel and pooled epoch scores, sample-standard-deviation normalization across complete epochs, and a two-sided cutoff of six. Local tests use the original mapped positions 1 through 61. Global tests use all 63 mapped positions. Both omit explicitly blocked channels. These selections include auxiliary channels; the interval viewer displays the retained EEG channels. The CSV lists local triggers and global scores for inspection.

Epoch width and step both equal one second at the file sampling rate, starting at sample zero. The full last partial second is available for manual inspection and receives no automated score. The reference HC script constructs event latencies with a fixed 500-sample step. The project retains its configured MNE filtering and notch, named channel mapping, confirmed block-specific masks, and manual interval decisions. The reference uses EEGLAB filtering and CleanLine and combines probability, kurtosis and manual marks before removing epochs. This port covers interval scoring on the project input. An independent Python recomputation is a separate check from a comparison to a live EEGLAB output.

The new entry point bypasses the older chunk z-score and absolute PTP screens. Candidate intervals have exact epoch boundaries. Its initial PCD109 HC2 run covers 314 complete seconds and a 0.35-second tail at 1000 Hz. Previous reviewer exports and completed fits belong to their recorded screening version.

**ICA interval policy (November 8).** Exclude the union of complete seconds flagged by joint probability or kurtosis and all manually excluded intervals. Manual review may add exclusions. The last partial epoch retains its manual decision. For retrospective comparison, carry forward verified manual exclusions and channel decisions. The [17-block refit queue](outputs/yang_epoch_comparison_17hc/epoch_union_refit_queue.csv) and [merged exclusion intervals](outputs/yang_epoch_comparison_17hc/epoch_union_exclusions.csv) supersede the historical interval statuses below for this policy. All 15 refits completed November 12 (464 ICs). The [review index](outputs/pcd_epoch_union_refits_20261112/review_index.html) links each new workbook and its component maps, spectra and time courses. Each saved model was checked against its confirmed channels and decimated training sample count. Component review and backprojection are complete for all 15 refits, including PCD109 HC1. Open the CSV and XLSX directly in each block's ICA_Review/ folder. Use each block’s own ICA_Figures/ folder for maps, spectra and traces. PCD101 HC4 run01 and PCD102 HC1 run01 have equivalent training masks for those acquisitions alone. Both combined blocks have now been recomputed under the [multi-run plan](../../../auto_fc_pipeline_v2/output/PCD_output/README.md#raw-hc-run-selection-and-pooling).

**November 8 channel decision audit.** All 17 completed raw-review blocks through PCD109 HC1 have channel screens and saved ICA channel lists. PCD106 HC1–HC4 were retrospectively confirmed on November 8 to retain all 57 screened channels. Each saved ICA model contains the same 57 channels as its block screen; the channel lists match; interval-based refit status is recorded in the queue above. PCD109 HC1-HC3 were confirmed on November 8 to retain all 57 screened EEG channels. HC1 was confirmed retrospectively and its saved ICA channel list was verified. HC2 and HC3 channel confirmation precedes manual interval approval. PCD102 channel decisions were confirmed retrospectively on November 8: retain all 57 EEG channels in HC1–HC3 and exclude O1 in HC4 (64 of 564 complete seconds above fivefold). PCD101 used the TP7/CP1 mask across four fits. PCD105 HC1–HC3 used the C3 mask and HC4 used C3/F2. The PCD105 HC2/HC3 decision to retain F2 has separate retrospective confirmation. An applied mask alone establishes the fit inputs. Check the scope of any prior approval before crediting a whole-block channel decision. TCP coverage remains to be verified separately.

### Review entry points and results before the epoch-policy refits

The channel-screen tables and figures are in each original block's `Manual_Review` folder. They record the four closest available EEG electrodes in standard montage coordinates, complete one-second peak-to-peak measurements and representative waveforms. The links below open the current interval candidates. Approval of a prior model or interval list does not carry over to a changed fit.

| Participant | Block status |
| --- | --- |
| PCD101 | TP7 and CP1 were omitted for a fresh interval screen in [HC1](outputs/pcd101_hc1_channel_checked/channel_reviewed/Manual_Review/review.html), [HC2](outputs/pcd101_remaining/HC2/channel_reviewed/Manual_Review/review.html), [HC3](outputs/pcd101_remaining/HC3/channel_reviewed/Manual_Review/review.html) and [HC4 run01](outputs/pcd101_remaining/HC4/channel_reviewed/Manual_Review/review.html). HC1 interval review is complete. Blank personal decisions were resolved to include. Six excluded intervals removed 31.0 s, leaving 355.2 s for the 31-component ICA fit. The [reviewed component workbook](outputs/pcd101_hc1_channel_checked/channel_reviewed/reviewed_fit/ICA_Review/PCD101_HC1_ica_review.xlsx) records 17 exclusions and 14 retained ICs. The saved fit was backprojected with these decisions. HC2 retained its entire 276.0 s after interval review. ICA used 55 EEG channels and produced 32 components for [manual review](outputs/pcd101_remaining/HC2/channel_reviewed/reviewed_fit/ICA_Review/PCD101_HC2_ica_review.xlsx). The HC2 review retained 16 and excluded 16 ICs. The reviewed HC2 backprojection and v2 FC outputs are complete. HC3 excluded 20–21 s and retained 330.65 s for ICA. Of 31 components, 18 were retained and 13 excluded after [manual review](outputs/pcd101_remaining/HC3/channel_reviewed/reviewed_fit/ICA_Review/PCD101_HC3_ica_review.xlsx). The reviewed HC3 v2 output reached ROI rank 14/14 across the retained samples. HC4 run01 excluded 53.5–56.06 s, retaining 53.5 s for ICA. The saved ICA fit retained 15 components and excluded 14 after [manual review](outputs/pcd101_remaining/HC4/channel_reviewed/reviewed_fit/ICA_Review/PCD101_HC4_ica_review.xlsx). HC4 run01 reached ROI rank 14/14 over 53.5 retained seconds. Broadband, alpha and beta matrices on both the 14-ROI and pairwise-100 routes were checked for symmetry and finite off-diagonal values. Historical run01-only results were superseded by the approved and completed two-run HC4 combination. Earlier ICA fits and matrices predate the updated channel masks. |
| PCD102 | HC1–HC3 retain their reviewed fits. The [current HC4 interval reviewer](outputs/pcd102_review/HC4_O1_excluded/Manual_Review/review.html) uses 56 EEG channels after blocking O1. The new screen flagged six intervals. Manual review excluded 26.5–28.5 and 75.5–77.5 s and retained the rest (560.45 s). The 56-channel refit produced 31 ICs and stopped under the small-angle rule at iteration 189. [HC4 component review](outputs/pcd102_review/HC4_O1_excluded/reviewed_fit/ICA_Review/PCD102_HC4_ica_review.xlsx) is complete: 14 retained and 17 excluded. Four-block [updated matrices and QC](../../../auto_fc_pipeline_v2/output/PCD_output/outputs/raw_pilot_PCD102_four_blocks_HC4_O1_excluded) use 56 shared EEG channels. The previous 57-channel HC4 input is still represented in the [historical four-block QC report](../../../auto_fc_pipeline_v2/output/PCD_output/outputs/raw_pilot_PCD102_four_blocks/quality_review/split_stability.csv). Historical run01-only results were superseded by the approved and completed two-run HC1 combination. Its 49.15 s duration and split-half stability flag remain relevant. |
| PCD105 | All four interval/component reviews and backprojections are complete. Existing HC2/HC3 results retain F2 by explicit November 4 confirmation; HC1–HC3 exclude C3 and HC4 excludes C3/F2 upstream. Four-block common-inverse v2 and QC are complete using 55 common EEG channels. All four ROI ranks are 14/14. Alpha split stability is low in every block, and HC3 Fp1 has a retained-data amplitude flag. See the [v2 completion and QC record](../../../auto_fc_pipeline_v2/output/PCD_output/outputs/raw_pilot_PCD105_four_blocks/README.md). |

### PCD101 comparison after channel review, November 3, 2026

Paired checks used the earlier raw-review backprojections and the current channel-reviewed backprojections, with 55 common EEG channels, a common average reference recomputed for comparison, and overlapping accepted samples. Sensor spectra and amplitudes used complete two-second windows on the same recording-time grid. These checks compare the complete processing revisions, including changed ICA training samples and component decisions. They do not isolate channel exclusion as the sole cause.

| HC | Earlier/current retained seconds | Earlier/current median 35–55 Hz power fraction | Earlier/current alpha split FC r | Earlier/current beta split FC r |
| --- | --- | --- | --- | --- |
| HC1 | 280 / 355.2 | 8.97% / 8.20% | 0.488 / 0.635 | 0.319 / 0.374 |
| HC2 | 247.5 / 276 | 10.23% / 8.32% | 0.509 / 0.527 | 0.550 / 0.647 |
| HC3 | 242 / 330.65 | 8.82% / 6.71% | 0.211 / 0.208 | 0.267 / 0.347 |
| HC4 run01 | 32 / 53.5 | 11.71% / 11.29% | -0.031 / 0.101 | -0.210 / 0.141 |

High-frequency fractions are channel medians relative to 1–55 Hz power and cannot distinguish neural activity from artifacts by themselves. Split FC compares upper-triangle edges of symmetric-orthogonalized 14-ROI matrices from chronological halves of overlapping accepted source samples, using the saved per-block inverses, alpha 8–12 Hz, beta 13–30 Hz, two-second filter-edge trimming and 10 Hz envelopes. Each half contains 129.5, 109.25, 85.75 and 5.0 seconds respectively. HC4 overlap is too short to support a reliability conclusion. Its median two-second peak-to-peak amplitude increased from 18.65 to 25.87 µV, whereas HC1–HC3 changed from 26.82 to 23.78, 29.65 to 27.22 and 28.62 to 28.57 µV. Total retained time increased by 213.85 s (26.7%). The added samples have not been independently validated by this overlap comparison. The strongest stability improvement is HC1 alpha and HC2 beta. HC3 alpha remains weak. Updated four-block common-inverse QC remains pending.

### PCD101 HC4 acquisition details

The raw inventory lists two separate acquisitions on November 7, 2018. Run01 (`PCD2018_101_2_height4l.eeg`) began at 18:08:32 and lasted 56.06 s. Run02 (`PCD2018_101_2_height4_2.eeg`) began at 18:12:57 and lasted 266.10 s. Both have supplied ICA weights and component lists. The supplied `101_time_HC4_backproject.set` identifies the run01 EEG in its internal comments and contains 56,060 samples at 1,000 Hz.

The earlier raw-review output used run01 alone. The combined v2 result is available in the November 12 diagnostics. Following TTL reconstruction, the approved combination of both HC4 runs was completed, with a 209 s gap recorded as metadata. The incomplete run01 TTL code limits timing verification, not the processing status. For PCD102 HC1, combine both runs. For PCD109 HC4, use HC4_2 alone. Keep run boundaries during preprocessing. See the [run decisions, timing evidence and FC pooling steps](../../../auto_fc_pipeline_v2/output/PCD_output/README.md#raw-hc-run-selection-and-pooling).

### PCD102 HC1 run02 and the recurring F4 circle

F4 makes a cameo in several ICA maps. In IC10 its weight has the opposite sign to all four neighboring electrodes, so the interpolated contours close into a little ring. IC14 shows a ring in the same spot with reversed colors. The maps show scalp weights and carry no anatomical diagnosis. [ICA topographies](outputs/pcd102_review/HC1_run02_interval_review/reviewed_fit/ICA_Figures/ica_components_1.png)

F4 passed the amplitude screen across all 125 complete seconds. Its median peak-to-peak ratio to its neighbors was 0.56, yet its waveform correlations with F2, F6, AF4 and FC4 over retained samples ranged from 0.04 to 0.16. The run02 fit includes F4. The recurring circle warrants a closer look at the electrode trace before any decision to exclude the channel or an IC. [Channel screen](outputs/pcd102_review/HC1_run02_channel_screen/channel_screen.json)

## PCD105 HC3 recording-specific C3 exclusion

The HC3-specific decision marks C3 bad for this block, excluding it from interval screening, average reference and ICA fitting. Raw samples are preserved. Median one-second peak-to-peak amplitude was 807 µV at C3 versus 54–56 µV at C1/C5/CP3. C3 exceeded five times the neighboring median in 318 of 319 complete seconds. Recomputing the original automatic BAD screen and the interval screen using the remaining channels reduced the candidates from 21 intervals (101.2 s) to 5 (11.2 s). Use the [current interval viewer](outputs/pcd105_review/HC3_C3_excluded/Manual_Review/review.html) and its sibling PreICA/config for subsequent fitting. The original HC3 folder preserves the earlier screen. All five candidate intervals were approved for exclusion. The reviewed HC3 ICA fit used 308.0 seconds and 56 EEG channels, yielding 24 components for review in [reviewed_fit](outputs/pcd105_review/HC3_C3_excluded/reviewed_fit). The four-block downstream model uses the 55 common EEG channels (excluding C3 and F2); the existing HC3 ICA retains F2 as confirmed on November 4.

For the separate PCD102 HC1 statistical inclusion flag, see the [v2 QC record](../../../auto_fc_pipeline_v2/output/PCD_output/README.md#pcd102-hc1-quality-review-flag-raw-reprocessing-run01).

Next-push side task: package the interval viewer as a reusable function. Clicking an interval should populate its row number and exact start/end inputs and redraw the waveform. Verify the selection and saved decisions after a JSON export/import round trip.

This directory contains the extra-review topic, separate from the original v1 pipeline scripts. No analysis was rerun during relocation.

- scripts/: TCP screening, raw/PreICA evidence plotting, and isolated experimental ICA refitting.
- [Five-block pilot comparison](outputs/five_block_pilot_20261030_005542/comparison.html): 105 HC3, 409 HC4, 411 HC3, 102 HC1 and 406 HC3; new outputs stay here. See the [pilot README](outputs/five_block_pilot_20261030_005542/README.md) for decisions and limitations.
- outputs/tcp_preica_screen_20261030_003851/: 72-block screening, shortlist and evidence images.
- manual_preica_review_404/: complete 404 case with its own scripts/, src/, outputs/ and detailed README, including the manual viewer, interval decisions, ICA comparisons and old-HC4 backup.

The normal v1 scripts remain in ../scripts. Extra-review scripts reuse those existing functions when fitting or exporting; they do not duplicate the pipeline implementation. Current production 404 artifacts remain in ../outputs/TCP_output. Detailed case: [manual_preica_review_404/README.md](manual_preica_review_404/README.md).

Historical provenance can contain original absolute paths. These describe past runs; active script paths and the selected config have been updated. Original source data and production models were not changed.

### PCD105 HC2 interval approval, November 4, 2026

The existing viewer interval list was approved in chat. Excluded intervals: 0–1.5, 23.5–26, 26.5–28.5, 47.5–49.5, 232.5–235.5 and 285.5–286.85 s. Retained duration is 274.5 s. C3 remains the only blocked EEG channel (56 EEG channels for ICA). F2 retention in the existing upstream result was explicitly confirmed on November 4 after the screening comparison; the discussed 8–11.5 s disturbance was not added to the approved list. Confirmation is stored in `outputs/pcd105_review/HC2/channel_reviewed/Manual_Review/confirmed_interval_decisions.json`. The saved viewer preloads the approved choices. The 25-component fit is in `outputs/pcd105_review/HC2/channel_reviewed/reviewed_fit`. Component review is complete: excluded ICs 0, 2, 3, 4, 5, 8, 9, 11, 13, 15, 18, 19, 20, 21 and 22; retained 10 components. Explicit notes and decision fields agreed (`brian` interpreted as brain; original workbook unchanged). ICs 7, 14, 16, 23 and 24 remain provisionally included with unsure notes. The synchronized CSV is the backprojection input. Backprojection and per-block v2 are complete in `auto_fc_pipeline_v2/output/PCD_output/outputs/raw_pilot_PCD105_HC2_C3_excluded`. The ROI rank is 14/14 at relative tolerance 1e-6, with minimum/maximum singular value 0.110767 on the 274.5 accepted seconds. All six broadband/alpha/beta 14-ROI and pairwise-100 correlation matrices have finite off-diagonal values, are symmetric and bounded by [-1, 1]. F2 retention is now confirmed. Participant common-inverse and split-half QC are complete; see the current review table for limitations.

### PCD105 F2 screening comparison, November 4, 2026

[Before/after reviewer comparison](outputs/pcd105_review/F2_screen_comparison/comparison.html) recomputes both z-score QC and amplitude/flat flags from identical saved filtered samples. The C3-only baseline exactly reproduces each existing viewer. Adding F2 to the proposed screening mask leaves HC2 unchanged (12.35 s excluded, 274.5 s retained); HC3 changes only the terminal exclusion from 317.5–319.2 to 318.5–319.2 s (11.2 to 10.2 s excluded; 308 to 309 s provisionally retained). This is a screening comparison only: approved decisions, average reference, ICA models and v2 outputs are unchanged. No conclusion about F2 reliability or downstream improvement follows from these interval counts. Reproduction: `scripts/compare_channel_mask.py SOURCE DESTINATION --add-bad-channel F2`.

### PCD105 F2 retention decision, November 4, 2026

The current HC2 and HC3 results were explicitly accepted with F2 retained. This confirmation is recorded now, not attributed to an earlier review. Existing interval decisions, ICA fits, component decisions and backprojections remain unchanged; HC3 retains 308 seconds, not the alternative 309-second proposal. The comparison viewer is diagnostic only and was not applied. The decision is stored in `outputs/pcd105_review/F2_retention_confirmation.json`.

For the four-block common inverse, C3 and F2 are excluded downstream from every block because HC4 already excludes both upstream. This gives 55 common EEG channels, followed by a common average-reference policy. Excluding F2 from this downstream model does not alter the saved HC2/HC3 ICA fits. Original backprojections are copied byte-for-byte with hashes into `auto_fc_pipeline_v2/output/PCD_output/outputs/raw_pilot_PCD105_four_blocks/inputs`; channel alignment occurs in v2. Common-inverse FC and split-half QC are complete. All four blocks have ROI rank 14/14. See the linked v2 report for low split stability and the HC3 Fp1 amplitude flag; no upstream decision was changed by QC.

Single-block ICA fits store all figures directly in the fit’s `ICA_Figures/` directory. For example, the PCD refit review uses `PCD101/HC1/ICA_Figures/`. Shared output roots containing multiple recordings use `ICA_Figures/<participant>/<HC>/`.
## PCD110 HC2 channel review

AFz was blocked for interval screening, average referencing and ICA in HC2. Its one-second peak-to-peak amplitude was below one fifth of the neighboring median in all 253 complete seconds.

C2 was retained. Its peak-to-peak amplitude exceeded five times the median of FC2, CP2, C4 and Cz in 14 of 253 complete seconds. The median ratio over the recording was 1.15. This pattern supported reviewing individual bursts and provided insufficient evidence to block C2 throughout HC2. At 248–249 s, C2 reached 848 µV peak-to-peak against a neighboring median of 53 µV. At 249–250 s the values were 68 and 66 µV. The fivefold ratio flags intervals for inspection. The final partial epoch (253–253.60 s) was manually excluded. [Channel screen](outputs/pcd110_review/HC2/Manual_Review/channel_screen.json) · [Interval reviewer](outputs/pcd110_review/HC2_AFz_excluded/Manual_Review/review.html)

The confirmed interval decisions retained 247–249 s and excluded the six automatically flagged seconds plus the 0.60 s tail. ICA used 247.00 s and 56 EEG channels and yielded 19 components. [Confirmed intervals](outputs/pcd110_review/HC2_AFz_excluded/Manual_Review/confirmed_interval_decisions.json) · [Component review workbook](outputs/pcd110_review/HC2_AFz_excluded/reviewed_fit/ICA_Review/PCD110_HC2_ica_review.xlsx)

## PCD110 HC3 channel and interval review

The selected HC3 fit retains C2 and blocks AFz. The 11 automatically flagged seconds and the final 254–254.30 s were excluded. ICA used 243.00 s across 56 EEG channels and produced 14 components. [Confirmed intervals](outputs/pcd110_review/HC3_AFz_excluded/Manual_Review/confirmed_interval_decisions.json) · [Component review workbook](outputs/pcd110_review/HC3_AFz_excluded/reviewed_fit/ICA_Review/PCD110_HC3_ica_review.xlsx)

## PCD110 HC4 channel and interval review

The selected fit blocks AFz and retains C2, Fz and FCz. Fourteen automatically flagged seconds and the final 258–258.35 s were excluded, leaving 244.00 s and 56 EEG channels for the 24-component ICA fit. Use the [selected component review workbook](outputs/pcd110_review/HC4_AFz_excluded/reviewed_fit/ICA_Review/PCD110_HC4_ica_review.xlsx). The [C2 comparison](outputs/pcd110_review/HC4_C2_topography_comparison.html) documents the alternative fit.

## PCD111 channel review

The confirmed channel decision for HC1–HC4 excludes Fp1, Cz, O2 and O1 and retains the other 53 EEG channels in each block. Fp1, Cz and O2 showed sustained excess amplitude relative to neighboring electrodes. O1 showed sustained low amplitude. [HC1 interval reviewer](outputs/pcd111_review/HC1_Fp1_Cz_O2_O1_excluded/Manual_Review/review.html)

All four blocks completed epoch-union interval review, ICA component review and backprojection. Retained durations in HC1–HC4 order were 284, 299, 288 and 295 s. HC4 excluded the 17 automatically flagged seconds. Of its 15 fitted components, IC2, IC3, IC4, IC5 and IC6 were retained. [HC4 confirmed intervals](outputs/pcd111_review/HC4_Fp1_Cz_O2_O1_excluded/Manual_Review/confirmed_interval_decisions.json) · [HC4 component review](outputs/pcd111_review/HC4_Fp1_Cz_O2_O1_excluded/reviewed_fit/ICA_Review/PCD111_HC4_ica_review.xlsx) · [Participant FC and rank register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register)

## PCD112 channel and interval review

All four HC blocks excluded AFz and retained the other 56 EEG channels. After interval and component review, the backprojected recordings retained 262.00, 254.25, 245.10 and 297.00 seconds for HC1–HC4. HC4 kept P3 as a channel and excluded 174–175 s because the P3 deflection continued into the flagged 175–176 s epoch. The 18 automatically flagged seconds and final 316–316.8 s were also excluded. Component review retained 14 of 28 ICs. [HC4 confirmed intervals](outputs/pcd112_review/HC4_AFz_excluded/Manual_Review/confirmed_interval_decisions.json) · [HC4 component review](outputs/pcd112_review/HC4_AFz_excluded/reviewed_fit/ICA_Review/PCD112_HC4_ica_review.xlsx) · [Participant FC and rank register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register)

## PCD113 channel and interval review

All four blocks excluded Fp1 and retained 56 EEG channels. At 1000 Hz, retained durations after interval review were 342.65, 286.00, 272.00 and 273.00 seconds for HC1–HC4. HC1 retained its final partial second. HC2–HC4 excluded theirs. HC4 excluded the 12 automatically flagged seconds and 285–285.9 s. Component review retained 13 of 31 HC4 components, including IC21 (note spelled usnure, interpreted as unsure). IC30 was excluded. [HC4 confirmed intervals](outputs/pcd113_review/HC4_Fp1_excluded/Manual_Review/confirmed_interval_decisions.json) · [HC4 component review](outputs/pcd113_review/HC4_Fp1_excluded/reviewed_fit/ICA_Review/PCD113_HC4_ica_review.xlsx) · [Participant FC and rank register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register)
## PCD114 channel and interval review

All four blocks retained all 57 EEG channels. Retained durations for HC1–HC4 were 302, 263, 270 and 279 seconds. HC4 excluded six automatically flagged seconds and the 285–285.65 s tail. Manual ICA review retained 7 of 23 HC4 components. IC15 was excluded as muscle. IC19's original note `msucle` was interpreted as muscle. [HC4 confirmed intervals](outputs/pcd114_review/HC4/Manual_Review/confirmed_interval_decisions.json) · [HC4 component review](outputs/pcd114_review/HC4/reviewed_fit/ICA_Review/PCD114_HC4_ica_review.xlsx) · [Participant FC and rank register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register)

## PCD115 channel and interval review

All four blocks retained all 57 EEG channels. HC1 through HC4 retained 280, 316, 279 and 278 seconds after interval review. HC4 excluded the 17 automatically flagged seconds and the 295–295.10 s tail. Manual component review retained IC12, IC14 and IC16 and excluded the other 18 components. The IC5 note classified it as muscle. The original IC1 note `musle` was interpreted as muscle. [HC4 confirmed intervals](outputs/pcd115_review/HC4/Manual_Review/confirmed_interval_decisions.json) | [HC4 component review](outputs/pcd115_review/HC4/reviewed_fit/ICA_Review/PCD115_HC4_ica_review.xlsx) | [Participant FC and rank register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register)

## PCD116 channel and interval review

All four blocks excluded Fp1 and AFz and retained 55 EEG channels. HC1 through HC4 retained 309, 281, 260 and 275 seconds respectively. HC4 excluded 17 automatically flagged seconds plus 13–14, 125–127, 294–295 and 296–296.30 s after visual review. Manual ICA review retained IC8, IC9, IC12, IC13 and IC16. IC14 and IC15 were excluded as channel noise. IC16 was retained with the note `unsure`. [Confirmed intervals](outputs/pcd116_review/HC4_Fp1_AFz_excluded/Manual_Review/confirmed_interval_decisions.json) · [HC4 component review](outputs/pcd116_review/HC4_Fp1_AFz_excluded/reviewed_fit/ICA_Review/PCD116_HC4_ica_review.xlsx) · [Participant FC and rank register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register)

## PCD117 channel and interval review

All four blocks retained all 57 EEG channels. HC1 through HC4 retained 268, 249, 263 and 270 seconds after interval review. HC4 excluded ten automatically flagged seconds and the final 280–280.85 s. Manual ICA review retained IC1, IC5, IC8 and IC9. Both IC10 and IC11 were excluded as muscle, and IC4 was excluded as eye artifact. [Confirmed intervals](outputs/pcd117_review/HC4/Manual_Review/confirmed_interval_decisions.json) · [HC4 component review](outputs/pcd117_review/HC4/reviewed_fit/ICA_Review/PCD117_HC4_ica_review.xlsx) · [Participant FC and rank register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register)

## PCD118 channel and interval review

Manual channel review confirmed exclusion of Fp1 alone for HC1–HC4. All four blocks retain the other 56 EEG channels. Fp1 exceeded five times its neighbors’ median peak-to-peak amplitude in every complete second (296/296, 277/277, 275/275 and 273/273, respectively). [HC1 interval reviewer](outputs/pcd118_review/HC1_Fp1_excluded/Manual_Review/review.html)

HC1 through HC4 retained 278, 267, 256 and 257 seconds after interval review. HC4 excluded 16 automatically flagged seconds and the final 273–273.10 s. All 22 components had explicit notes. Manual review retained IC4, IC5, IC6, IC7, IC8, IC11, IC15, IC17 and IC19. IC18 was excluded as muscle. [Confirmed intervals](outputs/pcd118_review/HC4_Fp1_excluded/Manual_Review/confirmed_interval_decisions.json) · [HC4 component review](outputs/pcd118_review/HC4_Fp1_excluded/reviewed_fit/ICA_Review/PCD118_HC4_ica_review.xlsx) · [Participant FC and rank register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register)
## PCD119 HC2 source metadata correction

On 2026-11-16 the reviewer manually changed the internal filename references from PCD_118 to PCD_119 in the source BrainVision header (DataFile and MarkerFile) and marker file (DataFile). The corrected source loaded at 1000 Hz for 284.95 s. Its 57 preprocessed EEG channels matched the existing aligned pre-ICA signals within numerical tolerance. [Source alignment record](../../../outputs/pcd_aligned/READ_ME.txt)

Manual channel review confirmed retention of all 57 EEG channels in each of PCD119 HC1–HC4. HC1 manual review excluded the 10 automatically flagged seconds and the final 280–280.60 s. ICA used the remaining 270 s. Manual component review retained IC3, IC4, IC5, IC7, IC11, IC13, IC28, IC30 and IC31. Backprojection excluded the other 25 components. [Confirmed intervals](outputs/pcd119_review/HC1/Manual_Review/confirmed_interval_decisions.json) · [HC1 component review](outputs/pcd119_review/HC1/reviewed_fit/ICA_Review/PCD119_HC1_ica_review.xlsx)

HC2 manual review excluded all 11 automatically flagged seconds and the final 284–284.95 s. ICA used 57 channels and 273 s of retained data, yielding 32 components. ICLabel classified IC18, IC20 and IC22 as Other. [Confirmed intervals](outputs/pcd119_review/HC2_identity_unverified/Manual_Review/confirmed_interval_decisions.json) · [HC2 component review](outputs/pcd119_review/HC2_identity_unverified/reviewed_fit/ICA_Review/PCD119_HC2_ica_review.xlsx)

HC2 component review used the original ICLabel probabilities. For the 18 components at or above 0.90, the ICLabel decision took precedence. All 18 notes agreed with that decision on retention or exclusion. For lower probabilities, the note took precedence and a blank note accepted ICLabel. Backprojection retained IC5, IC12, IC14, IC15, IC17, IC18 and IC30 and excluded 25 components. All 57 EEG channels had finite values across the retained 273 s.

HC3 manual review approved the 12 automatically flagged seconds, retained 282–283 s, and additionally excluded 283–284 s and the final 285–285.30 s. ICA used all 57 EEG channels and the remaining 272 s, yielding 33 components. [Confirmed intervals](outputs/pcd119_review/HC3/Manual_Review/confirmed_interval_decisions.json) · [HC3 component review](outputs/pcd119_review/HC3/reviewed_fit/ICA_Review/PCD119_HC3_ica_review.xlsx)

HC3 component review accepted ICLabel for the 17 components with probability at least 0.90 and used the notes for the remaining 16. Backprojection retained IC4, IC7, IC11, IC12, IC13, IC15, IC18, IC27, IC30 and IC32. All 57 EEG channels had finite values across the retained 272 s.

HC4 manual review excluded the 13 automatically flagged seconds, 2–3 s, 23–25 s and the final 285–285.10 s. ICA used all 57 EEG channels and the remaining 269 s, yielding 30 components. [Confirmed intervals](outputs/pcd119_review/HC4/Manual_Review/confirmed_interval_decisions.json) · [HC4 component review](outputs/pcd119_review/HC4/reviewed_fit/ICA_Review/PCD119_HC4_ica_review.xlsx)

HC4 component review accepted ICLabel for the 17 components with probability at least 0.90 and used the notes for the remaining 13. Backprojection retained IC5, IC10, IC12, IC15, IC18, IC21 and IC29 and excluded 23 components. All 57 EEG channels had finite values across the retained 269 s. [Four-block FC, rank and split-half results](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#pcd119-four-block-common-inverse-november-16-2026)

## PCD120 channel and interval review

Manual channel review confirmed all 57 EEG channels for HC1–HC4. HC1 manual review excluded the 21 automatically flagged seconds and the final 327–327.80 s. Both 1–22 s and 313–327 s were retained in full. ICA used 306 s and yielded 32 components. [Confirmed intervals](outputs/pcd120_review/HC1/Manual_Review/confirmed_interval_decisions.json) · [HC1 component review](outputs/pcd120_review/HC1/reviewed_fit/ICA_Review/PCD120_HC1_ica_review.xlsx)

HC1 component review accepted ICLabel for the 18 components with probability at least 0.90 and used the notes for the remaining 14. Backprojection retained IC2, IC3, IC4, IC5, IC7, IC10, IC11, IC12, IC13, IC15, IC16, IC21, IC23 and IC26. All 57 EEG channels had finite values across the retained 306 s.

HC2 manual review excluded the 19 automatically flagged seconds and the final 343–343.65 s. The Fp2 window at 69–70 s and CPz window at 312–313 s were among the automatic exclusions. The POz window at 78–79 s was retained. ICA used all 57 EEG channels and the remaining 324 s, yielding 31 components. [Confirmed intervals](outputs/pcd120_review/HC2/Manual_Review/confirmed_interval_decisions.json) · [HC2 component review](outputs/pcd120_review/HC2/reviewed_fit/ICA_Review/PCD120_HC2_ica_review.xlsx)

HC2 component review matched decisions by component ID. The 18 components with probability at least 0.90 followed ICLabel. The remaining 13 had explicit notes. Backprojection retained IC3, IC5, IC7, IC8, IC9, IC13, IC14, IC15, IC18, IC22 and IC23. All 57 EEG channels had finite values across the retained 324 s.

HC3 manual review excluded the 21 automatically flagged seconds, including 281–287 s, and the final 287–287.40 s. All remaining intervals were retained. ICA used all 57 EEG channels and 266 s of retained data, yielding 30 components. [Confirmed intervals](outputs/pcd120_review/HC3/Manual_Review/confirmed_interval_decisions.json) · [HC3 component review](outputs/pcd120_review/HC3/reviewed_fit/ICA_Review/PCD120_HC3_ica_review.xlsx)

HC3 component review retained IC3, IC5, IC6, IC7, IC8, IC9, IC10, IC13, IC14, IC23 and IC26. The saved ICA was backprojected with the 19 reviewed exclusions. All 57 EEG channels had finite values over the 266 retained seconds. The [HC4 interval reviewer](outputs/pcd120_review/HC4/Manual_Review/review.html) contains 26 automatically flagged seconds and a final partial epoch at 282-282.45 s pending manual review.

HC4 manual review excluded all 26 automatically flagged seconds and the final 282-282.45 s. ICA retained 256 s on 57 EEG channels and yielded 30 components. [Confirmed intervals](outputs/pcd120_review/HC4/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd120_review/HC4/reviewed_fit/ICA_Review/PCD120_HC4_ica_review.xlsx).

HC4 component review retained IC4, IC5, IC6, IC9, IC10, IC13, IC22 and IC28. Backprojection excluded the remaining 22 components. All four reviewed blocks completed the common-inverse FC analysis. [Rank and split-half results](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register)

## PCD201 channel and interval review

HC1 retained all 57 EEG channels. Manual review confirmed the seven automatic seconds, including 290-291 s, and four additional C2 seconds starting at 20, 22, 150 and 230 s. ICA used the remaining 280 s and yielded 22 components. [Confirmed intervals](outputs/pcd201_review/HC1/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd201_review/HC1/reviewed_fit/ICA_Review/PCD201_HC1_ica_review.xlsx).

HC1 component review and backprojection are complete. Decisions were matched by component ID. IC4, IC7, IC8, IC12, IC18 and IC19 were retained. All 57 EEG channels had finite values across the 280 retained seconds.

HC2 retained all 57 EEG channels and the 189-190 s C2 window. Manual review excluded the six automatically flagged seconds and the final 287-287.75 s. ICA used 281 s and yielded 24 components. [Confirmed intervals](outputs/pcd201_review/HC2/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd201_review/HC2/reviewed_fit/ICA_Review/PCD201_HC2_ica_review.xlsx).

HC2 component review and backprojection are complete. Decisions were matched by component ID. The 13 components with probability at least 0.90 followed ICLabel. The other 11 followed the review notes. IC3, IC4, IC5, IC7, IC11, IC14, IC15, IC16 and IC21 were retained. All 57 EEG channels had finite values across the 281 retained seconds.

HC3 retained all 57 EEG channels. Manual review confirmed the ten automatic seconds and the additional C2 intervals 24-25, 85-88 and 278-279 s. ICA used the remaining 264 s and yielded 25 components. [Confirmed intervals](outputs/pcd201_review/HC3/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd201_review/HC3/reviewed_fit/ICA_Review/PCD201_HC3_ica_review.xlsx).

HC3 component review and backprojection are complete. Decisions were matched by component ID. The 17 components with probability at least 0.90 followed ICLabel; the remaining eight followed the notes. Retained ICs: 3, 4, 5, 6, 8, 9, 12, 15, 21, 24. All 57 EEG channels had finite values across the 264 retained seconds.

HC4 channel review confirmed C2 exclusion for interval screening, average reference and ICA. C2 exceeded five times its neighbors in 29 of 274 complete seconds. The [56-channel interval reviewer](outputs/pcd201_review/HC4_C2_excluded/Manual_Review/review.html) flags 7 full seconds, including 0 of those 29 seconds. Manual review confirmed these seven seconds and the final 274-274.50 s. ICA used 56 channels and 267 retained seconds and yielded 23 components. [Confirmed intervals](outputs/pcd201_review/HC4_C2_excluded/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd201_review/HC4_C2_excluded/reviewed_fit/ICA_Review/PCD201_HC4_ica_review.xlsx).

HC4 component review retained IC2, IC3, IC4, IC5, IC7, IC8 and IC18. Backprojection excluded 16 components including IC20. Decisions followed ICLabel for 14 components at probability 0.90 or above and the notes for the remaining nine. Four-block common-inverse FC and split-half QC are complete using 56 common EEG channels. [Rank and stability results](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register)

## PCD203 channel review

Channel screening on the 57 filtered EEG signals in each block flagged persistent Fp1 and AF3 abnormalities. Fp1 exceeded five times its four-neighbor median in 400/400, 295/295, 280/290 and 290/290 complete seconds (HC1-HC4). AF3 exceeded it in 143, 134, 126 and 186 seconds. As a sensitivity check, AF7 was compared with F7 and F5, omitting Fp1 and AF3 from its comparison group. Its median ratio ranged from 1.04 to 1.14, with zero seconds below one fifth and 16 high seconds in HC1 only. [Neighbor comparison](outputs/pcd203_review/AF3_AF7_neighbor_check.png). Manual channel review confirmed exclusion of Fp1 and AF3 in HC1-HC4, retaining 55 EEG channels per block. The [HC1 interval reviewer](outputs/pcd203_review/HC1_Fp1_AF3_excluded/Manual_Review/review.html) shows the automatic flags and AF7 review intervals.

HC1 manual review confirmed 16 automatically flagged seconds, 15 additional seconds and the final 400-400.40 s. AF7 at 3-4 s was retained. ICA used 55 EEG channels and 369 s, yielding 34 components. [Confirmed intervals](outputs/pcd203_review/HC1_Fp1_AF3_excluded/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd203_review/HC1_Fp1_AF3_excluded/reviewed_fit/ICA_Review/PCD203_HC1_ica_review.xlsx).

HC1 backprojection retained IC7, IC8, IC12, IC15, IC16, IC18, IC20, IC23, IC28, IC29, IC30 and IC32. The other 22 components were excluded. All 55 retained EEG channels were finite across the 369 retained seconds. The [HC2 interval reviewer](outputs/pcd203_review/HC2_Fp1_AF3_excluded/Manual_Review/review.html) shows the six automatically flagged seconds and the final partial epoch at 295-295.90 s.

HC2 manual review confirmed all six automatically flagged seconds and the final 295-295.90 s. ICA used 55 EEG channels and 289 retained seconds, yielding 37 components. [Confirmed intervals](outputs/pcd203_review/HC2_Fp1_AF3_excluded/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd203_review/HC2_Fp1_AF3_excluded/reviewed_fit/ICA_Review/PCD203_HC2_ica_review.xlsx).

HC2 backprojection retained IC3, IC6, IC8, IC9, IC13, IC18, IC19, IC21, IC26, IC30, IC35 and IC36. The other 25 components were excluded. All 55 EEG channels were finite across the 289 retained seconds. The [HC3 interval reviewer](outputs/pcd203_review/HC3_Fp1_AF3_excluded/Manual_Review/review.html) flags six complete seconds and leaves the final 290-290.30 s for manual review.

HC3 manual review excluded six automatically flagged seconds, 207-211 s for the shared large excursion, and the final 290-290.30 s. ICA used 55 EEG channels and 280 retained seconds, yielding 34 components. [Confirmed intervals](outputs/pcd203_review/HC3_Fp1_AF3_excluded/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd203_review/HC3_Fp1_AF3_excluded/reviewed_fit/ICA_Review/PCD203_HC3_ica_review.xlsx).

HC3 backprojection retained IC5, IC8, IC10, IC12, IC19, IC20 and IC29 and excluded 27 components. The reviewer name and tags were shifted one column to the right in all 34 submitted rows and were aligned by component ID before applying the confirmed decision rule. All 55 retained EEG channels had finite values throughout the 280 retained seconds. The [HC4 interval reviewer](outputs/pcd203_review/HC4_Fp1_AF3_excluded/Manual_Review/review.html) flags 15 seconds across 14 intervals. The recording has 290 complete seconds.

HC4 manual review confirmed all 14 automatically flagged intervals (15 s total) and retained all other samples. ICA used 55 EEG channels and 275 retained seconds, yielding 35 components. [Confirmed intervals](outputs/pcd203_review/HC4_Fp1_AF3_excluded/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd203_review/HC4_Fp1_AF3_excluded/reviewed_fit/ICA_Review/PCD203_HC4_ica_review.xlsx).

HC4 backprojection retained IC4, IC6, IC13, IC16, IC18, IC19, IC26, IC30, IC31 and IC32, and excluded the other 25 components. At probability >=0.9 the ICLabel decision took precedence, including IC18 and IC31. IC30 was retained under its unsure note. All 55 retained EEG channels had finite values throughout the 275 retained seconds.

The four-block FC analysis is complete. See the [rank and split-half register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register).

## PCD204 channel review

Manual review confirmed Fp1 exclusion in all four HC blocks, retaining the other 56 EEG channels. Four-neighbor 1-second PTP screening found Fp1 above fivefold in every complete second of HC1-HC4 (320/320, 303/303, 297/297 and 68/68). Median ratios were 181.84, 121.63, 97.41 and 124.70. Neighbor waveform plots show large Fp1-local excursions throughout each block. Proposed decision is to exclude Fp1 in all four blocks and retain the other 56 EEG channels. HC2 AFz exceeds fivefold only at 0-1 s, with an onset oscillation that decays rapidly; proposed channel decision is to retain AFz and inspect this interval in the subsequent segment review. No other channels crossed the upper or lower ratio thresholds. HC4 source duration is 68.20 s. [HC1 evidence](outputs/pcd204_review/HC1/Manual_Review/channel_screen.png), [HC2 evidence](outputs/pcd204_review/HC2/Manual_Review/channel_screen.png), [HC3 evidence](outputs/pcd204_review/HC3/Manual_Review/channel_screen.png), [HC4 evidence](outputs/pcd204_review/HC4/Manual_Review/channel_screen.png).

PCD204 HC1 interval screening after Fp1 exclusion flags 12 intervals totaling 13 s. The final 320-320.70 s is pending manual review; an AFz oscillation grows toward the endpoint, so exclusion of this partial second is recommended. [HC1 reviewer](outputs/pcd204_review/HC1_Fp1_excluded/Manual_Review/review.html).

PCD204 HC1 manual review confirmed the 12 automatically flagged intervals totaling 13 s and exclusion of 320-320.70 s. ICA used 56 EEG channels and 307 retained seconds, yielding 33 components. [Confirmed intervals](outputs/pcd204_review/HC1_Fp1_excluded/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd204_review/HC1_Fp1_excluded/reviewed_fit/ICA_Review/PCD204_HC1_ica_review.xlsx).

PCD204 HC1 backprojection retained 18 ICs and excluded IC0, IC1, IC13, IC19, IC21, IC22, IC23, IC25, IC26, IC27, IC28, IC29, IC30, IC31 and IC32. All 56 retained EEG channels were finite throughout 307 retained seconds. The [HC2 interval reviewer](outputs/pcd204_review/HC2_Fp1_excluded/Manual_Review/review.html) flags 12 complete seconds, including 0-1 s with the previously identified AFz onset oscillation. The final 303-303.60 s awaits manual review.

PCD204 HC2 manual review confirmed all 12 automatically flagged seconds and exclusion of 303-303.60 s. ICA used 56 EEG channels and 291 retained seconds, yielding 30 components. [Confirmed intervals](outputs/pcd204_review/HC2_Fp1_excluded/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd204_review/HC2_Fp1_excluded/reviewed_fit/ICA_Review/PCD204_HC2_ica_review.xlsx).

PCD204 HC2 backprojection retained IC4, IC5, IC6, IC7, IC8, IC9, IC10, IC12, IC14, IC15, IC16 and IC18, excluding 18 components. All 56 retained EEG channels were finite throughout 291 retained seconds. The [HC3 interval reviewer](outputs/pcd204_review/HC3_Fp1_excluded/Manual_Review/review.html) flags 14 intervals totaling 17 complete seconds; the final 297-297.65 s awaits manual review.

PCD204 HC3 manual review confirmed all 14 automatically flagged intervals totaling 17 s and explicitly retained the final 297-297.65 s after tail inspection. Only Fp1 was blocked. ICA used 56 EEG channels and 280.65 retained seconds, yielding 30 components. [Confirmed intervals](outputs/pcd204_review/HC3_Fp1_excluded/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd204_review/HC3_Fp1_excluded/reviewed_fit/ICA_Review/PCD204_HC3_ica_review.xlsx). Component review is pending.

PCD204 HC3 component decisions were matched by component ID in the sorted workbook. Probability >=0.9 followed ICLabel; otherwise notes took precedence and blanks followed ICLabel. Backprojection retained IC2, IC3, IC4, IC5, IC7, IC9, IC10, IC12, IC14, IC15, IC16, IC19, IC20, IC21, IC25 and IC28 (16 total), excluding 14 components. All 56 retained EEG channels were finite throughout 280.65 retained seconds.

PCD204 HC4 interval screening, with the already confirmed Fp1 exclusion, flags 36-37 s by kurtosis (1 s total). The recording is 68.20 s long. The final 68-68.20 s remains pending manual review; endpoint inspection shows increasing AFz oscillation, so excluding that partial interval is suggested, not applied. [HC4 reviewer](outputs/pcd204_review/HC4_Fp1_excluded/Manual_Review/review.html) and [tail evidence](outputs/pcd204_review/HC4_Fp1_excluded/Manual_Review/tail_review.png). ICA has not been fitted for HC4.

PCD204 HC4 manual interval review confirmed exclusion of 36-37 s only and explicitly retained the final 68-68.20 s and all remaining samples. Only Fp1 was blocked. ICA used 56 EEG channels and 67.20 retained seconds, yielding 26 components. Topography, PSD and source figures and the component workbook were generated; component review is pending. This supersedes the earlier tail-exclusion suggestion. [Confirmed intervals](outputs/pcd204_review/HC4_Fp1_excluded/Manual_Review/confirmed_interval_decisions.json) and [component review workbook](outputs/pcd204_review/HC4_Fp1_excluded/reviewed_fit/ICA_Review/PCD204_HC4_ica_review.xlsx).

PCD204 HC4 component review was applied by component ID. IC9's eye? note was explicitly confirmed as exclude. Probability >=0.9 followed ICLabel, so IC23 was retained despite its channel note. Retained ICs: 2, 3, 4, 5, 7, 8, 11, 13, 15, 17, 18, 20, 23, 25 (14); the other 12 were excluded. All 56 retained EEG channels were finite across 67.20 retained seconds. Four-block FC and diagnostics are complete under PCD204_epoch_union_20261117.

PCD204 completion: all four blocks have 14/14 signed-ROI rank; all 24 primary FC matrices passed validation. Split-half centered r reached 0.5 in 2/12 combinations for 14 ROIs and 1/12 for 100 parcels. HC4 has only 67.20 retained seconds and low split-half agreement; this duration limitation is recorded in the [rank and stability register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register).


## PCD205 channel review

The 63 acquisition channels were selected by original channel name, omitting unmapped Ch21 and preserving AF4/RVEye; channel screening used the 57 EEG channels before average reference. Filtering followed the existing 1-55 Hz and 60 Hz notch configuration. No segment screening or ICA has been run. AF7 is proposed for exclusion in HC1-HC4, with the remaining 56 EEG channels retained, pending manual confirmation. Four nearest neighbors are F5, F7, Fp1 and AF3. Above-fivefold complete seconds: HC1 220/297, HC2 175/275, HC3 135/301, HC4 69/294. Median ratios: 7.666, 6.233, 4.592, 2.884. No other channel crossed the fivefold/one-fifth thresholds, and no EEG channel had a near-flat complete second. Waveform review shows repeated AF7-local spikes and shifts across separated windows; HC4 is less continuously affected and includes intervals resembling its neighbors, but also repeated local disturbances and large excursions near the end. Fivefold crossings are screening evidence, not an automatic whole-channel rejection rule. [Additional waveform windows](outputs/pcd205_review/AF7_additional_windows.png) and [proposal/evidence](outputs/pcd205_review/channel_review_proposal.json).

Manual channel review confirmed AF7 exclusion in HC1-HC4, retaining the other 56 EEG channels. HC1 interval screening flagged seven automatic seconds: 0-1, 8-9, 38-39, 53-54, 245-246, 290-291, 293-294. Waveform review additionally suggests excluding 296-297 s and the final 297-297.50 s because a shared downward shift and increasing oscillations develop around 296.7 s and continue to the endpoint. All interval decisions remain pending confirmation; no ICA has been fitted. [HC1 reviewer](outputs/pcd205_review/HC1_AF7_excluded/Manual_Review/review.html) and [tail evidence](outputs/pcd205_review/HC1_AF7_excluded/Manual_Review/tail_review.png).

PCD205 HC1 manual review confirmed all seven automatically flagged seconds, the additional 296-297 s, and the final 297-297.50 s; all remaining samples were retained. Total exclusion: 8.50 s. ICA used 56 EEG channels with AF7 excluded and 289 retained seconds, yielding 27 components. Component review is pending. [Confirmed intervals](outputs/pcd205_review/HC1_AF7_excluded/Manual_Review/confirmed_interval_decisions.json) and [ICA review workbook](outputs/pcd205_review/HC1_AF7_excluded/reviewed_fit/ICA_Review/PCD205_HC1_ica_review.xlsx).

PCD205 HC1 backprojection is complete. Decisions were matched by component ID; probability >=0.9 followed ICLabel, otherwise notes took precedence and blanks followed ICLabel. Retained IC3, IC5, IC8, IC12, IC20 and IC21 (6 total); excluded the remaining 21 components. IC13 retained the submitted eye tag. All 56 EEG channels were finite throughout 289 retained seconds. HC2 continues with the confirmed AF7 exclusion. Its automatic screen flags nine seconds: 0-1, 59-60, 115-116, 120-121, 123-124, 127-128, 135-136, 176-177 and 270-271. Tail inspection suggests excluding 275-275.50 s for growing rapid oscillations across multiple channels, pending manual confirmation. No HC2 ICA has been fitted. [HC2 reviewer](outputs/pcd205_review/HC2_AF7_excluded/Manual_Review/review.html) and [tail evidence](outputs/pcd205_review/HC2_AF7_excluded/Manual_Review/tail_review.png).

PCD205 HC2 manual review confirmed all nine automatically flagged seconds, additional 41-43 s for the shared abrupt excursion, and the final 275-275.50 s; all remaining samples were retained. Total exclusion: 11.50 s. ICA used 56 EEG channels with AF7 excluded and 264 retained seconds, yielding 25 components. Component review is pending. [Confirmed intervals](outputs/pcd205_review/HC2_AF7_excluded/Manual_Review/confirmed_interval_decisions.json) and [ICA review workbook](outputs/pcd205_review/HC2_AF7_excluded/reviewed_fit/ICA_Review/PCD205_HC2_ica_review.xlsx).


PCD205 HC2 component review and backprojection are complete. Decisions were matched by component ID in the sorted workbook. Probability >=0.9 followed ICLabel, otherwise notes took precedence and blanks followed ICLabel. Retained IC3, IC5, IC7, IC9, IC10, IC18, IC19, IC23 and IC24 (9 total); excluded the other 16. IC23 was retained despite its not brain note under the probability precedence rule; IC10 was retained under brain?. All 56 non-bad EEG channels were finite throughout 264 retained seconds.

PCD205 HC3 interval screening uses the confirmed AF7 exclusion, retaining 56 EEG channels. Nine automatic intervals total 13 seconds: 6-7, 64-65, 121-122, 159-160, 218-220, 249-250, 292-293, 295-297 and 298-301 s. The final 301-301.30 s awaits manual review. Tail waveform inspection shows growing rapid oscillations with a downward shift across multiple channels; exclusion of this partial second is recommended, not applied. HC3 ICA has not been fitted. [HC3 reviewer](outputs/pcd205_review/HC3_AF7_excluded/Manual_Review/review.html) and [tail evidence](outputs/pcd205_review/HC3_AF7_excluded/Manual_Review/tail_review.png).


PCD205 HC3 manual review confirmed all nine automatically flagged intervals totaling 13 s and exclusion of the final 301-301.30 s, with all other samples retained. Total exclusion is 13.30 s. ICA used 56 EEG channels with AF7 blocked and 288 retained seconds, yielding 23 components. The solution, ICLabel review workbook, topographies, PSD and source traces were generated. Component review is pending; backprojection has not been applied. [Confirmed intervals](outputs/pcd205_review/HC3_AF7_excluded/Manual_Review/confirmed_interval_decisions.json) and [ICA review workbook](outputs/pcd205_review/HC3_AF7_excluded/reviewed_fit/ICA_Review/PCD205_HC3_ica_review.xlsx).


PCD205 HC3 component review and backprojection are complete. Sorted workbook decisions were matched by component ID. Probability >=0.9 followed ICLabel, otherwise notes took precedence and blanks followed ICLabel. Retained IC3, IC5, IC8, IC10, IC11, IC14, IC16 and IC20 (8); excluded the other 15 components. IC10 and IC16 were retained under the submitted brain notes, and IC20 was retained under the automatic decision with an unsure note. All 56 non-bad EEG channels were finite throughout 288 retained seconds.

PCD205 HC4 interval screening uses the confirmed AF7 exclusion, retaining 56 EEG channels. Automatic flags total nine seconds: 0-1, 78-79, 123-124, 170-171, 226-227, 285-286, 286-287, 287-288 and 289-290 s. The final 294-294.40 s awaits manual review. Tail inspection shows rapid oscillations increasing toward the endpoint with a shared upward shift; exclusion of the partial second is suggested, not applied. No HC4 ICA has been fitted. [HC4 reviewer](outputs/pcd205_review/HC4_AF7_excluded/Manual_Review/review.html) and [tail evidence](outputs/pcd205_review/HC4_AF7_excluded/Manual_Review/tail_review.png).


PCD205 HC4 manual review confirmed all nine automatically flagged seconds and exclusion of the final 294-294.40 s, with all other samples retained. Total exclusion is 9.40 s. ICA used 56 EEG channels with AF7 blocked and 285 retained seconds, yielding 22 components. The solution, ICLabel review workbook, topographies, PSD and source traces were generated. Component review is pending; backprojection has not been applied. [Confirmed intervals](outputs/pcd205_review/HC4_AF7_excluded/Manual_Review/confirmed_interval_decisions.json) and [ICA review workbook](outputs/pcd205_review/HC4_AF7_excluded/reviewed_fit/ICA_Review/PCD205_HC4_ica_review.xlsx).


PCD205 HC4 component review and backprojection are complete. Decisions were matched by component ID; probability >=0.9 followed ICLabel, otherwise notes took precedence and blanks followed ICLabel. Retained IC3, IC5, IC6, IC10, IC12, IC14 and IC16 (7 total), excluding 15 components. IC12 was retained under unsure and IC16 under brain?. All 56 non-bad EEG channels were finite throughout 285 retained seconds.

PCD205 four-block FC and diagnostics completed November 18, 2026 under PCD205_epoch_union_20261117 (launch-date directory). All four blocks have signed-ROI rank 14/14 and all 24 primary FC matrices passed validation. Centered split-half r was below the exploratory 0.5 screen for all 12 block-band combinations on each route. This flags limited split-half agreement, not rank deficiency; no exclusion decision was inferred from this diagnostic. See the [rank and split-half register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register).


## PCD206 channel review (November 18, 2026)

The participant policy retains PCD206 for processing with additional quality review because the source notes say ICA performed really badly. Raw recordings were mapped by original channel name (63 mapped acquisition channels, including 57 EEG), filtered with the existing 1-55 Hz and 60 Hz notch settings, and inspected before average reference. No epoch screen, channel exclusion or ICA has been applied.

Proposed channel decision, awaiting manual confirmation: exclude AF7 and P7 in HC1-HC4 and retain the other 55 EEG channels. AF7 exceeded fivefold neighbor PTP in 471/471, 293/320, 286/298 and 286/286 complete seconds; median ratios were 110.54, 16.02, 15.59 and 46.14. Waveforms show large AF7-local jumps and drifts. P7 exceeded fivefold in 26/471, 17/320, 8/298 and 6/286 seconds, with median ratios 3.12, 3.67, 3.23 and 3.22. P7 is proposed for exclusion based on recurrent localized sharp transients visible in separated early/middle/late windows, not because it persistently crosses fivefold. Cardiac contamination is possible but not established. Some P7 intervals also contain shared physiological/background activity. [P7 additional windows](outputs/pcd206_review/P7_additional_windows.png).

Other screen flags are transient: HC1 C4 at 11-12 s, HC1 F5 at 5-6, 68-69, 71-72 and 244-245 s, HC2 F5 at 20-21 s, and HC2/HC3 CP6 at 0-1 s below one-fifth. CP6 low ratios coincide with larger onset oscillations in its neighbors and do not establish a flat or failed CP6 channel. Retain these channels and inspect the flagged intervals after channel confirmation. No channel had a near-flat complete second.

[HC1 evidence](outputs/pcd206_review/HC1/Manual_Review/channel_screen.png) | [HC2 evidence](outputs/pcd206_review/HC2/Manual_Review/channel_screen.png) | [HC3 evidence](outputs/pcd206_review/HC3/Manual_Review/channel_screen.png) | [HC4 evidence](outputs/pcd206_review/HC4/Manual_Review/channel_screen.png) | [Proposal](outputs/pcd206_review/channel_review_proposal.json).


### PCD206 channel confirmation and HC1 interval reviewer — 2026-11-18

Human confirmation obtained: HC1–HC4 exclude AF7 and P7; retain the other 55 EEG channels. The confirmed channel mask is recorded in `outputs/pcd206_review/channel_decisions.json`. HC1 screening was rerun after this mask, before average referencing and ICA.

HC1 reviewer: `outputs/pcd206_review/HC1_AF7_P7_excluded/Manual_Review/review.html`. Automatic epoch-union exclusions: 11–12, 14–19, 32–33, 38–39, 40–41, 76–77, 137–139, 165–166, 173–174 s (9 intervals, 14 s). Additional manual proposals cover F5 artifact episodes 0–14, 68–85 and 243–245 s; overlaps with automatic intervals are counted once, adding 31 s. These show channel-local excursions/abrupt level shifts absent from F7/F3/FC5, rather than merely shared activity or a fixed amplitude cutoff. The 471–471.65 s tail is also proposed for exclusion because of growing widespread terminal oscillations (0.65 s). Total proposed exclusion union: 45.65 s; proposed retained duration: 426 s of 471.65 s.

All interval proposals await human confirmation; no ICA has been fitted. Original automatic provenance is retained in reviewer rows, manual proposals are separately flagged, and my_decision remains blank. Context plots are saved alongside the reviewer as F5_boundary_review.png, F5_context_review.png and tail_review.png. F5 remains retained as a channel under the confirmed channel decision.


PCD206 HC1 final interval confirmation (2026-11-18): exclude only the automatic 14 s and terminal 471–471.65 s. All remaining intervals are retained, including the proposed F5 exclusions (0–14, 68–85, 243–245 s, except automatically excluded overlaps) and 28–30 s. This supersedes the preceding pending proposal: excluded 14.65 s, retained 457 s. AF7/P7 remain blocked; 55 EEG channels. Source hashes verified and confirmed annotations saved in reviewed_fit/PreICA before ICA fitting.

PCD206 HC1 ICA completed on the confirmed 457 s / 55 EEG channels: 22 components. ICA model, ICLabel review CSV/XLSX, topographies, PSD and source traces exported under HC1_AF7_P7_excluded/reviewed_fit. Component review is pending; no backprojection performed.


PCD206 HC1 component review completed (2026-11-18): prob >= 0.9 follows auto_exclude, otherwise note takes precedence and blank follows auto_exclude. Excluded ICs 0,1,2,4,6,7,8,10,12,18,19,20; retained 3,5,9,11,13,14,15,16,17,21. IC18 unsure note is superseded by high-confidence muscle classification per user rule. Sorted workbook mapped by component ID and CSV synchronized. Backprojection completed and verified finite, 55 nonbad EEG channels and 457 s retained.

PCD206 HC2 interval reviewer prepared with AF7/P7 blocked, 55 retained EEG channels. Automatic flags total 10 s across 9 rows (147–148 and 148–149 adjacent). Manual proposals, pending user approval: 20–22 s for F5 isolated level changes and recovery, and 319–320.40 s for growing terminal oscillations/drift. Total proposed exclusion 13.40 s, proposed retention 307 s. No HC2 ICA fit yet. Reviewer: outputs/pcd206_review/HC2_AF7_P7_excluded/Manual_Review/review.html.


PCD206 HC2 interval approval and ICA completed (2026-11-18): human confirmed the automatic 10 s plus 20–22 s and 319–320.40 s; all remaining samples retained. Total exclusion 13.40 s, retention 307 s. AF7/P7 blocked, 55 EEG channels. Source hashes verified; confirmed annotations and interval decisions saved. ICA fitted 25 components; review CSV/XLSX, topographies, PSD and source traces exported under outputs/pcd206_review/HC2_AF7_P7_excluded/reviewed_fit. Other IDs: [1, 2, 3, 7, 8, 12, 14, 16, 22]. Component review pending; no backprojection applied.


PCD206 HC2 component review and backprojection completed (2026-11-18). Applied priority: prob >= 0.9 follows ICLabel auto_exclude, otherwise note takes precedence, blank follows auto_exclude. Sorted XLSX matched by component ID; notes and row order preserved; CSV synchronized. Excluded 0,1,2,4,5,6,10,12,15,19,20,21,23,24; retained 3,7,8,9,11,13,14,16,17,18,22 (11/25). Backprojected FIF verified finite, 55 nonbad EEG channels and 307 retained seconds.

PCD206 HC3 reviewer generated after confirmed AF7/P7 blocking. Automatic exclusion: 0–1,8–9,92–93,115–116,152–153,235–236,282–283,286–287,296–297 s (9 s). Manual proposal: 297–298.35 s because widespread growing terminal oscillations start before the partial epoch; pending human approval. No HC3 ICA fit yet. Reviewer: outputs/pcd206_review/HC3_AF7_P7_excluded/Manual_Review/review.html; evidence tail_review.png.


PCD206 HC3 interval approval and ICA completed (2026-11-18): human confirmed automatic 9 s plus 297–298.35 s, all remaining samples retained. Total exclusion 10.35 s, retention 288 s. AF7/P7 blocked; 55 EEG channels. Source hashes and retained sample count verified. Confirmed decisions saved in Manual_Review/confirmed_interval_decisions.json and annotations applied to reviewed_fit/PreICA. ICA fitted 23 components, with review CSV/XLSX and topography/PSD/source-trace figures exported. Other IDs: [1, 2, 4, 6, 9, 10, 12, 15, 17, 22]. Component review pending; no backprojection applied.


PCD206 HC3 component review/backprojection completed (2026-11-18). User priority applied: prob >= 0.9 follows auto_exclude; otherwise note, with blank following auto_exclude. Workbook sorted order and notes preserved; CSV synchronized by component ID. Excluded ICs 0,1,2,3,5,11,13,14,16,18,19,20,21; retained 4,6,7,8,9,10,12,15,17,22 (10/23). Backprojected FIF verified finite, 55 nonbad EEG channels, 288 retained seconds.

PCD206 HC4 interval reviewer prepared with confirmed AF7/P7 exclusion. Automatic flags: 0–1,6–7,7–8,8–9,13–14,31–32,40–41,49–50,121–122,174–175 s (10 s; adjacent 6–9 s rows). Tail 286–286.80 s proposed for manual exclusion because of growing widespread terminal oscillations and common drift; human interval review pending. Reviewer: outputs/pcd206_review/HC4_AF7_P7_excluded/Manual_Review/review.html. No HC4 ICA fitted yet.


PCD206 HC4 interval approval and ICA completed (2026-11-18): human confirmed automatic 10 s plus 286–286.80 s; all remaining samples retained. Excluded 10.80 s; retained 276 s. AF7/P7 blocked, 55 EEG channels. Source hashes and retained sample count verified. Confirmed annotations saved to reviewed_fit/PreICA; reviewer decisions synchronized. ICA fitted 23 components with CSV/XLSX and topography/PSD/source-trace figures exported. Other IDs: [2, 4, 6, 7, 8, 10, 11, 12, 15, 20]. Component review pending; no HC4 backprojection yet.


PCD206 HC4 component review and backprojection completed (2026-11-18). Applied probability >=0.9 ICLabel priority, otherwise note priority with blank following ICLabel. Sorted workbook mapped by component ID; all notes and row order preserved; CSV synchronized. Excluded ICs 0,1,3,4,5,9,17,18,21,22; retained 2,6,7,8,10,11,12,13,14,15,16,19,20 (13/23). All 55 nonbad EEG channels were finite throughout 276 retained seconds. All four backprojections were verified and copied with matching SHA256 hashes into the v2 PCD206_epoch_union_20261118 run; FC and final diagnostics subsequently completed (see below).


PCD206 four-block FC and final diagnostics completed (2026-11-18), run PCD206_epoch_union_20261118. All four blocks use the confirmed AF7/P7 mask, retaining 55 EEG channels. HC1-HC4 retained 457/307/288/276 seconds and 10/11/10/13 reviewed ICs, respectively. All four signed-ROI time series have rank 14/14; all 24 primary FC matrices passed numerical checks. The centered split-half exploratory screen r >=0.5 was met by 1/12 block-band combinations on the 14-ROI route (HC3 broadband, 0.525190), and 0/12 on the 100-parcel route. This is limited split-half edge-pattern agreement, not rank deficiency or an automatic exclusion decision. Source-note quality concerns remain recorded. See the [rank and split-half register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register).


## PCD207 channel review (November 18, 2026)

Channel-only preparation completed for HC1-HC4: 57 EEG channels, existing 1-55 Hz filtering and 60 Hz notch, before average reference. No channel block, epoch screening or ICA has been applied. Proposed decision awaiting human confirmation: retain all 57 EEG channels in all four blocks. One-second PTP ratios versus the four nearest EEG neighbors (>5 or <0.2) and near-flat windows are inspection prompts, not automatic blocking rules.

HC1: No complete second crossed neighbor-ratio limits or was near-flat. F8 is relatively larger but shares neighboring activity in early/middle/late excerpts; insufficient evidence for whole-channel blocking.

HC2: AF3 crosses fivefold only at 14-15 s (1/386 seconds), with a localized step/drift. Its median ratio is 1.055 and separated windows track neighbors; retain channel and review transient in interval stage.

HC3: No ratio or flatline flags. AF3 has localized early transients, including around 19-20 s, despite not crossing fivefold; later separated windows track neighbors. Retain channel; inspect early intervals at the interval stage.

HC4: All 57 channels have some flags, confined to seconds >=310; no neighbor-ratio flags before 310 s. Terminal large excursions and widespread near-flat signals indicate a recording-tail problem rather than persistent failure of individual channels. Retain all channels; separately review the terminal interval including context from ~308 s before ICA. Exact exclusion boundaries await interval review.

HC4 filtered near-flat counts rise to 48/57 channels at 323-326 s, 53/57 at 326-327 s and 57/57 at 327-328 s. These terminal samples must be reviewed at the interval stage; the all-channel-retain proposal does not approve these time intervals. Original raw terminal values were checked and are finite but also contain very large excursions.

[Channel proposal](outputs/pcd207_review/channel_review_proposal.json) | [Early/middle/late evidence](outputs/pcd207_review/channel_early_middle_late.png) | [HC4 tail context](outputs/pcd207_review/HC4_tail_channel_context.png). Per-block ratio/neighbor plots and detailed statistics are in HC1-HC4/Manual_Review.


### PCD207 channel confirmation and HC1 interval reviewer (2026-11-18)

Human confirmed all 57 EEG channels retained in HC1-HC4; channel_decisions.json records empty bad-channel lists. HC1 epoch-union screen completed before average reference and ICA. Automatic exclusions total 9 s: 6-9, 11-12, 35-36, 41-42, 175-176 and 247-249 s (8 reviewer rows because 6-9 s has different statistical flags).

Manual proposals awaiting confirmation: 4-6 s for an abrupt widespread trough/irregular burst with recovery around 4.6-5.4 s; 295-296.05 s for growing terminal high-frequency oscillations consistent with residual/filter-edge ringing, including the 0.05 s partial epoch. Proposed total exclusion 12.05 s, retention 284 s of 296.05 s. No ICA fitted and no interval exclusions applied. Original automatic provenance preserved; manual proposals separately tagged, my_decision blank.

[HC1 reviewer](outputs/pcd207_review/HC1_all_channels/Manual_Review/review.html) | [Interval context](outputs/pcd207_review/HC1_all_channels/Manual_Review/interval_context.png) | [Raw/filtered supplementary context](outputs/pcd207_review/HC1_all_channels/Manual_Review/supplementary_context.png).


PCD207 HC1 interval approval and ICA completed (2026-11-18). Human confirmed all automatic 9 s plus 4-6 s and 295-296.05 s; all other samples retained. Excluded 12.05 s, retained 284 s. All 57 EEG channels retained. Source hashes and retained sample count verified; confirmed decisions synchronized to the reviewer and saved to Manual_Review/confirmed_interval_decisions.json; BAD annotations applied in reviewed_fit/PreICA. ICA fitted 28 components. Review CSV/XLSX, topographies, PSD and source traces are complete under HC1_all_channels/reviewed_fit. Component review is pending; no backprojection applied.


PCD207 HC1 component review/backprojection completed (2026-11-18). Probability >=0.9 follows ICLabel; otherwise note takes precedence, blanks follow ICLabel. Sorted workbook matched by component ID; notes and row order preserved; CSV synchronized. Retained ICs 4,5,8,9,13,16,17,23,24,25 (10/28); other 18 excluded. IC24 brain? retained; IC18 muscle excluded. Backprojected FIF verified finite for 57 EEG channels and 284 retained seconds.

PCD207 HC2 interval reviewer prepared with all 57 EEG channels retained. Automatic epoch-union flags total 20 seconds. Manual proposals: 14-16 s for AF3-local step/drift and recovery; 385-386.75 s for growing terminal oscillations including the partial epoch. Total proposed exclusion 23.75 s, retention 363 s. AF3 event at ~56.5 s is already covered by automatic 56-57 s. Human interval confirmation pending; no HC2 ICA fitted. [Reviewer](outputs/pcd207_review/HC2_all_channels/Manual_Review/review.html) | [AF3 and tail context](outputs/pcd207_review/HC2_all_channels/Manual_Review/AF3_tail_context.png).


PCD207 HC2 interval approval and ICA completed (2026-11-18). Human confirmed automatic 20 s plus 14-16 s and 385-386.75 s; all other samples retained. Excluded 23.75 s, retained 363 s; all 57 EEG channels retained. Source hashes and retained sample count verified. Confirmed decisions saved and synchronized to the reviewer, BAD annotations applied in reviewed_fit/PreICA. ICA fitted 28 components; CSV/XLSX, topographies, PSD and source traces exported under HC2_all_channels/reviewed_fit. Other component IDs: [21]. Component review pending; no backprojection applied.


PCD207 HC2 component review/backprojection completed (2026-11-18). Probability >=0.9 followed ICLabel; otherwise notes took precedence, blanks followed ICLabel. Sorted workbook synchronized by component ID, preserving notes and row order. Retained ICs 5,6,12,17,18,19,22,23,24 (9/28); remaining 19 excluded. IC15/21 muscle excluded; IC22/24 unsure retained. Backprojected FIF verified finite, 57 EEG channels, 363 retained seconds.

PCD207 HC3 reviewer prepared with all 57 EEG channels retained. Automatic epoch-union flags total 17 s. Pending manual proposals: 13-14, 19-22 and 24-26 s for AF3-local abrupt steps/recovery; 306-308.10 s for terminal growing oscillations/drift (307-308 s already automatic). Additional exclusion beyond automatic is 7.10 s; proposed total 24.10 s, retention 284 s. All my_decision fields remain blank; no HC3 ICA fitted. [Reviewer](outputs/pcd207_review/HC3_all_channels/Manual_Review/review.html) | [AF3 and tail evidence](outputs/pcd207_review/HC3_all_channels/Manual_Review/AF3_tail_context.png).


PCD207 HC3 interval approval and ICA completed (2026-11-18). Human confirmed automatic 17 s and all manual proposals: 13-14, 19-22, 24-26 and 306-308.10 s, including the final partial epoch (307-308 s already automatic). All other samples retained. Excluded 24.10 s, retained 284 s; all 57 EEG channels retained. Source hashes and retained sample count verified. Confirmed decisions saved and synchronized to reviewer; BAD annotations applied in reviewed_fit/PreICA. ICA fitted 28 components, with CSV/XLSX, topographies, PSD and source traces exported under HC3_all_channels/reviewed_fit. Other component IDs: []. Component review pending; no backprojection applied.


PCD207 HC3 component review and backprojection completed (2026-11-18). Probability >=0.9 followed ICLabel; otherwise note took precedence, blanks followed ICLabel. Sorted workbook synchronized by component ID with notes and row order preserved. Retained ICs 4,10,15,16,17,18,27 (7/28); remaining 21 excluded. IC24 muscle excluded, IC27 brain retained. Backprojected FIF verified finite, 57 EEG channels, 284 retained seconds.

PCD207 HC4 reviewer prepared with all 57 EEG channels retained. Automatic epoch-union flags total 22 s. Manual proposals: 0-2 s for opening decaying rapid oscillations; 306-308 s for AF3-local abrupt step/recovery; 308-328.15 s for widespread terminal bursts, huge excursions and near-flat tail, filling gaps between automatic flags and covering the partial epoch. Total proposed exclusion 32.15 s, retention 296 s. Near-flat tail caused a kurtosis precision-loss warning; automatic flags alone do not establish tail validity. Proposals remain pending human approval; no HC4 ICA fitted. [Reviewer](outputs/pcd207_review/HC4_all_channels/Manual_Review/review.html) | [Boundary evidence](outputs/pcd207_review/HC4_all_channels/Manual_Review/boundary_context.png) | [Overview and tail](outputs/pcd207_review/HC4_all_channels/Manual_Review/interval_context.png).


PCD207 HC4 interval approval and ICA completed (2026-11-18). Human confirmed all reviewer exclusions: automatic 22 s plus manual proposals 0-2 and 306-328.15 s (overlaps counted once). Total exclusion 32.15 s, retention 296 s; all 57 EEG channels retained. Source hashes and retained sample count verified. Confirmed decisions synchronized to reviewer and saved in Manual_Review/confirmed_interval_decisions.json; BAD annotations applied to reviewed_fit/PreICA. ICA fitted 26 components; CSV/XLSX and five topography/PSD/source-trace figures verified. Other IDs: [4, 10, 11, 15, 18, 20, 22, 23, 25]. Component review pending; no HC4 backprojection applied.


PCD207 HC4 component review/backprojection completed (2026-11-18). Probability >=0.9 followed ICLabel; otherwise note took precedence, blanks followed ICLabel. Sorted workbook synchronized by component ID, notes and row order preserved. Retained ICs 2,7,8,12,16,17,19 (7/26); remaining 19 excluded. IC2/16 unsure retained; IC25 excluded following the final human muscle note (overriding the earlier assistant unsure suggestion). All four backprojections verified finite, 57 EEG channels, retained HC1-HC4 seconds 284/363/284/296. Input copies SHA256-verified for PCD207_epoch_union_20261118; common-inverse FC processing pending completion.


PCD207 four-block FC and final diagnostics completed (2026-11-18), run PCD207_epoch_union_20261118. All four blocks retained 57 EEG channels. HC1-HC4 retained 284/363/284/296 seconds and 10/9/7/7 reviewed ICs. All four signed 14-ROI time series reached rank 14/14 at relative tolerance 1e-6; all 24 primary FC matrices passed validation. Centered split-half r >=0.5 was met by 3/12 block-band combinations on the 14-ROI route and 2/12 on the 100-parcel route. Minimum full-recording-versus-saved edge correlation was 0.99992042. These split-half statistics measure relative edge-pattern agreement and do not establish the cause of low agreement or constitute automatic exclusion. HC4 had 9 Other components and low ICLabel confidence before manual review; final decisions followed the human workbook. Input copies were SHA256-verified. See the [rank and split-half register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register).


## PCD208 completion - 2026-11-18

PCD208 completed 2026-11-18: five reviewed acquisitions form four HC results. All 57 EEG channels retained. Valid HC1-HC4 durations: 284.5, 276.5, 277.5, 228 s. Reviewed ICs retained: HC1 9/16, HC2 11/24, HC3 15/29, HC4 run01 10/21 and run02 11/17. Both HC4 runs were processed separately before downstream pooling (170 + 58 valid seconds); the 47.455 s physical gap contributes no observations. Stored boundary at 181.05 s verified in the extracted segment metadata. All four signed 14-ROI time series have rank 14/14 at relative tolerance 1e-6. All 24 FC matrices passed dimension, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 4/12 block-band pairs on the 14-ROI route and 4/12 on the 100-parcel route. Minimum full-versus-saved edge correlation 0.99986510. These exploratory stability checks measure relative edge-pattern agreement, not directionality, and are not automatic participant exclusion.

[Recording decisions](outputs/pcd208_review/README.md) | [Rank and stability register](../../../auto_fc_pipeline_v2/output/PCD_output/raw_review_fc_diagnostics.md#current-rank-and-split-half-fc-register).


## PCD209 channel review - pending approval

All four HC channel-only screens completed. Proposed block Fp1 in HC1-HC4, retain other 56 EEG channels. Fp1 exceeds 5x neighbor PTP in every complete second (301/301, 295/295, 286/286, 289/289), with persistent isolated fluctuations in early/middle/late excerpts. No interval screening or ICA yet. [Metrics and visual evidence](outputs/pcd209_review/README.md).


PCD209 HC1 interval approval/ICA completed 2026-11-18: Fp1 blocked, 56 EEG channels retained. Automatic 5 s plus approved 0-1,38-39,300.5-301.5 s exclusions: 8 s total, 293.5 s retained. ICA has 42 components; synchronized CSV/XLSX IDs and six figures verified. Manual component review pending, no backprojection. [Recording details](outputs/pcd209_review/README.md).


PCD209 HC1 manual review/BP complete: 22 ICs excluded, 20 retained, 293.5 s valid. IC24 high-probability Other retained per explicit rule despite muscle note. HC2 reviewer prepared with Fp1 blocked, automatic 14 s plus proposed 3-4,42.5-43,44-44.5 s exclusions; final 295-295.65 s proposed retain. Pending interval approval; no HC2 ICA. [Details](outputs/pcd209_review/README.md).


## PCD209 HC2 ICA ready - 2026-11-18

Automatic-only interval approval applied: 14 s excluded, 281.65 s retained; manual proposals 3-4, 42.5-43 and 44-44.5 s withdrawn, final 295-295.65 s retained. Fp1 blocked; other 56 EEG channels retained. ICA completed with 38 components. CSV/XLSX component IDs and labels/probabilities agree; all five topography/PSD/source-trace PNGs present. Other components: 0, 6, 15, 17, 18, 19, 21, 23, 24, 26, 27, 28, 29, 30, 31, 32, 34, 35, 36, 37. Manual component review pending; no backprojection performed. ICLabel reported the expected input-band warning (current protocol 1-55 Hz versus its recommended 1-100 Hz); protocol was not changed.


## PCD209 HC2 completed; HC3 reviewer ready - 2026-11-18

HC2: applied user rule by component ID, preserving sorted workbook and notes. Excluded ICs [1, 3, 4, 11, 12, 13, 15, 16, 17, 18, 19, 22, 23, 25, 26, 29, 30, 32]; retained [0, 2, 5, 6, 7, 8, 9, 10, 14, 20, 21, 24, 27, 28, 31, 33, 34, 35, 36, 37]. IC0 and IC20 unsure retained; IC6 and IC37 high-probability Other retained. Backprojection completed and verified finite, Fp1 bad, 56 retained EEG channels, 281.65 valid seconds.

HC3: approved channel choice unchanged (Fp1 only). Automatic exclusions 28-30,50-52,240-241 s (5 s total); pending user approval. Automatic-context and tail plot inspected. Tail 286-286.25 s has no clear terminal burst or clipping in this view; recommend retain, pending review. Only targeted windows inspected, not exhaustive visual review. No HC3 ICA fitted. Reviewer: HC3_Fp1_excluded/Manual_Review/review.html.


## PCD209 HC3 ICA ready - 2026-11-18

User confirmed automatic-only 5 s exclusion (28-30,50-52,240-241 s), retained final 286-286.25 s and all other samples. Source hashes verified and decisions synchronized. Separate reviewed_fit PreICA retains 281.25 s; Fp1 blocked, 56 EEG retained. ICA completed with 37 components; CSV/XLSX IDs, labels and probabilities verified, all five diagnostic figures present. Other IDs: [0, 4, 11, 13, 17, 18, 20, 21, 23, 24, 26, 27, 28, 29, 30, 31, 32, 36]. Awaiting component review; no backprojection performed.

Reviewer window update: shared viewer template and current HC3 reviewer reject End-Start >=60 s with explicit Chinese too-long message, identifying the plot as the previous valid interval. Interval buttons use at most 30 s. Boundary checks:59.999 accepted;60 and61 rejected with message. Applies to future reviewers; historical reviewers unchanged.


## HC3 completed; HC4 reviewer ready - 2026-11-18

HC3 user notes applied by component ID: 12 ICs excluded [1,7,8,12,13,14,19,22,23,24,33,35],25 retained. IC15 original note brian? preserved and interpreted as brain? (retain). High-probability Other IC26,27,30,32 retained. Sorted XLSX and CSV synchronized and verified. Backprojection finite; 56 retained EEG, Fp1 bad,281.25 valid seconds.

HC4 retains approved channel decision Fp1 blocked,other56 retained. Automatic exclusions 0-1,142-143,226-227 s (3 s total). Targeted automatic-context and tail windows inspected; no additional exclusion proposed from those windows. Final289-289.90 s provisionally retained: no pronounced terminal burst/clipping in inspected plot. This is targeted inspection,not exhaustive visual review. Reviewer pending user confirmation; no HC4 ICA run. Shared >=60s window message is included.


Reviewer UI language: English only, including validation messages and future additions. Updated shared template and generated PCD209 HC3/HC4 pages to use the English >=60-second warning.


## PCD209 HC4 ICA ready - 2026-11-18

User approved only automatic 0-1,142-143,226-227 s exclusions (3 s); final289-289.90 s and all other samples retained. Source hashes verified, reviewer/confirmation synchronized, annotations applied in separate reviewed_fit. Verified286.90 valid seconds, Fp1 blocked,56 EEG retained. ICA completed with39 components; CSV/XLSX IDs, labels and probabilities agree,all five diagnostic PNGs present. Other ICs: [12, 13, 15, 21, 23, 27, 28, 31, 34, 35, 37]. Manual component review pending; no backprojection performed.


## PCD209 four-block results - 2026-11-19

PCD209 completed manual ICA review and four-block common-inverse FC. Fp1 excluded in every block; other 56 EEG channels retained. Valid HC1-HC4 durations: 293.50, 281.65, 281.25, 286.90 seconds. Retained IC counts: 20/42, 20/38, 25/37, 23/39. All four signed 14-ROI time series have rank 14/14 at relative tolerance 1e-6. All 24 FC matrices passed dimension, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 1/12 block-band pairs on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-versus-saved edge correlation: 0.99969963. Limited split-half agreement is an exploratory QC flag, not rank deficiency or automatic participant exclusion.

[Current results and provenance](../../../auto_fc_pipeline_v2/output/PCD_output/outputs/PCD209_epoch_union_20261119/README.md).


## PCD212 channel review - 2026-11-19

Channel-only review completed for HC1-HC4. Recommend blocking AFz in all four and retaining the other 56 EEG channels; user confirmation pending. AFz is below 0.2x neighbors in every complete second, with median ratio about 0.02 and nearly flat early/middle/late excerpts. HC3 F5 exceeds 5x only at 216-217 and 228-229 seconds; retain the channel and review these intervals later. No interval screening or ICA performed. [Evidence and full metrics](outputs/pcd212_review/README.md).

PCD212 channel decision confirmed: AFz blocked in HC1-HC4; remaining 56 EEG retained. HC1 reviewer prepared: automatic 11 s plus proposed manual 81.5-82,184.5-185,377-380.70 s. User interval approval pending; no ICA. [HC1 reviewer](outputs/pcd212_review/HC1_AFz_excluded/Manual_Review/review.html).

## PCD212 HC1 ICA ready - 2026-11-19

ICA completed with33 components from56 EEG channels and369.00 retained seconds; AFz excluded. CSV/XLSX component IDs, labels and probabilities agree. 5 diagnostic PNGs exported. Other ICs: [5, 9, 19, 25, 26, 30]. Awaiting manual component review; no backprojection performed.

PCD212 HC1 completed:22 excluded/11 retained ICs,369 valid seconds,AFz blocked. HC2 reviewer ready with automatic11 seconds and proposed0-1,59.5-60,299-299.20 seconds;pending approval,no ICA.

## PCD212 HC2 ICA ready - 2026-11-19

User approved automatic11 seconds and manual0-1,59.5-60,299-299.20 seconds; all other samples retained. Source hashes verified, reviewer and confirmation synchronized. Applied12.70 seconds BAD annotations in separate reviewed_fit input, preserving acquisition time. Verified286.50 seconds retained,AFz excluded,56 EEG channels. ICA completed with32 components; CSV/XLSX IDs,labels and probabilities agree;5 diagnostic PNGs exported. Other ICs:[18, 21, 23, 26]. Pending manual component review; no backprojection.


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
