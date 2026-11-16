# Model provenance and actual training

The following original external weights are locally stored, hash-recorded in
`data/resource_receipts.jsonl` and excluded from Git history. TorchVision
repository code is BSD-3-Clause, with a separate publisher disclaimer about
training-data-derived model terms. No raw weight redistribution has occurred.

| Model | Origin / training data | What this project actually did | Local asset |
|---|---|---|---|
| Faster R-CNN ResNet50 FPN V2 COCO_V1 | TorchVision, externally trained on COCO | Inference only; not fine-tuned here | models/pretrained/fasterrcnn_resnet50_fpn_v2.pth |
| Mask R-CNN ResNet50 FPN COCO_V1 | TorchVision, externally trained on COCO | Inference with actual predicted instance masks | models/pretrained/maskrcnn_resnet50_fpn.pth |
| ResNet18 ImageNet1K V1 | TorchVision, externally trained on ImageNet | Frozen feature extraction; new linear occupancy head trained on original PKLot labels | models/pretrained/resnet18_imagenet.pth; models/checkpoints/occupancy_resnet18.pt |

## Project-trained components

| Component | Real training provenance | Actual result and scope | Exact run |
|---|---|---|---|
| Occupancy classifier | 2,605 training crops; 360 validation; 360 test; original PKLot polygons/labels, grouped capture dates | Accuracy 0.952778, F1 0.967370; convenience subset only | VISION-20261024T093740679027Z |
| Parking-region semantic U-Net | 42 training frames, 9 validation, 10 final test frames on distinct dates | IoU 0.251785, Dice 0.402281; weak experimental union mask, not slot IDs | SEGMENTATION-20261024T094218935781Z |
| Historical LSTM | Actual UCI Birmingham observations; causal half-hour grid; 787/322/204 chronological windows | MAE 121.210 slots; persistence 61.142, which is better | LSTM-20261024T091132028689Z |
| VAE | Real PKLot training crops; grayscale 32×32, 2-D latent space | Held-out reconstruction MSE 0.026740; generated samples labelled synthetic, no augmentation-benefit claim | VAE-20261024T094355270123Z |
| NumPy MLP | Synthetic XOR teaching fixture | Handwritten forward/backward, momentum, parameter persistence and numerical gradient checking; not parking accuracy | See MLP run in experiment registry |

Original/classifier labels are never read by the inference decision logic.
Layout files passed to the product contain geometry and IDs only. The original
semantic test was inspected after its foreground-collapse failure; it remains
failed development evidence. The replacement semantic run reserved previously
unused dates for final testing before changing training. The frozen classifier
and its original holdout were not changed.

Code/config/manifest/checkpoint hashes, seed, optimizer and actual metrics are
in each `experiments/results/<run_id>/run.json` and small model cards under
`models/`. No detector mAP or actual vehicle-mask IoU has been measured without
matching ground truth. A pretrained detector producing output is never described
as a detector trained by the student. All implementation/training here was
AI-assisted; student independent explanation/modification remains unassessed.


## 24October2026 / fourth scheduled session

The AI assistant authored and ran the development-only source-geometry audit and ORB/RANSAC layout-transfer candidate, retained its failed gate, added48-check software evidence, continued causal prospective collection, and drafted the editable technical report. Geometric transfer is not a trained neural mask or occupancy classifier. No production checkpoints changed; hashes verified. The report compiler did not return, so no compiled/layout success is claimed. Student authorship, independent learning and complete paper review are not invented. See AUTONOMOUS_PROGRESS.md for exact paths and measured evidence.


## Frozen-encoder region candidate

REGION-TRANSFER-20261024T204533261212Z reuses SRC-MOD-003 local ImageNet ResNet18 weights with a frozen stem/layers1-3 and BN statistics. Only its project decoder learns. Candidate/latest optimizer/RNG checkpoints remain in its run folder; production files unchanged. Same6development masks replay exactly. ValidationIoU0.77054; gate failed, final6 remains undecoded. Architecture/augmentation/pretraining differ from tiny comparators; no component-isolation or independent final improvement claimed. models/region_transfer_candidate.json is the method/model card.


