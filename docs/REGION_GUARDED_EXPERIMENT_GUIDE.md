# Matched warm-start raw / guarded SGD study

Overall admission FAILED. The guarded arm passed every retention/gain check against
the fixed PKLot starting model. Against the new matched raw-SGD arm,PKLot macro gain
was 0.013989578,below the prespecified.02. ACPDS mean change was -0.003949867,within the
-.02 noninferiority limit. Every matched PKLot camera/image retention check passed.
Absolute source/camera/image and conditional-template quality gates still failed.
No gate was relaxed and no app model was replaced.

| Selected checkpoint | PKLot macro IoU | ACPDS mean IoU | New selected updates |
|---|---:|---:|---:|
| Fixed starting model | 0.631898 | 0.375212 | 0 |
| Matched raw SGD | 0.630808 | 0.526999 | 325 |
| Guarded SGD | 0.644798 | 0.523049 | 400 |

The starting model already had600historical PKLot training updates. Both new arms
started from its identical weights and ran550NEW updates before the shared early-stop
rule fired at round22. The same batches,plainSGDlr.01/no momentum/no weight decay,
class weight4.593998,source-balanced selection,loss,threshold.5 andfrozen encoder were
used. Selected checkpoint steps differ. Projection PLUS norm capping is one combined
intervention;this does not isolate their individual effects. Common warm start and
SGD differ from the old from-scratch AdamW experiment,so do not attribute cross-study
differences only to this rule.

The auxiliary gradient component opposing PKLot is removed,then its norm is capped
at PKLot gradient norm. After float64-to-float32 conversion,the maximum guarded
relative projection violation was 2.48296615223e-09
and maximum auxiliary/reference norm ratio 1.00000000676,
within the frozen1e-5 tolerance. Guarded positive PKLot TRAIN directional derivatives
were0/550;raw control14/550. These are first-order numerical checks,not measured
finite-step loss,held-out/camera accuracy or a universal retention guarantee.

The actual shared save/load helpers passed a SYNTHETIC interruption between arms:
resumed weights,optimizer state/groups,cursor andlogs exactly matched uninterrupted
execution. Malformed bindings and AdamW/momentum/maximize misuse were rejected.
This fixture does not establish real OS-kill/power-loss/physical deployment behavior.

One paired study,not550or1100runs. Phase40.425s,
sampled peakRSS1.151GB;no new encoder image forwards.
Verified previously cached496image features were reused with byte/protocol/pretrained/
normalization bindings. Source data remain PKLot200TRAIN/30DEV andACPDS231TRAIN/35DEV.
ACPDS nonpadding masks exclude padding from loss/metrics. Raw/source/final images
were not opened. Derived supplied-bay masks and reused DEV are not exhaustive facility,
occupancy truth or fresh final evidence. Source physical/date/pretraining independence
is unknown. All consumed/quarantined final boundaries remain closed.

Source credits: SRC-DS-001 PKLot / Almeida etal./UFPR,CC BY4.0;SRC-DS-021 ACPDS /
MartinMarek,explicit MIT2021 grant;SRC-MOD-003 existing ImageNet ResNet18 under
retained local academic terms. All old/best/failed weights and original app models kept.

Next: test one additional image-detail branch under a separately sealed matched
guarded-SGD recipe,with zero-output initialization and common warm start. First
check the existing detail decoder input/normalization contract and initial-output
parity;retain all absolute/retention gates. Do not tune thresholds,step tolerances
or source coefficients on this DEV cohort to erase the current failure. New detail
capacity is a hypothesis,not a proven cause or accepted candidate. Fresh qualified
final/controller evidence is still required before any promotion.


491 full software tests passed in7.450sec. Final archive audit verified550bound hashes,496qualified caches,65saved development pairs,metrics/selection,shared schedule/warm start,SGDstate andearlystop with no new model calls.

Handoff resumed at14:18UTC after the last visible12:33tool activity. No execution is claimed during the gap,its cause was not independently established,and observations were not backfilled. Queued timer ticks are not experiments.
