# Tai Chi Neural Balance EEG Pipelines

This repo contains two draft Python/MNE pipelines for the Tai Chi / Height
Control EEG functional connectivity project.

## Current Status

The original cleaned/backprojected EEG files may not be available, so the active
work starts from raw BrainVision EEG files.

The current tested path is:

```text
raw EEG
-> v1 preprocessing
-> ICA review files and figures
-> manual ICA component review
-> cleaned/backprojected EEG
-> v2 source localization and connectivity
```

## Folder Overview

```text
auto_fc_pipeline_v1/
```

Starts from raw BrainVision EEG and prepares cleaned/backprojected EEG files.
It currently handles channel selection, channel naming, montage application,
1-55 Hz filtering, 60 Hz notch filtering, 1-second noisy-chunk marking, ICA,
ICLabel output, and manual ICA review files.

```text
auto_fc_pipeline_v2/
```

Starts after cleaned/backprojected EEG files exist. It is the downstream draft
for source localization, Schaefer parcel time series, and alpha/beta static
functional connectivity matrices.

## Local Outputs

Generated outputs are kept locally and are not committed to GitHub.

Current local test outputs are under:

```text
auto_fc_pipeline_v1/outputs/v1_preica_test
```

That folder currently contains ICA review outputs for participants `101`-`105`,
`221`, `402`, `404`, and `406`-`416`, blocks `HC1`-`HC4`, where HC files are
present.

Participants `401`, `403`, and `410` were checked in the selected local EEG
folder, but only `EC`, `EO`, and `NC` files were present, not HC files.

## Data Safety

The repo intentionally ignores raw EEG files, generated EEG-derived outputs,
local config files, and lab reference materials.

Do not commit:

```text
TCP_EEG_sync-selected/
references/
outputs/
auto_fc_pipeline_v1/outputs/
config.local.json
*.fif, *.eeg, *.vhdr, *.vmrk, *.set, *.fdt, *.mat
*.png, *.csv, *.xlsx
```

Use each pipeline folder's README for exact commands.