## Loss-only contrast and runtime model identities

REGION-TRANSFER-20261024T211449049328Z changes positive BCE weight only, seed71; gate failed. Its separate models/region_loss_unweighted_candidate.json and run/checkpoints preserve the comparison. New runtime records include exact loaded classifier checkpoint SHA and training run as well as detector SHA. Copied geometry and processed RGB/dimensions have their own identities. Actual real-image exports verified these links without scoring accuracy; all production weights unchanged.

## 25October2026 / explicit gate counting and notebook04

GateCounter is an independently implemented geometric association/counting method, not a newly trained neural model. It consumes existing Faster R-CNN detections; no new pretrained assets or copied third-party algorithm code. Protocol/source snapshots and limitations: models/gate_counter_method_card.json; GATE-VIDEO-20261024T231251838602Z/.

## 25October2026 / actual forecast target times

Forecast timing metadata is additive and does not alter the model architecture/features/targets or checkpoints. FORECAST-TIMING-20261024T234223029035Z verifies exact old development fields and frozen score joins. Original model cards retain their historical code hashes; models/forecast_timing_audit.json records the new audit separately.


27Oct2026 REGION-DATA-V2-20261027T054847435415Z adds qualified200TRAIN/30DEV bay-footprint data with full archive opaque-byte alias checks and460source receipts. No neural calls/training/new checkpoint or app promotion;original and best/failed weights unchanged. manifest SHA256 640dee731bd7d070fda114a86b534c9d646e3fc05e56431e910d7be938cffc9b. See REGION_DATASET_V2_GUIDE.md.


27Oct2026 REGION-FPN-V1-20261027T061402381508Z:SRC-DS-001/SRC-MOD-003,frozenImageNetResNet18/allBN plus32channeldecoder,seed169,200TRAIN/30DEV,epoch7of8. CandidateSHA bee3fa7dbcdf68321adbb73c9706c684104de61926fef3d2f323ec0f03af556a. Originalweights unchanged;foursealedadmissiongatesFAILED despite pairedDEVgain;noapp/finalpromotion. Feature/protocol/split/code/config hashes and failed checkpoint preserved. GuideREGION_FPN_EXPERIMENT_GUIDE.md.


27Oct2026 REGION-FPN-DURATION-20261027T064327135442Z:separatecontrolleddurationdriver;max32/patience6,sameseed169/uniformTRAIN/architecture/loss/gates. First8loss/IoU exact. Selected19/earlystop25. CandidateSHA 74fd7780c30ff8bed50619a2a8ab597e5ab51a23e728dbe1d9e3d19f06838588. PairedDEVgain.054156 passesdurationobjective but4qualitygatesFAIL;noapp/finalpromotion. OriginalV1/model/backbone/BN unchanged. SourcesSRC-DS-001/SRC-MOD-003existingterms.


27Oct REGION-FPN-DETAIL-20261027T091901724291Z:SRC-DS-001/SRC-MOD-003;zero-startfullresRGB8residual,coarseinit/BNfrozenencoder preserved,samplerRNGcontrolsverified. Selected30of32SHA 62a830f6a991cb468fc37aefce61647dbef2ba6d23907c616cb0faa843b109d4. MeanDEVgain.029285butworstimage.400726/fourgatesFAIL;noapp/finalpromotion. Previousweights/cards/sourcesunchanged. Newselfresumecommand/executorguard correct;historicaldurationcopiedhintneverused.


27Oct REGION-FPN-BOUNDED-20261027T094324175595Z:boundedscore-gateddelta.5,allinitialparams/sampler/loss/budget/gates fixed. Selected32SHA 7834476ab1790536785da7b399c463f127d244780236caf17dd4438d8ffbadba. MeanDEV.651700worsens andpairedobjectivefails;4qualitygatesFAIL,noapp/finalpromotion. Softwareboundprooflimitedtocurrentcoarsecomponent. Previousweights/source/cardsunchanged.466tests. ProposedSRC-DS-021regiondatareuseismetadatareviewonly,noregiontraining.


