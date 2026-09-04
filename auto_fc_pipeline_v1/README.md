# Auto FC Pipeline v1

This folder is a Python/MNE draft of the upstream preprocessing steps from
Yang's MATLAB Height Control EEG scripts.

The current purpose is practical:

```text
raw BrainVision EEG
-> prepare data for ICA
-> run ICA and export files for manual IC checking
-> remove reviewed bad ICs
-> create cleaned/backprojected files for v2
```

v1 is not a replacement for lab review. It is a Python version of the workflow
logic so we can inspect, document, and batch the raw-to-backprojected stage if
the clean backprojected files cannot be restored.

## What Was Copied From Yang's Logic

Yang's MATLAB Step 1 does this before and during ICA:

```text
load raw BrainVision .vhdr
-> skip physical channel 21
-> filter 1-55 Hz
-> remove 60 Hz line noise
-> split/check data in 1-second chunks
-> mark noisy chunks
-> manual noisy-data review
-> set channel names and montage
-> run ICA
-> ICLabel + manual IC checking
-> remove bad ICs
-> backproject cleaned data
```

This Python draft follows the same broad order, with one safety change:

```text
noisy 1-second chunks are annotated as BAD_preICA_auto
```

They are not silently concatenated into a fake continuous block. MNE can skip
these annotated spans while fitting ICA.

## Folder Layout

```text
auto_fc_pipeline_v1/
  README.md
  config.example.json
  requirements-colab.txt
  outputs/        local generated files, ignored by Git
  scripts/
    00_inspect_raw.py
    01_preprocess_filter.py
    02_detect_bad_channels.py
    03_mark_bad_channels.py
    04_run_ica.py
    05_make_epochs.py
  src/
    fc_pipeline/
      config.py
      io.py
      montage.py
      preica.py
```

## Config

Copy the example config:

```powershell
copy config.example.json config.local.json
```

Then edit these paths:

```text
paths.raw_data_dir
paths.output_dir
paths.montage_path
```

The default assumes BrainVision raw files:

```text
.vhdr + .eeg + .vmrk
```

## Step 0: Inspect Raw Files

Run this first after receiving a raw EEG folder:

```powershell
python scripts/00_inspect_raw.py --config config.local.json --recursive
```

This script checks the practical details that need to be monitored before
preprocessing:

1. How many BrainVision `.vhdr` files are present.
2. Sampling rate.
3. Number of channels.
4. Channel 21 label.
5. Aux channel list.
6. Which participants have HC1-HC4.

Outputs:

```text
raw_inventory.csv
hc_block_summary.csv
```

For the current selected raw folder, the files checked were 72-channel
BrainVision recordings sampled at 1000 Hz, with `Ch65`-`Ch72` listed as
`Aux1`-`Aux8`. Most participants have separate raw HC1-HC4 files.

## Step 1: Pre-ICA Cleaning

Run:

```powershell
python scripts/01_preprocess_filter.py --config config.local.json
```

This script:

1. Reads raw BrainVision files.
2. Keeps physical channels `1:20,22:64`, matching Yang's channel-21 skip and
   the current suggestion to drop channel 21.
3. Renames channels using the configured cap map.
4. Applies the `.sfp` montage.
5. Filters 1-55 Hz.
6. Applies 60 Hz notch filtering.
7. Marks noisy 1-second chunks with `BAD_preICA_auto`.
8. Saves filtered and preICA `.fif` files.

Outputs:

```text
Filtered/
PreICA/
PreICA_QC/
```

Important check:

Yang's MATLAB code used a fixed `500` samples when creating the short chunks.
The raw files currently checked are 1000 Hz, so `500` samples would be 0.5
seconds for these files. This Python draft uses true 1-second chunks by default:

```json
"chunk_length_seconds": 1.0
```

That means the QC window stays 1 second even if the sampling rate changes.

## Step 2: Optional Bad-Channel Helpers

Run:

```powershell
python scripts/02_detect_bad_channels.py --config config.local.json
python scripts/03_mark_bad_channels.py --config config.local.json
```

