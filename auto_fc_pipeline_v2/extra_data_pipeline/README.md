# Teacher Clean BP v2 analysis

## Current cohort policy (2026-10-30)

Use [participant_policy.json](participant_policy.json) and [effective_input_manifest.json](effective_input_manifest.json) for current inclusion decisions. Teacher-confirmed exclusions are PCD103, PCD104, PCD107, PCD202 and PCD210. PCD119/206/218 remain quality-review cases, not automatic exclusions or approvals. The original input manifest and historical outputs are preserved. The effective selected queue is 34 participants; PCD208 HC4 remains held because its alternatives are ambiguous.

The filtered historical QC view is [teacher_cohort](rank_corrected/qc_validation/teacher_cohort), not a completed harmonized analysis. See the [main v2 README](../readme.md) for shared TCP/PCD numerical code, the centered projection correction, TCP404 sequencing, and unresolved participant identity. Re-running the historical PCD runner skips historical completed entries; it does not certify that their projection-policy version matches a new run. The [compatibility audit](rank_corrected/projection_compatibility.json) records input/covariance differences separately.

This independent run reads `data/VRHCT_CleanData-selected/Clean BP` directly.
It does not use the experimental backprojections produced under v1.
Clean BP signals are converted from EEGLAB SET/FDT to FIF without another ICA
application or upstream filtering. The lab's MATLAB 63-channel positional labels
are assigned and eye/neck/ground channels are typed before source modeling.

Run from the project root:

```powershell
python auto_fc_pipeline_v2/extra_data_pipeline/run_clean_bp.py
```

Use `--subject PCD105` for one participant. A repeat invocation skips participants
recorded as completed. Do not change inputs or settings while reusing completion
records; use a separate output location for a different analysis.

- `input_manifest.csv`: selected inputs and explicit holds.
- `config.clean_bp.json`: local v2 paths and PCD group assignments.
- `inputs/`: format-converted teacher Clean BP inputs.
- `outputs/PCD105/`, etc.: standard v2 participant results.
- `logs/`: participant execution logs.
- `run_status.json`: completion, failures and route limitations.

PCD103 remains on hold because the supplied subject summary marks it excluded.
Both PCD208 HC4 alternatives are held until recording selection is resolved;
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
from the teacher files. Existing TCP/TCOA results remain in their original output
directory and are not pooled by this run.