27OctACPDS-REGION-DATA-20261027T101700848553Z qualifies231TRAIN/35DEVderivedbaymasks/validity;no modeltraining. ACPDS-REGION-BASELINES-20261027T102856322278Z evaluates4fixedcheckpointsonall35DEV,originalmeanIoU.325371highest;allabsolutegatesfail. Source/weight/protocol hashes retained;no weightsmodified/promotion/finalclaim. SourceSRC-DS-021authorMIT2021grant,TEST27closed. Newmaskmetrics ignorepadding;notoccupancy/exhaustivefacilitytruth.


## 27 October 2026 — frozen Singapore prospective final and loss parity

The real once-only final SG-FINAL-20261027T105114261864Z started after10:51UTC and completed in
68.656s under the canonical global claim. 23,960 genuine
pre-target forecasts yielded 18,557 matched later observations (77.4499%),
18 global origins and1,337 series. Paired MAE6.198762892149141spaces versus persistence
7.338578434014119,15.5318302% lower. Macro-origin MAE6.1297333824446625 versus
7.253601605432916. OVERALL GATE FAILED: worst-origin regression0.5145131936449854
exceeds the frozen0.5space limit; all six other gates passed. No gate relaxation,
app promotion or final-method rerun.5,403unmatched (5,393no admissible target;
10capacity changes) have no invented error. Actual archived target leads27.15887235–
42.71952783min within frozen20–45min; notexact30min. Forecasts are correlated within origins.
ALL-carpark interval26Oct10:00UTC–27Oct10:51UTC is CONSUMED. See completed claim/outcome,
models/singapore_prospective_final.json and docs/SINGAPORE_FINAL_RESULT.md. Frozen original
reservation text remains unchanged; durable consumption claim is authoritative.

SRC-LIVE-001 official data.gov.sg / Singapore Open Data Licence1.0. Latest due acquisition
79 at10:48:45UTC saved immutable raw JSON/URL/hash/receipt and normalized CSV;0new learned
origins (closed). Rolling persistence71426scores/MAE5.970696945090023spaces is a different
cohort from this final. Next history collection after2026-10-27T11:18:45.546639+00:00. Account gaps not
backfilled. Local clocks/receipts are audit evidence,not external timestamp attestations.
Aggregate availability is not camera/segmentation/occupancy truth or Birmingham transfer.

New all-valid loss/gradient parity test:36seed175cases acrossfloat32/64,two shapes,
three class weights,empty/full/mixed targets pass;475fullsoftwaretests/10.744sec pass.
No neural fit/new weights. Padding helper source and14frozen scoring sources unchanged.
Archive-only audit verified18,557CSVrows,91input/source hashes,seven protected files,
completion/claim/forecast-ledger/report hashes;no raw target JSON or scorer replay.
CSV/plot/explanation render saved metrics only; figure visually reviewed. Rendering,
audit,tests,rows and routine collection are not extra experiments. Trial109->110,
wakeups74->75,121registry entries (11historic excluded),63sourceIDs,no active jobs.
Next required100-run checkpoint200; milestone100already passed. Mixed-source segmentation
recipe/control/gates still need sealing and implementation; no model promotion.
Offline copy/notebook12 unchanged;physical/manual/student/university acceptance open.


## 27 October 2026 — paired mixed-source region study

REGION-MIXED-20261027T112422539381Z completed one prespecified paired DEVELOPMENT experiment.
Two same-initialization frozen-ResNet18/FPN arms trained800updates each,32validation
rounds;duration53.3875622sec,sampled peakRSS1.194799104GB. Control8PKLot versus
mixed4samePKLot+4ACPDS per batch;seed169,independent sampler176/177,AdamW.001,
fixed PKLotTRAIN class weight4.593998,masked BCE+Dice,threshold.5,no augmentation.
Both used equal-source selection and shared early-stop rule. Neither jointly stopped;
selected checkpoints differ: control round24/600updates,mixed round32/800updates.

