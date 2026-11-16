# Controlled longer training, 27 October 2026

Run `REGION-FPN-DURATION-20261027T064327135442Z` changed only the optimization
stopping budget from max8epochs/patience3 to max32epochs/patience6. Seed169,
architecture, uniform TRAIN sampling, data, loss, optimizer, normalization,
threshold0.5 and all six admission gates were unchanged. The original V1 source,
card and failed checkpoint remain untouched. The first eight training losses
and development mean IoUs reproduce exactly: both maximum differences are0.0.

| Metric | Earlier candidate | Longer candidate |
|---|---:|---:|
| Equal-camera mean DEV IoU | 0.581960 | 0.636116 |
| Equal-camera mean DEV Dice | 0.734500 | 0.775435 |
| Worst-image DEV IoU | 0.452406 | 0.479886 |
| Selected epoch | 7 | 19 |
| Completed epochs | 8 | 25 |

Early stopping ended the run at epoch25. The prespecified duration objective,
gain at least0.02IoU over V1, passed with0.054156356. Of30 paired development
images,29 improved and one regressed. This supports the hypothesis for this
same-seed reused DEV cohort, not repeated-seed stability or fresh final accuracy.
Four admission failures remain: meanIoU0.80, each-camera0.75, each-image0.65 and
no camera regression greater than0.05 from the TRAIN-only template. No gate or
threshold was relaxed. The app retains its original model.

New camera means: PUCPR0.711806, UFPR040.603953, UFPR050.592590. The original
common-cache U-Net mean remains0.287151 and conditional TRAIN-template mean0.761297.
These are supplied bay-footprint IoU values, not occupancy accuracy. The fixed-view
template1.0 on two cameras reflects repeated label geometry, not scene understanding.
All17consumed and16quarantined PKLot groups and other protected final sources remain
closed. No protected/quarantined pixels or XML were decoded.

Measured phase after initial checks:16.696seconds, sampled process RSS peak
1,462,804,480bytes. Per-batch cancellation/optimizer/RNG/order checkpoints and a
900second invocation limit remain. Source/split/config hashes and early-stopping
history are retained in the immutable result folder. Selected failed research
checkpoint: `models/checkpoints/region_fpn/REGION-FPN-DURATION-20261027T064327135442Z/epoch_19_064358240679.pt`,
SHA256 `74fd7780c30ff8bed50619a2a8ab597e5ab51a23e728dbe1d9e3d19f06838588`.
All previous and failed weights are preserved; no app promotion.

Full explanation, visually reviewed learning/camera plots and every paired
per-image result are in
`reports/region_duration_REGION-FPN-DURATION-20261027T064327135442Z/`.
Software regression460tests/OK7.539s. The original notebook12 remains a bound
archive of the eight-epoch study; it was not repointed. The accepted offline
app copy, original models, all frozen Singapore methods and other final claims
remain unchanged. No extra trial was counted for plots/analysis/epochs.

Next hypothesis: a separate image-only RGB detail residual can refine the coarse
upsampled mask. Preserve the current backbone/coarse decoder and use a small
full-resolution RGB branch with a zero-initialized last residual layer. Keep
TRAIN sampling, loss and gates fixed. Isolate added-head initialization in a
forked RNG context so the sampler stream can match the duration control. Seal
code/config/split hashes and numeric objectives before fitting. This is a proposed
experiment, not an implemented model or proven cause of the remaining errors.
TRAIN-pattern balancing should be a separate later hypothesis. Repeated unchanged
longer-budget trials or threshold sweeps do not address the failed quality gates.

Sources: existing SRC-DS-001 PKLot (Almeida et al./UFPR,CC BY4.0) and SRC-MOD-003
TorchVision ImageNet ResNet18 under recorded local academic terms. No new download.
Fresh rights-qualified final data is required before a general reliability claim.
Official university compliance, student mastery and physical offline/new-machine/
visible manual acceptance remain open.
