# Local Test Outputs

The current local test output is saved here:

```text
C:\Users\98768\Desktop\taichi\auto_fc_pipeline_v1\outputs\v1_preica_test
```

This folder currently contains the test results for:

```text
participants: 101-105, 221, 402, 404, 406-416
blocks: HC1-HC4
```

Participants `401`, `403`, and `410` do not have HC files in the selected local
EEG folder, so there was no HC output to generate for them.

Main output folders:

```text
Filtered\       filtered raw FIF
PreICA\         pre-ICA FIF with noisy 1-second BAD annotations
PreICA_QC\      1-second chunk QC table
ICA\            saved ICA solution
ICA_Review\     CSV file for manual ICA component review
ICA_Figures\    ICA component/source figures for manual review
Backprojected\  cleaned backprojected files after reviewed IC removal
```

ICA now has a fallback for low-component cases: if the automatic setting gives
fewer than 10 components, the script reruns ICA with `n_components=10`.

The review CSV includes `low_confidence_label`. When `write_review_xlsx` is
enabled, the matching Excel file highlights those low-confidence rows so
reviewers can find the harder components faster.

Example files from the current test:

```text
C:\Users\98768\Desktop\taichi\auto_fc_pipeline_v1\outputs\v1_preica_test\ICA_Review\101\101_HC1_ica_review.csv
C:\Users\98768\Desktop\taichi\auto_fc_pipeline_v1\outputs\v1_preica_test\ICA_Figures\101\HC1\ica_components_1.png
C:\Users\98768\Desktop\taichi\auto_fc_pipeline_v1\outputs\v1_preica_test\ICA_Figures\101\HC1\ica_sources_1.png
C:\Users\98768\Desktop\taichi\auto_fc_pipeline_v1\outputs\v1_preica_test\ICA_Figures\101\HC1\ica_sources_2.png
C:\Users\98768\Desktop\taichi\auto_fc_pipeline_v1\outputs\v1_preica_test\ICA_Figures\101\HC1\ica_psd.png
```

The ICA review CSVs use three reviewer slots:

```text
review_exclude1, reviewer1, reviewer1_note
review_exclude2, reviewer2, reviewer2_note
review_exclude3, reviewer3, reviewer3_note
```

These outputs are intentionally not committed to GitHub. They are generated
files and may contain participant EEG-derived data. The root `.gitignore`
ignores `auto_fc_pipeline_v1/outputs/`.

The local `.numba_cache/` and `.mne_fake_home/` folders are also ignored. They
only prevent slow MNE startup on Windows/Codex and are not research outputs.

To recreate them, run:

```powershell
python scripts\00_inspect_raw.py --config config.local.json --recursive
python scripts\01_preprocess_filter.py --config config.local.json
python scripts\04_run_ica.py --config config.local.json
```
