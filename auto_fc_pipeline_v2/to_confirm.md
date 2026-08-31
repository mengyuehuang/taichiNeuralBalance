# Source Localization Notes

This file lists the practical decisions for the heavier source-localization step
on Colab, based on lab feedback.

## 1. Input Files

v2 currently assumes the input files are already cleaned/backprojected EEG
files, then converted to montage-aligned block-level `.fif` files.

Current block mapping:

- `HC1` and `HC4`: non-perturbation
- `HC2` and `HC3`: perturbation

## 2. Adapting Old Step 2

The old `Step_2_Source_Localisation` scripts were written for the Flanker task.
They used:

- congruent / incongruent trials
- left / right trial labels
- many short epochs

The v2 draft changes this to:

- HC1-HC4 block files
- non-perturbation / perturbation blocks
- one shared inverse operator per participant

In plain terms, for one participant, v2 would make one source-localization
mapping and reuse it for that participant's HC blocks.

## 3. Source-Localization Settings

Lab feedback: keep the settings from the old Step 2 scripts unless a later
issue comes up during testing.

Settings copied from the old scripts:

- template subject: `fsaverage`
- transform: `trans = fsaverage`
- source space: `ico5`
- BEM: `fsaverage-5120-5120-5120-bem-sol.fif`
- method: `eLORETA`
- SNR: `3.0`
- lambda2: `1 / snr^2`
- loose orientation: `0.2`
- depth weighting: `0.8`
- mindist: `5.0`
- covariance method: `shrunk` and `empirical`
- average reference projection: `true`

## 4. Montage File

The montage file I tested is:

```text
MFPRL_UPDATED_V2.sfp
```

It came from the EEG signal MATLAB analysis folder. Lab feedback confirmed this
is the correct montage, as long as the local filename matches the downloaded
file.

## 5. Channels To Exclude

The local QC found six channels that look like ground/eye/neck channels rather
than regular scalp EEG channels:

- `GND`
- `LHEye`
- `RHEye`
- `RVEye`
- `Lneck`
- `Rneck`

Lab feedback confirmed these should be dropped before source localization.

## 6. Full Dataset / Block Parsing

The original clean/backprojected files may not be recoverable. If they cannot be
restored, v1/upstream preprocessing must regenerate cleaned/backprojected HC
files from raw BrainVision EEG before v2 starts.

The old sample files were already separated into HC blocks, for example:

```text
213_time_HC1_backproject.set
213_time_HC2_backproject.set
213_time_HC3_backproject.set
213_time_HC4_backproject.set
```

For the current raw data folder, HC files are already separated as raw
`TCOA_<subject>_HC1-HC4.vhdr` recordings for most participants. v1 should create
cleaned/backprojected outputs from those raw HC files, then v2 can consume them.

## 7. Correlation Sign / Absolute Value

There is one wording conflict in the original instructions:

- one line says taking absolute values is okay;
- a later line says not to automatically convert negative correlations to
  absolute values.

Current v2 default is the stricter option:

```text
apply_absolute_value = false
threshold = null
```

This keeps signed correlations unless the lab later asks to use absolute values.

## Next Step

After upstream preprocessing creates cleaned/backprojected HC files, the next
step is:

```text
run eLORETA on Colab
-> extract signed Schaefer 100-region time series
-> generate static alpha/beta connectivity matrices
```
