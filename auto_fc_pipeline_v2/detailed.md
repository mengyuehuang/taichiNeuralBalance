# Auto FC Pipeline v2

This is the longer technical note. For a quick overview, start with
`readme.md`. For the exact questions to send to the lab, use `to_confirm.md`.

Plain-English summary:

```text
We checked that the sample EEG files can be read.
We converted them to MNE .fif files.
We fixed channel names and checked the montage.
We drafted the source-localization step, but only as a dry-run locally.
The real source-localization run should happen on Colab after lab confirmation.
```

This version reflects the updated project direction from the August thread.
v2 does not start from raw EEG. Its expected starting point is cleaned,
backprojected ICA EEG data. Because the original clean/backprojected files may
not be available, the active upstream work is now in `auto_fc_pipeline_v1`.
After v1 creates cleaned/backprojected HC files, v2 can handle source
localization and static amplitude-envelope connectivity.

## Requirement Alignment

Current alignment with the August thread:

- Do not run raw preprocessing inside v2: aligned. v2 starts from
  backprojected ICA `.set/.fdt` files or v1-created cleaned files.
- Confirm upstream cleaning/filtering: partially aligned. README records the
  lab's MATLAB notes: Step 2 filtered 1-55 Hz, CleanLine at 60 Hz, mastoid
  reference, manual ICA component rejection, 1-second noisy-data inspection.
- Use complete blocks rather than short trial epochs: aligned for the current
  sample files. MNE reads them as `Raw`/`RawEEGLAB` block-level data, not as
  many short trial epochs.
- Replace Flanker congruent/incongruent logic: aligned. v2 maps HC1/HC4 to
  `non_perturbation` and HC2/HC3 to `perturbation`.
- Confirm montage/channel names/electrode locations: aligned for the sample.
  Numeric `Ch#` channel names are renamed by the MATLAB/MFPRL order while
  skipping `Ch21`, then matched to `MFPRL_UPDATED_V2.sfp`.
- Create one common eLORETA inverse operator per participant: drafted as a
  dry-run plan. The real run should move to Colab after lab confirmation.
- Do not estimate separate alpha/beta inverse operators: recorded in config and
  source-localization placeholder.
- Extract signed 100-parcel Schaefer time series and drop medial-wall labels if
  present: not implemented yet.
- Alpha/beta static amplitude-envelope FC: implemented for already-extracted
  signed parcel `.npy` time series.
- Preserve full amplitude-envelope time courses: implemented. v2 correlates
  each parcel pair across all retained samples, not parcel averages.
- Save raw Pearson `r` and Fisher-z matrices: implemented.
- Preserve HC block identity in output filenames: implemented. This prevents
  HC1 and HC4, or HC2 and HC3, from overwriting each other when they share the
  same condition label.
- Skip HMM/dynamic-state scripts: aligned.
- Do not threshold and do not automatically take absolute values: aligned by
  default with `threshold: null` and `apply_absolute_value: false`.

## MATLAB Upstream Sanity Notes

The downloaded `MatLab analysis code` folder appears to contain the upstream
EEGLAB workflow that created the backprojected files:

- `Step1_Run_EEG_HC_2021_YH.m`: single-participant preprocessing, 1-second
  inspection epochs, epoch rejection, channel relabeling/montage lookup, ICA,
  ICLabel/manual component selection, and backprojection.
- `2. Run_EEG_HC1_CleanTimeData_Bunch_YH.m` through
  `2. Run_EEG_HC4_CleanTimeData_Bunch_YH.m`: batch scripts for HC1-HC4 that
  reload BrainVision `.vhdr` files, filter 1-55 Hz, apply CleanLine at 60 Hz,
  load pre-saved ICA weights/components, remove bad ICs, and save
  `*_HC*_backproject.set` files.

Important interpretation:

- The current BP starting files are likely EEGLAB `.set` files.
- HC1-HC4 appear to be block labels, not participant IDs.
- `create_study_pp.m` maps HC2/HC3 to `Perturb` and HC1/HC4 to
  `No-perturb`; v2 config follows that mapping.
- Step 2 does 1-55 Hz filtering, so v2 should not assume the upstream data were
  filtered exactly 1-50 Hz.
- The MATLAB code loads channels `[1:20,22:64]`, apparently skipping channel 21
  as ground.
- The MATLAB code uses mastoid-referenced data according to the lab response;
  no additional rereferencing is reported.

About the `1.61` and `6` criteria:

- `6` is visible in the Step 1 scripts as the 1-second epoch rejection criterion
  for noisy data inspection/rejection with joint probability and kurtosis.
- `1.61` was reported by the lab as the bad-channel kurtosis criterion, but it
  was not yet located in the main HC Step 1/Step 2 scripts I inspected. Keep it
  as reported preprocessing metadata unless we find the exact MATLAB line.

