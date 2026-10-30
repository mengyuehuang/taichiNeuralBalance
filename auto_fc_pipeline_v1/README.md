# Auto FC Pipeline v1

This folder is a Python/MNE draft of the upstream preprocessing steps from
The MATLAB Height Control EEG scripts.

The current purpose is practical:

```text
raw BrainVision EEG
-> prepare data for ICA
-> run ICA and export files for manual IC checking
-> remove reviewed bad ICs
-> create cleaned/backprojected files for v2
```

v1 is not a replacement for manual review. It is a Python version of the workflow
logic for inspecting, documenting, and batching the raw-to-backprojected stage if
the clean backprojected files cannot be restored.

## Preprocessing steps

The MATLAB Step 1 does this before and during ICA:

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

The commands in this README assume the working directory is `auto_fc_pipeline_v1`.
Relative v1 config paths resolve from the config's directory. The v2 HC config
instead resolves paths from the `taichi` repository root; its runner checks that
`v1 output_dir/Backprojected` and `v2 backprojected_dir` refer to the same folder.

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
2. Keeps physical channels `1:20,22:64`, matching the preprocessing channel-21 skip and
   the current suggestion to drop channel 21.
3. Renames channels using the configured cap map.
4. Applies the `.sfp` montage.
5. Filters 1-55 Hz.
6. Applies 60 Hz notch filtering.
7. Marks noisy 1-second chunks with `BAD_preICA_auto`.
8. Saves filtered and preICA `.fif` files.

The HC glob in the local/example configs now covers all available HC recordings,
not only the initial 101-105 test subset. Existing ICA models protect their PreICA
inputs from accidental overwrite. To change preprocessing, use a new output
directory and refit/review ICA; do not apply an old ICA to changed input data.

Outputs:

```text
Filtered/
PreICA/
PreICA_QC/
```

Important check:

The MATLAB code used a fixed `500` samples when creating the short chunks.
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

These are Python helper scripts using MNE LOF. The MATLAB workflow mainly
relies on EEGLAB rejection and manual review, so treat these as optional QC
helpers unless the analysis requires this exact Python bad-channel route.
They write `bad_channels.csv` and `Bad_Channels_Marked/`; the current ICA entry
point reads `PreICA/`, not `Bad_Channels_Marked/`. These optional helpers are not
automatically applied to the active cohort and do not interpolate bad channels.

## Step 3: ICA Review Files

Run:

```powershell
python scripts/04_run_ica.py --config config.local.json
```

This script:

1. Loads files from `PreICA/`.
2. Applies common average reference before ICA when configured.
3. Fits ICA while skipping `BAD_*` annotations.
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

To refresh the review CSV/XLSX and figures from an existing
ICA file, run (only after synchronizing manual XLSX edits to CSV):

```powershell
python scripts/04_run_ica.py --config config.local.json --reuse-existing-ica
```

