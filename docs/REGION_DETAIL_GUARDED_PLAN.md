# Proposed image-detail test after guarded SGD

This is a proposal, not a sealed protocol, trained candidate or app update.
The guarded-SGD study retained every fixed PKLot starting-model limit but failed
its required.02gain over matched rawSGD (actual.013989578) and absolute source
quality. More image detail is a capacity hypothesis; the current results do not
prove that missing detail caused the failures. Earlier from-scratch RGB-detail
and bounded-detail studies also failed; preserve them and their limitations.

Use a new matched two-arm driver, keeping completed controllers unchanged.
Both arms should start from the selected guarded coarse checkpoint:
`models/checkpoints/region_guarded/REGION-GUARDED-20261027T122727629566Z/guarded_round_16_122824975957.pt`
(SHA256 `e5f2f9a890307d705510cd8ad7a719211e722bfa20c531b49e00525637f33b30`).
It inherited600PKLot updates and then selected400new mixed updates; describe that
ancestry accurately. Preserve its weights, all earlier best/failed snapshots and
the550-update last-state checkpoint separately.

Compare the coarse decoder against the existing8-channel full-resolution RGB
residual architecture under a COMMON guarded-SGD recipe. Only the detail branch
is the architectural intervention. Both arms use the same warm coarse state,
plainSGDlr.01/no momentum/no decay, source gradients, class weight4.593997955322266,
source validity, matched4PKLot+4ACPDS batches, validation and early-stop rules.
Propose branch seed183 and sampler seed184/185; seal these and all gates before
fitting. Do not sweep branch widths, thresholds, step sizes or source weights.

First inspect and test `RegionDetailDecoder` in
`src/smart_parking/region_detail.py`. Its forward contract is
`forward(features,normalized_rgb)`; RGB must be converted from uint8 to[0,1] and
normalized once with the recorded ImageNet mean/std. The final residual conv is
zero-initialized. Load the common checkpoint into `.coarse`, then verify exact
initial output parity, identical coarse weights and sampler-stream independence.
Use an adapter to give both models the same tuple interface required by
`region_guarded_training.source_step`. Test normalized-RGB handling and checkpoint
round trips. Do not modify the old scientific modules merely to add adapters.

Reuse the verified four-scale496-image encoder feature cache only after binding
its original protocol/pretrained/normalization/split hashes. Keep RGB as uint8
until batching to avoid a219MB full-pool float32 RGB allocation. Adapted evaluation
must retain the same nonpadding mask semantics and immutable source roles.
Monitor the existing1.7GB sampled RSS bound and900second cancellable limit.

Propose800maximum NEW updates per arm, validation every25, shared early stop when
both arms are stale6rounds, and the same source-balanced selection objective.
Record actual shared updates and differing selected steps separately. The tested
paired save/load helpers and synthetic mid-pair rollback must still pass with
the adapters before fitting. Real OS-kill/power-loss behavior remains untested.

Seal a hypothesis of at least.02ACPDS meanIoU gain over matched coarse control,
PKLot macro loss at most.02, and every PKLot camera/image loss at most.05. Retain
all existing absolute source/camera/image/template and previous-coarse limits,
plus fixed starting-model retention and source-gain comparisons. Finalize exact
comparison roles before fitting; do not rewrite completed gates if they fail.
No additional final access or app promotion follows from a development gain.

These remain reused development datasets, derived supplied-bay supervision and
unknown physical/date/pretraining/near-duplicate independence. Outside supplied
polygons is not exhaustive nonparking truth. ACPDS27TEST, consumed/quarantined
PKLot groups, HighwayDrive and the Singapore final interval stay closed.
