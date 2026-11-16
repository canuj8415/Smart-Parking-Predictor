# One bounded occupancy adaptation

The unchanged classifier scored 89.50% on the new source's validation spaces
and confidently called 62 occupied spaces vacant. This motivates one specific
training experiment. Its protocol is saved before fitting and its test partition
remains closed. A successful training run alone cannot qualify the application.

The experiment freezes the original ResNet18 feature extractor, including its
batch-normalization state. It trains only the final 512-to-2 linear classifier.
It starts from the original production head, uses the existing polygon crop and
normalization, and leaves the prediction thresholds at 0.5, 0.25 and 0.75.
There is no crop, perspective, threshold or architecture search in this study.

Training combines 7,842 ACPDS spaces with 10,104 existing PKLot training spaces.
Each source receives half of the training loss weight. The weight calculation
uses training targets only and balances camera/class strata within each source.
ACPDS uses one collection stratum; its image names are not invented camera or
capture-date identifiers. No validation target contributes to a training gradient.

Validation has two parts: all 1,904 ACPDS validation spaces, and the existing
2,028 PKLot development spaces. The latter have been reused in earlier studies;
they measure retention and provide no independent final evidence. A metadata
preflight found no overlap with any consumed PKLot camera/date group. The run
also checks the durable claim metadata and cached feature identities.

Epoch selection minimizes an equally weighted mean of the ACPDS per-image
cross-entropy and the PKLot per-camera cross-entropy. Including the original
head as epoch zero prevents a forced replacement when fitting does not help.
The fixed recipe uses AdamW, learning rate 0.001, weight decay 0.001, batches
of 128, at most 12 epochs, minimum loss improvement 0.0001 and patience 3.
An epoch is not a recorded experiment. This entire bounded trial counts once
only when its result is completed and registered.

Before fitting, probabilities reproduced from the extracted features must match
the unchanged ACPDS baseline within 0.00001. This catches a feature or transform
mismatch before it can masquerade as adaptation. Features are cached per image,
with image, layout, protocol and implementation bindings. Each finished epoch
saves the optimizer, random state, current head and selected head. A 900-second
invocation limit and a CANCEL file stop the work at checked boundaries; the same
protocol can resume from completed feature files and epochs.

Readiness requires all the original new-source gates: at least 95% hard accuracy,
at least 90% for every validation image, no more than 1% of actual occupied
spaces confidently called vacant, and at most 10% uncertain decisions. Retention
also limits PKLot aggregate and camera accuracy drops, false-vacancy increases,
uncertainty growth and losses of previously correct vacant-space decisions.

The last check follows each space's identity. Replacing a lost correct vacancy
with a newly correct vacancy elsewhere does not retain the original decision.
At least 95% of the original correct confident vacancies must remain correct
and confident on each development camera/date. A date with no such baseline
decisions has no retention fraction, rather than an invented perfect score.

All gates are evaluated on the head chosen by the prespecified loss rule.
An epoch cannot be selected afterwards because its safety metrics look better.
If a gate fails, preserve the checkpoint and failure. Do not adjust thresholds
or rerun a parameter grid to turn this development result into an acceptance.
Even a passing development result needs a tested durable whole-test claim and
frozen final protocol before opening the reserved source test data.

Production weights and all original checkpoints remain unchanged. The separate
candidate is research evidence. Automatic parking-region discovery, continuous
CCTV performance, detector fusion, physical offline operation, student mastery
and university acceptance are separate claims.

## 27 October 2026 IST / one bounded source-balanced head trial and complete TRAIN acquisition

Completed trial ACPDS-BALANCED-HEAD-20261026T234728842213Z selected epoch 5 of 8. Development gate=False. Failed checks: new_overall_accuracy, new_every_image_accuracy, new_false_vacancy. Full evidence:models/acpds_balanced_head.json. Original checkpoint, all earlier failures and the reserved TEST remain unchanged. A passing training loss alone does not justify a parameter-grid continuation.
