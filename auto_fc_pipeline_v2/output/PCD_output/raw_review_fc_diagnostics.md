# Split-half FC diagnostics for the raw-reviewed PCD recordings

## Final reviewed PCD cohort and recording selection (2026-11-23)

Processing and FC matrix calculations are complete for 33 participants, each with all four HC blocks (132 block results). The final cohort excludes PCD103, PCD104, PCD107, PCD202 and PCD210 according to confirmed study notes; PCD211 was excluded by user decision because only HC1 is available. No local raw recordings were found for PCD108; this is a data-availability limitation, not an EEG-quality exclusion. None of these seven IDs is included in the final 33.

Two recordings contributed to one block for three included participants: PCD101 HC4, PCD102 HC1 and PCD208 HC4. All three combination decisions were approved and implemented; they are not pending or provisional processing decisions. Each acquisition was processed separately with boundaries preserved, and valid observations were pooled to calculate one matrix per block and frequency band. Recording gaps contributed no observations. Each participant counts once. PCD101 run01 has an incomplete TTL time code, limiting verification of timing continuity; this evidence limitation remains documented despite the completed combination. PCD109 HC4 used only the second recording (HC4_2), with no combination.

Historical 34-participant Clean BP summaries describe an earlier cohort/version and are not the current reviewed cohort. PCD119, PCD206 and PCD218 have historical quality notes but were reviewed and are included; completion does not erase their QC history.


## Current rank and split-half FC register

November 20, 2026. This register covers the thirty raw-reviewed PCD participants with a completed four-block epoch-union common inverse. PCD101 HC4, PCD102 HC1 and PCD208 HC4 pool their two reviewed acquisitions with their boundaries preserved. Earlier fit versions remain in the dated sections below.

For rank, concatenate retained samples of the 14 signed ROI time series, subtract each ROI’s time mean and count singular values greater than the largest singular value times 1e-6. Rank is measured once per block before band-specific FC. The retained seconds below refer to the backprojected EEG; band-specific filtering and trimming can shorten the usable halves.

For stability, split each band’s usable samples chronologically, preserving segment boundaries, and compute one symmetric FC matrix per half. Fisher-transform both matrices, omit their diagonals, subtract each edge’s two endpoint means and add the grand off-diagonal mean within that half. Take the Pearson correlation between the corresponding upper-triangle values (91 edges for 14 ROIs, 4,950 for 100 parcels). Swapping halves gives the same correlation. It measures agreement of relative edge patterns; a signed change in mean FC would require a separate paired difference. The exploratory threshold is r ≥ 0.5 on unrounded values.

