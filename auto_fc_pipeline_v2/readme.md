# FC Pipeline v2

This folder is the updated pipeline draft for the Tai Chi / Height Control EEG
project.

The main idea is simple:

```text
cleaned backprojected EEG files
-> check file format and channel names
-> align channels to the cap/montage file
-> run source localization on Colab
-> extract 100 brain-region time series
-> create alpha/beta connectivity matrices
```

This pipeline does **not** start from raw EEG. It expects cleaned/backprojected
EEGLAB files such as `.set/.fdt`. If the old clean/backprojected files cannot be
restored, run the upstream v1 preprocessing first.

Current project status: the old clean/backprojected files may not be available,
so the active upstream work is in `auto_fc_pipeline_v1`. Use v2 after v1 creates
cleaned/backprojected HC files.

## Block Labels

Current mapping:

- `HC1` and `HC4`: non-perturbation
- `HC2` and `HC3`: perturbation

This mapping matches the current lab guidance.

## What Works Now

The local checks currently do these things:

1. Find the available `.set` files.
2. Read them with MNE.
3. Save block-level `.fif` files.
4. Check boundary markers.
5. Rename numeric channel names such as `Ch1`, `Ch2`, etc. to cap labels.
6. Apply/check the available `.sfp` montage file.
7. Save montage-aligned `.fif` files.
8. QC the aligned files.
9. Dry-run the source-localization plan without doing the heavy computation.

The source-localization script has been drafted, but the real run should happen
on Colab after upstream cleaned/backprojected HC files are ready.

## What Is Not Done Yet

These steps are still pending:

- Run eLORETA/source localization for real.
- Extract signed Schaefer 100-region time series.
- Run the final alpha/beta connectivity matrices from real parcel time series.

## Config

Use `config.example.json` as the template:

```powershell
copy config.example.json config.local.json
```

Then edit `config.local.json` with local paths.

Do not commit `config.local.json`; it contains paths from one computer.

## Commands

Run commands from this folder:

```powershell
cd auto_fc_pipeline_v2
```

Inspect `.set` files:

```powershell
python scripts/00_inspect_inputs.py --config config.local.json --read-eeglab
```

Create block-level `.fif` files:

```powershell
python scripts/01_prepare_blocks.py --config config.local.json
```

Rename channels and apply/check montage:

```powershell
python scripts/02_check_montage_and_channels.py --config config.local.json
```

QC the montage-aligned files:

```powershell
python scripts/03_check_aligned_fif.py --config config.local.json
```

Dry-run the source-localization plan:

```powershell
python scripts/02_source_localization_hc_blocks.py --config config.local.json
```

Only run this on Colab or another larger machine after lab confirmation:

```powershell
python scripts/02_source_localization_hc_blocks.py --config config.local.json --run
```

After source localization and parcel extraction are ready, compute static FC:

```powershell
python scripts/04_static_connectivity.py --config config.local.json
```

## Current Sample Check

The current sample files passed the local format checks:

- MNE can read them.
- They look like complete HC block files, not many short trials.
- Sampling rate: 1000 Hz.
- Channel count: 63.
- Boundary marker: only at 0 seconds in the sample files.
- Channel rename/montage check: no missing or extra montage channels.

The QC found six channels that lab feedback confirmed should be excluded before
source localization:

- `GND`
- `LHEye`
- `RHEye`
- `RVEye`
- `Lneck`
- `Rneck`

## Expected Final Output

For each participant and HC block, the final output should include alpha and
beta matrices, for example:

```text
213_HC1_non_perturbation_alpha_r.npy
213_HC1_non_perturbation_beta_r.npy
213_HC2_perturbation_alpha_r.npy
213_HC2_perturbation_beta_r.npy
```

Fisher-z versions are saved too.

The final matrices should not be thresholded, and negative correlations should
not be automatically changed to absolute values.
