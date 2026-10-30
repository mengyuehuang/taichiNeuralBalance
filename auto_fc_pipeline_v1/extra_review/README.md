# Extra pre-ICA review

This directory contains the extra-review topic, separate from the original v1 pipeline scripts. No analysis was rerun during relocation.

- scripts/: TCP screening, raw/PreICA evidence plotting, and isolated experimental ICA refitting.
- [Five-block pilot comparison](outputs/five_block_pilot_20261030_005542/comparison.html): 105 HC3, 409 HC4, 411 HC3, 102 HC1 and 406 HC3; new outputs stay here. See the [pilot README](outputs/five_block_pilot_20261030_005542/README.md) for decisions and limitations.
- outputs/tcp_preica_screen_20261030_003851/: 72-block screening, shortlist and evidence images.
- manual_preica_review_404/: complete 404 case with its own scripts/, src/, outputs/ and detailed README, including the manual viewer, interval decisions, ICA comparisons and old-HC4 backup.

The normal v1 scripts remain in ../scripts. Extra-review scripts reuse those existing functions when fitting or exporting; they do not duplicate the pipeline implementation. Current production 404 artifacts remain in ../outputs/v1_preica_test. Detailed case: [manual_preica_review_404/README.md](manual_preica_review_404/README.md).

Historical provenance can contain original absolute paths. These describe past runs; active script paths and the selected config have been updated. Original source data and production models were not changed.