These are Python helper scripts using MNE LOF. Yang's MATLAB workflow mainly
relies on EEGLAB rejection and manual review, so treat these as optional QC
helpers unless the lab wants this exact Python bad-channel route.

## Step 3: ICA Review Files

Run:

```powershell
python scripts/04_run_ica.py --config config.local.json
```

This script:

1. Loads files from `PreICA/`.
2. Fits ICA while skipping `BAD_*` annotations.
3. Applies common average reference before ICA when configured.
4. If the automatic ICA setting gives fewer than 10 components, reruns ICA with
   `n_components=10` so there are enough components to review.
5. Saves the ICA solution.
6. Runs ICLabel if `mne-icalabel` is installed.
7. Saves review CSV files, component topography figures, 0-10 s source trace
   pages, and a PSD grid.

The review table can also flag low-confidence ICLabel results. By default,
components with ICLabel probability below `0.8` get `low_confidence_label=True`.
If `write_review_xlsx` is on, the script also writes an Excel copy with those
rows highlighted.

If you only need to refresh the review CSV/XLSX and figures from an existing
ICA file, run:

```powershell
python scripts/04_run_ica.py --config config.local.json --reuse-existing-ica
```

On Windows, the script also writes MNE/numba cache files inside the project
folder so MNE does not get stuck trying to write to a locked user-level config
folder.

Outputs:

```text
ICA/
ICA_Review/
ICA_Figures/
```

The review figures include:

```text
ICA_Figures/101/HC1/ica_components_1.png   topography
ICA_Figures/101/HC1/ica_components_2.png   topography, continued
ICA_Figures/101/HC1/ica_sources_1.png      source traces, first half of ICs
ICA_Figures/101/HC1/ica_sources_2.png      source traces, second half of ICs
ICA_Figures/101/HC1/ica_psd.png            IC power spectra
```

The matching review table is stored under the participant folder:

```text
ICA_Review/101/101_HC1_ica_review.csv
```

For the current local test batch, the generated files are under:

```text
C:\Users\98768\Desktop\taichi\auto_fc_pipeline_v1\outputs\v1_preica_test
```

The current local batch includes participants `101`-`105`, HC1-HC4. See
`TEST_OUTPUTS.md` for the exact test-output locations.

The review CSV has columns like:

```text
component, iclabel, iclabel_probability, auto_exclude
review_exclude1, reviewer1, reviewer1_note
review_exclude2, reviewer2, reviewer2_note
review_exclude3, reviewer3, reviewer3_note
```

The important manual step is:

```text
Michelle / professor / trained reviewer checks components
-> set one review_exclude column to true for bad ICs
-> rerun 04_run_ica.py
```

After reviewed exclusions exist, the script applies ICA removal and saves:

```text
Backprojected/
```

This is the Python equivalent of Yang's `pop_subcomp(... EEG.bad ...)` step.

There is also an emergency option:

```powershell
python scripts/04_run_ica.py --config config.local.json --apply-auto
```

This applies automatic ICLabel suggestions without manual review. Do not use it
for final analysis unless the lab explicitly approves it.

## How This Connects To v2

v1 prepares the upstream cleaned/backprojected data.

v2 starts after that:

```text
v1 Backprojected/
-> v2 montage/block checks
-> source localization
-> Schaefer parcel time series
-> alpha/beta static connectivity matrices
```

## Things To Confirm Before Real Use

- Whether the selected Box/raw folder is the final dataset for this analysis.
- Whether all raw files should be processed or only the HC1-HC4 files.
- Monitor whether physical channel 21 behaves consistently across participants.
- The current montage is `MFPRL_UPDATED_V2.sfp`.
- Current v1 default uses true 1-second chunking for pre-ICA noisy-segment QC.
- Which channels should be excluded from ICA fitting.
- Common average reference is currently turned on before ICA.
- ICA components must be manually reviewed before final backprojection.
- Whether the output should be continuous HC blocks or epoched perturbation
  files for any specific side analysis.
