# A bounded test of learned image features

The frozen-feature head improved ACPDS validation accuracy to 93.07%, with 31
occupied spaces confidently called vacant. It retained the earlier PKLot
development decisions but failed three new-source readiness gates. This motivates
one distinct experiment that lets the final convolution block learn.

The new model starts from the saved head candidate. Layers before `layer4` stay
frozen. Convolution weights in `layer4` and the final classifier can update.
All batch-normalization parameters and running statistics stay frozen, including
those in the last block. The model remains in evaluation mode while gradients
update only the permitted parameters. A synthetic one-step test checks that
these parameters change and every other state value remains identical.

The crop pipeline does not change. The new source uses the exact cache validated
against all 9,746 reference crops. Old-source preparation also compared all
12,132 PKLot crops against the original function. Original image/XML identities,
explicit known occupancy labels, cached feature-row identities and consumed
camera/date exclusions are checked before old-source data is admitted. Routine
crop preparation does not add an experiment for every image or space.

Training contains 7,842 ACPDS and 10,104 PKLot spaces. Each source gets half of
the loss mass, with training-only camera/class balancing. No validation target
is used for a training gradient. Source validation has 1,904 spaces; the reused
PKLot retention cohort has 2,028. These are development cohorts. Neither is a
fresh final benchmark for this experiment.

The fixed recipe uses AdamW at learning rate 0.0001 and weight decay 0.0001,
batches of 64, gradient-norm clipping at 1, at most four epochs and patience two.
Selection minimizes the same equally weighted per-image ACPDS and per-camera
PKLot cross-entropy, calculated stably from logits. The warm epoch zero remains
eligible. The selected epoch is chosen by this loss, not by searching afterwards
for an epoch whose readiness metrics happen to pass.

The initial RGB predictions must reproduce the saved warm-model probabilities
within 0.00001 before any fitting. A separate test requires the batched uint8
RGB normalization to equal the existing single-crop transform exactly. This
keeps a preprocessing change from masquerading as a feature-learning result.

Every source readiness and old-source retention gate remains unchanged. They
include 95% source hard accuracy, 90% for every source image, no more than 1% of
actual occupied source spaces confidently called vacant, and at most 10%
uncertain decisions. Old-source checks limit aggregate/camera accuracy loss,
confident false-vacancy growth and uncertainty growth, and require at least 95%
retention of the same previously correct confident vacancies per camera/date.
This retention baseline is the improved warm head, rather than an easier model.

The run has a 900-second invocation budget, a CANCEL file and memory checks.
Checkpoints retain the model, selected state, optimizer, random state, shuffled
epoch order and next batch offset. A pause can resume the same sealed protocol;
it is not another completed experiment. A full completed trial counts once.

The result must verify the saved checkpoint round-trip and that lower layers
and every batch-normalization state value stayed unchanged. The candidate stays
separate from production even if development passes. The whole ACPDS test
partition and all previous consumed final groups remain closed. A passing
development result still needs a tested durable final claim and a frozen final
evaluation protocol. Automatic region discovery, continuous traffic-video
reliability, detector fusion, physical offline operation, student mastery and
university acceptance remain separate questions.

## 27 October 2026 IST / last-block adaptation improves accuracy but fails vacancy safety

Completed trial ACPDS-LAST-BLOCK-20261027T004612152849Z selected epoch 3/4. Accuracy improved, but new-source per-image and false-vacancy gates and old-source confident false-vacancy non-regression failed. The result remains a research candidate. Full evidence:models/acpds_last_block.json. Do not change the original gates or open final data to excuse these failures.