Selected ACPDS meanIoU improves.37521168166431157->.5760753206867221 (+.2008636390),
minimum.12889572912658714->.3424325144070367. PKLot macroIoU falls
.6318977304892645->.6024336027121105 (-.0294641278;limit-.02),minimum
.4433030164234771->.42616959064327486. Worst individual PKLot index12/UFPR04 loses
.11707891126854553IoU (limit-.05). Relative source-gain/every-camera retention PASS;
macro/every-image retention FAIL. Absolute source/camera/image/template gates also
FAIL. No app-model promotion or gate relaxation. Original,best and failed weights kept.
Both full paths/SHA256s in models/region_mixed.json;curves,pairedCSV,figures,protocol,
code snapshots,split/cache/sampler hashes,features and last paired checkpoint retained.

All496qualified caches (PKLot200TRAIN/30DEV,ACPDS231TRAIN/35DEV),536input/source/
protected hashes and65archived DEV cache pairs verified. Saved prediction metrics and
checkpoint selection replay exactly with0new model forwards. Equalinitialweights,
fixedencoder/BN,800optimizer-step states,offline/raw guard and completed-protocol
refusal pass. Cancel/resume execution remains untested;structural resume state checked.
479softwaretests/7.907sec pass,including4new sampler/source-selection/retention tests.
Initial strictfloat test failure retained;fixed assertion tolerance before sealing/fitting.
No TEST/rawsource images opened by trainer/audit. Derived supplied-bay union and reused
DEV are not exhaustive facility/occupancy truth or fresh final. ACPDS near-duplicate,
location/date/pretraining independence unknown. Source SRC-DS-001/Almeida etal./PKLot
CCBY4.0,SRC-DS-021/MartinMarek/ACPDS MIT2021,SRC-MOD-003 local academic terms.

Both diagnostic figures visually reviewed;post-scoring worst-image choice explicitly
labelled,not representative evidence. No new nativeGUI/manual/student/offline claims.
Guide REGION_MIXED_EXPERIMENT_GUIDE.md.
Next seal an eight-batch TRAIN-only source-loss/gradient-conflict diagnostic (seed178),
then one retention-aware intervention with frozen teacher/control and unchanged gates.
Do not tune DEV thresholds/mixture grids or open finals to erase the failure.

Due Singapore snapshot80 at11:18:59UTC:0new learned origins (closed),1226new rolling
persistence forecasts/1188later outcomes ->72614scores/MAE6.040694631889167spaces.
Nextcollection after2026-10-27T11:48:59.391604+00:00. Immutable rawJSON/receipt/URL/hash/normalizedCSV
saved. Source SRC-LIVE-001/Singapore Open Data Licence1.0. Whole Singapore final remains
CONSUMED with its failed origin-retention gate;no rescore,refit,backfill or changed claim.
Trial110->111,wakeups75->76,122registry entries (11historic),63sourceIDs,noactivejobs.
Milestone100livecheckpoint passed,next200. Notebook12/currentofflinecopy unchanged;
latest studies not packaged,physical/manual/student/university acceptance remains open.


## 27 October 2026 — TRAIN-only source-gradient diagnosis

REGION-GRADIENTS-20261027T115248152177Z completed one sealed diagnostic,seed178:32PKLotTRAIN and32ACPDSTRAIN,
eight fixed batch pairs per frozen selected control/mixed decoder. No optimizer,
model fitting,DEV/final images or weight changes. All16pair journals/105bound hashes/
64TRAIN caches and sampling replay verified;DEV-cache/raw guards block access.
Diagnostic phase1.9240383sec,sampledRSS615075840bytes;64encoder image forwards and
32decoder gradient evaluations are not separate runs. Completed protocol refuses
another execution. Actual cancel/resume execution remains untested;batch journals retained.

