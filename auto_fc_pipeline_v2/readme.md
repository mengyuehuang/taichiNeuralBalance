# Tai Chi EEG Functional Connectivity Pipeline v2

## Current project status — 2026-11-23

**PCD: preprocessing/manual review and FC matrix calculations are complete for 33 participants across all four HC blocks (132 blocks). Group figures, QC summaries and the results-sharing package are complete.**

**TCP: awaiting continuation of review under the current protocol.** Previously computed TCP matrices remain available, but their existence does not establish completion of the current channel/interval/ICA review protocol. Next work is TCP review, with channel decisions confirmed before interval screening and component review. No new TCP review was started by this status update.

This is the current project status; dated completion statements below about earlier TCP computations describe historical runs, not completion of the forthcoming protocol-aligned review.


## Final reviewed PCD cohort and recording selection (2026-11-23)

Processing and FC matrix calculations are complete for 33 participants, each with all four HC blocks (132 block results). The final cohort excludes PCD103, PCD104, PCD107, PCD202 and PCD210 according to confirmed study notes; PCD211 was excluded by user decision because only HC1 is available. No local raw recordings were found for PCD108; this is a data-availability limitation, not an EEG-quality exclusion. None of these seven IDs is included in the final 33.

Two recordings contributed to one block for three included participants: PCD101 HC4, PCD102 HC1 and PCD208 HC4. All three combination decisions were approved and implemented; they are not pending or provisional processing decisions. Each acquisition was processed separately with boundaries preserved, and valid observations were pooled to calculate one matrix per block and frequency band. Recording gaps contributed no observations. Each participant counts once. PCD101 run01 has an incomplete TTL time code, limiting verification of timing continuity; this evidence limitation remains documented despite the completed combination. PCD109 HC4 used only the second recording (HC4_2), with no combination.

Historical 34-participant Clean BP summaries describe an earlier cohort/version and are not the current reviewed cohort. PCD119, PCD206 and PCD218 have historical quality notes but were reviewed and are included; completion does not erase their QC history.


> **Archive relocation (2026-11-21):** Historical PCD Clean BP inputs/results and TCP `corrected` were moved to [the persistent archive register](maintenance/archive_plan_20261121/README.md). Historical paths below describe the original run layout; restore instructions and exact mappings are in that archive. Current reviewed PCD and TCP `tcp_rank_harmonized` results remain local.


## Output organization

Both cohort workspaces live under the singular `output/` directory. Shared code remains in `shared_code/`; the dataset move does not change processing results.

- [PCD_output](output/PCD_output/README.md): PCD inputs, processing scripts, historical Clean BP results, raw-reviewed results and diagnostics.
- [TCP_output](output/TCP_output/README.md): TCP processing results and the existing cross-study diagnostic/delivery summaries.
- `shared_code/`: shared processing entry points in `scripts/`, core modules in `src/`, and maintained regression tests in `tests/`. Both cohorts use this code.
- `maintenance/`: compact migration/cleanup records. Delete disposable migration or validation helpers and staging copies once their work is verified; retain operational code, maintained regression tests and necessary audit results.

These directories were renamed on 2026-11-18 without rerunning processing. Participant/run subdirectories keep their existing structure. See the [migration and v1 path recheck](maintenance/path_migration_20261118/README.md).

See the [raw-reviewed PCD stability diagnostics](output/PCD_output/raw_review_fc_diagnostics.md) for participant and block results, review flags and the versions of the FC matrices checked.

This folder contains the downstream EEG source-connectivity workflow. It begins with the manually reviewed, ICA-cleaned HC recordings produced by v1 and ends with participant/block-level functional-connectivity matrices.

## TCP/PCD harmonization — 2026-10-30

The corrected PCD numerical implementation is shared with TCP: measured signal rank, removal of tiny storage residuals, rank-aware covariance/inverse estimation, signed source extraction, and the same FC definitions. Study-specific input paths, channel mapping and participant labels remain separate. This does not redo ICA or establish that the upstream preprocessing is identical; the [raw review protocol](../auto_fc_pipeline_v1/outputs/PCD_output/README.md) records the upstream decisions and refit queue.

