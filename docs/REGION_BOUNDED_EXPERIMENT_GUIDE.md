# Bounded RGB residual, 27 October 2026

Run `REGION-FPN-BOUNDED-20261027T094324175595Z` failed its reliability hypothesis.
The residual became0.5*tanh(raw)*4*p*(1-p),using a detached current-coarse sigmoid
score p. This score gate is not calibrated uncertainty. All initial parameters,
seeds169/170,uniform TRAIN sampling,loss,optimizer,max32/patience6,threshold0.5 and
six admission gates were unchanged. All32sampler hashes match the reference stream.

| Metric | Unbounded detail | Bounded detail |
|---|---:|---:|
| Equal-camera mean DEV IoU | 0.665401 | 0.651700 |
| Equal-camera mean DEV Dice | 0.796214 | 0.786379 |
| Worst-image DEV IoU | 0.400726 | 0.432576 |

Mean change-0.013700731 fails the prespecified gain>=0.02. Worst paired change
-0.128913450 fails the prespecified no paired loss beyond0.05. Eight images improve
and22regress. The worst paired case is UFPR05,2013-02-26,0.669741->0.540828IoU.
All four previous admission failures remain. No threshold/gate relaxation or app
promotion. Selectedepoch32of32;phase50.331seconds,sampled RSS peak1,452,507,136bytes.
Selected failed research checkpoint SHA256:
`7834476ab1790536785da7b399c463f127d244780236caf17dd4438d8ffbadba`.
All previous and failed source/cards/weights are retained.

The finite-input forward audit observes max logit addition0.499920577<=0.5 and
preserves1,070,295strong current-coarse pixel signs. This compares the trained
model with its own coarse component,not with ground truth or a separately trained
older model. A software bound therefore coexists with image regressions. Three
new generated/model tests cover bound/sign behavior,detached-gate/raw gradients
and identical initial parameters/RNG/zero start. Fullsuite466/OK7.680s. Numeric
fixtures are software evidence,not real-world accuracy. One pre-fit finite-value
audit amendment was sealed before training;its unexecuted original protocol and
source snapshots are retained without adding a run.

The paired CSV and two visually reviewed figures are in
`reports/region_bounded_REGION-FPN-BOUNDED-20261027T094324175595Z/`.
No protected/quarantined images/XML were decoded. Normal forbidden accesses0 and
unqualified-cache probe blocked;encoder/BN/protected hashes remain unchanged.
Perbatch checkpoint/cancel/900secondlimit and sealed executor guard remain.

Next assess broader already-qualified ACPDS TRAIN/VALID bay supervision rather
than sweep residual coefficients on the same small fixed-view cohort. See
REGION_DATA_EXPANSION_PLAN.md. That dataset preparation is proposed,not performed.
Existing ACPDS TEST27 and all17consumed/16quarantined PKLot groups remain closed.
Current metrics measure agreement with supplied bay unions,not exhaustive facility,
vehicle occupancy,unseen-camera or independent final accuracy. Current sources:
SRC-DS-001 PKLot,Almeida et al./UFPR,CC BY4.0;SRC-MOD-003 TorchVision ImageNet
ResNet18 under existing local academic terms. No new training source download.
Original app/accepted copy/notebook12 unchanged. Student mastery,physical offline/
new-machine/manual acceptance and official university compliance remain open.