Prespecified hypothesis NOT SUPPORTED at mixed checkpoint:3/8negative gradient pairs
(required>=4),mean cosine+.0684822358,median ACPDS/PKLot gradient norm1.38587195,
0/8predicted PKLot first-order worsening (required>=1). At PKLot-only checkpoint,
8/8pairs conflict,mean cosine-.5786272797,median norm ratio15.57362738,and7/8predicted
PKLot first-order worsening. Mean TRAIN losses:control PKLot.52227068/ACPDS3.10637456;
mixed PKLot.61492644/ACPDS.72030045. These static endpoints do not establish when or
why AdamW training lost DEV retention. Raw-gradient first-order geometry is not
finite-step loss,AdamW momentum/preconditioning,causal proof or accuracy. Do not
change samples/thresholds and repeat to force the failed hypothesis to pass.

Implemented SOFTWARE-ONLY auxiliary-gradient projection/norm-cap prototype in
region_gradient_guard.py:remove opposition to PKLot gradient,cap auxiliary norm,
explicit zero-reference policy. Known-plane/zero/invalid cases and512seed179random
vector properties pass. Not used in training or app;no accuracy/retention guarantee.
487softwaretests/7.177sec pass (four new geometry andfour new guard tests beyond479).
Guide REGION_SOURCE_GRADIENT_GUIDE.md,modelscards,CSV/figure/explanation and source
snapshots retained. Figure visually reviewed;TRAIN-only/noncausal/hypothesis scope clear.

Next proposal REGION_GRADIENT_GUARD_PLAN.md:common PKLot-control warm start andplain
SGD/no momentum/no decay for matched raw-versus-guarded source directions,samebatches,
800maximum updates,source-separated validation andunchanged absolute/teacher limits.
The proposal is not yet a sealed protocol or trained candidate. First execute a
synthetic interrupted/restarted optimizer-state equivalence check. Preserve prior
mixed study's failed source/retention gates,all original/best/failed checkpoints.
No app promotion or new final admission. Sources PKLot/Almeidaetal.,CCBY4.0;
ACPDS/MartinMarek,MIT2021;existingImageNetResNet18 retained local academic terms.
TRAIN examples were previously fitted;source independence/exhaustive truth unknown.

Due official Singapore snapshot81 at11:49:49UTC saved rawJSON/receipt/URL/hash/CSV;
0newlearned origins (closed),1339new rollingpersistenceforecasts/1146lateroutcomes
->73760scores/MAE6.08736442516269spaces. Nextcollection after2026-10-27T12:19:49.196440+00:00.
SRC-LIVE-001/Singapore Open Data Licence1.0. Learned final whole interval remains
CONSUMED/failed origin-retention gate;notrescored orchanged;feednotcameraGT.
Trial111->112,wakeups76->77,123registryentries (11historic),63sourceIDs,noactivejobs.
Milestone100livecheckpoint passed,next200. Notebook12/offlinecopy unchanged;latest
studiesnotpackaged. Physical/manual/student/university acceptance remains open.


## 27 October 2026 — matched warm-start guarded SGD; resumed handoff

REGION-GUARDED-20261027T122727629566Z completed one new paired experiment from the identical preserved
PKLot-only600-update checkpoint. Both arms received identical4PKLot+4ACPDS batches,
plainSGDlr.01/no momentum/no decay,fixedclassweight4.593998,nonpadding loss andsource-
balanced selection. Sharedearlystop22rounds/550NEWupdates each (max800);phase40.4253238s,
sampledRSS1151471616bytes. Selected raw325/guarded400newupdates;ancestry/steps distinct.
SourceIDs SRC-DS-001/SRC-DS-021/SRC-MOD-003 and existing licences retained.

Guarded PKLotmacroIoU.6447980579791354 vsraw.6308084799438576 (+.0139895780) FAILS
required+.02. ACPDSmean.523049417200129 vsraw.5269992844589236 (-.0039498673) passes
-.02noninferiority. All matchedPKcamera/image retention pass (worstimage-.0276063).
ALLfixed-PKLot-start teacher retention/source-gain checks pass. Absolute source,
camera,image andconditional-template quality gates stillFAIL. No gate relaxation,
new final or app promotion. GuardedACPDSminimum.20101076 shows substantial quality
gap. Bothselected/last/failedweights and original app checkpoints preserved.