This refresh can rewrite the XLSX formatting. Use `--figures-only` to redraw
figures without touching review files, or `--backproject-only` to apply decisions
without relabeling/redrawing. Existing models/reviews are protected from a plain
rerun that would refit ICA: a new fit requires a separate output directory and
new manual review, since component numbers are model-specific.

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
auto_fc_pipeline_v1/outputs/v1_preica_test
```

The local ICA batch contains 18 participants / 72 HC blocks: `101`-`105`, `221`,
`402`, `404`, `406`-`409`, and `411`-`416`. Participants `401`, `403`, and `410`
have no HC files in the selected local dataset. This does not imply they have no EEG.

| Folder | Contents |
| --- | --- |
| `Filtered` | EEG after initial preprocessing, before automatic noisy-period annotations |
| `PreICA` | Same continuous EEG with `BAD_preICA_auto` annotations |
| `PreICA_QC` | The 1-second noisy-period measurements and flags |
| `ICA` | Saved ICA models, needed to reproduce backprojection |
| `ICA_Review/<participant>` | Matching CSV/XLSX manual decision tables |
| `ICA_Figures/<participant>/<HC>` | Topography, source traces, and PSD |
| `Backprojected` | Channel-space EEG after the explicit IC exclusions |

The source-trace panels show only the first 10 seconds for readability, not the
duration used to fit ICA or calculate FC. Pale blue spans show each displayed IC's
25th-75th percentiles after per-IC standard-deviation scaling; red spans are BAD
annotations. PSD uses the available recording, excludes BAD samples, and marks
8-12 Hz (blue), 13-30 Hz (green), and 60 Hz (dashed line). No dipole-fit/RV plots
are generated.

The 2026-10-13 code audit corrected PSD plotting to average Welch windows within
continuous clean segments, without joining across BAD/boundary gaps. Existing
ICA review PNGs were not regenerated during this cleanup; use `--figures-only`
to refresh them when needed. This plotting change does not alter v2 FC outputs,
which already process continuous fragments separately.

The review CSV has columns like:

```text
component, iclabel, iclabel_probability, auto_exclude
review_exclude1, reviewer1, reviewer1_note
review_exclude2, reviewer2, reviewer2_note
review_exclude3, reviewer3, reviewer3_note
```

The important manual step is:

```text
Manual component review
-> set one review_exclude column to true for bad ICs
-> synchronize XLSX edits to the matching CSV
-> run 04_run_ica.py --config config.local.json --backproject-only
```

After reviewed exclusions exist, the script applies ICA removal and saves:

```text
Backprojected/
```

This is the Python equivalent of the preprocessing `pop_subcomp(... EEG.bad ...)` step.

The union of explicit TRUE decisions in the three `review_exclude` columns is
removed. FALSE and blank cells are retained; neither ICLabel nor note text
overrides those columns. A blank is not evidence of completed review. The script
stops on a mismatched XLSX/CSV, invalid decision value, or component IDs that do
not match the saved ICA. It also stops when no IC is marked for removal; a genuine
all-keep decision currently requires a separately agreed workflow.

There is also an emergency option:

```powershell
python scripts/04_run_ica.py --config config.local.json --apply-auto
```

This applies automatic ICLabel suggestions without manual review. Do not use it
for final analysis unless the analysis protocol explicitly permits it.

## How This Connects To v2

v1 prepares the upstream cleaned/backprojected data.

v2 starts after that:

```text
v1 Backprojected/
-> v2 montage/block checks
-> source localization
-> signed 14-ROI and Schaefer-100 time series
-> 14-ROI symmetric / 100-parcel pairwise whole-recording FC
```

Both harmonized v2 routes are now complete for all 18 TCP participants, including `404`, under `../auto_fc_pipeline_v2/outputs/tcp_rank_harmonized/outputs/`. The older `outputs/corrected` results remain historical. Updated QC/group summaries are still outstanding.
See [v2 workflow](../auto_fc_pipeline_v2/readme.md) for commands and result counts.
There is no active event-epoching stage or HMM in this whole-recording workflow;
the old epoching placeholder has been removed.

## Current Choices

These are the choices currently used in v1:

- Process only HC files for this pipeline.
- Skip physical channel 21 when loading the raw BrainVision files.
- Use `MFPRL_UPDATED_V2.sfp` as the montage file.
- Use true 1-second chunks for pre-ICA noisy-segment QC.
- Use common average reference before ICA.
- Exclude `GND`, `LHEye`, `RHEye`, `RVEye`, `Lneck`, and `Rneck` from ICA
  fitting.
- Force at least 10 ICA components when the automatic setting keeps too few.
- Flag low-confidence ICLabel results with `low_confidence_label`; Excel review
  files highlight those rows.
- Apply explicit manual IC decisions; this does not certify that every row is finalized.

## Still To Confirm / Watch

- Confirm whether the current raw EEG folder is the complete final dataset to process: TCP_EEG_sync-selected.
- Confirm whether participants `401`, `403`, and `410` truly have no HC files
  or whether those files are stored elsewhere.
- Watch lower-component blocks during review, especially blocks that were forced
  to 10 components.
- Decide whether the ICLabel 1-100 Hz warning needs any special handling. The
  current preprocessing uses a 1-55 Hz passband.
- `404` HC4 v1 review/BP and harmonized v2 are complete; updated downstream QC is still required before scientific inclusion. Do not mix old/new results.


## TCP404 HC4 special handling (2026-10-30)

This recording received an additional **manual time-interval review before ICA**, distinct from the later manual IC review. The raw first 64 channels become constant after 190.329 s; the routine automatic annotations did not remove the full failure period. The selected human interval decisions retain 158 s and exclude 431.7 s. BAD annotations preserve original timing; downstream processing must respect them.

ICA was refitted on the retained samples. Audited iteration tracing confirmed the weight-change stop at actual iteration 129 (30 ICs); stored n_iter=500 is not evidence of failed convergence. The 108 s strict alternative is a comparison only. New IC decisions came from the completed review workbook; explicit reviewer1_note instructions were given priority, with no explicit conflicts found. `other`/`uncertain` notes were not interpreted as automatic rejection. Twenty ICs were removed; ten fitted ICs retained. Existing v1 backprojection also restores residual PCA dimensions, so this is not a claim of rank 10.

The **current production files** are in `outputs/v1_preica_test/`: `PreICA/404_HC4_preica_raw.fif`, `ICA/404_HC4-ica.fif`, `ICA_Figures/404/HC4/`, `ICA_Review/404/`, and `Backprojected/404_HC4_backproject_raw.fif`. HC1-HC3 BP was verified and retained. All four BP files are readable and finite on retained samples. BP completion is not final scientific/QC approval; 404 harmonized v2 is now complete; this does not establish final QC approval.

**For the viewer, detailed decisions, scripts, convergence evidence, and old-HC4 backup, see [extra_review/manual_preica_review_404/README.md](extra_review/manual_preica_review_404/README.md).** This case-specific layer has not yet been generalized to all recordings. The standard BP script still reads boolean review columns, not free-text notes; the note-priority rule was reconciled before execution for this case.