| Participant | Block | Retained s | ROI rank | 14 broadband | 14 alpha | 14 beta | 100 broadband | 100 alpha | 100 beta |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [PCD101](outputs/PCD101_epoch_union_20261112/quality_review/split_stability.csv) | HC1 | 331.7 | 14/14 | 0.219 | 0.321 | 0.272 | 0.200 | 0.431 | 0.346 |
| [PCD101](outputs/PCD101_epoch_union_20261112/quality_review/split_stability.csv) | HC2 | 262 | 14/14 | 0.195 | 0.446 | 0.472 | 0.339 | 0.583 | 0.444 |
| [PCD101](outputs/PCD101_epoch_union_20261112/quality_review/split_stability.csv) | HC3 | 319.65 | 14/14 | 0.400 | 0.437 | 0.573 | 0.466 | 0.689 | 0.616 |
| [PCD101](outputs/PCD101_epoch_union_20261112/quality_review/split_stability.csv) | HC4 | 307.1 | 14/14 | 0.020 | 0.452 | 0.349 | 0.173 | 0.623 | 0.318 |
| [PCD102](outputs/PCD102_epoch_union_20261112/quality_review/split_stability.csv) | HC1 | 171.45 | 14/14 | -0.123 | 0.214 | 0.086 | 0.117 | 0.155 | 0.162 |
| [PCD102](outputs/PCD102_epoch_union_20261112/quality_review/split_stability.csv) | HC2 | 314.7 | 14/14 | 0.540 | 0.086 | 0.099 | 0.485 | 0.340 | 0.259 |
| [PCD102](outputs/PCD102_epoch_union_20261112/quality_review/split_stability.csv) | HC3 | 279.5 | 14/14 | 0.627 | 0.063 | 0.262 | 0.541 | 0.345 | 0.429 |
| [PCD102](outputs/PCD102_epoch_union_20261112/quality_review/split_stability.csv) | HC4 | 533.45 | 14/14 | 0.236 | 0.304 | 0.405 | 0.541 | 0.453 | 0.450 |
| [PCD105](outputs/PCD105_epoch_union_20261112/quality_review/split_stability.csv) | HC1 | 278.5 | 14/14 | 0.306 | 0.101 | 0.044 | 0.247 | 0.621 | 0.205 |
| [PCD105](outputs/PCD105_epoch_union_20261112/quality_review/split_stability.csv) | HC2 | 266 | 14/14 | 0.575 | 0.177 | 0.664 | 0.778 | 0.530 | 0.675 |
| [PCD105](outputs/PCD105_epoch_union_20261112/quality_review/split_stability.csv) | HC3 | 296.5 | 14/14 | 0.646 | 0.245 | 0.547 | 0.638 | 0.495 | 0.546 |
| [PCD105](outputs/PCD105_epoch_union_20261112/quality_review/split_stability.csv) | HC4 | 285.5 | 14/14 | 0.347 | 0.141 | 0.389 | 0.276 | 0.580 | 0.251 |
| [PCD106](outputs/PCD106_epoch_union_20261112/quality_review/split_stability.csv) | HC1 | 264.1 | 14/14 | 0.082 | 0.186 | 0.257 | 0.327 | 0.184 | 0.237 |
| [PCD106](outputs/PCD106_epoch_union_20261112/quality_review/split_stability.csv) | HC2 | 245.65 | 14/14 | 0.175 | 0.221 | 0.138 | 0.158 | 0.204 | 0.078 |
| [PCD106](outputs/PCD106_epoch_union_20261112/quality_review/split_stability.csv) | HC3 | 257.9 | 14/14 | 0.187 | 0.199 | 0.352 | 0.270 | 0.070 | 0.252 |
| [PCD106](outputs/PCD106_epoch_union_20261112/quality_review/split_stability.csv) | HC4 | 260.95 | 14/14 | 0.144 | 0.083 | 0.104 | 0.386 | 0.172 | 0.131 |
| [PCD109](outputs/PCD109_epoch_union_20261112/quality_review/split_stability.csv) | HC1 | 288.5 | 14/14 | 0.294 | 0.509 | 0.427 | 0.364 | 0.278 | 0.445 |
| [PCD109](outputs/PCD109_epoch_union_20261112/quality_review/split_stability.csv) | HC2 | 302 | 14/14 | 0.488 | 0.335 | 0.421 | 0.466 | 0.270 | 0.460 |
| [PCD109](outputs/PCD109_epoch_union_20261112/quality_review/split_stability.csv) | HC3 | 273.4 | 14/14 | 0.388 | 0.154 | 0.139 | 0.284 | 0.250 | 0.402 |
| [PCD109](outputs/PCD109_epoch_union_20261112/quality_review/split_stability.csv) | HC4 | 258.3 | 14/14 | 0.453 | 0.236 | 0.268 | 0.462 | 0.229 | 0.477 |
| [PCD110](outputs/PCD110_epoch_union_20261113/quality_review/split_stability.csv) | HC1 | 252 | 14/14 | 0.543 | 0.519 | 0.428 | 0.403 | 0.595 | 0.328 |
| [PCD110](outputs/PCD110_epoch_union_20261113/quality_review/split_stability.csv) | HC2 | 247 | 14/14 | 0.474 | 0.328 | 0.548 | 0.460 | 0.589 | 0.352 |
| [PCD110](outputs/PCD110_epoch_union_20261113/quality_review/split_stability.csv) | HC3 | 243 | 14/14 | 0.398 | 0.467 | 0.444 | 0.293 | 0.525 | 0.307 |
| [PCD110](outputs/PCD110_epoch_union_20261113/quality_review/split_stability.csv) | HC4 | 244 | 14/14 | 0.513 | 0.246 | 0.466 | 0.348 | 0.375 | 0.248 |
| [PCD111](outputs/PCD111_epoch_union_20261114/quality_review/split_stability.csv) | HC1 | 284 | 14/14 | 0.700 | 0.304 | 0.298 | 0.527 | 0.324 | 0.275 |
| [PCD111](outputs/PCD111_epoch_union_20261114/quality_review/split_stability.csv) | HC2 | 299 | 14/14 | 0.634 | 0.362 | 0.454 | 0.608 | 0.386 | 0.440 |
| [PCD111](outputs/PCD111_epoch_union_20261114/quality_review/split_stability.csv) | HC3 | 288 | 14/14 | 0.779 | 0.302 | 0.688 | 0.696 | 0.505 | 0.758 |
| [PCD111](outputs/PCD111_epoch_union_20261114/quality_review/split_stability.csv) | HC4 | 295 | 14/14 | 0.305 | 0.185 | 0.612 | 0.494 | 0.327 | 0.640 |
| [PCD112](outputs/PCD112_epoch_union_20261115/quality_review/split_stability.csv) | HC1 | 262 | 14/14 | 0.353 | 0.568 | 0.392 | 0.200 | 0.607 | 0.336 |
| [PCD112](outputs/PCD112_epoch_union_20261115/quality_review/split_stability.csv) | HC2 | 254.25 | 14/14 | 0.127 | 0.600 | 0.064 | 0.284 | 0.504 | 0.300 |
| [PCD112](outputs/PCD112_epoch_union_20261115/quality_review/split_stability.csv) | HC3 | 245.1 | 14/14 | 0.253 | 0.066 | 0.150 | 0.308 | 0.329 | 0.182 |
| [PCD112](outputs/PCD112_epoch_union_20261115/quality_review/split_stability.csv) | HC4 | 297 | 14/14 | 0.277 | 0.326 | 0.348 | 0.520 | 0.473 | 0.516 |
| [PCD113](outputs/PCD113_epoch_union_20261115/quality_review/split_stability.csv) | HC1 | 342.65 | 14/14 | 0.474 | -0.105 | 0.286 | 0.326 | 0.021 | 0.274 |
| [PCD113](outputs/PCD113_epoch_union_20261115/quality_review/split_stability.csv) | HC2 | 286 | 14/14 | 0.227 | 0.199 | 0.410 | 0.263 | 0.210 | 0.201 |
| [PCD113](outputs/PCD113_epoch_union_20261115/quality_review/split_stability.csv) | HC3 | 272 | 14/14 | 0.472 | 0.370 | 0.031 | 0.276 | 0.090 | 0.297 |
| [PCD113](outputs/PCD113_epoch_union_20261115/quality_review/split_stability.csv) | HC4 | 273 | 14/14 | 0.029 | 0.106 | 0.218 | 0.148 | 0.064 | 0.182 |
| [PCD114](outputs/PCD114_epoch_union_20261115/quality_review/split_stability.csv) | HC1 | 302 | 14/14 | -0.145 | 0.476 | 0.265 | 0.459 | 0.359 | 0.191 |
| [PCD114](outputs/PCD114_epoch_union_20261115/quality_review/split_stability.csv) | HC2 | 263 | 14/14 | 0.080 | 0.268 | 0.023 | 0.239 | 0.332 | 0.175 |
| [PCD114](outputs/PCD114_epoch_union_20261115/quality_review/split_stability.csv) | HC3 | 270 | 14/14 | 0.385 | 0.395 | 0.115 | 0.467 | 0.430 | 0.108 |
| [PCD114](outputs/PCD114_epoch_union_20261115/quality_review/split_stability.csv) | HC4 | 279 | 14/14 | 0.212 | 0.443 | 0.014 | 0.319 | 0.526 | 0.094 |
| [PCD115](outputs/PCD115_epoch_union_20261115/quality_review/split_stability.csv) | HC1 | 280 | 14/14 | 0.717 | 0.378 | 0.402 | 0.550 | 0.251 | 0.212 |
| [PCD115](outputs/PCD115_epoch_union_20261115/quality_review/split_stability.csv) | HC2 | 316 | 14/14 | 0.667 | 0.447 | 0.256 | 0.654 | 0.347 | 0.307 |
| [PCD115](outputs/PCD115_epoch_union_20261115/quality_review/split_stability.csv) | HC3 | 279 | 14/14 | 0.595 | 0.403 | 0.357 | 0.582 | 0.421 | 0.299 |
| [PCD115](outputs/PCD115_epoch_union_20261115/quality_review/split_stability.csv) | HC4 | 278 | 14/14 | 0.704 | 0.326 | 0.030 | 0.577 | 0.527 | 0.189 |
| [PCD116](outputs/PCD116_epoch_union_20261115/quality_review/split_stability.csv) | HC1 | 309 | 14/14 | 0.317 | 0.308 | 0.309 | 0.439 | 0.633 | 0.477 |
| [PCD116](outputs/PCD116_epoch_union_20261115/quality_review/split_stability.csv) | HC2 | 281 | 14/14 | 0.394 | 0.204 | 0.291 | 0.296 | 0.474 | 0.433 |
| [PCD116](outputs/PCD116_epoch_union_20261115/quality_review/split_stability.csv) | HC3 | 260 | 14/14 | 0.138 | 0.203 | 0.290 | 0.634 | 0.507 | 0.725 |
| [PCD116](outputs/PCD116_epoch_union_20261115/quality_review/split_stability.csv) | HC4 | 275 | 14/14 | 0.216 | 0.540 | 0.343 | 0.669 | 0.530 | 0.727 |
| [PCD117](outputs/PCD117_epoch_union_20261115/quality_review/split_stability.csv) | HC1 | 268 | 14/14 | 0.332 | 0.563 | 0.191 | 0.363 | 0.489 | 0.592 |
| [PCD117](outputs/PCD117_epoch_union_20261115/quality_review/split_stability.csv) | HC2 | 249 | 14/14 | 0.331 | 0.524 | 0.429 | 0.320 | 0.416 | 0.427 |
| [PCD117](outputs/PCD117_epoch_union_20261115/quality_review/split_stability.csv) | HC3 | 263 | 14/14 | 0.169 | 0.435 | 0.526 | 0.177 | 0.470 | 0.614 |
| [PCD117](outputs/PCD117_epoch_union_20261115/quality_review/split_stability.csv) | HC4 | 270 | 14/14 | 0.660 | 0.526 | 0.631 | 0.617 | 0.496 | 0.677 |
| [PCD118](outputs/PCD118_epoch_union_20261116/quality_review/split_stability.csv) | HC1 | 278 | 14/14 | 0.334 | 0.320 | 0.424 | 0.524 | 0.257 | 0.405 |
| [PCD118](outputs/PCD118_epoch_union_20261116/quality_review/split_stability.csv) | HC2 | 267 | 14/14 | 0.560 | 0.286 | 0.293 | 0.524 | 0.295 | 0.413 |
| [PCD118](outputs/PCD118_epoch_union_20261116/quality_review/split_stability.csv) | HC3 | 256 | 14/14 | 0.507 | 0.316 | 0.361 | 0.532 | 0.268 | 0.404 |
| [PCD118](outputs/PCD118_epoch_union_20261116/quality_review/split_stability.csv) | HC4 | 257 | 14/14 | 0.791 | 0.467 | 0.364 | 0.704 | 0.360 | 0.326 |
| [PCD119](outputs/PCD119_epoch_union_20261116/quality_review/split_stability.csv) | HC1 | 270 | 14/14 | 0.166 | 0.114 | 0.093 | 0.257 | 0.021 | 0.051 |
| [PCD119](outputs/PCD119_epoch_union_20261116/quality_review/split_stability.csv) | HC2 | 273 | 14/14 | 0.234 | 0.263 | 0.240 | 0.347 | 0.074 | 0.115 |
| [PCD119](outputs/PCD119_epoch_union_20261116/quality_review/split_stability.csv) | HC3 | 272 | 14/14 | 0.514 | 0.433 | 0.204 | 0.442 | 0.276 | 0.072 |
| [PCD119](outputs/PCD119_epoch_union_20261116/quality_review/split_stability.csv) | HC4 | 269 | 14/14 | 0.238 | 0.312 | -0.084 | 0.356 | 0.081 | 0.089 |
| [PCD120](outputs/PCD120_epoch_union_20261116/quality_review/split_stability.csv) | HC1 | 306 | 14/14 | 0.459 | 0.584 | 0.470 | 0.553 | 0.661 | 0.401 |
| [PCD120](outputs/PCD120_epoch_union_20261116/quality_review/split_stability.csv) | HC2 | 324 | 14/14 | 0.131 | 0.491 | 0.344 | 0.376 | 0.583 | 0.417 |
| [PCD120](outputs/PCD120_epoch_union_20261116/quality_review/split_stability.csv) | HC3 | 266 | 14/14 | 0.269 | 0.310 | 0.394 | 0.318 | 0.519 | 0.320 |
| [PCD120](outputs/PCD120_epoch_union_20261116/quality_review/split_stability.csv) | HC4 | 256 | 14/14 | 0.319 | 0.386 | 0.287 | 0.466 | 0.544 | 0.400 |
| [PCD201](outputs/PCD201_epoch_union_20261116/quality_review/split_stability.csv) | HC1 | 280 | 14/14 | 0.437 | 0.318 | 0.117 | 0.475 | 0.224 | 0.218 |
| [PCD201](outputs/PCD201_epoch_union_20261116/quality_review/split_stability.csv) | HC2 | 281 | 14/14 | 0.327 | 0.295 | -0.008 | 0.390 | 0.242 | 0.191 |
| [PCD201](outputs/PCD201_epoch_union_20261116/quality_review/split_stability.csv) | HC3 | 264 | 14/14 | 0.368 | 0.181 | 0.222 | 0.485 | 0.242 | 0.183 |
| [PCD201](outputs/PCD201_epoch_union_20261116/quality_review/split_stability.csv) | HC4 | 267 | 14/14 | 0.489 | 0.202 | 0.157 | 0.334 | 0.254 | 0.236 |
| [PCD203](outputs/PCD203_epoch_union_20261117/quality_review/split_stability.csv) | HC1 | 369 | 14/14 | 0.661 | 0.593 | 0.544 | 0.397 | 0.342 | 0.448 |
| [PCD203](outputs/PCD203_epoch_union_20261117/quality_review/split_stability.csv) | HC2 | 289 | 14/14 | 0.562 | 0.599 | 0.579 | 0.405 | 0.571 | 0.626 |
| [PCD203](outputs/PCD203_epoch_union_20261117/quality_review/split_stability.csv) | HC3 | 280 | 14/14 | 0.210 | 0.290 | 0.555 | 0.245 | 0.055 | 0.252 |
| [PCD203](outputs/PCD203_epoch_union_20261117/quality_review/split_stability.csv) | HC4 | 275 | 14/14 | 0.372 | 0.454 | 0.660 | 0.271 | 0.542 | 0.496 |
| [PCD204](outputs/PCD204_epoch_union_20261117/quality_review/split_stability.csv) | HC1 | 307 | 14/14 | 0.648 | 0.361 | 0.226 | 0.526 | 0.295 | 0.249 |
| [PCD204](outputs/PCD204_epoch_union_20261117/quality_review/split_stability.csv) | HC2 | 291 | 14/14 | 0.413 | 0.410 | 0.065 | 0.417 | 0.233 | 0.170 |
| [PCD204](outputs/PCD204_epoch_union_20261117/quality_review/split_stability.csv) | HC3 | 280.65 | 14/14 | 0.569 | 0.428 | 0.445 | 0.459 | 0.289 | 0.288 |
| [PCD204](outputs/PCD204_epoch_union_20261117/quality_review/split_stability.csv) | HC4 | 67.2 | 14/14 | 0.056 | 0.036 | 0.130 | 0.271 | 0.090 | 0.090 |
| [PCD205](outputs/PCD205_epoch_union_20261117/quality_review/split_stability.csv) | HC1 | 289 | 14/14 | 0.390 | 0.018 | 0.185 | 0.299 | 0.248 | 0.270 |
| [PCD205](outputs/PCD205_epoch_union_20261117/quality_review/split_stability.csv) | HC2 | 264 | 14/14 | 0.211 | 0.385 | 0.295 | 0.227 | 0.243 | 0.241 |
| [PCD205](outputs/PCD205_epoch_union_20261117/quality_review/split_stability.csv) | HC3 | 288 | 14/14 | 0.484 | 0.427 | 0.346 | 0.138 | 0.331 | 0.337 |
| [PCD205](outputs/PCD205_epoch_union_20261117/quality_review/split_stability.csv) | HC4 | 285 | 14/14 | 0.444 | 0.472 | 0.141 | 0.400 | 0.483 | 0.271 |
| [PCD206](outputs/PCD206_epoch_union_20261118/quality_review/split_stability.csv) | HC1 | 457 | 14/14 | 0.137 | 0.045 | 0.304 | 0.131 | 0.187 | 0.410 |
| [PCD206](outputs/PCD206_epoch_union_20261118/quality_review/split_stability.csv) | HC2 | 307 | 14/14 | 0.479 | 0.241 | 0.173 | 0.410 | 0.128 | 0.219 |
| [PCD206](outputs/PCD206_epoch_union_20261118/quality_review/split_stability.csv) | HC3 | 288 | 14/14 | 0.525 | 0.042 | 0.024 | 0.495 | 0.174 | 0.250 |
| [PCD206](outputs/PCD206_epoch_union_20261118/quality_review/split_stability.csv) | HC4 | 276 | 14/14 | 0.462 | 0.146 | 0.069 | 0.430 | 0.266 | 0.233 |
| [PCD207](outputs/PCD207_epoch_union_20261118/quality_review/split_stability.csv) | HC1 | 284 | 14/14 | 0.298 | 0.149 | 0.419 | 0.454 | 0.362 | 0.513 |
| [PCD207](outputs/PCD207_epoch_union_20261118/quality_review/split_stability.csv) | HC2 | 363 | 14/14 | 0.622 | 0.319 | 0.314 | 0.515 | 0.295 | 0.420 |
| [PCD207](outputs/PCD207_epoch_union_20261118/quality_review/split_stability.csv) | HC3 | 284 | 14/14 | 0.463 | 0.246 | 0.126 | 0.492 | 0.272 | 0.337 |
| [PCD207](outputs/PCD207_epoch_union_20261118/quality_review/split_stability.csv) | HC4 | 296 | 14/14 | 0.533 | 0.519 | 0.348 | 0.484 | 0.336 | 0.454 |
| [PCD208](outputs/PCD208_epoch_union_20261118/quality_review/split_stability.csv) | HC1 | 284.5 | 14/14 | 0.605 | 0.408 | 0.716 | 0.552 | 0.137 | 0.558 |
| [PCD208](outputs/PCD208_epoch_union_20261118/quality_review/split_stability.csv) | HC2 | 276.5 | 14/14 | 0.249 | 0.039 | 0.578 | 0.361 | 0.169 | 0.551 |
| [PCD208](outputs/PCD208_epoch_union_20261118/quality_review/split_stability.csv) | HC3 | 277.5 | 14/14 | 0.472 | 0.276 | 0.591 | 0.485 | 0.118 | 0.463 |
| [PCD208](outputs/PCD208_epoch_union_20261118/quality_review/split_stability.csv) | HC4 | 228 | 14/14 | 0.492 | 0.347 | 0.467 | 0.423 | 0.121 | 0.518 |
| [PCD209](outputs/PCD209_epoch_union_20261119/quality_review/split_stability.csv) | HC1 | 293.5 | 14/14 | 0.369 | 0.015 | 0.293 | 0.237 | 0.085 | 0.073 |
| [PCD209](outputs/PCD209_epoch_union_20261119/quality_review/split_stability.csv) | HC2 | 281.65 | 14/14 | 0.230 | 0.260 | 0.157 | 0.355 | 0.119 | 0.079 |
| [PCD209](outputs/PCD209_epoch_union_20261119/quality_review/split_stability.csv) | HC3 | 281.25 | 14/14 | 0.543 | 0.106 | 0.039 | 0.447 | 0.143 | 0.157 |
| [PCD209](outputs/PCD209_epoch_union_20261119/quality_review/split_stability.csv) | HC4 | 286.9 | 14/14 | 0.442 | 0.063 | 0.282 | 0.491 | 0.159 | 0.358 |
| [PCD212](outputs/PCD212_epoch_union_20261119/quality_review/split_stability.csv) | HC1 | 369 | 14/14 | 0.671 | 0.415 | 0.496 | 0.659 | 0.342 | 0.475 |
| [PCD212](outputs/PCD212_epoch_union_20261119/quality_review/split_stability.csv) | HC2 | 286.5 | 14/14 | 0.569 | 0.230 | 0.474 | 0.509 | 0.352 | 0.426 |
| [PCD212](outputs/PCD212_epoch_union_20261119/quality_review/split_stability.csv) | HC3 | 292 | 14/14 | 0.514 | 0.327 | 0.323 | 0.516 | 0.352 | 0.465 |
| [PCD212](outputs/PCD212_epoch_union_20261119/quality_review/split_stability.csv) | HC4 | 286.85 | 14/14 | 0.577 | 0.534 | 0.401 | 0.631 | 0.298 | 0.501 |
| [PCD213](outputs/PCD213_epoch_union_20261119/quality_review/split_stability.csv) | HC1 | 303 | 14/14 | 0.315 | -0.058 | 0.084 | 0.193 | -0.063 | 0.346 |
| [PCD213](outputs/PCD213_epoch_union_20261119/quality_review/split_stability.csv) | HC2 | 310.5 | 14/14 | 0.258 | 0.126 | 0.119 | 0.222 | -0.079 | 0.376 |
| [PCD213](outputs/PCD213_epoch_union_20261119/quality_review/split_stability.csv) | HC3 | 283 | 14/14 | 0.640 | 0.217 | 0.360 | 0.433 | 0.238 | 0.346 |
| [PCD213](outputs/PCD213_epoch_union_20261119/quality_review/split_stability.csv) | HC4 | 295.5 | 14/14 | 0.267 | 0.131 | 0.201 | 0.305 | -0.022 | 0.443 |
| [PCD214](outputs/PCD214_epoch_union_20261119/quality_review/split_stability.csv) | HC1 | 308.5 | 14/14 | 0.490 | 0.011 | 0.325 | 0.583 | 0.347 | 0.588 |
| [PCD214](outputs/PCD214_epoch_union_20261119/quality_review/split_stability.csv) | HC2 | 266 | 14/14 | 0.780 | 0.537 | 0.520 | 0.671 | 0.445 | 0.603 |
| [PCD214](outputs/PCD214_epoch_union_20261119/quality_review/split_stability.csv) | HC3 | 289 | 14/14 | 0.438 | 0.303 | 0.475 | 0.621 | 0.489 | 0.587 |
| [PCD214](outputs/PCD214_epoch_union_20261119/quality_review/split_stability.csv) | HC4 | 263.5 | 14/14 | 0.263 | 0.314 | 0.449 | 0.498 | 0.311 | 0.520 |
| [PCD215](outputs/PCD215_epoch_union_20261120/quality_review/split_stability.csv) | HC1 | 293.25 | 14/14 | 0.263 | 0.100 | 0.168 | 0.366 | 0.078 | 0.423 |
| [PCD215](outputs/PCD215_epoch_union_20261120/quality_review/split_stability.csv) | HC2 | 248.9 | 14/14 | 0.645 | 0.664 | 0.678 | 0.427 | 0.037 | 0.412 |
| [PCD215](outputs/PCD215_epoch_union_20261120/quality_review/split_stability.csv) | HC3 | 268.65 | 14/14 | 0.477 | 0.255 | 0.463 | 0.445 | 0.060 | 0.389 |
| [PCD215](outputs/PCD215_epoch_union_20261120/quality_review/split_stability.csv) | HC4 | 282.9 | 14/14 | 0.224 | 0.045 | 0.383 | 0.389 | 0.179 | 0.400 |
| [PCD216](outputs/PCD216_epoch_union_20261120/quality_review/split_stability.csv) | HC1 | 278.5 | 14/14 | 0.334 | 0.342 | 0.499 | 0.328 | 0.346 | 0.352 |
| [PCD216](outputs/PCD216_epoch_union_20261120/quality_review/split_stability.csv) | HC2 | 276 | 14/14 | 0.508 | 0.686 | 0.379 | 0.366 | 0.486 | 0.229 |
| [PCD216](outputs/PCD216_epoch_union_20261120/quality_review/split_stability.csv) | HC3 | 281 | 14/14 | 0.374 | 0.353 | 0.392 | 0.331 | 0.404 | 0.294 |
| [PCD216](outputs/PCD216_epoch_union_20261120/quality_review/split_stability.csv) | HC4 | 271 | 14/14 | 0.510 | 0.426 | 0.261 | 0.488 | 0.327 | 0.226 |