New shared update/save/load helpers passed SYNTHETIC mid-pair interruption andexact
restart equivalence for weights,optimizer groups,logs andcursor. Protocol mismatch,
AdamW/momentum/maximize misuse rejected beforeupdate. Real OS-kill/powerloss untested.
Afterfloat64->float32conversion,guarded maxrelativeprojectionviolation2.482966e-9,
maxauxiliarynormratio1.0000000068 within frozen1e-5. GuardedpositivePKTRAINdirectional
derivative0/550 versusraw14/550 is a first-order numerical property,notfinite-step
loss/held-out/camera accuracy or universal retention. Guard software nowexperimentally
used;modeladmissionstillfailed. Oldsoftware-only record preserved inthiswakeevidence.

491softwaretests/7.450s pass. Archive audit verifies550bound hashes/all496qualified
caches/65savedDEVpairs/metrics/selection/identicalwarmstart andsampling/sharedstop/
SGDgroups/completed-protocol refusal,with0newmodel forwards. Frozen552602059byte
encoder features reused;0newencoder image forwards. Pre-fit driver amendment bound
finalsyntheticrestartlog/helper hashes before sealing/fitting;originalunexecuted
driver snapshot retained. Completed scientific source/protocol hashes unchanged.

Bothfigures visually reviewed;worstACPDS image selectedafter scoring,notrepresentative.
ReusedDEV/derivedsuppliedbay masks remain limited andnotfreshfinal/occupancytruth.
Guide REGION_GUARDED_EXPERIMENT_GUIDE.md;next proposal REGION_DETAIL_GUARDED_PLAN.md.
Test oneRGBdetailbranch under a newmatched guarded-SGD recipe,zero-output/coarseweight/
normalization/sampler parity first;retainabsolute/teacher limits,no DEVparametergrid.
This capacity hypothesis is unproven;earlierdetail failures stayvisible.

Handoff resumed14:18UTC afterlastvisible12:33toolactivity;noexecutionclaimedinthegap,
causeunverified,noobservationbackfill. Queued12:48/13:18/13:48/14:18ticks didnotcreate
experiments oradditionalworkedwakeups. Twoactualofficialcollections82(12:21)and83
(14:19)receipted. Latestrolling74888persistenceoutcomes/MAE6.1241320371755155spaces;
latest1247newforecasts/0newmatches isnotzeroerror. Nextcollectafter2026-10-27T14:49:03.468349+00:00.
Singaporewholefinal remainsCONSUMED/failedorigin-retentiongate;norescore/refit/backdate.
Source SRC-LIVE-001/Singapore Open Data Licence1.0,aggregatefeednotcameraGT.
Trial112->113,wakeups77->78,124registryentries(11historic),63sourceIDs,noactivejobs.
Milestone100livecheckpoint passed,next200. Notebook12/currentofflinecopy unchanged;
lateststudiesnotpackaged. Physical/manual/student/university acceptance remainsopen.


## 27 October 2026 — matched RGB-detail study and archived lesson13

REGION-DETAIL-GUARDED-20261027T145519365050Z completed one paired capacity experiment. Common guarded coarse
start(600historicalPK+400selectedmixed updates),branchseed183,sampler184/185,same
4PK+4ACP batches andguardedSGDlr.01/no momentum/no decay. Initialcoarse weights and
realTRAINlogits exactlyequal(maxdifference0);finalRGBresidual initiallyzero.
RGBuint8 until batching,ImageNetnormalization once;verified frozen features reused.
200NEWupdates each/8rounds/shared earlystop,bothselectedround2/50updates;phase26.4385355s,
sampledRSS1216729088bytes. Actualunique trainingcoverage199PK/229ACP,800draws/source;
admittedpools200/231 are not claimsthat everyTRAIN example wasseen.