Important caution about Michelle/timing-style code:

- `event_platform_perturbation_updated.m` adds `platform_perturb` events from
  `HC_timing/*.csv` and `trialB.txt`, then epochs around each perturbation event
  from -1 to +2 seconds.
- That is perturbation-event epoching, not the complete continuous-block static
  FC requested in the August thread.
- Do not directly use those short perturbation epochs as the v2 FC input unless
  the team explicitly approves handling discontinuities and filter-edge effects.
  The preferred v2 input remains a continuous time series for each complete HC
  block, or one long epoch representing that block.

## Main Change From v1

`v1` assumed we might need to begin with raw EEG preprocessing:

```text
raw EEG -> montage/channel rename -> filtering -> bad channels -> ICA -> epochs
```

`v2` assumes we should begin later:

```text
backprojected cleaned EEG
-> non-perturbation / perturbation block separation
-> one common eLORETA inverse operator per participant
-> signed Schaefer parcel time series
-> alpha and beta amplitude-envelope connectivity
-> 100 x 100 matrices
```

## What v2 Should Do

For each participant:

1. Load the available cleaned/backprojected EEG files.
2. Parse data into complete experimental blocks:
   - `non_perturbation`
   - `perturbation`
3. Confirm montage, channel names, electrode locations, removed channels, and
   reference are appropriate for this dataset.
4. Estimate one common eLORETA inverse operator per participant.
5. Apply the same inverse operator to both block types.
6. Extract one signed time series for each of the 100 Schaefer parcels.
7. Drop medial-wall labels if they are present in the atlas output.
8. For each block and frequency band:
   - Alpha: 8-12 Hz
   - Beta: 13-30 Hz
9. Filter the signed parcel time series in the target band.
10. Remove filter-edge samples.
11. Apply symmetric orthogonalization within that band.
12. Apply Hilbert transform and take magnitude to get amplitude envelopes.
13. Correlate every parcel pair across retained block samples.
14. Save:
   - raw Pearson `r` matrix
   - Fisher `r-to-z` matrix

## What v2 Explicitly Skips

Do not run these unless the plan changes:

- `Step_1_Preprocessing`
- congruent/incongruent Flanker logic
- left/right trial logic
- HMM fitting
- optimal state selection
- median states
- fractional occupancy
- transition analysis
- bootstrapping
- edge count
- thresholding
- automatic absolute-value conversion of correlations

Static connectivity does not mean averaging each parcel time series into one
number. The full amplitude-envelope time courses must be preserved, and one
correlation is calculated for every parcel pair using all retained samples from
the complete block.

## Current Folder Layout

```text
auto_fc_pipeline_v2/
  readme.md
  config.example.json
  scripts/
    00_inspect_inputs.py
    01_prepare_blocks.py
    02_check_montage_and_channels.py
    02_source_localization.py
    03_check_aligned_fif.py
    03_extract_parcel_timeseries.py
    04_static_connectivity.py
  src/
    fc_pipeline_v2/
      __init__.py
      config.py
      connectivity.py
      io.py
```

## Current Implementation Status

Implemented:

- Config loading.
- Input-file discovery and basic participant/block parsing.
- Backprojected EEGLAB `.set/.fdt` reading, boundary reporting, and optional
  export to MNE `.fif` block files.
- Lightweight montage/channel-name check against the custom `.sfp` montage.
- Lightweight QC for montage-aligned `.fif` files before source localization.
- Static alpha/beta amplitude-envelope connectivity from parcel time series
  stored as `.npy` arrays.
- Raw Pearson correlation and Fisher-z matrix saving.

Still pending:

- Real eLORETA/source-localization run on Colab.
- Schaefer 100-region time-series extraction.

Do not start the real eLORETA run locally. The script has a dry-run mode for
checking file names and block labels without launching the heavy computation.

## How To Run the Implemented Static FC Step

First copy the config:

```bash
cp auto_fc_pipeline_v2/config.example.json auto_fc_pipeline_v2/config.local.json
```

Edit `config.local.json`, especially:

- `paths.parcel_timeseries_dir`
- `paths.output_dir`
- `naming.subject_regex`
- `naming.block_patterns`
- `timeseries.sfreq`

Be careful not to treat `HC1`, `HC2`, `HC3`, or `HC4` as participant IDs if
those strings are block labels in the file names. The default subject regex
therefore expects at least three digits unless the file uses a `sub-...` label.

Then run:

```bash
python auto_fc_pipeline_v2/scripts/04_static_connectivity.py --config auto_fc_pipeline_v2/config.local.json
```

To first inspect available backprojected `.set` files:

```bash
python auto_fc_pipeline_v2/scripts/00_inspect_inputs.py --config auto_fc_pipeline_v2/config.local.json
```

