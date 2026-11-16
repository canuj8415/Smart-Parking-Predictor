# RGB detail refinement, 27 October 2026

Run `REGION-FPN-DETAIL-20261027T091901724291Z` adds a full-resolution normalized
RGB residual to the frozen-encoder/coarse FPN. Zero final residual weights preserve
the initial coarse output. Extra-head seed170 is isolated so seed169 TRAIN orders
stay unchanged. Runtime control verifies the coarse parameters, zero start, all32
epoch-order hashes and the reference stream against the actual duration checkpoint.
The unchanged recipe includes uniform sampling, weighted BCE+Dice, AdamW0.001,
max32/patience6, threshold0.5 and all six admission gates. No camera IDs are inputs.

| Metric | Coarse duration | RGB detail |
|---|---:|---:|
| Equal-camera mean DEV IoU | 0.636116 | 0.665401 |
| Equal-camera mean DEV Dice | 0.775435 | 0.796214 |
| Worst-image DEV IoU | 0.479886 | 0.400726 |
| Selected / completed epochs | 19 / 25 | 30 / 32 |

Gain0.029284608 meets the prespecified0.02 mean-IoU objective on reused same-seed
DEVELOPMENT data. Of30pairs,26improve and4regress. The worst paired case drops
0.136582899IoU: UFPR05,2013-02-28,0.537309->0.400726. All four quality failures
remain: mean0.80, each-camera0.75, each-image0.65 and template regression0.05.
No gate/threshold relaxation or app promotion. Average improvement does not establish
individual-image reliability, repeated-seed performance or independent final accuracy.

Camera means: PUCPR0.750588, UFPR040.644365, UFPR050.601250. Across supplied target
pixels, precision0.738960/recall0.843151,62403extra/32862missed pixels, predicted/true
area1.140998. These are bay-mask measurements, not occupancy or exhaustive facility
truth. The reviewed regression panel shows missed supplied bays; its post-scoring
selection and source hash are explicit. Source-bound curves/CSV/panel and full
explanation are in `reports/region_detail_REGION-FPN-DETAIL-20261027T091901724291Z/`.

Measured execution phase49.513seconds; sampled process RSS peak1,452,830,720bytes.
Selected failed research checkpoint:
`models/checkpoints/region_fpn/REGION-FPN-DETAIL-20261027T091901724291Z/epoch_30_092019428346.pt`,
SHA256 `62a830f6a991cb468fc37aefce61647dbef2ba6d23907c616cb0faa843b109d4`.
All previous/failed weights, last optimizer/RNG/order checkpoint, exact predictions
and frozen inputs are preserved. Per-batch cancellation and900second limit remain.
The new driver checks its sealed executor and emits its own recovery command.
The historical duration driver had a copied V1 recovery suggestion; no resume
occurred in that completed run. Preserve its source and use the explicit duration
driver only for an actually interrupted valid protocol. Completed runs refuse rerun.

463softwaretests pass, including zero-output identity, unchanged coarse weights/RNG,
finite residual/RGB gradients and reference-order generation without global RNG
changes. Normal training forbidden accesses0; unqualified-cache probe blocked.
All17consumed/16quarantined PKLot groups and other final sources remain closed.

Next proposed hypothesis: bound the RGB contribution, for example a prespecified
0.5*tanh(raw residual) multiplied by4*p*(1-p), where p is the current coarse sigmoid
score. Treat this as a score-based gate, not calibrated uncertainty. A software
bound on a forward contribution does not guarantee accuracy or protect a separately
trained old checkpoint. Keep loss/sampling/budget/threshold/gates fixed; test the
bound and sampler controls before sealing a separate experiment. This is an
unimplemented proposal. A loss-weight ablation or TRAIN-pattern balancing would
be separate later changes; reducing positive weight could worsen missed bays.

Sources: SRC-DS-001 PKLot (Almeida et al./UFPR,CC BY4.0), SRC-MOD-003 TorchVision
ImageNet ResNet18 under recorded local academic terms. No new training-source
download. Notebook12 remains the earlier bound V1 lesson and the accepted offline
app copy is unchanged. Fresh rights-qualified final groups, student mastery,
physical offline/new-machine/visible manual use and official compliance remain open.