| [PCD217](outputs/PCD217_epoch_union_20261120/quality_review/split_stability.csv) | HC1 | 219.5 | 14/14 | -0.028 | 0.006 | 0.171 | 0.054 | 0.121 | 0.165 |
| [PCD217](outputs/PCD217_epoch_union_20261120/quality_review/split_stability.csv) | HC2 | 324 | 14/14 | 0.028 | 0.162 | 0.188 | 0.159 | 0.090 | 0.276 |
| [PCD217](outputs/PCD217_epoch_union_20261120/quality_review/split_stability.csv) | HC3 | 303 | 14/14 | 0.296 | 0.272 | 0.245 | 0.218 | 0.227 | 0.492 |
| [PCD217](outputs/PCD217_epoch_union_20261120/quality_review/split_stability.csv) | HC4 | 296 | 14/14 | 0.242 | 0.207 | 0.303 | 0.202 | 0.043 | 0.325 |

120 of 120 blocks reached 14/14 ROI rank. Of 360 block-band pairs, 69 met the exploratory stability screen on the 14-ROI route and 74 on the 100-parcel route.

## Historical diagnostics

## 2026-11-07 review

The 16 available blocks cover PCD101, PCD102, PCD105 and PCD106. PCD101 uses channel-reviewed single-block inverses. PCD102, PCD105 and PCD106 use four-block common inverses. Comparisons across participants must account for these model versions.

