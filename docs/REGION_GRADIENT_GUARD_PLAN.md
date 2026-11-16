# Proposed retention-aware experiment

This is an implementation plan, not a sealed protocol or a trained candidate.
The TRAIN-only diagnostic rejected persistent conflict at the selected mixed
checkpoint: only3/8 pairs conflicted and0/8 predicted local PKLot loss growth.
At the fixed PKLot-only checkpoint,8/8 pairs conflicted,7/8 predicted PKLot
first-order worsening, and the median ACPDS/PKLot gradient norm ratio was15.573627.
This motivates testing a bounded adaptation direction from that starting point;
it does not establish the cause of the earlier AdamW development regression.

Implement a new two-arm driver. Do not modify the completed mixed or gradient
controllers. Both arms start from the identical preserved PKLot-only checkpoint:
`models/checkpoints/region_mixed/REGION-MIXED-20261027T112422539381Z/control_round_24_112526188690.pt`
(SHA256 `3da3166c6a3ea6a311178e5bf916a832d91d85fa7001664c12bab21a3bdf85e8`).
The selected checkpoint was trained600updates; do not describe it as the800-step
endpoint. Use the same frozen encoder,431TRAIN/65reusedDEV caches, source validity,
class weight4.593997955322266 and threshold.5.

The matched control uses the equal-source raw decoder gradient. The candidate
uses `region_gradient_guard.guard_auxiliary_gradient(g_PK,g_AC)`: remove the
auxiliary component opposing the PKLot gradient and cap auxiliary norm at PKLot
norm. Average the resulting auxiliary and PKLot directions with equal weight.
Zero PKLot gradient suppresses auxiliary direction explicitly. This combined rule
tests projection plus norm capping together; it cannot identify each component's
individual effect.

Use plain SGD with no momentum or weight decay for BOTH arms, so the tested
direction matches the raw-gradient geometry. An initial fixed learning rate.01
is proposed; fix it before fitting and do not select it using DEV. This changes
the common optimizer/warm start from the earlier experiment, so compare the new
matched arms rather than attributing differences against the old AdamW run only
to the gradient guard. Float64 geometry must be converted deliberately to each
parameter's training dtype; record numerical residuals after conversion.

Use sampler seed180 with the existing paired_schedule function's mixed schedule:
fourPKLot and fourACPDS examples per batch, exactly the SAME batch indices for both
arms. Maximum800updates each, validation every25updates, the same source-balanced
selection objective and shared early-stop rule as the earlier paired experiment.
Keep update counts equal, preserve all selected/failed checkpoints and record
selected checkpoint steps separately. Use bounded runtime/RSS, cancellation,
per-pair checkpoints and the completed-protocol refusal guard. Add and execute a
synthetic interrupted/restarted optimizer-state equivalence check before fitting;
actual cancel/resume remains untested in the earlier training study.

Seal all code/config/split/cache/warm-start/sampler hashes and comparison gates
before any fitting. Preserve existing absolute PKLot macro.80/camera.75/image.65,
ACPDS mean.80/image.65, original/template retention and prior-coarse gates.
The fixed PKLot teacher comparison still requires ACPDS gain at least.05, PKLot
macro loss at most.02, and every camera/image loss at most.05. For the NEW matched
balanced control comparison, propose PKLot macro gain at least.02, ACPDS mean
loss at most.02, and no camera/image loss above.05. These are new prospective
comparison roles, not a relaxation of failed old-study gates. Finalize all gates
before starting; never rewrite a completed protocol if they fail.

The helper's four software tests include known-plane, zero/invalid-gradient and
512seed179random-vector properties. It has not trained a model. First-order
geometry does not guarantee finite-step loss, source accuracy, AdamW behavior or
fresh-data retention. Previously exposed DEV, supplied-bay masks, unknown source
independence and all consumed/quarantined final boundaries retain their limits.
No app promotion is authorized by software properties or development gains alone.