**Completed: all 18 TCP participants, including 404, passed both FC routes (216 matrices per route; zero failed participants).** All 17 existing TCP participants passed input/channel/rank preflight. The isolated batch is [run_tcp_rank_harmonized.py](shared_code/scripts/run_tcp_rank_harmonized.py), with progress in [run_status.json](output/TCP_output/tcp_rank_harmonized/run_status.json) and outputs under [tcp_rank_harmonized](output/TCP_output/tcp_rank_harmonized/outputs). TCP404 ran after successful completion and verification of those 17 participants, and is now complete. Old `output/TCP_output/corrected` matrices are preserved; do not treat them as newly harmonized outputs. The five extra-review pilot ICA fits have not replaced their production BP inputs.

Compatibility testing identified a mean-handling issue: the rank basis is estimated on centered samples, so residual projection now also centers samples and restores each channel's mean. Previously the projection could remove a fixed baseline outside the varying signal subspace (TCP101 HC1: relative change 0.00211). The residual tolerance was not loosened. New runs record `projection_policy=centered_preserve_mean_v2` and numerical code hashes. [PCD compatibility audit](output/PCD_output/rank_corrected/projection_compatibility.json) measures the impact on historical PCD inputs; it is not by itself a proof of identical FC. Historical PCD output metadata must not be relabeled as newly recomputed.

The historical Clean BP compatibility audit covered 34 then-selected PCD participants / 131 available blocks; these counts do not describe the final reviewed cohort. Maximum relative projected-input difference is `1.6214e-8`; maximum per-channel mean difference is `2.00585e-5 uV`; maximum pooled empirical covariance relative difference is `6.7863e-9`. No pooled rank changed. These are negligible input-level differences, supporting preservation of historical PCD results pending downstream equivalence verification; they are not an FC recomputation or formal statistical approval. The audit includes annotated samples and does not reproduce the fitted shrunk covariance estimator.

### Cohort decisions and participant identity

The study-qualified [participant policy](output/PCD_output/participant_policy.json) records workbook cells and its source hash. Exclude **PCD103, PCD104, PCD107, PCD202 and PCD210** from the current cohort. These decisions do not exclude TCP participants with the same numeric suffix. PCD119, PCD206 and PCD218 have serious quality warnings and remain available for processing/manual review; they are not automatically approved or treated as explicitly excluded. PCD208 HC4 combining is approved: both raw acquisitions are selected with a 47.455 s gap and run boundaries preserved. Raw channel/interval/ICA reviews and pooled four-block FC are complete (PCD208_epoch_union_20261118); historical Clean BP alternatives remain held (see the PCD run-selection record). Existing files from excluded participants are retained for provenance, not group analysis.

The final reviewed PCD cohort contains **33 participants / 132 HC blocks**. The earlier provided-Clean-BP selected cohort contained 34 participants. The [selected-cohort QC view](output/PCD_output/rank_corrected/qc_validation/selected_cohort/validation_summary.json) filters historical QC to 34 PCD plus 17 TCP. It still uses historical TCP results and must be refreshed after harmonized results and their QC are complete.

PCD101, PCD203, and PCD213 are confirmed to be three distinct participants. The master sheet lists GLOBAL_ID 1012 for all three. The entries for PCD203 and PCD213 are incorrect, as supported by their age, height, and weight records. Retain all three participant IDs and count each separately under the usual inclusion and QC rules. This identity decision also applies when using the current sheet ahead of a corrected version. Other repeated IDs and reused numbers across studies still require independent reconciliation before formal statistics.

## Rank diagnosis and preliminary study display