Each block was split chronologically at half of the retained usable samples for each frequency band, preserving gaps. The table reports the correlation between the two halves across distinct ROI pairs after Fisher transformation and double centering. Higher values indicate that the *relative pattern* of stronger and weaker connections repeats across halves. A low value flags temporal variability or imprecision. The check alone cannot identify its cause.

## Results

B, A and Beta denote broadband, alpha and beta. The 14-ROI route is the primary analysis. The 100-parcel route is a secondary visualization and QC measure. Values below 0.5 flag a block and band for review. Apply the rule to unrounded values.

| Participant | Block | Retained BP (s) | 14 B | 14 A | 14 Beta | 100 B | 100 A | 100 Beta |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| PCD101 | HC1 | 355.2 | 0.0762 | 0.4995 | 0.3436 | 0.2305 | 0.3839 | 0.3531 |
| PCD101 | HC2 | 276 | 0.5756 | 0.5777 | 0.5568 | 0.3268 | 0.5775 | 0.4953 |
| PCD101 | HC3 | 330.65 | 0.7488 | 0.4763 | 0.5945 | 0.4610 | 0.6571 | 0.5627 |
| PCD101 | HC4 | 53.5 | 0.2012 | 0.1235 | 0.2102 | 0.0360 | 0.1233 | 0.0368 |
| PCD102 | HC1 | 49.15 | -0.0775 | -0.1875 | 0.3760 | 0.0105 | 0.0576 | 0.1167 |
| PCD102 | HC2 | 329.2 | 0.5824 | 0.3690 | 0.4616 | 0.5491 | 0.3824 | 0.6464 |
| PCD102 | HC3 | 293.5 | 0.6213 | 0.3580 | 0.5264 | 0.5447 | 0.3756 | 0.5285 |
| PCD102 | HC4 | 516.45 | 0.5281 | 0.2998 | 0.5286 | 0.5855 | 0.4724 | 0.6328 |
| PCD105 | HC1 | 290.5 | 0.3423 | 0.2023 | 0.0982 | 0.2997 | 0.6758 | 0.3231 |
| PCD105 | HC2 | 274.5 | 0.6553 | 0.1826 | 0.5036 | 0.7258 | 0.6310 | 0.7407 |
| PCD105 | HC3 | 308 | 0.2044 | 0.1883 | 0.6063 | 0.6233 | 0.5672 | 0.5924 |
| PCD105 | HC4 | 293.5 | 0.4092 | 0.1628 | 0.3793 | 0.4433 | 0.6807 | 0.3180 |
| PCD106 | HC1 | 277.6 | 0.2315 | 0.2657 | 0.4067 | 0.3101 | 0.2749 | 0.2814 |
| PCD106 | HC2 | 255.65 | 0.3147 | 0.1826 | -0.0432 | 0.2561 | 0.1955 | 0.0245 |
| PCD106 | HC3 | 266.4 | 0.1779 | 0.1751 | 0.2327 | 0.2753 | 0.1776 | 0.2654 |
| PCD106 | HC4 | 277.45 | 0.4366 | 0.0724 | 0.4211 | 0.3924 | 0.3224 | 0.3517 |