To also try reading each `.set` file with MNE:

```bash
python auto_fc_pipeline_v2/scripts/00_inspect_inputs.py --config auto_fc_pipeline_v2/config.local.json --read-eeglab
```

To prepare the cleaned/backprojected HC files for later source localization:

```bash
python auto_fc_pipeline_v2/scripts/01_prepare_blocks.py --config auto_fc_pipeline_v2/config.local.json
```

This creates `block_manifest.csv`, `boundary_events.csv`, and, by default,
MNE `.fif` exports in `paths.block_data_dir`. This step does not filter,
epoch, concatenate, source-localize, or compute FC. Its main job is to preserve
the available complete HC block files and make discontinuities visible before
the expensive steps begin.

To check whether the exported `.fif` files match the custom montage:

```bash
python auto_fc_pipeline_v2/scripts/02_check_montage_and_channels.py --config auto_fc_pipeline_v2/config.local.json
```

This creates `montage_channel_check.csv` in `paths.block_data_dir`. This step is
local and lightweight. It does not run eLORETA or any source-space computation.

The sample backprojected files preserve raw numeric channel names such as
`Ch1`, `Ch2`, and `Ch64`. The MATLAB reference code maps those numeric channels
to electrode labels by order while skipping raw channel `Ch21`. The montage
check script therefore supports the same numeric-to-montage-order rename and,
by default, writes montage-aligned `.fif` files under
`paths.block_data_dir/montage_aligned`.

To QC the montage-aligned `.fif` files before any source-space computation:

```bash
python auto_fc_pipeline_v2/scripts/03_check_aligned_fif.py --config auto_fc_pipeline_v2/config.local.json
```

This creates `aligned_fif_qc.csv` under
`paths.block_data_dir/montage_aligned`. It reports sample rate, total channels,
probable EEG/source channels, non-source channels such as eye/neck/GND, marked
bad channels, available channel locations, and boundary annotations.

The current sample QC found 63 total channels and 57 probable EEG/source
channels. The six channels to exclude before source localization are:
`LHEye`, `RHEye`, `RVEye`, `Lneck`, `Rneck`, and `GND`.

This expects one parcel time-series `.npy` file per participant/block. Each file
should contain a 2D array shaped either:

```text
n_parcels x n_times
```

or:

```text
n_times x n_parcels
```

The config field `timeseries.orientation` controls how the array is interpreted.

## Expected Final Outputs

If a participant has one non-perturbation block and one perturbation block, the
final raw correlation outputs should be:

```text
sub-XXX_HC1_non_perturbation_alpha_r.npy
sub-XXX_HC1_non_perturbation_beta_r.npy
sub-XXX_HC2_perturbation_alpha_r.npy
sub-XXX_HC2_perturbation_beta_r.npy
```

Fisher-z versions are also saved:

```text
sub-XXX_HC1_non_perturbation_alpha_fisher_z.npy
sub-XXX_HC1_non_perturbation_beta_fisher_z.npy
sub-XXX_HC2_perturbation_alpha_fisher_z.npy
sub-XXX_HC2_perturbation_beta_fisher_z.npy
```

If a participant has HC1-HC4 files, each HC block is kept as a separate block
instance unless the team later decides to average or merge within condition.

## Questions Still Needing Answers

- Can we locate all backprojected files?
- What file format are the backprojected files in?
- Are files already separated by `HC1`, `HC2`, `HC3`, `HC4` blocks? The
  current sample files are.
- Should we keep the `create_study_pp.m` mapping HC1/HC4 = non-perturbation and
  HC2/HC3 = perturbation for all downstream FC analyses?
- Are the files continuous per complete block, or are they many short epochs?
- If many short epochs exist, how should discontinuities and filter edges be
  handled?
- Is the data still mastoid-referenced, and is that acceptable for source
  localization?
- Were bad channels interpolated or merely retained after ICA backprojection?
- Which montage and channel-name convention should be used for this dataset?
- Should the final matrices be saved as `.npy`, `.csv`, or both?
- The custom .sfp montage has electrode positions but no fiducials such as nasion/LPA/RPA. For source localization, should we use a template transform/standard montage approximation, or is there a lab-specific head-coordinate transform?
- Should the six non-source channels identified in the sample QC always be
  excluded before source localization?

## Reference MATLAB upstream code:
2026 Tai Chi Project > sample data > data analysis.zip

## Confirmation
Sample BP files read as RawEEGLAB/Raw, 63 channels, 1000 Hz, ~250-322s.
Each sample file contains one boundary annotation at 0.0 seconds with 0.0
duration; no mid-block boundary/discontinuity was found in the current sample.
After numeric channel renaming and custom montage alignment, all files had
missing montage channels = 0 and extra montage channels = 0.