Across the 18 harmonized TCP records, all 72 blocks support 14 ROI dimensions. For the 34 historical selected Clean BP PCD records, 97 of 131 blocks (30 participant folders) have both source-input and ROI rank below 14. In all 97, the sampled ICA-channel rank of the original Clean BP matches its stored mixing-map column count. On all stored channels, 96 already have rank below 14. The exception, PCD209 HC3, has rank 14 across all BP channels, 12 within the ICA channel subset and 13 at source input. See [block audit](output/TCP_output/study_fc_display/pcd_bp_rank_trace.csv).

For PCD101 HC1 the supplied Clean BP had sampled rank 11 within its ICA channels and rank 12 across all channels. The source-input and ROI ranks were both 12. The [first raw-reviewed fit](output/PCD_output/outputs/raw_pilot_PCD101_HC1/pilot_result.json) reached ROI rank 14/14 before block-specific channel exclusion. Recheck rank and stability after the planned epoch-policy refit.

The [preliminary study figure](output/TCP_output/study_fc_display/study_mean_corrected_fc.png) summarizes the available blocks within each participant and weights participant folders equally. Each alpha/beta panel has a labeled scale. Updated signal-quality assessment and reconciliation of other repeated IDs remain pending.

## Current PCD group display (2026-11-21)

The [reviewed 33-participant PCD display](output/PCD_output/group_fc_display/README.md) supersedes the historical PCD panel in the preliminary study figure above. `shared_code/scripts/refresh_fc_display.py` now builds PCD-only figures from reviewed epoch-union results using the reference Step0b group-plot method. It does not refresh historical TCP or Clean BP panels.

## Configuration and result versions

`config.hc_corrected.example.json` now enables `rank_policy=data_relative` with tolerance `1e-6`. Its default destination is `output/TCP_output/new_rank_corrected_runs`, protecting the completed `output/TCP_output/tcp_rank_harmonized/outputs` and historical `output/TCP_output/corrected` directories. v1's reviewed BP input remains `../auto_fc_pipeline_v1/outputs/TCP_output/Backprojected` relative to this pipeline directory. Set raw/montage paths in local configurations; generated run configs store absolute paths and are excluded from Git.