## Interpretation

- 14 regions: 35/48 block-band results fell below the split-half screen. The minimum full-recording versus saved edge correlation was 1.000000.
- 100 regions: 31/48 block-band results fell below the split-half screen. The minimum full-recording versus saved edge correlation was 0.999576.
- PCD101 HC2 cleared the primary screen in all three bands. HC4 uses provisional run01 with 53.5 retained seconds, leaving 24.75 seconds per filtered half.
- PCD102 HC1 remains flagged before statistical inclusion. It retained 49.15 seconds and all three primary split correlations fell below 0.5.
- PCD105 alpha fell below 0.5 in all four blocks.
- PCD106 HC3 retained 15 of 39 reviewed ICs. The note on IC7 (brain?) took precedence over its exclusion checkbox. The six unsure notes retained their explicit include decisions. The recording spans 272.4 s with 266.4 usable seconds in four segments. The current table uses the four-block common inverse.
- PCD106 HC4 retained 10 of 36 ICs under note-first review, including IC29 marked unsure with an explicit include decision. Across the four blocks, 0 of 12 primary block-band results met the stability screen. See the [four-block QC results](outputs/raw_pilot_PCD106_four_blocks/quality_review/summary.json).

Treat flags as prompts for review at the block-band level. They do not authorize participant exclusion, establish an ICA error, or demonstrate group differences. For PCD101, repeat this check when four-block common-inverse matrices replace the single-block outputs.

The [complete QC table](outputs/raw_review_split_stability.csv) includes unrounded values, both edge correlations, usable duration per half, peak channel and amplitude, spectral metrics and the path to each source report. The CSV and per-run figures are stored with the separately distributed outputs.

## 2026-11-08 PCD109 HC1

This single-block inverse used 299.0 retained seconds after manual review. Of 26 reviewed ICs, 12 were retained, including IC11, IC17, IC22 and IC24 marked unsure with explicit include decisions. The measured input rank was 42. The centered split-half correlations for broadband, alpha and beta were 0.4455, 0.3639 and 0.5466 for 14 ROIs, and 0.3610, 0.3465 and 0.4430 for 100 parcels. Only primary beta cleared the 0.5 screen. Full-recording recalculation agreed with the saved matrices across all six checks (minimum edge correlation 0.99990). Repeat the stability check when the participant common inverse is available. [Block-level diagnostic results](outputs/raw_pilot_PCD109_HC1/quality_review/split_stability.csv)

## PCD102 after the HC4 O1 exclusion

The four-block common inverse uses 56 EEG channels. HC1–HC3 reuse the reviewed backprojections; HC4 uses 560.45 retained seconds and 14 retained ICs. The table below supersedes the November 7 PCD102 rows. All four retained ROI series reached rank 14/14 at relative tolerance 1e-6.

| Block | Retained seconds | 14 broadband | 14 alpha | 14 beta | 100 broadband | 100 alpha | 100 beta |
|---|---:|---:|---:|---:|---:|---:|
| HC1 | 49.15 | -0.1146 | 0.0129 | 0.2011 | 0.0243 | 0.0319 | 0.0925 |
| HC2 | 329.2 | 0.4316 | 0.3282 | 0.3938 | 0.5793 | 0.3935 | 0.6348 |
| HC3 | 293.5 | 0.5490 | 0.3040 | 0.4108 | 0.4895 | 0.3586 | 0.4483 |
| HC4 | 560.45 | 0.5948 | 0.3565 | 0.6630 | 0.4856 | 0.5926 | 0.6088 |

[Current block and band diagnostics](outputs/raw_pilot_PCD102_four_blocks_HC4_O1_excluded/quality_review/split_stability.csv). HC1 remains flagged for statistical review given its duration (49.15 s).

## November 12 combined runs

Both participant common inverses and all four HC outputs were recomputed using existing reviewed inputs for the other blocks. The November 8 epoch-policy refits for other blocks remain separate. Retained-sample timelines preserve acquisition boundaries; the 209.001 s and 106.943 s gaps are recorded in input_provenance.json and contribute zero observations. Neither target had an analysis segment crossing the join. Both target blocks reached 14/14 retained ROI rank at relative tolerance 1e-6. Each participant produced 12 primary and 12 pairwise matrices. Across all combined blocks and bands the minimum full-replay edge correlation exceeded 0.9998.

| Participant/block | Retained seconds before / combined | Primary alpha split r | Primary beta split r | Old vs combined centered FC r (alpha / beta) |
|---|---|---|---|---|
| PCD101 HC4 | 53.50 / 307.10 | 0.086 / 0.457 | 0.138 / 0.320 | 0.392 / 0.316 |
| PCD102 HC1 | 49.15 / 171.45 | 0.013 / 0.198 | 0.201 / 0.152 | 0.220 / 0.715 |