ACPDSmean coarse.5334609790587741/detail.5336515113242111,gain.000190532265437 FAILS
frozen.02requirement. PKLotmacro.6495367933320022/.6496366168776596;PKmacro/camera/
image retentionpass. FixedstartingACPDSgain andabsolute source/camera/image/template
qualitygatesFAIL. No apppromotion/recipe/threshold/gatechange. Small effect here doesnot
establish universal lackofRGBvalue. Bothselected/last/failedweights preserved.

495softwaretests/8.497sec pass:fournewadapter contracts/normalization/parity/roundtrip/
SYNTHETIC midpairrestart cases beyond491. Bothguarded200step streams satisfytyped
1e-5constraints andhave0positivePKTRAINdirectionalderivatives;notfinite-step/held-out/
cameraaccuracy. RealOS-kill/powerloss untested.553bound hashes/all496caches/65savedDEV
pairs/metrics/selection/initialcoarse parity/sharedschedule/stop/SGDstate/refusal verify
with0newmodelforwards.0newencoder imageforwards;no219MBfull-poolfloatRGB allocation.
ReusedDEV/partialbay supervision/sourceindependence limits andallclosedfinals retained.
SourceIDs PKLotCCBY4.0/ACPDSMIT2021/existingImageNetlocalacademicterms unchanged.
Bothdiagnostic figures visuallyreviewed;worstACPDSimagechosenpostscoring,notrepresentative.

NEW notebook13_guarded_multisource_segmentation.ipynb actuallyexecuted inlocalJupyter:
5codecells/2inlinePNGs/6checksum-bound immutable archivedoutputs. Threefile andoneDNS
negativeprobes deny raw/prospective reads,projectwrites andexternalnetwork. Probe cell
removed;cellhash/inputhash checks pass. No raw/final/modelweight reads,modelcalls ornew
accuracy. It explains mixed/gradient/guarded/detail failures andsynthetic gradienttoy.
Extra scientificexperiments0;cells/images/probes notruns. Sourcecellhash/binding and
actualkernel audits retained. Pythonfile/socket audits arenotOSisolation;physical/
newmachine/browser/studentmastery unassessed. Notebook12 unchanged;13notebooks total,
notall13freshlyrerun. Current468-fileofflineapp copy stillincludesnotebook08only.

Next:portable read-only lesson13capsule with explicitoriginal-projectfallback denial,
payload/licence/hash/ZIProundtrip andactualrelocatedkernel acceptance,usingexisting
runtime. See GUARDED_LESSON_CAPSULE_PLAN.md. Do not repeattraininggrids to erase this
fixedrecipe's failure. Further representation work needs a newbounded hypothesis,
TRAIN-onlydiagnostics andfresh final/controllerqualification beforepromotion.

DueSingaporecollection84at14:51:29UTC:0newlearnedorigins(closed),1276newrollingbaseline
forecasts/1176lateroutcomes ->76064scores/MAE6.11886043331931spaces. Nextcollectafter
2026-10-27T15:21:29.714381+00:00;actualrawJSON/URL/hash/receipt/CSV preserved,nobackfill. Wholelearned
final remainsCONSUMED/failedorigin-retentiongate,notrescored orchanged;aggregatefeed
isnotcameraGT. SRC-LIVE-001/Singapore Open Data Licence1.0 retained.
Trial113->114,wakeups78->79,125registryentries(11historic),63sourceIDs,noactivejobs.
Milestone100livecheckpoint passed,next200. Official/manual/studentacceptance remainsopen.


## 27 October 2026 — portable archived lesson13 accepted locally

