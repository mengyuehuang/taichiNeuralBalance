# TCP404 HC4 manual review

Selected analysis: original human interval decisions, 158 seconds retained. The strict 108-second alternative is retained for comparison only. Both fits reached the weight-change threshold: selected 129 actual iterations; strict 121. Saved n_iter=500 does not mean failure. User IC review and main-v1 HC4 BP were completed on 2026-10-30. v2 has not been rerun.

## Layout

- scripts/: review exporter, evidence generation, ICA fitting/comparison, labeling and topography exporter.
- src/viewer_template.html: viewer source template.
- outputs/Manual_Review/: open review.html here; waveform_data and review_evidence must remain alongside it. human_review_decisions.json contains your selected judgments; import it to restore My decision. strict_review_decisions.json is the alternative.
- outputs/Selected_158s/: selected v1-style output with PreICA/, ICA/, ICA_Review/404/, ICA_Figures/404/HC4/. Topographies are ica_components_1.png and ica_components_2.png. Component numbering is zero-based IC00-29. Do not reuse old-model IC labels.
- outputs/Comparisons/termination_comparison_20261029_223545/: both instrumented runs, per-iteration logs, actual stopping reasons, convergence plot and comparison.json. The selected model here reproduces outputs/Selected_158s/ICA/404_HC4-ica.fif exactly.
- outputs/Comparisons/ica_iteration_audit.json: historical TCP model counters, with their interpretation limitations.

## Saving decisions

Download review decisions JSON saves My decision independently. The viewer reads the displayed dropdown values at export time. Import the downloaded file to resume; browser edits are not automatically written to disk.

## Reproduction

Run scripts/export_selected_topographies.py to redraw the selected model in the original v1 format. It reads the audited model and writes into outputs/Selected_158s/ICA_Figures/404/HC4. It does not fit ICA.
Run scripts/compare_ica_termination.py only when a new comparison is intended; it creates a timestamped directory under outputs/Comparisons. Instrumentation adds observations without changing mathematical updates; exact model reproduction was checked.

## Cleanup

Removed 30 individual topographies, alternate-format overview copies and their duplicate export folder, plus two empty launch logs. Original-format overview pages already exist in the selected output. Kept review evidence, decisions, models and convergence traces. Historical provenance may contain original locations; these are historical records, not active script inputs. No original EEG was changed. On 2026-10-30 the selected HC4 artifacts were promoted to main v1 after backing up previous HC4 artifacts.


## Main-v1 promotion (2026-10-30)

Canonical current outputs are in [../../outputs/v1_preica_test](../../outputs/v1_preica_test). Selected_158s is the local analysis snapshot, not a second final BP location. The completed workbook and synchronized CSV were copied into main ICA_Review/404; images into main ICA_Figures/404/HC4. The matching new PreICA and ICA files were copied together, then main HC4 BP was regenerated. No old component decisions were reused.

Excluded ICs: 0, 5, 6, 7, 9, 10, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 26, 27, 28, 29. Retained fitted ICs: 1, 2, 3, 4, 8, 11, 12, 14, 24, 25. Explicit note priority was checked; other/uncertain category notes use the corresponding checkbox decision. See main ICA_Review/404/404_HC4_decision_resolution.json and 404_HC4_completion.json. The standard BP code restores residual PCA components too; retained IC count is not effective rank.

Previous main HC4 artifacts are backed up in outputs/Previous_Main_HC4_20261030. HC1-HC3 were not rerun. Main HC1-HC4 BP files were checked for readability and finite retained data; HC4 retains exactly 158 seconds after BAD omission. The strict alternative was not promoted. Subsequent harmonized v2 processing is complete for all four blocks, including HC4. See [v2 results](../../../auto_fc_pipeline_v2/outputs/tcp_rank_harmonized/outputs/404/); updated downstream QC remains outstanding.