PCD101's matched run01 comparator uses the same channel-reviewed four inputs and common-inverse settings as the combined version except for the additional acquisition. The older 32 s four-block result represents a different processing version. PCD102 uses the previous four-block version with O1 excluded downstream. Split correlations describe similarity of chronological halves over usable samples. Both target blocks remain below the exploratory 0.5 primary stability screen in alpha and beta. Comparing run01 and run02 individually under the combined inverse gave centered alpha/beta edge correlations of 0.329/0.275 (PCD101) and -0.116/0.317 (PCD102). After band-edge trimming the two runs contribute 49.5/220.6 s for PCD101 and 39.15/108.3 s for PCD102. PCD101's acquisition interpretation remains provisional. PCD102 HC1 still has limited stability despite increased duration.

[PCD101 matrix comparison](outputs/PCD101_HC4_combined_20261112/quality_review/run_comparison_14roi.png) and [all block/band values](outputs/PCD101_HC4_combined_20261112/quality_review/comparison_to_run01.csv).
[PCD102 matrix comparison](outputs/PCD102_HC1_combined_20261112/quality_review/run_comparison_14roi.png) and [all block/band values](outputs/PCD102_HC1_combined_20261112/quality_review/comparison_to_run01.csv).

### PCD105 epoch-union refits (November 12, 2026)

All four inputs use the reviewed November 12 ICA refits. Values below are chronological split-half centered edge correlations for the 14-ROI route. The exploratory stability screen is r >= 0.5. All 24 saved 14-ROI and pairwise-100 matrices passed shape, finite off-diagonal, symmetry and bound checks.

| Block | Retained s | ROI rank | Broadband r | Alpha r | Beta r |
|---|---:|---:|---:|---:|---:|
| HC1 | 278.50 | 14/14 | 0.306 | 0.101 | 0.044 |
| HC2 | 266.00 | 14/14 | 0.575 | 0.177 | 0.664 |
| HC3 | 296.50 | 14/14 | 0.646 | 0.245 | 0.547 |
| HC4 | 285.50 | 14/14 | 0.347 | 0.141 | 0.389 |

[Full QC results](outputs/PCD105_epoch_union_20261112/quality_review/split_stability.csv) and [FC output](outputs/PCD105_epoch_union_20261112/outputs/PCD105/04_static_fc).

### PCD106 epoch-union refits (November 12, 2026)

All four inputs use the reviewed November 12 ICA refits. Values below are chronological split-half centered edge correlations for the 14-ROI route. The exploratory stability screen is r >= 0.5. All 24 saved 14-ROI and pairwise-100 matrices passed shape, finite off-diagonal, symmetry and bound checks.

| Block | Retained s | ROI rank | Broadband r | Alpha r | Beta r |
|---|---:|---:|---:|---:|---:|
| HC1 | 264.10 | 14/14 | 0.082 | 0.186 | 0.257 |
| HC2 | 245.65 | 14/14 | 0.175 | 0.221 | 0.138 |
| HC3 | 257.90 | 14/14 | 0.187 | 0.199 | 0.352 |
| HC4 | 260.95 | 14/14 | 0.144 | 0.083 | 0.104 |

[Full QC results](outputs/PCD106_epoch_union_20261112/quality_review/split_stability.csv) and [FC output](outputs/PCD106_epoch_union_20261112/outputs/PCD106/04_static_fc).

### PCD109 HC1 epoch-union refit (November 12, 2026)

Single-block inverse. The reviewed fit retained 10 of 26 ICs and 288.5 seconds. The accepted 14-ROI time series had rank 14/14 at relative tolerance 1e-6. All six matrices passed shape, finite off-diagonal, symmetry and bound checks. The table reports chronological split-half centered edge correlations (exploratory screen r >= 0.5).

| Band | Previous 14-ROI r | Updated 14-ROI r | Updated 100-parcel r |
|---|---:|---:|---:|
| broadband | 0.445 | 0.340 | 0.340 |
| alpha | 0.364 | 0.530 | 0.341 |
| beta | 0.547 | 0.510 | 0.365 |

[Full QC results](outputs/PCD109_HC1_epoch_union_20261112/quality_review/split_stability.csv) and [FC output](outputs/PCD109_HC1_epoch_union_20261112/outputs/PCD109/04_static_fc).

### PCD109 four-block common inverse (November 13, 2026)

The common inverse uses the 56 shared EEG channels. HC4 uses the second acquisition with Oz blocked. HC1–HC3 used all 57 EEG channels for ICA. The table reports chronological split-half centered edge correlations for 14 ROIs. The exploratory screen is r >= 0.5. All 24 saved matrices passed shape, finite off-diagonal, symmetry and bound checks.

| Block | Retained s | ROI rank | Broadband r | Alpha r | Beta r |
|---|---:|---:|---:|---:|---:|
| HC1 | 288.50 | 14/14 | 0.294 | 0.509 | 0.427 |
| HC2 | 302.00 | 14/14 | 0.488 | 0.335 | 0.421 |
| HC3 | 273.40 | 14/14 | 0.388 | 0.154 | 0.139 |
| HC4 | 258.30 | 14/14 | 0.453 | 0.236 | 0.268 |

[Full QC results](outputs/PCD109_epoch_union_20261112/quality_review/split_stability.csv) and [FC output](outputs/PCD109_epoch_union_20261112/outputs/PCD109/04_static_fc).

### PCD110 four-block common inverse (November 13, 2026)

All four reviewed fits retained C2 and excluded AFz. HC4 excluded IC12 following explicit confirmation. The common inverse used 56 EEG channels. All 24 matrices passed numerical checks. Minimum full-recording QC agreement was 0.99995. The table reports centered split-half edge correlations for the 14-ROI route (exploratory screen r ≥ 0.5).

| Block | Retained s | ROI rank | Broadband r | Alpha r | Beta r |
|---|---:|---:|---:|---:|---:|
| HC1 | 252.0 | 14/14 | 0.543 | 0.519 | 0.428 |
| HC2 | 247.0 | 14/14 | 0.474 | 0.328 | 0.548 |
| HC3 | 243.0 | 14/14 | 0.398 | 0.467 | 0.444 |
| HC4 | 244.0 | 14/14 | 0.513 | 0.246 | 0.466 |

[Full QC results](outputs/PCD110_epoch_union_20261113/quality_review/split_stability.csv) · [FC results](outputs/PCD110_epoch_union_20261113/outputs/PCD110/04_static_fc)

### PCD111 four-block common inverse (November 14, 2026)

The common inverse used 53 EEG channels after excluding Fp1, Cz, O2 and O1 across all four blocks. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-bound checks. Minimum full-recording QC agreement was 0.99996. The centered split-half screen reached r ≥ 0.5 for 5/12 block-band pairs on the 14-ROI route and 6/12 on the 100-parcel route.

[Rank results](outputs/PCD111_epoch_union_20261114/rank_validation.json) · [Split-half results](outputs/PCD111_epoch_union_20261114/quality_review/split_stability.csv) · [FC matrices](outputs/PCD111_epoch_union_20261114/outputs/PCD111/04_static_fc)

### PCD112 four-block common inverse (November 15, 2026)

The four blocks used 56 EEG channels after excluding AFz. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-bound checks. Minimum full-recording QC agreement was 0.99992. Centered split-half correlations reached the exploratory threshold of 0.5 in 2/12 block-band pairs for 14 ROIs and 4/12 for 100 parcels.

[Rank results](outputs/PCD112_epoch_union_20261115/rank_validation.json) · [Split-half results](outputs/PCD112_epoch_union_20261115/quality_review/split_stability.csv) · [FC matrices](outputs/PCD112_epoch_union_20261115/outputs/PCD112/04_static_fc)