Code, tests, templates, example configs and cohort rules belong in Git. Data, references, results, QC reports, images, arrays, logs, run status and generated configs belong in the separate local/Drive archive. Restore local artifacts before using output links in this README. See [repository sharing instructions](../README.md#git-versus-google-drive).

## Research Design

- Groups: younger adult controls (YAC), older adult controls (OAC), and older adult Tai Chi practitioners (TCOA), using the documented ID lists. Available HC data currently contain 5 YAC, 1 OAC, and 12 TCOA participants; these are not balanced groups.
- Recordings: four HC blocks per participant when available.
- Conditions:
  - `HC1` and `HC4`: non-perturbation.
  - `HC2` and `HC3`: perturbation.
- Frequency bands:
  - broadband: quality-control reference.
  - alpha: 8-12 Hz.
  - beta: 13-30 Hz.
- Main outcome: static, undirected functional connectivity computed over the full usable recording.

The group comparison is observational. The matrices measure association between regions; they do not show which region causes activity in another region, and they do not by themselves establish that Tai Chi caused a group difference.

## Complete Logic Chain

```text
Raw BrainVision EEG
  -> v1 preprocessing and ICA
  -> manual IC exclusion decisions
  -> cleaned/backprojected HC FIF files
  -> common participant-level inverse model
  -> source-space ROI time series
  -> per-continuous-segment alpha/beta filtering and edge trimming (broadband skips this)
  -> symmetric (14 ROI) or pairwise (100 parcel) leakage correction
  -> Hilbert amplitude envelopes and route-specific temporal reduction
  -> Pearson correlation
  -> raw-r and Fisher-z FC matrices
  -> group and condition analysis
```

v1 owns preprocessing, ICA review, and backprojection. v2 starts from the cleaned/backprojected HC files; it does not repeat IC classification.

## Primary and Secondary Routes

| Route | Leakage correction | Intended role | Reason |
|---|---|---|---|
| 14 ROIs | Symmetric orthogonalization | Primary analysis | The number of ROI signals is below the usable EEG rank, so simultaneous correction is mathematically supported. |
| 100 parcels | Pairwise orthogonalization | Secondary visualization/QC | Cleaned sensor rank for participants 101-103 was 43-52 (relative SVD tolerance 1e-6), below 100. Pairwise correction does not require 100 jointly independent signals. |

The primary 14 ROIs are the seven Schaefer functional networks in each hemisphere. The 100-parcel route is retained to generate 100 x 100 matrices, but it must not be described as equivalent to the rank-valid 14-ROI symmetric analysis.

## Methods

### 1. Cleaned EEG input

The preferred input is the v1 backprojected HC file after manual ICA decisions have been applied. The six non-source channels are excluded:

```text
GND, LHEye, RHEye, RVEye, Lneck, Rneck
```

This leaves 57 scalp EEG channels for source modeling. Existing `BAD_*` and boundary annotations are preserved.

### 2. Forward and inverse model

The workflow uses:

- MNE `fsaverage` anatomy.
- ico5 source space.
- eLORETA inverse solution.
- `SNR = 3`, therefore `lambda2 = 1/9`.
- `loose = 0.2`.
- `depth = 0.8`.
- minimum source-to-inner-skull distance of 5 mm.
- average-reference projection.
- MNE noise-covariance model selection between shrunk and empirical estimators.
- signed normal-orientation estimates: `pick_ori="normal"`.

One common inverse operator is built per participant from all available HC blocks. This keeps the source model consistent across that participant's perturbation and non-perturbation recordings. For blocks with multiple raw acquisitions, see the [PCD run selection and segment pooling plan](output/PCD_output/README.md#raw-hc-run-selection-and-pooling).

### 3. ROI extraction

The extractor processes the recording in 2-second chunks. This avoids allocating a very large whole-recording source estimate in memory. Each chunk is projected into source space and reduced immediately into 14 signed ROI and, by default, 100 signed parcel time series using `mean_flip`. Both resolutions reuse the same inverse projection. These chunks are a memory strategy, not separate FC analysis windows.

Annotated bad/boundary periods remain represented in the timeline. For band-specific analysis, unusable or too-short clean fragments are skipped and the retained duration is recorded.

### 4. Leakage correction and envelopes

For the 14-ROI route:

1. For alpha and beta, band-pass filter each valid continuous fragment and trim filter edges.
2. Center the retained signals and symmetrically orthogonalize them jointly; check rank first.
3. Compute Hilbert amplitudes separately within each continuous fragment.
4. Resample each envelope fragment to a target 10 Hz with MNE FFT anti-alias resampling, matching Step0.
5. Concatenate the reduced envelopes across fragments, retaining the full usable recording rather than selecting HMM states.
6. Calculate Pearson correlation between every ROI pair.

The 100-parcel route instead uses pairwise correction and approximately 8 Hz block-mean envelope reduction, matching Step0b. It does not apply simultaneous symmetric correction to 100 signals. QC defines within-network edges as same network **and same hemisphere**, while Step2b network features pool hemispheres. The 14-ROI comparison embedded in 100-parcel QC also uses 10 Hz FFT resampling.

10 Hz is the envelope sampling rate, not the EEG frequency band and not a recording duration. It represents envelope strength about every 0.1 seconds. Anti-alias filtering removes fast envelope fluctuations before reducing the sampling rate. Whole clean segments still contribute to FC; rounding can make the effective segment rate differ slightly from the target.

No connectivity threshold is applied, and correlations are not automatically converted to absolute values.

### 5. Matrix outputs

Each block and frequency band produces:

- raw Pearson-correlation matrix (`raw_r`).
- Fisher-z transformed matrix (`fisher_z`).
- compressed NPZ containing matrices and metadata.

The raw-r diagonal is 1. The Fisher-z diagonal is stored as 0 because self-connectivity is not analyzed.

## Primary Workflow

Run commands from the repository root.

### One-command participant run

The normal entry point handles reviewed v1 backprojection and then runs the five v2 stages for one participant, including both resolutions by default. Use `--route 14` for the primary route only. Backprojection is rebuilt if its FIF is missing or older than the PreICA input, saved ICA solution, or manual review CSV.

The current v2 config is `config.hc_corrected.example.json`; obsolete legacy
`config.example.json`/`config.local.json` files were removed. Relative paths in
this config resolve from the repository root. V1 relative paths resolve from
the v1 config directory. The runner checks that both configs refer to the same
Backprojected folder before doing any computation. A newer review XLSX also
invalidates backprojection reuse, and v1 refuses to proceed if manual XLSX/CSV
fields differ. Sync the human-reviewed workbook to CSV before rerunning.

Resume options deliberately trust completed upstream stages. After editing IC
decisions, start at 0; do not use `--start-at 4/5` with an old inverse or old source
time series. A scientific config change likewise requires rerunning its affected
stage and all later stages. Input timestamps do not detect every config change.

```powershell
python .\auto_fc_pipeline_v2\shared_code\scripts\run_participant.py 101
```

To resume after an already completed stage, use `--start-at`. For example, to reuse the prepared EEG and existing inverse operator and restart ROI extraction:

```powershell
python .\auto_fc_pipeline_v2\shared_code\scripts\run_participant.py 101 --start-at 4
```

Stage `0` applies explicit `TRUE` decisions from `review_exclude1/2/3` in the v1 review CSV using the saved ICA solution. Blank and `FALSE` cells do not exclude a component; note text and ICLabel predictions do not override these columns. This does not establish that every retained component has a finalized human review. The step does not refit ICA. For participant 102, four HC files were backprojected in under 30 seconds. In the 2026-10-13 cohort run, both routes together took approximately 10-14 minutes per participant locally, including source modeling and extraction where needed. Colab was not required; runtime and memory needs vary with the computer and recording length.

The individual commands below remain available for debugging or rerunning one stage.

### Step 0: create the reviewed Backprojected inputs

This stage is included automatically in `run_participant.py`. It reads the v1 PreICA FIF, saved ICA solution, and participant's manual ICA review CSV, then applies the reviewed exclusions and writes the cleaned/backprojected FIF. It stops if a review CSV has no exclusion marked. It reruns when the existing output is older than its input, ICA model, or review CSV.

The direct v1 command is:

```powershell
python .\auto_fc_pipeline_v1\scripts\04_run_ica.py `
  --config .\auto_fc_pipeline_v1\config.local.json `
  --backproject-only `
  --include-regex '^101_HC'
```

### Step 1: inventory and prepare blocks

```powershell
python auto_fc_pipeline_v2/shared_code/scripts/01_prepare_blocks.py `
  --config auto_fc_pipeline_v2/config.hc_corrected.example.json `
  --subject 101
```

This identifies available HC inputs and creates the block-level working files expected by v2.

### Step 2: verify montage and source channels

```powershell
python auto_fc_pipeline_v2/shared_code/scripts/02_check_montage_and_channels.py `
  --config auto_fc_pipeline_v2/config.hc_corrected.example.json `
  --subject 101
```

This checks channel names, montage coverage, and the channel set used for source localization.

### Step 3: build the common inverse operator

```powershell
python auto_fc_pipeline_v2/shared_code/scripts/02_source_localization_hc_blocks.py `
  --config auto_fc_pipeline_v2/config.hc_corrected.example.json `
  --subject 101 --run --inverse-only
```

`--inverse-only` is intentional. It saves the participant-level inverse operator without creating a very large full-duration source estimate.

### Step 4: extract signed source time series

```powershell
python auto_fc_pipeline_v2/shared_code/scripts/03_extract_14roi_timeseries.py `
  --config auto_fc_pipeline_v2/config.hc_corrected.example.json `
  --subject 101
```

This direct command writes 14-ROI files. Add `--include-parcels` to extract both resolutions, as the default runner does. `03_extract_parcel_timeseries.py` is an equivalent entry point for both resolutions and accepts the same config, subject, and chunk-size arguments. No full-duration STC or legacy global manifest is needed.

### Step 5: calculate whole-recording FC

```powershell
python auto_fc_pipeline_v2/shared_code/scripts/04_whole_recording_fc14.py `
  --config auto_fc_pipeline_v2/config.hc_corrected.example.json `
  --subject 101
```

This generates broadband, alpha, and beta raw-r/Fisher-z matrices and a participant summary figure.

## Output Structure

```text
auto_fc_pipeline_v2/output/TCP_output/new_rank_corrected_runs/
  <participant>/
    01_block_level_eeg/
      cleaned/backprojected HC working files
      montage_aligned/
      preparation and channel-check reports
    02_source_model/
      participant inverse operator and forward model
      source-model plan/metadata
    03_roi_timeseries/
      signed_rois14.npz and signed_parcels.npz files per HC block
    04_static_fc/
      matrices/
        raw-r CSV matrices
        Fisher-z CSV matrices
        matrix/metadata NPZ files
      figures/
        participant summary PNG
      tables/
        participant network-feature CSV
      pairwise_100parcels/
        100-parcel raw-r/Fisher-z CSVs and matrix/metadata NPZs
        <participant>_fc100_summary.png (one uncorrected-versus-corrected QC summary)
        recording_qc.csv and network-feature table
```

### How to read the output

- One participant has several files because each HC block and each frequency band is a separate measurement.
- Four HC blocks x three bands gives 12 matrices per resolution for a participant with complete recordings.
- The CSV files are easy to inspect and use in statistics.
- The NPZ files preserve matrices plus processing metadata for reproducibility.
- `<participant>_fc14_summary.png` places all block/band matrices in one review figure; it is a visual summary, not an additional analysis result.
- The 14-ROI figure uses a separate symmetric color limit for each participant/band
  (99th percentile of absolute off-diagonal values, minimum 0.1), shared across HC
  rows. Its diagonal is hidden. Compare numbers/color bars, not color intensity
  across different participants. The 100-parcel figure uses the display convention below.

For Drive review, share each completed participant's entire `04_static_fc` folder
plus this README. Keep PNG, CSV, NPZ, and QC/feature tables together. Source FIFs,
inverse files, and time-series NPZs are optional separate reproducibility exports,
not required for routine review. Include 404 from the harmonized directory; its updated signal-quality QC remains pending.

### Why the participant summary is mostly red

The participant summary displays raw 14-ROI amplitude-envelope correlations. Slow, shared changes in envelope strength often make these raw correlations predominantly positive. Small negative values are retained and appear blue; the code does not take an absolute value.

The reference `FC_group_matrices_leakage_corrected.png` is not the same quantity. It shows group-averaged Schaefer-100 Fisher-z matrices after removing each participant's brain-wide shared component by double-centering. Its colors therefore mean positive or negative *relative to the participant's brain-wide mean*, which naturally produces both red and blue cells. It also combines participants and uses 100 parcels, whereas the v2 summary shows one participant and 14 ROIs. The two color patterns should not be compared as if they were generated at the same analysis stage.

## Current Verified Status

### 2026-10-30 delivery audit update

The October 13 counts below describe legacy TCP outputs, not a newly harmonized cohort. The read-only `shared_code/scripts/audit_matrix_delivery.py` check currently finds 204 TCP 14-ROI matrices and 204 TCP 100-parcel matrices across 17 participants. PCD rank-corrected outputs contain 396 100-parcel matrices across 35 participants and 39 14-ROI matrices across four participants; 31 participants were skipped by the 14-ROI route for insufficient signal rank. All 843 saved primary-route matrices passed shape, finite-value, symmetry, diagonal and correlation-bound checks. This is numerical validation, not scientific inclusion approval. Audit details: [matrix inventory](output/TCP_output/delivery_audit/matrix_inventory.json).

QC v3 finished for 52 participants / 600 block-band rows: 48 technical-candidate rows, 552 requiring review, no native-agreement failures. These are historical QC classifications, not the documented inclusion list. Existing group figures predate the updated exclusion policy and must not be delivered as final cohorts. Matching TCP/PCD HC protocols are documented; the identity decisions above govern interpretation of historical participant counts. Preprocessing harmonization remains pending.

Remaining work: refresh QC and cohort summaries against the completed harmonized TCP outputs, verify downstream PCD compatibility, and finalize extra-review pilot IC decisions before producing replacement BP/FC. Documented exclusions have already been applied to a separate historical QC view; see the identity decisions above for the corrected PCD records. The five extra-review ICA pilots do not replace any existing v2 matrices. No new v2 batch was launched by this delivery audit.

Historical provided-Clean-BP PCD outputs: [rank-corrected participant folders](output/PCD_output/rank_corrected/outputs). Missing blocks: PCD107 and PCD211 lack HC2-HC4; PCD109 and PCD208 lack HC4 in that historical route. Their current raw-reviewed HC4 results are available separately; consult [the raw-review register](output/PCD_output/raw_review_fc_diagnostics.md) for current harmonized runs.

As of 2026-10-13, both routes are complete for 17 participants:

```text
101 102 103 104 105 221 402 406 407 408 409 411 412 413 414 415 416
```

The October 13 legacy subset had 5 YAC, 1 OAC and 11 TCOA participants. TCP404 subsequently completed special v1 review and harmonized v2, bringing the current TCP output cohort to 5 YAC, 1 OAC and 12 TCOA. See [the special handling record](../auto_fc_pipeline_v1/outputs/PCD_output/manual_preica_review_404/README.md) and `output/TCP_output/tcp_rank_harmonized/outputs/404/`. The legacy counts below remain historical.

Each completed participant has four cleaned HC blocks, four signed time-series files at each resolution, and 12 matrix NPZs plus 24 raw-r/Fisher-z CSVs and one summary PNG per route. Across the 17 participants this gives:

- 68 HC blocks.
- 204 primary 14-ROI matrices and 204 secondary 100-parcel matrices.
- 816 matrix CSVs, counting raw-r and Fisher-z separately.
- 34 participant summary PNGs, two per participant.

Final checks passed across both routes: expected shapes/counts, finite values, symmetry, raw-r diagonals of 1, Fisher-z diagonals of 0, valid correlation bounds, and CSV/NPZ agreement. The embedded 14-ROI comparisons in the pairwise files match the primary matrices. Primary symmetric-orthogonalization residuals are below `4.5e-15`; retained primary durations range from 227.7 to 309.7 seconds across blocks/bands. Backprojected inputs were checked against the current PreICA, ICA-model, and review-CSV timestamps. These are outputs under the current explicit exclusion decisions, not a declaration that all human reviews are finalized.

The 14-ROI outputs use `envelope_method="mne_fft_resample_per_segment"` with target 10 Hz; 100-parcel outputs use `block_mean_per_segment` at 8 Hz. Old 14-ROI outputs without the updated method metadata must not be mixed with this cohort. Use `--start-at 5 --route 14` to refresh matrices from existing signed ROI files. For missing signed-parcel files, restart at `--start-at 4` before running 100-parcel FC.

Run logs and per-participant completion records are in `output/TCP_output/batch_runs/20261013_013831/` and `output/TCP_output/batch_runs/20261013_024439/`. The first batch was stopped to defer 404; the continuation finished successfully. Existing warnings concern template/fiducial assumptions and MNE filename conventions; no numerical failures were detected in the completed cohort. Template source-localization limitations still apply.

Fourteen focused tests pass, covering MNE pairwise agreement, Step0 per-segment FFT resampling, lower-rank pairwise-100 data, manual-review contracts, v1/v2 path resolution, and gap-aware ICA PSD plotting. These checks verify implementation, not biological validity or readiness for group inference.

## 100-Parcel QC Route

Each participant has one `<participant>_fc100_summary.png`: rows are HC blocks; each frequency band has adjacent uncorrected and pairwise-corrected panels. Each band and correction method uses a symmetric raw-r color scale set by the 99th percentile of absolute off-diagonal values across available HC blocks. Color bars give the limits; values beyond those limits use the endpoint colors. Add `--plots-only` to `04_whole_recording_fc.py` to rebuild this figure from saved NPZ matrices without recalculating connectivity. Successful plotting replaces the corresponding legacy per-block/per-band PNGs; matrix and table files are unchanged.

The following scripts retain the corrected 100-parcel pairwise route for secondary inspection:

```text
shared_code/scripts/03_extract_parcel_timeseries.py
shared_code/scripts/04_whole_recording_fc.py
```

These now run through the default participant entry point. Use `--route 100` for the secondary route only (including when primary 14-ROI rank checks fail). To rerun only 100-parcel FC from existing signed parcel signals, use `04_whole_recording_fc.py --config auto_fc_pipeline_v2/config.hc_corrected.example.json --subject 101`. Pairwise correction treats every parcel pair independently and is not simultaneous symmetric correction of all signals. It remains secondary QC per Step0b; choosing it as a primary outcome requires a study-level decision. Participant QC is not a group-level analysis or a test of group reliability.

## Dependencies and Resources

- Python dependencies are listed in `requirements-colab.txt`.
- `nibabel` is required for the source-space/parcellation workflow.
- MNE may download `fsaverage` if not cached. The matching Schaefer annotation
  files must already be present in `subjects_dir/fsaverage/label`; the active
  extractor reads them and does not install the atlas automatically.
- Configuration template: `config.hc_corrected.example.json`.

The focused tests in `shared_code/tests/` check the scientific implementation and interface
contracts; they are retained rather than treated as disposable debug files.
Run them with the EEG Python environment and the same project-local MNE/Numba
environment variables used by the runner. The production symmetric correction
is implemented locally; `mne-connectivity` is retained for reference comparisons.

## Known Limitations and Decisions

- `fsaverage` is a template anatomy, not each participant's individual MRI.
- Source accuracy depends on the available electrode montage and lacks participant-specific digitized fiducials.
- HC blocks are repeated observations within participants; downstream statistics must model this dependence rather than treating all matrices as independent subjects.
- Missing HC blocks must be reported explicitly.
- Group assignment and participant covariates must come from confirmed study metadata, not inferred from participant number alone.
- Tai Chi group differences are observational associations unless supported by a separate causal design and assumptions.

## Reference Code

The corrected downstream implementation was aligned with the updated reference notebooks in `references/`, especially:

```text
Step0_Rebuild_Source_Envelopes.ipynb
Step0b_Connectome_Sanity_Check_100parcels.ipynb
Step2b_Network_and_Temporal_Features.ipynb
```

The workflow intentionally skips HMM discretization because the current design uses the full recording to estimate static FC.

## Persistent legacy archive register (2026-11-21)

[Exact archived paths, retained outputs and restoration dependencies](maintenance/archive_plan_20261121/README.md). The archive is not required for current PCD reporting; historical TCP and Clean BP reruns can require restoration. User confirmed upload completion on 2026-11-22 and authorized local deletion; remote integrity was not independently verified.

## Cloud offload and local deletion — 2026-11-22

User confirmed the upload completed and authorized deletion. The local legacy_results_20261121 directory and ZIP were deleted. Observed disk free-space increase: 94.00 GiB. Before deletion, ZIP entries covered all 6,997 inventoried data files at expected uncompressed sizes; full CRC and remote cloud integrity were not independently checked. Exact mappings, the copied archived file inventory and offload_20261122.json remain in the local maintenance register. Download and extract the cloud archive before restoring historical paths. Current reviewed PCD, current TCP and local report comparisons remain available.
