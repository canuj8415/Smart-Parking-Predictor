# Mixed-source bay-union study

One prespecified two-arm DEVELOPMENT experiment trained the same frozen-encoder FPN
with PKLot-only versus balanced PKLot/ACPDS batches. Both arms started from the same
decoder state, used the same class weight, learning rate, loss, validation objective
and 800 optimizer updates. No augmentation or new pretrained acquisition occurred.

| Selected model | PKLot macro-camera IoU | ACPDS mean-image IoU | Selected updates |
|---|---:|---:|---:|
| Control | 0.631898 | 0.375212 | 600 |
| Mixed | 0.602434 | 0.576075 | 800 |

Mixed improved ACPDS by 0.200864
IoU, but PKLot macro IoU changed by -0.029464
(limit -.02). Worst PKLot image change -0.117079 exceeded the -.05 retention limit.
All-camera relative retention passed; aggregate and individual-image retention failed.
Absolute source quality and conditional-template gates also failed. Overall admission FAILED.
No application model was replaced and no gate was relaxed.

Selection maximized equal-source mean IoU for both arms; selected checkpoint steps differ.
Training budgets were equal, not selected-step checkpoints.32 rounds were validations,
not32 experiments. The full paired study took 53.388s;
sampled peak process RSS 1.195GB. Checkpoints and batch
hashes, the paired last-state resume file, frozen features and unsuccessful selected models
remain available locally. Completed protocols refuse another training execution.

Data: PKLot200TRAIN/30DEV, ACPDS231TRAIN/35DEV, all496 qualified caches. Mixed batches use
4PKLot examples shared with each8-example control batch and4ACPDS examples. Each round
uses100unique ACPDS images, and all231 appear across the complete schedule. Encoder
parameters/BN stayed frozen. ACPDS padding is excluded from loss/metrics; PKLot validity
is all true. Class weight4.593998 came only from PKLot TRAIN for both arms.

These are previously exposed development sets and derived supplied-bay masks, not fresh
final, exhaustive facility or occupancy truth. ACPDS source location/date/pretraining and
near-duplicate independence remain unknown. Camera ID enters the PKLot template comparator
and macro reporting only, never the image model. Matching ACPDS camera templates are N/A.
The worst regression image was chosen after scoring for diagnosis, not representative proof.
No final pixels/semantics, source body acquisition, threshold search or app promotion occurred.

Sources: SRC-DS-001 PKLot / Almeida et al./UFPR, CC BY4.0; SRC-DS-021 ACPDS / Martin Marek,
explicit MIT2021 grant; SRC-MOD-003 existing ImageNet ResNet18 under retained local academic
terms. Preserve all original, previous best and failed weights.

Next: design one retention-aware mixed-source objective under a new sealed protocol,
with a frozen PKLot teacher/control and source-specific validation. First diagnose TRAIN-only
source loss/gradient conflicts; avoid development threshold or mixture-coefficient grids.
Keep the current absolute/retention gates. Fresh qualified final data/controller is still
required before any promotion; consumed/quarantined groups remain closed.


479 full software tests passed in7.907sec, including four new sampler/selection/retention tests. An initial floating-point exact-equality test failed (0.6000000000000001 versus0.6); the assertion now uses tolerance and the failed log is preserved. No scientific result was changed.

Actual cancellation/restart has not been execution-tested; paired checkpoint structure and optimizer800-step states were verified. The completed protocol refuses rerun before active registration or training.

The proof-only archive audit verified536bound hashes and all65saved development image/target/validity pairs, metrics and checkpoint selection with zero new model forwards.