### PCD113 four-block common inverse (November 15, 2026)

All four blocks used 56 EEG channels after excluding Fp1. The 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-bound checks. Minimum full-recording QC agreement was 0.99974. Centered split-half correlations reached the exploratory threshold of 0.5 in 0/12 block-band pairs for 14 ROIs and 0/12 for 100 parcels.

[Rank results](outputs/PCD113_epoch_union_20261115/rank_validation.json) · [Split-half results](outputs/PCD113_epoch_union_20261115/quality_review/split_stability.csv) · [FC matrices](outputs/PCD113_epoch_union_20261115/outputs/PCD113/04_static_fc)

### PCD114 four-block common inverse (November 15, 2026)

All four blocks used 57 EEG channels. All 24 matrices passed shape, finite off-diagonal, symmetry and correlation-bound checks. Minimum full-recording QC agreement was 0.99967. Centered split-half correlations reached 0.5 in 0/12 block-band pairs for 14 ROIs and 1/12 for 100 parcels.

[Rank results](outputs/PCD114_epoch_union_20261115/rank_validation.json) · [Split-half results](outputs/PCD114_epoch_union_20261115/quality_review/split_stability.csv) · [FC matrices](outputs/PCD114_epoch_union_20261115/outputs/PCD114/04_static_fc)

### PCD115 four-block common inverse (November 15, 2026)

All four blocks retained 57 EEG channels. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-bound checks. Minimum full-recording QC agreement was 0.99980. Centered split-half correlations reached 0.5 in 4/12 block-band pairs for 14 ROIs and 5/12 for 100 parcels.

[Rank results](outputs/PCD115_epoch_union_20261115/rank_validation.json) | [Split-half results](outputs/PCD115_epoch_union_20261115/quality_review/split_stability.csv) | [FC matrices](outputs/PCD115_epoch_union_20261115/outputs/PCD115/04_static_fc)

### PCD116 four-block common inverse (November 15, 2026)

All four blocks used 55 EEG channels after excluding Fp1 and AFz. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-bound checks. Minimum full-recording QC agreement was 0.99996. Centered split-half correlations reached 0.5 in 1/12 block-band pairs for 14 ROIs and 7/12 for 100 parcels.

[Rank results](outputs/PCD116_epoch_union_20261115/rank_validation.json) · [Split-half results](outputs/PCD116_epoch_union_20261115/quality_review/split_stability.csv) · [FC matrices](outputs/PCD116_epoch_union_20261115/outputs/PCD116/04_static_fc)

### PCD117 four-block common inverse (November 15, 2026)

All four blocks retained 57 EEG channels. All 24 FC matrices passed validation. Minimum full-recording QC agreement was 0.99991. Centered split-half correlations reached 0.5 in 6/12 block-band pairs for 14 ROIs and 4/12 for 100 parcels.

[Rank results](outputs/PCD117_epoch_union_20261115/rank_validation.json) · [Split-half results](outputs/PCD117_epoch_union_20261115/quality_review/split_stability.csv) · [FC matrices](outputs/PCD117_epoch_union_20261115/outputs/PCD117/04_static_fc)

### PCD118 four-block common inverse (November 16, 2026)

All four blocks retained 56 EEG channels. All 24 FC matrices passed validation. Minimum full-recording QC agreement was 0.99990. Centered split-half correlations reached 0.5 in 3/12 block-band pairs for 14 ROIs and 4/12 for 100 parcels.

[Rank results](outputs/PCD118_epoch_union_20261116/rank_validation.json) · [Split-half results](outputs/PCD118_epoch_union_20261116/quality_review/split_stability.csv) · [FC matrices](outputs/PCD118_epoch_union_20261116/outputs/PCD118/04_static_fc)

### PCD119 four-block common inverse (November 16, 2026)

All four blocks used 57 EEG channels. All 24 FC matrices passed validation. Minimum full-recording QC agreement was 0.99969. Centered split-half correlations reached 0.5 in 1/12 block-band pairs for 14 ROIs and 0/12 for 100 parcels. HC2 used the manually corrected recording links. Independent participant-identity confirmation remains undocumented.

[Rank results](outputs/PCD119_epoch_union_20261116/rank_validation.json) · [Split-half results](outputs/PCD119_epoch_union_20261116/quality_review/split_stability.csv) · [FC matrices](outputs/PCD119_epoch_union_20261116/outputs/PCD119/04_static_fc)

### PCD120 four-block common inverse (November 16, 2026)

All four blocks used 57 EEG channels. All 24 FC matrices passed validation. Minimum full-recording QC agreement was 0.99991. Centered split-half correlations reached 0.5 in 1/12 block-band pairs for 14 ROIs and 5/12 for 100 parcels.

[Rank results](outputs/PCD120_epoch_union_20261116/rank_validation.json) | [Split-half results](outputs/PCD120_epoch_union_20261116/quality_review/split_stability.csv) | [FC matrices](outputs/PCD120_epoch_union_20261116/outputs/PCD120/04_static_fc)

### PCD201 four-block common inverse (November 16, 2026)

HC4 excluded C2 upstream. All four blocks used the same 56 channels for the participant inverse, with the average reference recomputed on those channels. All 24 FC matrices passed validation. Minimum full-recording QC agreement was 0.99981. Centered split-half correlations reached 0.5 in 0/12 block-band pairs for 14 ROIs and 0/12 for 100 parcels.

[Rank results](outputs/PCD201_epoch_union_20261116/rank_validation.json) | [Split-half results](outputs/PCD201_epoch_union_20261116/quality_review/split_stability.csv) | [FC matrices](outputs/PCD201_epoch_union_20261116/outputs/PCD201/04_static_fc)

### PCD203 four-block common inverse (November 17, 2026)

All four blocks excluded Fp1 and AF3 and used the same 55 EEG channels for the common inverse. All 24 FC matrices passed validation. Minimum full-recording QC agreement was 0.99986. Centered split-half correlations reached 0.5 in 8/12 block-band pairs for 14 ROIs and 3/12 for 100 parcels.

[Rank results](outputs/PCD203_epoch_union_20261117/rank_validation.json) | [Split-half results](outputs/PCD203_epoch_union_20261117/quality_review/split_stability.csv) | [FC matrices](outputs/PCD203_epoch_union_20261117/outputs/PCD203/04_static_fc)


### PCD204 four-block common inverse (November 17, 2026)

All four blocks excluded Fp1 and used the same 56 EEG channels for the common inverse. All four blocks reached 14/14 ROI rank and all 24 primary FC matrices passed validation. Minimum full-recording QC agreement was 0.99975. Centered split-half correlations reached 0.5 in 2/12 block-band pairs for 14 ROIs and 1/12 for 100 parcels. HC4 retained only 67.20 s; each half had approximately 33.6 s for broadband and 29.6 s after alpha/beta filtering and trimming (100-parcel sampling gives 33.5/29.5 s). Its low split-half agreement should be interpreted alongside this short duration; the diagnostic alone does not identify the cause or automatically exclude the block.

[Rank results](outputs/PCD204_epoch_union_20261117/rank_validation.json) | [Split-half results](outputs/PCD204_epoch_union_20261117/quality_review/split_stability.csv) | [FC matrices](outputs/PCD204_epoch_union_20261117/outputs/PCD204/04_static_fc)


### PCD205 four-block common inverse (completed November 18, 2026)

All four blocks excluded AF7 and retained 56 EEG channels. HC1-HC4 retained 289, 264, 288 and 285 seconds. All four signed 14-ROI time series reached rank 14/14 at relative tolerance 1e-6. All 24 primary FC matrices passed dimension, symmetry, finite off-diagonal and correlation-range checks. The run directory retains its November 17 launch date.

