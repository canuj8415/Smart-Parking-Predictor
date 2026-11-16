# Matched RGB-detail capacity experiment

Admission FAILED:ACPDS meanIoU gain0.000190532265 is below the frozen.02 requirement.
Coarse ACPDS0.533460979,detail0.533651511;
coarse PKLotmacro0.649536793,detail0.649636617.
Relative PKLot macro/camera/image retention passed. Fixed-start ACPDS gain and absolute
source/camera/image/template gates failed. No threshold or recipe changed andno app
model was promoted. Tiny positive differences are not an accepted quality improvement.

Both arms trained200newupdates before shared early stopping at round8,and both selected
round2/50newupdates. Their starting coarse checkpoint had600historical PKLot and400
previously selected mixed updates. It was loaded identically; initial real TRAIN logits
matched exactly(maxdifference0),as did coarse weights. The candidate added one8-channel
RGB residual withseed183 andzero final conv. Both usedguarded plainSGDlr.01/no momentum/
no decay,same4PKLot+4ACPDS batches(seed184/185),classweight4.593998,loss,selection,
threshold.5 andnonpadding validity. Existing encoder features were reused;RGB stayed
uint8 until batching andwas normalized once. No219MBfull-pool floatRGB array was made.

Synthetic tests verified normalization/initial-output/coarse-weight/RNG parity,
post-update adapter checkpoint roundtrip andexact mid-pair restart.495fullsoftware
tests pass(8.497sec). This does not assess real OS-kill/powerloss/physical deployment.
Afterfloat64-to-float32 conversion,both arms met the frozen1e-5gradient tolerances.
Their200steps each had0positive PKLotTRAIN directional derivatives. This is a local
first-order numerical property,not finite-step loss or held-out accuracy assurance.

One paired trial,not400runs. Phase26.439s,sampledpeak
RSS1.217GB. No new encoder image forwards;two
initial TRAIN output-parity checks are not new experiments. Allselected/last/failed
weights,source/code/config/sampler hashes andoriginal app models remain preserved.

This tests one fixed warm-start/guarded-SGD/early-stop recipe. A small effect here does
not establish that RGB detail is universally useless or that the representation has
enough capacity. Earlier detail failures stay visible. Do not change widths,thresholds,
step sizes or stopping rules on this reused DEV cohort to force the failed gain gate.

Source data remain PKLot200TRAIN/30DEV andACPDS231TRAIN/35DEV,all496qualified caches.
Provided bay-union supervision is not exhaustive facility/occupancy truth;source
physical/date/pretraining/near-duplicate independence remains unknown. All consumed/
quarantined PKLot groups,HighwayDrive,ACPDS27TEST andSingapore final stay closed.
Credits:SRC-DS-001 PKLot/Almeidaetal./UFPR,CC BY4.0;SRC-DS-021 ACPDS/MartinMarek,MIT2021;
SRC-MOD-003 existing ImageNet ResNet18 under recorded local academic terms.

Next:complete a separate read-only archived-study lesson andexplanations;preserve the
failed gains andallquality gates. Further representation changes need a new bounded
hypothesis andfresh qualified final evidence before any promotion.


Actual early-stop coverage:199unique PKLot and229unique ACPDS TRAIN images,800draws per source;pool sizes200/231 are admission counts.495tests/8.497sec pass. Archive audit verifies553bound hashes/496caches/65DEVpairs/metrics/selection with no new model calls.

New notebook13 actually executed in local Jupyter:5code cells,2PNGs,6archived inputs,4denial probes. It added0scientific experiments/modelcalls. The accepted offline app copy andnotebook12 remain unchanged;portable lesson13 andstudent mastery are unassessed.