GUARDED-LESSON-CAPSULE-20261027T153015370814Z completed one sealed portable-lesson validation in4.375sec.
17payload files/938343bytes exclude ownmanifest;18ZIPmembers/700765bytes.
ManifestSHA16518d31f96ee44018a782b1c1bbdf9df1c5c8c7aa9a81a4c84b95c0ef0d1e5e;
ZIP SHAab9814cfa0edceb9c6a25b9b2e09815646a16315a90ed654694f4dca10956f9f.
Versioned public delivery `experiments/results/GUARDED-LESSON-CAPSULE-20261027T153015370814Z/lesson13.zip` matches thevalidated archive.
All CRC/member hashes,exactZIPrelocation,payload invariance andmissing-input rejection
beforekernel pass. FullMITnotice/sourceCCBY4.0attribution/source3records retained.

Actual relocated Jupyter:5codecells/2PNGs/6archivedinputs;4file+1DNSnegativeprobes
blockraw/prospective reads,payloadwrites,ORIGINALprojectfallback andexternalPython
network. Copiedhelpers loadinsidecapsule;successful projectreads areexactlybinding+
sixinputs. InlinePNGbytes match previouslyreviewed artifacts. Privatekernel/runtime/
keys remain outsidepayload. No models/weights/rawdata/final data copied orcalled;
0newaccuracy evaluations. ExistingPython3.12.10/Jupyterruntime required,notbundled.
Pythonaudits notOS/networkisolation;physicaloffline/newmachine/browser/studentmastery
remainopen. Accepted468-filefullapp copy unchanged;thisis a separatelocal lessoncapsule.

501softwaretests/8.370sec pass,including6newcapsule boundary/manifest/ZIP fixtures.
Completedprotocolrefusal andarchive/kernel/delivery/inputhash audits passwithout
rerunningkernel/model. One trial115,not perfile/cell/probe;registry126includes11historic.
Guide GUARDED_LESSON_CAPSULE_GUIDE.md,modelcard/pointer,source snapshots andreceipts saved.
Workedwakeups79->80,noactivejobs,milestone100livecheckpoint passed,next200.
All sourceIDs remain63. Original/best/failedweights andfailed modeladmission gates kept.

Next:seal a TRAIN-only target-representation diagnostic,checkingexistingPKLot coarse
reconstruction evidence beforeanyrepeat.32ACPDSTRAINmasks/seed187,fixedstride4area-
downsample/bilinear-upsample/.5reconstruction,nonpaddingvalidity,noDEV/TEST. Thisis
particularlabel interpolation reconstruction,NOT modelaccuracy orprovenupperbound.
Avoidthreshold/LR/width/sourceweightgrids toforcefailedgain tests. Freshfinal/controller
qualificationstillrequired beforepromotion;allclosed sourcegroups remainclosed.

DueofficialSingapore snapshot85 savedactualrawJSON/receipt/URL/SHA/normalizedCSV.
Latest baselinechecked2026-10-27T15:23:41.955774+00:00;rollingoutcomes77225/
MAE6.0965749433473615spaces;1318newpersistence
forecasts/1161lateroutcomes. Learnedissuer0neworigins(closed),
wholefinal remainsCONSUMED/notrescored. Nextcollectafter2026-10-27T15:53:41.955774+00:00;noearlypoll
orbackfill. SRC-LIVE-001/Singapore Open Data Licence1.0,aggregatefeednotcameraGT.
Manual/student/universityacceptance andsourceindependence limits remainopen.


## 2026-11-16 No model change
Trial116 ACPDS-TARGET-REPRESENTATION-20261116T093422210992Z is label-only;no weights trained,loaded or promoted;application model unchanged.


## 2026-11-16 No model change
Trial117 ACPDS-FEATURE-PROBE-20261116T094551398633Z fit four unsaved linear probes for diagnosis only;no weights saved or promoted;application model unchanged.


## 2026-11-16 New research weights(not promoted)
REGION-ENCODER-ADAPT-20261116T101716238167Z candidate/control checkpoints under models/checkpoints/region_encoder_adapt/ (candidate includes adapted ResNet18 layer3/4 derived from SRC-MOD-003 ImageNet weights;same no-redistribution terms). MLP baseline seed0 checkpoint experiments/results/MLP-CONTROLLED-20261116T102002732022Z/baseline_seed0_mlp.npz. App model unchanged.