Neither route reached the exploratory centered split-half r >=0.5 screen in any of its 12 block-band combinations (0/12 for 14 ROIs, 0/12 for 100 parcels). This indicates limited agreement in relative edge patterns across halves, not rank deficiency or evidence that one half has uniformly stronger FC. It does not by itself identify noise, physiological change or a processing error as the cause, and no participant exclusion was applied. Minimum full-recording-versus-saved edge correlation was 0.99987180.

[Rank results](outputs/PCD205_epoch_union_20261117/rank_validation.json) | [Split-half results](outputs/PCD205_epoch_union_20261117/quality_review/split_stability.csv) | [FC matrices](outputs/PCD205_epoch_union_20261117/outputs/PCD205/04_static_fc)


### PCD206 four-block common inverse (November 18, 2026)

All four blocks excluded AF7 and P7 and used the same 55 EEG channels for the common inverse. HC1-HC4 retained 457, 307, 288 and 276 seconds. All four signed 14-ROI time series reached rank 14/14 at relative tolerance 1e-6. All 24 primary FC matrices passed dimension, symmetry, finite off-diagonal and correlation-range checks. Input copies were verified against the reviewed backprojections with SHA256 hashes.

Centered split-half r reached the exploratory 0.5 screen in 1/12 block-band combinations for 14 ROIs (HC3 broadband, r=0.525190) and 0/12 for 100 parcels. The 100-parcel HC3 broadband value is 0.495364 and remains below the threshold on unrounded values. This indicates limited relative edge-pattern agreement across chronological halves; it is not rank deficiency, does not show uniformly stronger FC in one half, and does not by itself establish a noise or physiological cause. Minimum full-recording-versus-saved edge correlation was 0.99976952. No additional exclusion was inferred from these diagnostics. The pre-existing source-note quality concern remains documented; completed review does not establish that all residual contamination is absent.

[Rank results](outputs/PCD206_epoch_union_20261118/rank_validation.json) | [Split-half results](outputs/PCD206_epoch_union_20261118/quality_review/split_stability.csv) | [FC matrices](outputs/PCD206_epoch_union_20261118/outputs/PCD206/04_static_fc)


### PCD207 four-block common inverse (November 18, 2026)

All four blocks retained 57 EEG channels. HC1-HC4 retained 284/363/284/296 seconds and 10/9/7/7 reviewed ICs. All four signed 14-ROI time series reached rank 14/14 at relative tolerance 1e-6; all 24 primary FC matrices passed validation. Centered split-half r >=0.5 was met by 3/12 block-band combinations on the 14-ROI route and 2/12 on the 100-parcel route. Minimum full-recording-versus-saved edge correlation was 0.99992042. These split-half statistics measure relative edge-pattern agreement and do not establish the cause of low agreement or constitute automatic exclusion. HC4 had 9 Other components and low ICLabel confidence before manual review; final decisions followed the human workbook. Input copies were SHA256-verified.

[Rank results](outputs/PCD207_epoch_union_20261118/rank_validation.json) | [Split-half results](outputs/PCD207_epoch_union_20261118/quality_review/split_stability.csv) | [FC matrices](outputs/PCD207_epoch_union_20261118/outputs/PCD207/04_static_fc)


### PCD212 four-block common inverse (November 19, 2026)

All four blocks excluded AFz and used 56 EEG channels. Reviewed valid durations:369,286.50,292,286.85 seconds; retained IC counts:11,14,16,16. All four signed 14-ROI time series reached rank14/14 at relative tolerance1e-6. All24 FC matrices passed shape,finite off-diagonal,symmetry and correlation-range checks. Centered split-half r>=0.5: 5/12 on the14-ROI route and 5/12 on the100-parcel route. Minimum full-recording-versus-saved edge correlation:0.99994140. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

[Full results](outputs/PCD212_epoch_union_20261119/README.md)


### PCD213 four-block common inverse (November 19, 2026)

All four blocks excluded AFz and used 56 EEG channels. Reviewed valid durations: 303, 310.50, 283 and 295.50 seconds; retained IC counts: 8, 8, 8 and 6. Signed 14-ROI ranks (HC1-HC4): 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 1/12 on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-recording-versus-saved edge correlation: 0.99957239. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

[Full results](outputs/PCD213_epoch_union_20261119/README.md)


### PCD214 four-block common inverse (November 19, 2026)

All four blocks retained 57 EEG channels. Valid durations HC1-HC4: 308.50, 266.00, 289.00 and 263.50 seconds; retained IC counts: 9, 8, 8 and 7. Signed 14-ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 3/12 on the 14-ROI route and 7/12 on the 100-parcel route. Minimum full-recording-versus-saved edge correlation: 0.99992535. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

[Full results](outputs/PCD214_epoch_union_20261119/README.md)


### PCD215 four-block common inverse (November 20, 2026)

All four blocks exclude Fp1 and retain 56 EEG channels. Valid durations HC1-HC4: 293.25, 248.90, 268.65 and 282.90 seconds. Retained IC counts: 4, 3, 5 and 5. Signed ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 3/12 on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-recording-versus-saved edge correlation: 0.99989116. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

[Full results](outputs/PCD215_epoch_union_20261120/README.md)

### PCD216 four-block common inverse (November 20, 2026)

All four blocks exclude F1 and retain 56 EEG channels. Valid durations HC1–HC4: 278.50, 276.00, 281.00 and 271.00 seconds. Retained IC counts: 4, 3, 4 and 6. Signed ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 3/12 on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-recording-versus-saved edge correlation: 0.99990393. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

[Full results](outputs/PCD216_epoch_union_20261120/README.md)


### PCD217 four-block common inverse (November 20, 2026)

All four blocks exclude P7 and retain 56 EEG channels. Valid durations HC1-HC4: 219.50, 324.00, 303.00 and 296.00 seconds. Retained IC counts: 8, 6, 7 and 5. Signed ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 0/12 on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-recording-versus-saved edge correlation: 0.99979477. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

[Full results](outputs/PCD217_epoch_union_20261120/README.md)


### PCD218 four-block results (November 21, 2026)

All four blocks retain 57 EEG channels. Valid durations HC1-HC4: 364.50, 278.50, 265.00 and 240.50 seconds. Retained IC counts: 1, 3, 3 and 5. Signed 14-ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 1/12 on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-versus-saved edge correlation: 0.99959282. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

[Full results](outputs/PCD218_epoch_union_20261121/README.md)


### PCD219 four-block results (November 21, 2026)

All four blocks retain 57 EEG channels. Valid durations HC1-HC4: 307.00, 262.30, 436.00 and 269.50 seconds. Retained IC counts: 6, 2, 5 and 5. Signed 14-ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >=0.5: 0/12 on the 14-ROI route and 0/12 on the 100-parcel route. Minimum full-versus-saved edge correlation: 0.99969933. Split-half agreement is exploratory QC, not a rank test or automatic exclusion.

[Full results](outputs/PCD219_epoch_union_20261121/README.md)


### PCD220 four-block results (November 21, 2026)

All four blocks retain 57 EEG channels. Retained durations HC1–HC4: 253.50, 245.60, 242.85 and 304.00 seconds. Retained IC counts: 14, 19, 13 and 16. Signed 14-ROI ranks: 14/14, 14/14, 14/14, 14/14. All 24 FC matrices passed shape, finite off-diagonal, symmetry and correlation-range checks. Centered split-half r >= 0.5: 5/12 on the 14-ROI route and 2/12 on the 100-parcel route. Minimum full-versus-saved edge correlation: 0.99987000. Split-half agreement compares connection patterns from the chronological halves of retained data within each HC; it is exploratory QC, not a rank test or automatic exclusion. The rank above concerns signed ROI time series, not FC matrix rank.

[Full results](outputs/PCD220_epoch_union_20261121/README.md)
