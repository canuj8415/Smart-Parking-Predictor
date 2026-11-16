# Scheduled Smart Parking development

The user authorized autonomous project work every 30 minutes on 24 October 2026.
Active app automation: `smart-parking-development-and-validation`, attached to
this chat. This is a saved development schedule, not evidence that future runs
have already executed. Local execution requires the computer and app to be running;
account and execution limits still apply.

## Starting checkpoint

- Python/Jupyter implementation and source traceability remain required.
- Latest committed product/QA checkpoints: `809e1de`; inventory correction `a2c0de4`.
- 23 automated tests pass. Two notebooks have executed code cells without errors.
- Occupancy classifier: 95.28% on 360 held-out small-subset crops.
- Semantic U-Net: IoU 0.2518, experimental; original failed run retained.
- Birmingham LSTM: MAE 121.21 versus persistence 61.14; no superiority claimed.
- Three original Singapore snapshots retained; latest captured provider time
  2026-10-24T18:55:36+08:00. Existing live observations are not camera ground truth.
- Native export-dialog save, real traffic-video validation, physical offline
  rehearsal and official academic acceptance remain incomplete.

## Resume here

Read current applicable instructions, progress/requirements/test records and model
cards. Choose the highest-impact executable improvement, state its hypothesis and
validation gate, implement it, run meaningful targeted checks and preserve the
outcome. Do not rerun setup or tune repeatedly against the existing final test.
Use unused appropriate data for fresh final evaluation of changed methods.

Improve segmentation and historical forecasting, expand legitimate real-world
evaluation, finish application reliability and build the remaining submission
materials. Missing university files block official compliance assertions only.
Retain all original assets, attribution, failures and best verified checkpoints.

Counter and exact next actions: `data/automation_state.json`. The counter starts
at zero for work after schedule creation; prior registry IDs are preserved
separately. Count completed uniquely recorded experiments or validation trials,
not frames, epochs, simulated loop iterations or status checks. Update the counter
after writing durable experiment evidence. Prevent overlapping trainers.

At each 100-run milestone, acquire a valid official live snapshot if reachable,
record raw JSON/CSV/source/time/hash, and test freshness/schema/count bounds and
app behavior. Score forecasts only against matching later observed target values
from the same source; record not evaluable when those targets do not exist.
Never infer camera detection/segmentation accuracy from aggregate live counts.
Use source-compliant polling and a defined collection plan where more history is
needed. The schedule does not imply continuous background data collection is
already installed or running.

Prefer purposeful experiments and varied stress tests over identical repeated
simulations. Preserve checkpoints before execution limits; resume later when
capacity is available. Never bypass limits or approvals or purchase services.
Save exact next steps, active jobs, measured gains/failures and blockers after
each productive run. Surface substantive changes and failures requiring action;
avoid routine unchanged summaries. Completion needs implemented and tested
acceptance criteria with honest residual limitations, not a claim of perfection.

## First manually triggered scheduled-work session

Completed experiment `FORECAST-RESIDUAL-20261024T161926856855Z`: residual LSTM
trained for 44 epochs, best checkpoint at epoch 32, using 787 training and 322
validation windows. Validation MAE was 24.563 spaces versus persistence 40.220
and the previous absolute LSTM 85.580 on the SAME validation windows. Overall
error reduction versus persistence was 38.93%. This is development validation,
not the earlier final-test result or live accuracy. Final-test windows were
excluded from this experiment. The production forecast checkpoint is unchanged.

The preregistered validation gate failed: NIA Car Parks and Others-CCCPS119a
had more than 10% MAE regression relative to persistence. Candidate and complete
predictions/curves/protocol are saved separately under the experiment folder.
Three new regression tests bring the software suite to 26 passing tests.
Counter: 1 completed new run; the next scheduled 100-run live checkpoint is 100.

User-facing Excel report:
`outputs/01a16cf3-1f03-7631-8fac-d3d382c5b25c/smart_parking_training_run_001.xlsx`.
It contains summary/settings/source locations, all 44 epochs, all 27 validation
car parks and all 322 predictions. Artifact formulas and input-change behavior,
visual renders, exported XML/cached results and ZIP integrity were checked.
Native Excel was not opened; artifact reimport did not complete in its bounded
attempt. The exported workbook has no formula error cells. Exact output checksum
and these verification limits are saved in the run's report_provenance.json.

Next: diagnose these two per-park failures using training and validation evidence,
confirm stability across predeclared seeds, and reserve fresh appropriate final
data before a frozen candidate is independently evaluated or promoted. Avoid
repeatedly tuning against the already inspected final Birmingham test. Complete
the outstanding real-video/application and submission tasks independently.

## First scheduled heartbeat — 24 October 2026, 16:44 UTC

Completed five predeclared training runs: raw residual seeds 45/46, and a new
past-hour trend-constrained residual at seeds 44/45/46. Combined with the first
run, the completed new-experiment counter is 6. All used only training and
development-validation windows. Protocol and complete per-seed/per-park results:
`experiments/results/FORECAST-CONFIRMATION-20261024T164706701529Z/`.

Raw residual validation MAE over three seeds: mean 24.658, range 24.563-24.806
spaces. Trend-constrained residual: mean 21.088, range 20.902-21.195 versus
persistence 40.220. The best development run reduces aggregate error 48.03%,
but ALL seeds fail at least one per-park gate. No production model was changed,
no final-test windows were constructed/scored, and no live neural accuracy is
claimed. Do not promote on aggregate error alone.

Diagnosis: the two originally failing parks have mean signed 30-minute changes
of +22.17/+44.24 spaces in training versus -2.67/-2.83 in validation. This shows
temporal distribution shift consistent with their failures, not proof of a sole
cause. The trend constraint improved overall development error but introduced
other per-park failures, all retained. Avoid endless validation-guided tuning.

Established a defined prospective live collection protocol in
LIVE_EVALUATION_PROTOCOL.md. Run `scripts/collect_prospective_live.py` once at the
start of each heartbeat when reachable. It saves a source-compliant raw snapshot
and freezes a non-neural next-snapshot persistence baseline for later evaluation.
First collection: provider 2026-10-25T00:49:36+08:00, 2,005 parks/2,423 lot-type
records, 1,230 sufficiently fresh baseline forecasts frozen, ZERO scored outcomes
so far. Match only real later same-capacity observations 20-45 minutes after
issue; report actual horizons and do not imply an exact 30-minute benchmark.
Missing targets are not zero error. This supplies real future evidence while
the separate 100-experiment live checkpoint remains due at run 100.

All 33 software tests pass, including prospective timing/deduplication checks
and trend constraints. Next actions are saved in data/automation_state.json.
First collect the eligible future snapshot, then work on training-only calibration
or an interpretable trend baseline and fresh final data. Independent segmentation,
real-video and application work remains available without further neural tuning.

## Second scheduled heartbeat — 24 October 2026, 22:44 IST

The next official Singapore snapshot produced the FIRST prospective baseline
outcomes: 1,098 earlier frozen predictions matched later real readings from 1,098
car-park IDs. Persistence MAE is 2.228 available spaces; actual observed horizons
range 21.43-24.31 minutes (mean 23.30). This is one cohort and a non-neural
next-snapshot baseline, NOT live neural/camera accuracy or an exact 30-minute
benchmark. No missing target was scored as zero error. Another 1,124 fresh
baseline predictions were frozen; cumulative issued forecasts 2,354. Five raw
snapshots are retained. Exact checkpoint: experiments/evidence/HEARTBEAT-20261024T171431Z/.

Completed a separate segmentation study, run SEGMENTATION-KNOWN-20261024T172100422056Z.
Its 48 new frames cover three source camera IDs and 24 dates excluded from all
previous configured-layout dates and the prior semantic final dates. Per camera,
six dates train, one validates, one tests; first/last frames per date. Thus
36/6/6 frames. This is a represented-camera/date holdout, not unseen-camera
generalization. Selection closed and its checkpoint hash was sealed before final
mask loading. 100 epochs completed; best validation epoch 95. On the SAME six
fresh final frames, new IoU 0.4814 vs original model 0.2533 vs a train-only camera
geometry baseline 0.7676. Candidate quality gate FAILED; original checkpoint and
app model stay unchanged. These final dates are now consumed and must not guide
further tuning. Full masks, comparison figure, metrics and selection seal retained.

Preparation caught two issues before training: one chosen date had only one
paired frame; eligible dates now require two before deterministic selection.
Then a genuine parser bug was found: original PKLot XML uses both `point` and
`Point`. The reader handled only lowercase and mistook capitalized contours for
empty polygons. Fixed tag handling preserves original coordinates and strict
geometry validation. The exact reserved frames were retained on recovery. Source
bytes were not edited; both preparation failures and initial protocol are saved.

Original image split audit: training used pucpr/ufpr04, while validation/test used
ufpr05. The new study deliberately answers a different deployment question with
all three camera IDs represented. Camera ID alone still does not establish view
alignment; the ufpr04 camera-geometry baseline only scored 0.2846 on new final
dates. Treat view/annotation drift as a hypothesis to investigate with training
and validation evidence, not a proven cause or permission to repair test labels.

Also fixed video processing ignoring the selected detection threshold and an
off-by-one decoded-frame count at natural end. Added meaningful decoder-setting
fixtures, not real traffic evidence. All 40 software tests pass. One completed
new training experiment brings the counter to 7; preparatory failures and frame
iterations are not counted as completed runs. Next 100-run live checkpoint is
still run 100. Exact next actions are saved in data/automation_state.json.


## Third scheduled heartbeat - 24 October 2026, 23:14 IST

Acquired SRC-VID-001: Editor's original Street traffic recording via Wikimedia
Commons, CC BY 3.0. Kept the 26,490,572-byte source unchanged; publisher SHA-1
and local SHA-256 verified. Source, creator, licence, changes, receipt and exact
local paths are recorded; attribution JSON accompanies each derived run.

REAL-VIDEO-20261024T174949479219Z completed a failed validation trial: the decoder
reported 1000 FPS/35004 frames, despite presentation timestamps and 1050 decoded
frames indicating about 30 FPS. FPS-derived sampling/seek chose only two frames
and failed the motion probe. Evidence retained; counted once as a completed
validation trial, not as successful inference validation or model training.

REAL-VIDEO-20261024T175346074895Z repaired sampling using actual presentation
timestamps and sequential motion probes. It decoded 1050 real moving frames,
processed 18 samples at 2-second intervals through 34 seconds, and verified three
distinct original motion frames. Observed rate 29.9997 FPS versus reported 1000.
CPU median inference 8.162s, p95 10.551s, load 2.119s; offline processed throughput
0.1104fps including output writing. Detection counts ranged 4-20 per sample.
These counts are predictions, not verified ground truth. No supplied boxes,
tracks, slots or flow labels: detector mAP, parking occupancy and entrance/exit
accuracy remain NOT EVALUABLE. The single street clip is not a parking benchmark.
Full protocol, hashes, JSON detections, CSV and overlays remain under each run.

Detection-only image/video paths now explicitly report occupancy unavailable,
not zero occupied/free spaces. CSV omits occupancy columns without a layout.
The desktop video workflow still requires a matching layout; the real road clip
was tested via the noninteractive API. Recorded threshold settings are respected.
The successful run used the vision implementation whose hash was sealed in its
protocol; the subsequent unknown-count display fix is covered by software tests.
All 44 software checks pass; no physical offline or native export-dialog claim.

Six official Singapore snapshots now retained. This collection added 1076 scored
future persistence outcomes and 1270 frozen forecasts. Cumulative outcomes 2174,
two issue cohorts, baseline MAE2.21849 spaces, actual horizons21.43-29.04min.
Issued forecasts total3624. This is not neural accuracy or a fixed30min benchmark.
Evidence: experiments/evidence/HEARTBEAT-20261024T174432Z/live_checkpoint.json.

A six-page beginner guide explains the independent camera/history/live paths,
real data locations, learning workflow, model results and unfinished work:
output/pdf/smart_parking_beginner_guide.pdf. All six pages rendered and visually
checked. This teaching handout does not replace the official final report.

Counter9 completed new experiments/trials; next 100-run live milestone100.
No trainers remain active. Existing production checkpoints unchanged. Exact next
actions saved in data/automation_state.json: continue prospective collection,
training/validation-only segmentation diagnosis, labelled parking-video planning,
and remaining report/presentation/application/offline work. Never reuse consumed
final dates to select model changes. University documents remain unavailable.


## Fourth scheduled heartbeat - 24 October2026, 23:44IST (saved after midnight25October)

Completed REGISTRATION-DEV-20261024T181938733562Z: a development-only audit and
geometric registration experiment, not a new neural training run. Final/unknown
rows are filtered before source files are opened. Audited36training+6validation
frames. Canonical slot geometries: pucpr1, ufpr04three, ufpr05one. Under ufpr04,
the change is already visible between training dates7December and29December2012;
validation16January2013 has a third geometry. Originals/labels remain unchanged.
This confirms coordinate geometry drift, but does not establish a single cause
(camera movement versus annotation policy) or justify editing final labels.

Preregistered ORB/Hamming/RANSAC layout transfer uses only same-camera training
references and image matches for selection. At768x448, five of six validation
proposals accepted; explicit baseline fallback on the rejection. Aggregate IoU
0.86560 vs train-only majority0.76697. ufpr04 improves0.28236->0.70227, but ufpr05
regresses1.0->0.84466. Prespecified per-camera/coverage gate FAILED. No final data
opened, no learned segmentation/occupancy accuracy claim, no production change.
Exact protocol/code/input hashes, each attempted reference, predictions, masks,
source geometry audit and two attributed/visually inspected figures are saved
under the run folder. Method card: models/registration_method_card.json.
Next research: investigate image-match selection harming stable geometry and
preregister a selective approach using development data only. Do not present this
post-diagnosis direction as independently confirmed or tune consumed final sets.

All48software checks pass, including a known synthetic translation direction,
blank-feature rejection, mirrored/off-frame/singular transform rejection, and
split filtering. The first attempt failed before tests ran with a BLAS allocation
error. Bounded BLAS1/OMP2/MKL2 pools resolved it. CIM memory query was unavailable;
no zero-memory measurement claimed. Evidence and full console saved under
experiments/evidence/HEARTBEAT-20261024T181432Z/. Existing three production
checkpoint hashes were verified unchanged; no training jobs remain. The app compiler request status is unconfirmed as described below.

Seventh official live snapshot saved with receipt: provider25October02:14:36UTC+8
is24October23:44:36IST. Added1166later outcomes and1278frozen forecasts. Cumulative
3340outcomes, three issue cohorts, MAE2.19162spaces, actual21.43-29.19min horizons;
4902issued forecasts. Persistence only, no neural/camera or exact30min claim.
Counter10completed new recorded runs; separate100-run checkpoint stilldue100.

Created editable report project reports/overleaf/smart_parking_draft/ with actual
methods/results/limitations, evidence index,12-entry source bibliography and two
attributed figures. Sources are bundled locally in output/reports/
smart_parking_report_draft_v001.zip; ZIP integrity checked. Cited keys and figure
paths resolve. Built-in compile_latex_document did not return during a bounded
attempt; waiting cell terminated and source preserved. No compiled PDF or rendered
layout success claimed. No terminal TeX engine found. App editor open was queued;
no external upload/publication occurred. Recheck compiler availability on a later
wake rather than stack overlapping compilation calls. Official template/metadata
and university docs remain absent; this is an AI-assisted technical draft only.

42source records now include exact installed-version OpenCV matching/homography
documentation. Stale bibliography notes claiming PKLot data were not acquired
were corrected; complete paper review and student independent mastery are not
claimed. Final report/presentation, labelled parking footage, vehicle flow and
physical offline/native-save checks remain unfinished. Exact next actions and
pending report compilation are saved in data/automation_state.json.


## Fifth scheduled heartbeat - 25 October2026, 02:09IST

Completed REGION-TRANSFER-20261024T204533261212Z: a frozen ImageNet ResNet18
stem/layers1-3 with a project-trained multiscale region decoder, global context,
explicitXY coordinates and full-resolutionRGB refinement. Same36training and
6development-validation frames as the earlier known-camera study. Train-only
brightness variants0.85/1.0/1.15 cache frozen-encoder features. Seed71, Adam0.002,
batch4, max80epochs/patience12; completed80, selected79. Timed preparation/cache/
training129.57seconds. No backbone/BN updates; decoder alone learns.

Development IoU0.770536/Dice0.870399. Supplemental comparison uses the SAME six
validation frames and nearest-neighbour truth masks: saved known-camera tiny
candidate0.466475, production tiny0.253016, train-only camera geometry0.767625.
Tiny models retain their original bicubic input pipeline; transfer uses its
preregistered bilinear/normalized encoder pipeline. Pretraining/capacity/augmentation
change together: not an isolated component ablation or independent final result.
Per-camera newIoU: pucpr0.851572, ufpr04 0.658121, ufpr05 0.760272.
The gate requires aggregate>=0.80, every camera>=0.65 and no camera more than0.10
below geometry. FAILED on aggregate and stable-camera regression. No production
promotion; coarse merged bands remain visible, not individual slot IDs.

Fresh later dates were reserved BEFORE training: pucpr2012-11-09,
ufpr04 2013-01-20, ufpr05 2013-04-12, two images/date. Duplicate screening hashes
image bytes only; all six final images/annotations remain UNDECODED because the
validation gate failed. Keep this unconsumed reservation closed for an eventual
gated candidate; avoid wasting fresh dates on successive failed development
variants. Before a future final evaluation, add an evaluation-start marker so
an interrupted evaluation cannot be mistaken for an untouched final set.

Best/latest checkpoints, optimizer and Torch RNG state, full80-epoch curves,
protocol/source/split/weight hashes, masks, comparisons, source-code snapshot and
visually checked figures are retained in the run folder. Reconstructed encoder+
decoder replay gives bit-identical six development masks. Existing three production
checkpoint hashes verified unchanged. Counter11 completed new runs; next100-run
live checkpoint100. No trainers or notebook kernels remain active.

Added honest live-forecast lifecycle coverage. It separates scored, pending before/
inside target window, awaiting late delivery and expired missing-target forecasts.
Six-minute delivery grace follows scoring's3min feed age+3min observation lag.
As-of accounting excludes future forecasts/scores and rejects duplicate forecast
IDs. Expired targets never become invented zero errors; pending forecasts stay
outside the resolved denominator. Three meaningful lifecycle regression tests
plus three architecture/reservation tests bring the suite to54passing checks.

Eighth official snapshot saved at20:41:38UTC (25October02:11:38IST) with rawJSON,
receipt/hash and normalized observations. Added1259frozen forecasts and ZERO new
outcomes: the preceding retained collection was18:15UTC, beyond the20-45min target
window. The reason for the collection gap is not established. Cumulative6161
issued,3340scored,1562expired missing targets,1259pending as of that collection.
Matching coverage3340/4902=68.14% among resolved forecasts, NOT accuracy. Baseline
MAE2.1916spaces still describes only the3340matched outcomes, three issue cohorts;
no neural/camera or exact30-minute score. Raw/prospective ledgers are unchanged
except legitimate new observations/forecasts; coverage is a derived summary.

Created and EXECUTED notebooks/03_region_transfer_and_live_coverage.ipynb: six
code cells, zero saved error outputs. It replays the candidate on validation only,
shows real photos/masks, explains transfer learning and calculates saved matching
coverage. Restricted execution stalled and was cancelled; an approved host retry
completed using the project-local kernel. Notebook checksum and execution evidence
saved. The earlier beginnerPDF and first Excel report remain distinct snapshots.

Updated editable report sources with the neural study and missing-target coverage;
new local source bundle output/reports/smart_parking_report_draft_v002.zip. Earlier
v001 retained unchanged. References/figures/ZIP/source bytes checked. Second
compile_latex_document attempt returned no diagnostics within45seconds; compilation/
rendered layout remain UNCONFIRMED. No compiled PDF or manual Overleaf upload/public
publication claimed. Sources/attributed figures preserved. Official university
documents/template and independent student mastery still unverified.

Exact state/next actions: data/automation_state.json. Next wake should collect one
source-compliant snapshot and score the1259previously frozen forecasts if eligible
future readings exist. Research boundary/false-positive merging and camera-specific
regression using training/validation only. No repeated tuning on consumed final
sets or brute-force run inflation. Report/presentation, labelled parking-video/
vehicle-flow, native-save and physical-offline checks remain unfinished.


## Sixth scheduled heartbeat - 25 October2026, 02:39IST

Completed controlled loss contrast REGION-TRANSFER-20261024T211449049328Z.
Same architecture/encoder weights/data/brightness variants/Adam0.002/batch4/seed71
as the prior transfer study; only positive BCE weight changed4.57419->1 while
Dice stayed fixed. Source/input/annotation/architecture hashes matched. Early
stopped at79epochs, best67, timed140.41seconds including cache/preparation.
ValidationIoU0.773284 vs balanced0.770536; pucpr0.845354, ufpr04 0.645331,
ufpr05 0.782195. Gate FAILED including ufpr04below0.65. The balanced candidate
has a better minimum-camera IoU and remains the preferred development reference.
Both separate checkpoints preserved; no production change.

Post-run descriptive pixel diagnostics: false-positive pixels3618->3571 and
false-negative2589->2551 on the same6development frames. A3x3closing-of-truth
background proxy has predicted pixels1058->1003. This proxy is not independent
slot-gap annotation, a selection gate, significance test or final score. The
small aggregate change does not solve coarse merged regions or view regression.
Next investigate spatial resolution/boundary representation rather than many
repeated weight sweeps. Full curves, source snapshot, protocol, matched settings,
pixel diagnostics and a visually checked comparison chart retained.

Training now requires an explicit existing final reservation and NEVER decodes
final images/annotations, even if its development gate passes. Shared reservation
2012-11-09/2013-01-20/2013-04-12 remains unchanged and undecoded. New holdouts.py
provides evaluate_final_once: checks reservation and selected checkpoint hashes,
requires a passed frozen validation gate, locks the claim operation, checks frame
overlap across previous attempts, and exclusive-creates/flushes/fsyncs a durable
claim BEFORE the evaluation callback. Interrupted/failed attempts stay consumed.
Tests cover callback order, failure persistence, overlapping/subset reservations,
failed gates, changed weights/manifests, duplicate/escaping frame paths. Only
synthetic fixtures exercised this guard; no real holdout claim was made.

Analysis results now fingerprint actual RGB pixels INCLUDING dimensions, ordered
inference geometry, detector weights, occupancy-classifier checkpoint and its
training run. Geometry excludes answer labels/descriptive metadata. The engine
owns a deep-copied layout before inference, so caller edits cannot silently change
which geometry matches the recorded identity. Hashes identify inputs/configs;
they do not prove camera/view identity, correct predictions or original-file
licensing. Pixel identity is distinct from raw-file receipt SHA.

Completed PROVENANCE-OFFLINE-20261024T212112979750Z: actual original training
photo/layout, real Faster R-CNN+occupancy classifier, source/raw hashes preserved.
34vehicle predictions;100configured slots produced68occupied/32vacant/0uncertain.
These are SOFTWARE INTEGRATION outputs, not accuracy evidence or the earlier
40-slot example. Exported overlay pixels and JSON match; overlay/record hashes,
input/geometry identities and exact classifier checksum verified. Cached live
rows2423 and historical checkpoint load work with urllib HTTP and standard socket
connection creation blocked. Zero implicit connection/download attempts before
an explicitly planned blocked-online error probe. That probe forces a missing
cache lookup and checks the Load saved snapshot guidance. OS networking unchanged;
no physical disconnect/fresh installation/native dialog success is claimed.
Original/derived source attribution and resource context accompany the real export.

62software checks pass. The first new identity test wrongly assumed polygon
coordinates were emitted in slot records; its fixture was corrected to assert
actual known overlap, and the failure is documented. No model result was hidden.
Existing3production checkpoint hashes verified unchanged. Counter13 completed
new runs (one loss study, one distinct provenance/offline validation this wake),
not frames/epochs/unit cases. Next100-run live checkpoint100. No trainers active.

Ninth official live snapshot21:11:32UTC matched1146previously frozen20:41cohort
forecasts to actual later readings and froze1201new predictions. Cumulative7362
issued,4486scored, persistenceMAE2.012706spaces across4scored issue cohorts.
As of that collection:1562expired missing targets,113remaining20:41forecasts
inside target window and1201before target window. Matching coverage4486/6048=
74.17%among resolved entries, not accuracy. Missing/pending cases have no invented
scores. RawJSON/CSV/receipt/checksum and cohort/horizon evidence retained. This
is aggregate-source persistence, not neural or camera accuracy.

The report/first Excel/beginnerPDF/notebook03 remain explicitly dated snapshots.
A progress addendum records this integration; the unconfirmed compiler was not
polled again without a state change. Report compilation, official university
requirements, final report/presentation, labelled parking-video/flow and physical
screen/export/offline checks remain incomplete. Exact next actions saved in
 data/automation_state.json. Retain the closed shared final set and use a single
frozen guarded evaluation only when justified by development evidence.

## 25October2026 / higher-resolution region trial and annotation inspection

Completed REGION-TRANSFER-20261024T214740232123Z: same36train/6development
images, architecture, seed71, augmentation and fixed positive BCE4.574; input
384x224 rather than192x112. Selected and scored projected logits on the SAME
192x112 truth grid, before sigmoid/threshold0.5. IoU0.7962915 vs0.7705360;
per-camera pucpr0.85596/ufpr040.67641/ufpr050.81643. Native-grid IoU0.79788
is secondary.80epochs, best69,427.51seconds. Acceptance FAILS: aggregate<0.80
and stable-camera drops>0.10 below train-only geometry. No final image/annotation
decoding, no production change, no unseen-camera or individual-slot claim.
All six saved common-grid masks exactly replay from the selected checkpoint;
truths match the reference. Protocol/code/data hashes, full source snapshot,
curves, native/common masks and visually checked comparison plot retained.

Checkpoint writes now save/flush/fsync a same-folder temporary then replace the
target. Fault-injected incomplete saves preserve the previous complete checkpoint;
temporary cleanup and successful load tested.66software checks pass, distinct
from model trials. All3production hashes verified unchanged. Counter14 completed
recorded runs; next100-run checkpoint100; no trainers active.

Tenth official Singapore snapshot21:41UTC added1115later matched outcomes and
1245frozen forecasts.5601scored across5issue cohorts; persistence MAE2.0114265
spaces.8607issued;1675expired missing targets,1245before-window and86in-window
as of collection. Target matching5601/7276=76.98%among resolved forecasts is
not accuracy. No invented missing scores or neural/camera live accuracy.

MetaPKLot SRC-DS-010: pinned UFPR04 vehicle-annotation archive1,426,408bytes
plus original README/CITATION acquired, Git-blob and SHA256 verified. Only tar
member headers inspected:97,715,961byte JSON not extracted/parsed. Zero images
downloaded/decoded; zero training/scoring use. Publisher declares PKLot portion
CC BY4.0 but repository contains mixed licences. Exact-file rights, source-image
identity, rectangle/ROI completeness and development-only filtering remain to
verify. Raw data dates/final reservations unchanged. TRANCOS SRC-DS-011 remains
unacquired: official download failed and DGT terms unresolved. KITTI registration
policy confirmed; no access controls bypassed.44source records now maintained.

Full next actions: data/automation_state.json. Report compilation/presentation,
official university documents, labelled parking-video/flow and physical native
save/offline/fresh-install validation remain unfinished. Earlier reports, Excel,
guide and notebook03 remain dated evidence snapshots.

## 25October2026 / explicit gate counting and notebook04

Implemented explicit finite-gate crossing predictions in Python video API and
local-file CLI, separate from occupancy. Directed line, two-observation side
confirmation, deadband, class-agnostic duplicate suppression, mutual-nearest
association with ambiguity rejection, missing-observation reset and0.75s gap
reset are configured and exported. This is simple box-centre tracking, not
re-identification or calibrated detector/flow accuracy. Desktop gate editor is
not implemented; existing desktop occupancy workflow remains separate.

GATE-VIDEO-20261024T231251838602Z used the original licensed street recording,
unchanged detector, fixed horizontal line(100,700)->(1900,700), and25samples
at0.5s across0-12s (361decoded frames). Predicted0entries/0exits,0gap resets,
14duplicate-box suppressions. CSV/JSON cumulative counts/events agree. No
positive real crossing was validated and no human flow labels exist: accuracy
NOT EVALUABLE.0predictions do not establish0physical crossings. Runtime126.33s,
median inference3.997s, detector load2.126s; offline only. Replay of the earlier
18two-second samples resets on17gaps and abstains; no claim of correct zero flow.
All protocol/settings/source/code hashes and implementation bytes retained.

77software checks pass, including10new counting-rule fixtures and1video/export
integration fixture. These synthetic cases are not model scores or separate
counted experiments. Notebook04executed7code cells without saved errors; synthetic
entry/exit lesson and actual25tracking records replay exactly. Both plots visually
checked. First notebook attempt failed because optional pandas was absent; tables
were replaced with escaped HTML using existing Python/IPython. No package added.

One new real-video validation trial brings counter15; next100-run checkpoint100.
No trainers/validation jobs remain;3production checkpoint hashes unchanged.
Region models/final6 and inspection-only MetaPKLot annotations were not opened
or retuned. New source use is only the already licensed street clip.

Eleventh official Singapore snapshot23:09:58UTC:1286new frozen forecasts,
0new scores because no recorded snapshot falls in the old target windows.
9893issued/5601scored;3006expired missing targets and1286pending at collection.
Resolved matching65.07%, matched-only persistenceMAE2.0114265 unchanged; missing
outcomes have no invented scores. This is aggregate persistence, not neural or
camera accuracy. RawJSON/normalized history/receipt/checksum preserved; accepted
and raw lot-row counts are now recorded separately. No unrecorded22:09/22:39
collection, work or cause of the gap is invented.

New teaching guide: docs/GATE_FLOW_GUIDE.md; executed notebook:
notebooks/04_vehicle_gate_flow.ipynb. Official documents, final report/presentation,
report compilation, native save/physical offline and labelled parking-video
evaluation remain incomplete. Exact continuation: data/automation_state.json.

## 25October2026 / actual forecast target times

FORECAST-TIMING-20261024T234223029035Z audited787train/322development windows
against the sealed c757d7f window implementation and frozen prior trend-candidate
predictions. Every ORIGINAL field, including features/targets/entity/source-row
membership, is exactly unchanged. New metadata retains input grid/source times,
ages, target source time, target age, actual lead from forecast origin and
reading-to-reading interval. All input readings as-of<=20minutes; targets are
genuinely after issue; training/validation source rows disjoint. Future candidate
exports retain these fields. No model retraining or final/test scoring.

Actual development target lead19.3167-29.3667min, median28.7667; source-to-source
interval19.9833-40.05min. Grid lead remains30min. Prior aggregate candidateMAE
20.9015035 and persistence40.220498 unchanged. Prespecified timing strata:
10-15min n0/no score;15-20min n8 candidate16.9459 vs persistence7.1250;
20-25min n1 10.5240 vs13.0000;25-30min n313 21.0358 vs41.1534. Small/empty
groups are disclosed, not model-selection gates or independent test evidence.
Prior candidate still FAILS per-park gate. No promotion or live-model claim.

App now says30-minute GRID targets and explains earlier as-of source readings.
Updated wording has software regression checks; no new desktop visual check.
81software tests pass, including4synthetic timing/age/causality fixtures. Original
3production checkpoint hashes unchanged. Protocol, exact source/code snapshots,
row-level timing JSON/CSV and visually checked reproducible figure retained.
New plain-language explanation: docs/FORECAST_TIMING_GUIDE.md. Old notebooks,
report/Excel/PDF remain dated snapshots, not silently reissued scores.

Twelfth official Singapore snapshot23:40:38UTC added1193actual later matched
outcomes and1150new frozen forecasts. Cumulative11043issued/6794scored across
6scored issue cohorts; persistenceMAE2.6390933spaces.3006expired missing,
93in-window and1150before-window at collection; matching6794/9800=69.33%of
resolved forecasts, not accuracy. No missing-score invention, neural Singapore
accuracy or camera/flow metric. RawJSON/history/receipt/checksum retained.

Counter16completed experiments/validation trials, not16training jobs; this wake
adds one deterministic temporal provenance audit. Next100-run checkpoint100.
No trainers/validation jobs active. Region finals and MetaPKLot annotation JSON
were not opened. Exact next actions in data/automation_state.json; report,
presentation, official compliance, labelled parking-video and native/offline
acceptance work remain unfinished.

## 25October2026 / presentation and practice guide

Created reports/presentations/smart_parking_walkthrough_v002.pptx:
14editable slides with speaker notes,6native tables,1native chart and an embedded
workbook. Real PKLot/output/video images carry credits; the3Dnumeric volume is
explicitly synthetic. Source URLs, model/run caveats and AI assistance appear
in notes/on slides. Companion docs/PRESENTATION_PRACTICE_GUIDE.md explains each
section in everyday language and proposes an8-10minute practice route. No timed
human rehearsal, student mastery or official-template compliance is claimed.

Final PPTX SHA256bc82cf12417612e6fd8e7b072535a34a37a1c48c68b1f349f71115917fdfae68,
2,119,461bytes. Documented finalizer passed package/layout/font/import/native
chart-workbook checks. All14slides rendered and individually reviewed in the
first final version; v002changes only the sixth title and its revised render
was inspected, with the other13rendered images byte-identical. Native Microsoft
PowerPoint opening remains unverified. Original v001retained. Chart values use
six decimals for workbook portability; full original model metrics unchanged.
Failed font-environment/table-policy/precision/temp-replacement attempts and
their resolutions are recorded, with no failed model result concealed.

The bundled @oai/artifact-tool2.8.105and Presentations skill authored this local
artifact. Runtime paths/version and source/image hashes are in the presentation
manifest. No Python dependency, model weights, training code or raw source data
changed. Prior81software checks remain the latest runtime suite; no unnecessary
rerun. Three production hashes verified unchanged. Artifact work does not add
model trials: counter stays16, next100-run milestone100; no jobs active.

Thirteenth official live snapshot00:10:03UTC added1080later matched outcomes and
1267frozen forecasts.12310issued/7874scored across7scored issue cohorts,
persistenceMAE3.2025654spaces.3099expired missing targets,70in-window and1267
before-window as of collection. Matching7874/10973=71.76%of resolved entries,
not accuracy. RawJSON/normalized history/receipt/checksum preserved. No neural
Singapore, camera or flow accuracy claim. A frozen00:10summary accompanies the
deck, so later live updates cannot silently alter its historical snapshot.

Final report compilation, official university documents, stronger region and
forecast validation, labelled parking video, native-save/offline acceptance and
student practice remain unfinished. Resume core development next wake; exact
actions in data/automation_state.json.

## 25October2026 / broader parking-region development

Prepared data/manifests/region_broader_development_v1.json before decoding:
141train images on18unused dates,24validation images on6later unused dates,
three represented cameras. All dates precede the existing per-camera final
boundaries. Previously used/original-test/semantic-test/known-study/reserved-final
dates excluded globally. Up to8train/4validation chronological samples per date.
All165original images/XML validated (camera, dimensions, polygons, nonempty
masks), with no selected exact duplicates or matches to protected image bytes.
Protected JPEGs were hash-only; final XML/images never decoded. Invalid raw date
labels stay rejected. Near-duplicate/perceptual independence remains unverified.

REGION-DATA-20261025T004308948713Z: frozen old high-resolution candidate scores0.758518IoU on the new24
development frames, train-majority geometry0.767625. Per-camera frozen scores
0.80975/0.67802/0.75789. This differs from its old six-frame0.79629 cohort.
Training data contains3ufpr04geometries, other cameras1each; validation weather
is12sunny/12cloudy, with no rain validation. These are known-camera development
checks, not a new final or vehicle-mask benchmark.

REGION-TRANSFER-20261025T004539209450Z: bounded maximum35epochs, seed71, frozen ResNet18 plus unchanged
decoder,384x224input/common192x112selection, balanced coefficient4.574fixed
from prior train-only reference, Adam0.002,batch4,brightness augmentation,
patience12. Encoder caching chunks8frames to bound peak memory. Data/date/sample
count/optimization steps/budget differ from old studies, so no single-factor
causal claim. Best epoch33/35; new common
IoU0.797653 versus frozen0.758518/geometry0.767625 on SAME24frames. Validation
gate passed=False. New per-camera IoUs are0.86169/0.66733/0.81611;ufpr04
slightly regresses from frozen0.67802. The overall<0.80and stable-camera
geometry-retention rules fail. No automatic promotion or final decoding, even if a gate
passes. Selected checkpoint/source bytes, protocol hashes, curves, masks and
exact replay evidence retained. All3production checkpoint hashes unchanged.

88software checks pass, including5metadata-selector and2training-audit/budget
guards. New data audit plus real training are2completed recorded trials; counter
18,next100-run checkpoint100. Frames/epochs/tests are not separate runs. No
trainers remain active after completion. Clock/collection timestamps show a long
observed gap during this invocation; its cause is not established and runtime
does not establish uninterrupted training or a CPU-speed improvement.

Official snapshot00:40UTC added1200later matched outcomes/1230frozen forecasts.
After the observed00:40-to08:25gap, one fresh snapshot resumed history and froze
1184new forecasts with0new scores. Total14724issued/9074scored across8scored
issue cohorts, persistenceMAE3.7976637spaces.4466expired missing targets and
1184pending at08:25UTC. Matching9074/13540=67.02%among resolved entries is
not accuracy. Missing readings/scores and the reason for the gap are not invented.
All15raw snapshots/history/URLs/checksums remain; no neural/camera live accuracy.

Presentation/report/guide retain their earlier dated evidence. Official documents,
final report compilation, labelled parking-video, desktop gate editor, native
export-save, physical/fresh offline and unaided student checks remain unfinished.
Exact next actions in data/automation_state.json.

## 25October2026 / frozen occupancy and detector-fusion reliability

Completed two frozen, preregistered development trials on the same24frames/
6dates/3known cameras.948slots have explicit original0/1labels;396slots in
4PUCPR2012-10-30frames lack the occupied attribute (99each) and stay unscored.
Label coverage948/1344=70.54%; crops/date groups are correlated. No full-camera
accuracy or independent final-test claim; no labels imputed or passed to engine.

OCCUPANCY-BROADER-20261025T084307397022Z: frozen existing ResNet18 classifier
hard0.5accuracy933/948=98.42%, confusion[[395,11],[4,538]]. Existing0.25/0.75
band:942decisions/6uncertain,3false-vacant among395vacant predictions(0.759%).
UFPR05has3/77wrong vacancy calls(3.90%), so the preregistered per-camera
diagnostic gate fails despite the aggregate. Brier0.01362 and probability
ECE0.01175 are descriptive, not individual confidence guarantees. Old360crop
test95.28%remains a separate cohort; this evaluation did not improve weights.

OCCUPANCY-FUSION-20261025T084837737165Z: unchanged Faster R-CNN/ResNet50+
classifier+existing geometry rules, confidence0.5and same uncertainty bands.
Geometry-only inputs exclude answer labels. Full24frame engine inference makes
7classifier-vacant decisions uncertain:2source-labelled occupied and5vacant.
False-vacant3->1,uncertain6->13. Fusion answers935/948(98.63%coverage), with
accuracy924/935=98.82%on answered cases. Vacancy precision387/388=99.74%,
wrong-free fraction1/388=0.258%; UFPR05remaining1/72=1.389%. The limited
diagnostic gate passes; deployment/whole-camera/perfect accuracy does not follow.
Remaining case:ufpr05slot40,2013-03-21,score0.0828. Original source labels remain
the reference, without independent human relabelling. No weights, thresholds or
production rules changed. Classifier score difference across batches<2e-10.

Protocols/code/checkpoint/input hashes, all crop scores, per-frame/date/camera
counts, label-availability audit, remaining error and credited real-input figures
retained.95software tests pass. Initial metrics import found a dictionary syntax
error before evaluation; it was corrected and all subsequent suites passed.
Three production checkpoint hashes unchanged; shared final6images/XML unopened.
Two real validation trials bring counter20; next100-run checkpoint100. No jobs
active. Mask/forecast acceptance failures remain separate from this diagnostic.

Official snapshot08:40UTC retained rawJSON/history/receipt/checksum and froze1139
new forecasts;0new scores because08:25targets had not reached20minutes yet.
15863issued/9074scored,4466expired and2323pending at collection. Matched-only
persistenceMAE3.7976637unchanged;67.02%resolved matching is not accuracy. No
neural Singapore or camera/flow live score invented. All16snapshots remain.

Publisher PKLot page rechecked25October: it describes XML occupancy annotations,
but no missing-attribute default was established from that page. Official readme
fetch timed out. Missing attributes remain unknown under the frozen protocol.
New easy explanation:docs/OCCUPANCY_RELIABILITY.md. Earlier reports/slide deck
remain dated snapshots. Remaining product/final-report/offline/student tasks and
exact next actions stay in data/automation_state.json.

## 25 October 2026 / video-bound desktop entrance and exit setup

The Python desktop app now has an Entrance / exit tab: local-video first-frame
preview, two-point counting line, explicit entering direction, video-bound setup
save/load, bounded half-second sampling, cancellation and automatic local results.
Exact video and first-frame hashes prevent silently reusing a setup for another
view. Advanced tracker configurations are rejected by the simple editor rather
than silently changing their settings; the existing CLI retains those options.

103 software checks pass, including eight new setup/output tests. A hidden native
Tk check created the actual widgets, drew the line/reference arrow, verified busy
controls, saved/reloaded a setup through real app methods, and displayed a test
frame event. File dialogs were mocked; visual layout, physical dialog interaction
and a human rehearsal remain unverified. Fixture display counts are not model data.

DESKTOP-FLOW-20261025T091303623986Z used the already-seen licensed street video
and unchanged Faster R-CNN/ResNet50 weights. Three real samples at 0/0.5/1 seconds
passed source, model and CSV/JSON consistency gates; zero crossings were predicted,
six duplicate boxes suppressed. This configured street line is not a known parking
entrance. No independently labelled positive crossing or flow accuracy is claimed.
Source attribution, sealed protocol, exact implementation and all predictions are
saved. One completed integration trial advances the experiment counter to 21;
tests/frames/cancellation fixtures do not add experiments. No jobs remain active.

Official Singapore acquisition at 09:07:58 UTC saved the 17th immutable snapshot,
receipt/checksum and normalized history. It scored 2,198 earlier frozen forecasts
against later matching readings: 11,272 matched outcomes total, persistence MAE
4.045245 spaces. There are 4,466 expired missing targets and 1,360 pending targets;
71.62% resolved target matching is not accuracy. Another 1,235 forecasts were frozen
for later readings. No neural/camera/flow live accuracy is implied. The separate
100-run checkpoint remains at run 100.

Three production checkpoints and the shared final manifest are unchanged; final
images/labels remain undecoded. Region and forecast acceptance failures persist.
See docs/ENTRANCE_EXIT_GUIDE.md for student steps and exact output/data locations.
The next actions, remaining UI/offline/report/labelled-data limitations and model
evidence are saved in data/automation_state.json.

## 25 October 2026 / training-only robust forecast selection

One predeclared group-relative LSTM procedure completed: three expanding training-only
folds choose a common epoch count, then a seed84 refit uses all 787 training windows.
The objective is half mean/half worst-park MAE divided by fitting-prefix persistence
MAE (floor one space); unknown parks use a fitting-only median scale. No new features.
Selection reached the fixed 80-epoch cap, not proven convergence. Four model fits are
one recorded experiment, not independent seed confirmation. Runtime 5.281 seconds.

Frozen checkpoint precedes development-target loading. On 322 reused development
windows/4 dates, candidate MAE30.197154 vs persistence40.220497 spaces, a 24.92098%
reduction. The existing >=5% overall/<=10% per-park regression gate passes: 26 parks
have >=10 windows; another has3. All27 show lower observed MAE. Earlier aggregate
winner20.9015 remains lower overall but failed its group gate; no causal single-factor
claim because objective and selection procedure both changed. No final/live neural
accuracy or production promotion. Actual target readings lead19.32–29.37 minutes.

New reservation seals 3844 source-row identifiers on Dec12–19/2016, 29 car parks,
absent from the only archived original test-prediction artifact (Dec8–11). This is
existing Birmingham data, not a newly blinded external source. No numeric future
outcomes were parsed for reservation/scoring. Whole source-manifest hash, original
prediction hash and selected checkpoint/result hash are pinned. A full durable
overlap-aware date claim is still required before final scoring. Legacy test loading
now refuses before opening numeric data while the reservation exists. Training and
development windows are byte-for-value equal to the sealed original implementation;
checkpoint replay reproduces every322 saved predictions exactly. Source snapshots
retain the pre-guard implementation, with the guard delta documented separately.

Coverage is limited: 10/51 source training dates and4/10 development dates yielded
these fixed-grid windows. Future final admissibility is not assumed. Diagnose any
alternate causal time/phase protocol using training/development alone, freeze it,
then evaluate reserved data once under the future guard. Preserve the current model.

110 software tests pass;3 production hashes and image-final reservation unchanged.
Counter22; no jobs active; next separate100-run live checkpoint100. New easy guide:
docs/FORECAST_ROBUSTNESS_GUIDE.md. Lesson05 executed with four code cells and no saved errors.

Official09:38 snapshot18 saved immutable raw JSON, receipt, checksum and normalized
history.1130 earlier frozen persistence forecasts newly matched later targets:
12402 scored total, MAE4.108853 spaces;4591 expired missing targets,1262 pending,
72.98% resolved target matching.1157 new forecasts frozen. No neural/camera/live-flow
accuracy implied. All earlier snapshots/failures/checkpoints remain. Remaining core
model, final-data, UI/offline/report/university/student limitations are in state.

## 25 October 2026 / clock coverage and one-time later-date forecast evaluation

Completed a training-count-only clock-offset study and one protected later-date
forecast evaluation. Phase10 (minutes10/40) gives14333 training windows vs787 at
phase0; no prediction errors used for phase selection. The frozen original candidate,
without retraining, passes broader development:2539windows/all10dates/28eligible
parks, MAE35.036354 vs43.790469 persistence,19.99%reduction, no park gate failure.
Six-phase pure-window refactor replay preserves every training/development field;
extra phase development counts were inspected only after phase10 was frozen.

Durable whole-source/date guard binds reservation, model, protocol and source SHA;
exclusive claim is flushed before any numeric final row is parsed. Synthetic tests
cover overlap across manifests, failed/interrupted callback consumption, bad gates,
changed weights/protocol/source and post-callback source mutation. Real final ran
once on the exact3844reserved source IDs; Dec8–11 old consumed windows excluded.
Claim and outcome retained in data/forecast_holdout_claims. Dec12–19 is CONSUMED;
no tuning or changed-method scoring may reuse these dates.

FORECAST-FINAL-20261025T101729300425Z:1853windows/all8dates/29eligibleparks;
candidate MAE31.723523 vs persistence39.071775 and original LSTM87.719680 on the
SAME rows.18.8071%error reduction vs persistence; frozen final gate passes, no
eligible park>10%regression. Existing-source temporal holdout, not external/blinded
collection or universal accuracy. Actual target readings10.02–29.12min after issue,
mostly15–25min; not exact30min. Correlated overlapping windows; all lead-bin/source
times and row-level evidence retained. Metrics/CSV-JSON rows replay from saved
predictions; no model inference or final evaluation repeated during output checks.

App offers an optional Later-date check report next to Original experiment. It
reads hash-checked archived predictions, clears stale charts on switch and explains
the historical source and actual lead times. Original default and3production
checkpoints remain unchanged. Hidden native Tk/Matplotlib rendering and round-trip
report switch passed; no screenshot/visible/native-user acceptance claimed.

123software checks pass. Two completed trials advance counter24; no jobs active;
next separate100-run live checkpoint100. Shared image final6 remains closed and
segmentation/occupancy/flow/offline/report/student/university limitations persist.
New easy result/data guide:docs/FORECAST_FINAL_EVALUATION.md. Earlier notebooks,
slides and reported scores remain their dated cohorts; do not substitute new MAE.

Official10:09 snapshot19 saved immutable rawJSON, normalized CSV, URL/receipt/SHA.
1099 earlier frozen persistence targets newly matched;13501scored, MAE4.190578;
4696expired missing targets,1288pending,74.19%resolved matching.1230new forecasts
frozen. This separate Singapore result does not score the neural/camera models.

## 25 October 2026 / conditional known-camera region stability

Three bounded regional-mask trials completed without new neural gradient training.
First unanimity-pixel hybrid:developmentIoU0.840285 vs frozenCNN0.797653 and
train-majority0.767625, but UFPR04drops0.667330->0.448052, so gate FAILS. It
locks old background on a changing view. Failure, exact old code/bundle/masks and
replay retained. Revised rule uses stored geometry only if ALL training masks for
a camera are identical; ANY variation routes the WHOLE view to frozenCNN. This
rule uses training geometry, not camera names or final labels. Reused-development
score0.910914, UFPR04unchanged0.667330; quality and added-value gates pass.

One guarded final test decoded the sealed6later-date images only after a flushed
exclusive claim. RouterIoU0.910393/Dice0.953095 vs frozenCNN0.802893 and
train-majority0.767625. Quality/added-value gates PASS. UFPR04isCNN-onlyIoU0.662114;
PUCPR/UFPR05areGEOMETRY-ONLYIoU1.0on2images each. Those perfect stored-geometry
scores are NOT neural image inference evidence. Six known-camera samples/3dates,
no automatic slot IDs/new-camera discovery or reliable moved-camera handling.
Production models/preview unchanged. Original pure-image quality limitations remain.

Image holdout guard now claims camera/date groups as well as exact frames. It
requires group metadata; same-day different-frame reservations are blocked.130tests
pass (5new composition tests plus2date-guard checks). All6finalimages and3camera/date
groups are CONSUMED; no changed-method re-evaluation/tuning, including other frames
on the same dates. Forecast final groups also remain consumed. Original reservation
bytes unchanged; durable claims/outcomes tracked.3production hashes unchanged.

Saved final mask metric arithmetic and first failed-policy masks replay exactly;
no raw final image/XML reopened or model inference repeated for those checks.
Credited comparison figure built only from saved final PNGs, visually reviewed.
New explanation/data locations:docs/REGION_STABILITY_GUIDE.md. Three real trials
advance counter27; no active jobs; next separate100-run live checkpoint100. Future
model changes need genuinely fresh final groups. Occupancy false-vacancy, labelled
flow, camera/view provenance, UI/offline, report/university/student limits persist.

Official10:38 snapshot20 saved rawJSON/normalizedCSV/receipt/URL/SHA.1137prior
frozen persistence forecasts newly matched later observations:14638scored total,
MAE4.249898spaces;4754expired/1181pending;75.48%resolved matching, not accuracy.
1088new forecasts frozen. No camera/region/neural live score inferred from Singapore.

## 25 October 2026 / licensed labelled sequences and frame-index tracking

Acquired a new real annotated source, DAVIS2017 SRC-DS-012:310original members,
155frame/mask pairs,20,197,285member bytes from the official832,766,765byte archive
using bounded verified ranges (~21.5MB transferred in acquisition, not full ZIP).
ETag, local member/range SHA256 and ZIP CRC retained; full archive SHA unknown.
Official README/SOURCES and website/license snapshots reviewed: dataset CC BY-NC4.0;
car-turn/car-roundabout absent from external footage exceptions. Local noncommercial
academic use with author attribution; code BSD licence is not the dataset licence.

Roles fixed before pixel inspection:car-turn80frames development (first5setup),
car-roundabout75frames reserved final. Headers/pairing/hashes/consecutive names
verified; reserved pixel/annotation values remain unopened. Source fps not established.
Added explicit frame-index tracker mode and frame_index events; no invented physical
seconds. Timestamp-video/Desktop paths reject frame configs. Default-seconds behavior
replays exactly on25archived real street detection frames, without model rerun.
139software checks pass, including6new ZIP/time-unit and3reference-rule tests.

One frozen Faster R-CNN/ResNet50 development trial evaluated the publisher-labelled
foreground car only. Same fixed middle-image gate; known mask ID1 reference crosses
without predicted association. No parameter fitting. Actual metrics:{"scored_visible_car_frames": 75, "annotated_car_detected_frames": 75, "annotated_car_box_recall": 1.0, "matched_tracking_frames": 74, "dominant_track_fraction": 0.7066666666666667, "matched_consecutive_id_switches": 0, "reference_events": 0, "recovered_events": 0, "annotated_event_recall": null, "unmatched_predicted_events": 0, "precision_evaluable": false, "matches": []}.
Diagnostic gate=True. These are correlated frames of ONEcar,
not independent vehicles or exhaustive traffic labels. Extra predicted events cannot
establish precision/mAP/overall flow accuracy. Image-plane line is not a parking
entrance; camera motion and unknown fps preclude physical-time/speed claims. No
project training on DAVIS; upstream pretrained-data overlap not audited.

Initial80frame inference finished but reporting failed on a duplicate metrics keyword;
no valid scores were saved or counted. Failure/protocol/progress retained. Writer
fixed and append-only per-frame journal added before a frozen-parameter development
rerun. No final data or threshold/model tuning used to correct the software error.
Two completed trials advance counter29; no active jobs. Final sequence still needs
a durable whole-sequence claim and frozen protocol before decoding. All old image/
forecast final groups remain consumed.3production hashes unchanged. Source receipts,
split/weights/code/config hashes and original data preserved. New beginner guide:
docs/LABELLED_SEQUENCE_GUIDE.md. Other model/runtime/offline/report/student limits remain.

Official11:09snapshot21:1046earlier frozen persistence forecasts newly matched,
15684scored total,MAE4.330528spaces;4847expired/1291pending,76.39%resolved matching.
1249new forecasts frozen. This separate Singapore study is not neural/camera accuracy.

## 25 October 2026 / source-ID repair and actual continuation checkpoint

Continuation integrity check:142software tests pass. Canonical source catalog now
has45unique IDs. A collision was found: early DAVIS records used SRC-DS-011,
already assigned to TRANCOS. DAVIS is now SRC-DS-012. Original receipts, raw
acquisition manifest, frozen protocols/results/source snapshots and v1 role records
remain intact.321append-only correction receipts preserve original URLs/times/SHA;
v2manifests correct metadata only, identical155frame roles/310member hashes. The
crosswalk is data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json. Catalog
guards now reject a reused identity before acquisition. Windows UTF8 read repairs
were also required; the repair is documented, no model metrics changed.

Successful development result:one car detected75/75scored frames; tracked74/75,
dominant identity53/75;0reference crossings. Event recall remains NOT EVALUABLE;
no positive counting-accuracy claim or exhaustive traffic precision. First reporting
failure is preserved and excluded from29completed trials. New final sequence still
unopened; no active jobs. See docs/LABELLED_SEQUENCE_GUIDE.md for real data paths.

Actual fresh official collection13:48UTC followed a159.82minute observed gap;
no intervening collections/runs are invented. Snapshot22adds1312future forecasts
but0scores:1291old pending forecasts expired without targets. Totals15684scored,
MAE4.330528,6138expired/1312pending,71.87%resolved matching, not accuracy.
Counter29; separate100-run checkpoint100. Continued work is the predeclared
setup-only gate replay on saved development detections, then a tested whole-sequence
claim/protocol before any reserved pixel decoding; no extra detector run needed.

## 25 October 2026 / positive image-line crossing and failed identity qualification

One predeclared setup-only replay used cached real DAVIS car-turn detections,
not another neural run. Object1 labelled boxes from frames0..4 set vertical x694
before scoring frames5..79. The reference crossing at frame22 was recovered at
frame22 (1/1). Detection75/75, matched tracking74/75, dominant identity53/75
(70.7%). The prespecified >=80%dominant-identity gate FAILS; qualification false.
No line search, alternative retry, training, reserved pixels or weights changes.
This is reused development, partial foreground labels and image-plane motion,
not exhaustive traffic precision, physical timing or parking-facility entry accuracy.

Whole-sequence guard implemented/tested: canonical collection/sequence identity,
full parent-manifest membership, path/content overlap, sealed method/protocol/
checkpoint hashes, exclusive fsynced claim before callback; callback failure
consumes the sequence. Synthetic tests include interruption, source-ID/path alias,
changed sequence with same assets, subset/path escape, failed/zero-reference gate,
changed weights/protocol and stale lock. Actual75frame final metadata preflight
passes, but the failed development selection is rejected BEFORE callback/claim.
No actual final claim created; final75pixels/mask values remain unopened.

150software tests pass. Notebook06executes4code cells with zero errors and shows
the real frame22overlay, saved metrics, source/data/CSV locations and limitations.
This is an educational cached-result display, not another counted experiment or
student mastery assessment. Counter30; no active jobs; next100-run checkpoint100.
Next work: diagnose cached identity break, freeze one conservative tracking
improvement hypothesis with no crossing inference across missing observations.

Actual14:16UTC official Singapore snapshot23newly matches1213earlier frozen
persistence forecasts;16897total matched, MAE4.386873spaces.6138expired missing
targets,1276pending (1177new+99earlier). Resolved matching73.35%, not accuracy.
Source raw JSON/normalized CSV/URL/time/checksum preserved. No neural/camera
accuracy or invented scores for missing targets.

Cached identity-break diagnostic:frame26still has foreground-overlapping car/truck boxes (IoU0.959/0.941), but confidence~0.637below0.7cutoff, so tracker drops the identity and restarts27. Evidence:experiments/evidence/HEARTBEAT-20261025T141530Z/identity_break_diagnostic.json. Not a new run/fix. Next:predeclare weak-confidence continuation only for unambiguous existing identities, preserve default policy and no guessed crossing through a missing observation; qualify on fixed development gates before any final. Notebook startup/missing-pandas failure retained; unnecessary dependency removed, final lesson executed with existing packages and visible attribution; chart reviewed.

## 25 October 2026 / identity-only continuation and whole-sequence final

A separate experimental identity-only continuation preserves actual low detector
scores and only reuses unambiguous existing identities; weak boxes cannot create
tracks and erase crossing memory before/after update. Real missing observations
or long gaps still drop identity. Original GateCounter source/config/output policy
is unchanged. On reused car-turn development, fixed x694line:tracking coverage
74/75->75/75, dominant identity53/75->75/75;1/1reference crossing recovered,
no extra unmatched event. Fixed development gates pass. No threshold/line sweep.

First development scorer attempt failed because candidate metadata was passed to
reference geometry. Failure/protocol/source snapshots preserved, not counted.
Separated reference config and added integration fixture, then reran unchanged
candidate on development only.159software tests pass, including500randomized
synthetic weak-only rule cases; synthetic checks are not camera accuracy.

Frozen final FLOW-SEQUENCE-FINAL-20261025T145525078714Z consumed the entire75frame car-roundabout
sequence with an exclusive fsynced source/sequence claim BEFORE pixel decoding.
First5labelled setup frames use the unchanged gate rule;70remaining frames scored.
No project training or final tuning. Actual final metrics:
{"reference_events": 0, "recovered_events": 0, "annotated_event_recall": null, "unmatched_predicted_events": 1, "precision_evaluable": false, "matches": [], "scored_visible_car_frames": 70, "annotated_car_box_recall": 1.0, "matched_track_coverage": 1.0, "dominant_track_fraction": 1.0}
Final gate passed:False. Baseline metrics are in the same
report. This is one selected foreground car, partial traffic labels, image-plane
crossings and unknown fps, not exhaustive traffic precision, occupancy/parking
entrance accuracy or broad deployment evidence. Foreground semantic vehicle
review performed after claim/freeze, no parameter adjustment. Entire sequence is
now consumed, including all setup frames; no changed-method reuse. Original role
manifest unchanged. No production promotion/weights change.32completed trials,
no active jobs; separate100-run live checkpoint100. Next:scoped runtime acceptance,
offline/native UI and student/report materials; fresh groups for model changes.

Actual14:47UTC authorized Singapore snapshot24matched1124later persistence
outcomes:18021total,MAE4.424949spaces;6237expired missing targets,1398pending.
Resolved matching74.29%, not accuracy. Immutable JSON/URL/time/SHA and normalized
CSV retained. No neural/camera accuracy or zero-error substitute for missing targets.

Student lesson07executed:4Python code cells, zero saved errors, actual cached baseline/candidate comparison and final limitations; identity timeline/DAVIS licence footer visually reviewed. Notebook06and all dated evidence snapshots preserved. Final70/70identity also achieved by the baseline, so no final identity gain claimed; zero reference crossings means unavailable recovery, overall final acceptance FAILS. One unmatched prediction is unassessable under partial labels, not a proven false positive. Whole sequence remains consumed; next model comparisons require fresh groups.

## 25 October 2026 / dated Excel report and Python progress exports

Added Python archived-progress loading with checksum/path validation, readable
dated display and JSON/four-CSV export. Sources & guide has View saved progress
and Save progress tables; source-view round-trip, busy controls and actual export
files/checksums pass hidden native Tk method checks with mocked folder chooser.
Zero-reference crossing numerator0/denominator0/valueNone stays unavailable;
CSV guards avoid spreadsheet-formula execution from source strings. No model
inference, raw-final decoding, training, candidate promotion or default tracker change.

162software tests pass. New four-tab Excel report contains11capabilities,12scoped
metrics,45source entries and43historical experiment rows (32scheduled completed,
9earlier,2interrupted). All source creators/URLs/licences/local paths and failed
experiments retained. Dated snapshots and exact input copies/checksums are in
reports/progress; original first-training workbook preserved. The new XLSX is
outputs/01a16cf3-1f03-7631-8fac-d3d382c5b25c/smart_parking_progress_20261025.xlsx.
Guide:docs/EXCEL_PROGRESS_GUIDE.md. Formula metrics match saved reports; positive
denominator zero-result and zero-reference unavailable boundaries checked. All
four sheets rendered/reviewed; native tables/freeze panes/cached unavailable
text/no-error cells verified in exported package. Native Excel use not checked.

Initial workbook build rejected non-date literals in7older registry rows. Builder
now preserves unknown date text and converts only genuine timestamps; no registry
dates invented. Authoring recovery recorded, not counted as a model experiment.
Main/Jupyter remain Python; bundled artifact-tool JS used only for Excel authoring.
These report/UI checks are not a new scientific trial:counter remains32, next
100-run checkpoint100, no active jobs. All final holdouts remain consumed.

Actual15:17UTC Singapore snapshot25matches1235earlier frozen persistence forecasts:
19256matched total,MAE4.406730spaces;6290expired/1442pending;75.38%resolved
matching, not accuracy. Raw JSON/normalized observations/URL/time/SHA saved.
No neural/camera accuracy. Remaining work:visible/native/offline acceptance,
fresh positive-crossing evidence, report compilation/presentation and student
explanations. No universal accuracy or full project completion claimed.

## 25 October 2026 / relocated local demo and shutdown cleanup

Two recorded software integration trials advanced counter32->34. First local
demo copy passed core gates but revealed a nonfatal orphaned Tk poll callback at
shutdown. Original package/protocol/source snapshots/stderr retained. The app now
cancels that callback once on destroy and requests video stop. Two regression
fixtures plus a second stricter relocated trial pass; latest stderr is empty.
No detector/classifier/forecast weights or base gate-counter policy changed.

Latest bundle:outputs/demo_packages/DEMO-BUNDLE-20261025T160503964992Z,
184files/544600770bytes, copied originals hash-verified before/after. Runtime reused
from installed Python3.12environment. Product modules/assets resolve inside copied
folder; reads back into original workspace denied. Python networking blocked:
zero normal attempts, explicit block probe passed. Actual hidden native app paths
verified:both detectors/paired exports on one hash-bound training image with100
geometry slots; separate semantic preview/export; two archived forecast charts;
cached live with STALElabel;2D/3D numeric lesson; progress tables; two local samples
of already-seen licensed street video. No raw final image/date/sequence decoded,
labels scored, model training or new accuracy claim. Both runs are software trials,
not per-frame/epoch counts.167software tests pass. No active jobs; checkpoint100.

Default Load real sample now uses explicitly recorded training data, not a consumed
final image. The prepared training manifest has no ufpr05rows, so the fixed policy
falls back to first training row:pucpr2012-09-11. Original image and geometry hashes
are in configs/demo_sample.json; no occupancy answers enter layout. No training
split/evaluation result changed. Launcher accepts explicit SMART_PARKING_PYTHON
or local/parent .venv; it does not install packages. Guide:docs/DEMO_PACKAGE_GUIDE.md;
pointer:reports/demo_package_latest.json; exact assets/validation retained.

This is a relocated local-demo check, not fresh offline installation, physical
disconnection/new-machine/cross-platform or visible/manual-dialog acceptance.
Windows networking/unrelated apps untouched. Full training datasets/Python runtime
not bundled; project-wide source catalog describes more than selected bundle.
Copies remain local, no publishing/purchases. Main/Jupyter remain Python. Dated
Excel15:32report intentionally remains32trials/162tests; newer ledger34/167. PKLot
licence action note corrected in original docs; bundled provenance is a dated copy.

Actual15:48UTC official Singapore snapshot26matches1221later persistence outcomes:
20477matched,MAE4.343507spaces;6400expired/1394pending,76.19%resolved matching,
not accuracy. Raw JSON/normalized CSV/URL/time/SHA retained. No neural/camera
accuracy. Next:visible/fresh-offline acceptance, meaningful fresh labelled crossing
evidence, report compilation/presentation and student explanation work. Missing
university sources block official compliance only; no whole-project completion.

## 25 October 2026 / current technical report and successful LaTeX compilation

A current 12-page technical report v003 is saved at
output/pdf/smart_parking_technical_report_v003.pdf. It explains the Python/Jupyter
product, methods, real-data inventory, original and later measured results,
failed studies, qualified claims, convolution lessons, reproducibility and
remaining acceptance work. Source IDs, licensing limits and local data/CSV/raw
JSON paths are explicit. All45 source records and acquisition receipts are
snapshotted;15 exact inputs pinned. Earlier drafts and original evidence remain.

The old LaTeX draft and the new editable main.tex both return successful built-in
compiler diagnostics. The delivered standalone PDF is typeset with ReportLab
from the shared report_content.json; it is not a compiler-exported TeX PDF.
All12 rendered PDF pages were visually reviewed; extracted metrics, page bounds,
source/cache hashes and final-failure wording pass artifact checks. Bundled Python
has no Matplotlib, so figures are generated with existing project Python and
ReportLab runs in the bundled authoring runtime; no packages installed. An initial
literal-text assertion missed a PDF line wrap; whitespace-normalized check passes.

No new model inference/training or raw final evaluation occurred. Only a previously
seen development car-turn frame22 was opened for a labelled illustration; charts
use archived metrics/cached development observations. Counter remains34 unique
completed trials,167 previously passed software tests; report authoring checks
are not new experiment runs. No product runtime changed. No active jobs; next
separate100-run checkpoint100. Excel15:32snapshot remains intentionally32/162.

Actual16:23UTC authorized Singapore snapshot27 matches1201 earlier frozen
persistence targets:21678 total,MAE4.298828spaces,6511expired/1374pending,
76.90%resolved matching. Raw JSON,normalized observations,URL,time,SHA and schema/
bounds/duplicate checks retained. No camera/neural live accuracy. Source targets
must arrive later; no per-simulation polling. Full project,physical-offline/native
manual acceptance,student mastery,official academic template and fresh labelled
crossing evidence remain unfinished. See docs/TECHNICAL_REPORT_GUIDE.md.

## 25 October 2026 / live input quality and traffic-source admission

One paired LIVE-QUALITY trial passes:28 real official snapshots/67,844 repeated
snapshot lot records reproduce the prior parser exactly. Synthetic duplicate
fixture previously yielded2 rows, now1; conflicting valid duplicate values fail.
Empty identities and float/boolean counts fail validation; equivalent Singapore
and UTC observation times identify the same history entry. All176 software tests
pass, including two raw-response retention/history scenarios. Rejected public
response bytes get separate immutable files/receipts, never replace usable cache
or append normalized history. Valid raw snapshots now use exclusive creation.
These are software checks, not detector or forecasting accuracy. Counter35;
no training/new weights/final evaluation. Earlier demo is a dated copy and lacks
this live.py update; do not call that copy the latest source.

Fresh traffic-source research has51 source records. Figshare partial drive-through
release declares CC BY4.0: public metadata,one3852-row headerless CSV and first2
camera3images acquired (4files/1,857,871bytes), publisher MD5 and local SHA checked.
Inspection exposes unresolved coordinate basis/column semantics/label independence;
raw coordinates exceed decoded2688x1520 dimensions. A0.7overlay was diagnostic
only, not an established conversion or score. Related article describes restricted
full study data; reconcile the public partial-release scope before further asset
use. Admission fails; originals/receipts retained, no model scoring/training,
other-camera acquisition,final claim or redistribution. Manual correspondence,
physical fps and exhaustive labels unverified. See docs/TRAFFIC_SOURCE_ADMISSION.md.
Four other dataset candidates remain unacquired: Mendeley multi-instance/HVSD
metadata routes404; HVSD processed outputs are not verified independent truth;
UA-DETRAC primary licence unresolved; Brno publisher requires contact (none sent).

Actual16:52UTC official snapshot28 matches1172 later persistence outcomes:
22,850total,MAE4.186346spaces,6593expired/1279pending,77.61%resolved target matching.
Fresh normalized rows/raw JSON/time/URL/SHA retained. No neural/camera live score.
Reportv003 and Excel/slides retain their dated evidence; do not mutate old results.
No active jobs; separate100-run milestone100. Next source-compliant collection
after17:22UTC,then fresh label acquisition/admission or remaining native/offline
acceptance. All original checkpoints,failed experiments and consumed final groups
preserved. Student mastery,official submission and overall completion unverified.

## 25 October 2026 / SVD lesson completed after usage-limit interruption

SVD lesson now works in the Python app Convolution lab and executed notebook08.
Use1to160patterns on a resized256x160 grayscale view. One existing hash-bound
training-only PKLot image, no final labels/pixels or detector preprocessing.
Rank16:6,672factor numbers vs40,960grayscale numbers,53,376vs327,680float64bytes
(16.29%),MSE0.00465324,retained numerical energy98.6283%. This is not JPEG file
compression,model accuracy or an image-quality guarantee. Full rank maximum error
2.0539e-14 and factor storage162.89%; more patterns can require more memory.
No trained weights changed. NumPy supplies SVD; implementation provides bounded
input/rank checks, complete storage accounting, plots and app/notebook integration.

One recorded numerical/native trial advances35->36, not one run per rank/cell.
Five new numerical unit checks; all181software tests pass. Hidden native app tests
check ranks16/48,invalid/busy guards,2D/3D/SVD switching and no accumulating figures.
Eight notebooks now executed; notebook08has4code cells,zero saved errors and an
inline figure. First notebook attempt cancelled without diagnostics after about
3minutes; project-kernel retry with explicit inline display passed. Original grid
had overlapping row labels and is retained; separate reviewed layout fixes that
without a model rerun. Native visible/manual acceptance and student understanding
remain unverified. Guide:docs/IMAGE_COMPRESSION_LESSON.md.

Earlier17:15wake stopped when automatic approval review hit the account usage
limit; the attempted follow-up patch/read was not executed. WIP files persisted;
no completed run was counted then. Work resumed at19:15after access returned,
without bypasses,purchases or credits. Skipped wakeups are not completed trials.
Source14official125044-byte HTML acquired; public client-script403stopped file
inspection,no bypass/login/dataset images/annotations. New official NumPy2.5SVD
reference SRC-DOC-018 brings catalog52. Traffic evidence remains unqualified.

Actual19:16UTC Singapore snapshot29 follows a16:52->19:16collection gap. No new
admissible prior-target matches:22850matched/MAE4.186346unchanged;7872expired,
1147pending,74.38%resolved matching. Missing targets are unscored,not zero error.
New1147forecasts await later actual observations. Raw JSON,normalized CSV,URL,time,
SHA and bounds/duplicates retained. No neural/camera live accuracy.

No active jobs; counter36,next100-run checkpoint100. Original weights,failed
experiments and consumed final groups remain preserved. Old demo/report/Excel/
slides retain their dated scope; demo lacks latest live/SVD source. Next:meaningful
demo acceptance,legitimate fresh labelled counting evidence,and student practice.
Whole project,official university compliance and universal accuracy unclaimed.

## 25 October 2026 / refreshed relocated demo with live guards and Jupyter lesson

A new copied demo passes one recorded integration trial:189files/545,111,075bytes
at outputs/demo_packages/DEMO-BUNDLE-20261025T194803443600Z. All copied hashes
verified before/after; original Python source/data fallback blocked. Original
weights/raw assets and all earlier demo folders remain unchanged. Reused installed
Python runtime and copied Windows decoder; no automatic package installation.

Actual hidden-native checks:both detectors and paired exports on the existing
training-only100-slot image, separate semantic preview/export, two archived
forecast charts,cached official live view,2D/3D arithmetic,progress export and
two already-seen licensed street-video samples. SVD app ranks16/48and selected
notebook08fourordinary Python cells pass inside the copy with inline magic/show
suppressed. Full Jupyter execution remains verified in main project only; copied
kernel/manual dialogs/visible layout/fresh install/physical disconnection/new
machine/cross-platform acceptance remain unverified. Zero normal Python network
attempts; explicit block probe passes; shutdown stderr empty. OS networking and
unrelated apps untouched. Only notebook08is included,not the full8notebook/data set.

Live JSON arrays/null now fail validation and preserve rejected bytes separately,
without replacing the accepted cache/history. Extended synthetic rejection cases
pass. All181software tests pass; all30real snapshots/72,690repeated lot records
exactly match prior valid parser output. Synthetic fixtures are software checks,
not live observations or camera/forecast accuracy. Counter36->37for one completed
integration trial,not perframe/rank/notebook cell. No scientific model evaluation.

Actual19:48UTC official snapshot30 matches1041previously frozen persistence
targets:23,891matched total,MAE4.050312spaces,7872expired/1296pending,
75.22%resolved target matching. Matching coverage is not accuracy. Raw JSON,
normalized CSV,provider/retrieval timestamps,URL,SHA,bounds/duplicate evidence
retained. No neural/camera live score; the earlier gap remains honestly unscored.

Current pointers updated; source catalog52. Earlier report/Excel/slides and failed
studies preserved with their dated scope. No active jobs; next100-run milestone100.
Next:legitimate fresh labelled counting evidence,reproducible installation/native
manual/physical-offline acceptance,and student practice. Whole project completion,
universal accuracy,student mastery and official academic compliance unclaimed.

## 25 October 2026 / clear startup preflight and failed clean offline readiness gate

Main launcher now discovers required modules before importing the heavy app.
Missing components produce clear setup guidance and exit2; --check-environment
returns discovery-only JSON without opening GUI,loading models or network use.
Import/ABI failures get a plain message plus local diagnostic log. Discovery is
not proof of binary/model compatibility. Existing runtime prerequisite check passes.

One bounded recorded trial creates a fresh local venv with no system site-packages,
reusing the existing base Python interpreter. Old launcher attempts app/numpy imports
and emits ModuleNotFoundError traceback. New normal/check modes exit2 with the
five missing app components before heavy imports. All four isolated child probes
make zero network attempts. Shared environment/data/weights unchanged. Local
ensurepip bootstraps pip only; no app package installation. Offline pip --dry-run
--no-index FAILS due missing torch2.14.0 wheel; selected wheelhouse contains only
verified OpenCV wheel. This preserves an explicit failed installation-acceptance
gate,not a successful fresh install/new-computer/physical-disconnection result.
184software tests pass; counter37->38for one completed trial,not per subprocess.

Official PyPI version metadata and PyTorch CPU indexes were then captured as
SRC-PKG-002:7immutable metadata files with SHA receipts,5compatible core wheel
candidates with publisher hashes for Windows64/Python3.12. Zero wheels downloaded
or installed. The core plan is not a complete dependency lock; transitive closure,
CPU artifact sizes/notices and total bounded acquisition budget remain to verify.
This is not a claim that missing wheels are unavailable online. Guide:
docs/INSTALLATION_READINESS.md; plan:data/manifests/runtime_core_candidates_v1.json.
Source catalog53. Later work must use a separate fresh environment,not shared .venv.

Actual20:19UTC authorized Singapore snapshot31 adds1051later matched persistence
targets:24,942total,MAE3.928634spaces;7978expired/1303pending,75.77%resolved matching.
Raw JSON,normalized CSV,URL,provider/retrieval time,SHA and bounds/duplicate checks
retained. These are source-consistent baseline outcomes,not neural/camera accuracy.
No final image/date/sequence reread,model retraining or production weight changes.

No active jobs; counter38,next100-run checkpoint100. Existing189-file demo remains
a dated copy without this new launcher module/guide; builder includes the guide
for a future meaningful rebuild. Prior demo versions and all failed/selected
studies retained. Next:complete verified offline dependency preparation or legitimate
fresh labelled counting evidence,and remaining native/manual/student acceptance.
Whole project completion,official compliance and universal accuracy unclaimed.

## 25 October 2026 / verified fresh app-only offline dependency installation

Fresh app-only offline installation PASS:24original Windows64/Python3.12 CPU
wheels,208,542,037bytes,complete hash-locked requirements. Publisher SHA256,ZIP
CRC and embedded licence/notice hashes verified. New venv installs with --no-index
--require-hashes;pip check and preflight pass. All184existing software tests pass
in that fresh venv. Installation,checks,app and tests make zero network attempts.
Sixcore modules import from the new venv; decoder preloaded explicitly to prove
the freshly installed artifact. Ordinary source can prefer its identical bundled
decoder. Shared .venv and original checkpoints/data remain unchanged.

Actual hidden-native app checks pass:both frozen detectors on existing training
sample agree with68occupied/32vacant/0uncertain;paired exports,semantic-preview
separation,two archived forecasts,cached live,SVD and2already-seen licensed video
samples. This is software/prediction agreement,not ground-truth accuracy. No
final images/dates/sequences reread or rescored. Existing base Python/Tk/Windows
reused; no fresh-machine,physical-disconnection,manual-dialog or student mastery
claim. Jupyter/IPython are not installed in this app-only profile. Prior failed
readiness trial38 retained; one completed fresh-install trial advances38->39,
not one run per wheel/subprocess/test/frame. Guide:docs/OFFLINE_APP_SETUP.md;
pointer:reports/offline_runtime_latest.json.

Important provenance correction:the resolver --dry-run downloaded complete wheel
archives into its project-local pip cache without installing packages. Initial
planv1incorrectly marked installer_files_acquired=False. Original plan/logs are
preserved;v2and RUNTIME_DRYRUN_CACHE_20261025.json explicitly correct it. Whole
archives were then recovered from that cache,verified and staged with no extra
network transfer. Actual total208542037bytesis within512MiB; size gate checked
after resolver caching,not claimed as a pre-transfer hard limit. Exact per-file
network times were not captured; resolver operation bounds and exact local cache
copy/verification receipts retained. Source catalog54:PKG-002metadata now33files,
PKG-003original24installer archives with full per-package licence/creator records.

Actual20:56UTC official snapshot32 matches1105later frozen persistence targets:
26,047total,MAE3.820977spaces,8117expired/1280pending,76.24%resolved matching.
Immutable raw JSON,normalized CSV,URL,time,SHA,bounds/duplicates retained; no
camera/neural live accuracy. Earlier source gaps remain unscored,not zero error.

No active jobs; next100-run milestone100. Next:Jupyter offline extension or
legitimate fresh labelled counting evidence,then remaining native/physical/
student acceptance. Old demo/report/Excel/slides keep dated scope; full project,
official academic compliance and universal accuracy are not claimed complete.

## 25 October 2026 / fresh offline Jupyter kernels verified

New isolated app+Jupyter environment passes hash-locked --no-index installation and pip check. 83additional publisher-hash/CRC/notice-verified wheels (49,287,471bytes);107packages with app profile (257,829,508bytes). Two genuine new kernels execute lesson08with inline graphics and a separate training-only both-detector/2D/3D check. Original notebook08source cells kept verbatim with a diagnostic setup cell; outputs saved separately,original notebooks unchanged. Same68occupied/32vacant/0uncertain fixed example agreement,not accuracy. No consumed final data reopened or model training. Python non-loopback socket access denied; native ZeroMQ/physical networking is outside Python audit coverage. Existing base Python/Windows/model/data assets reused. Not all8notebooks freshly rerun; JupyterLab server/browser UI,physical/new-machine/manual/student acceptance remain. Old app-only installation and failed readiness retained. Guide:docs/OFFLINE_JUPYTER_SETUP.md;pointer:reports/offline_jupyter_latest.json. Completed failed gate40retained:offline install succeeded but strict guard blocked harmless ::1 bind. Continuation41reuses that new venv without reinstalling,permits loopback and completes actual kernel checks. Interrupted bootstrap excluded. Source catalog55. Acquisition DNS and UTF8 failures preserved;resumed cached downloads without installing into shared runtime. Actual21:27UTC Singapore snapshot33matches1107earlier frozen persistence targets:27154total,MAE3.760072spaces. Missing targets remain unscored;raw JSON/URL/time/SHA/normalized rows retained. No new neural/camera live score.

## 25 October 2026 / local JupyterLab server route verified

New optional offline launcher disables update checks and makes extension management read-only,binds localhost and accepts notebook/port/no-browser/separate-state options. Actual isolated Jupyter server serves authenticated Lab HTML/local JS asset/notebook08source;anonymous kernelspec request403. Server-created project kernel uses the verified interpreter and returns a real inline training-image SVD plot;2D/3D arithmetic passes. Owned kernel deleted/server exits0;Python non-loopback audit attempts0.184regression tests and3invalid-launch controls pass. Usual project kernel state,original weights/notebooks and consumed final claims unchanged. No visible browser/frontend-JS execution,manual,physical/new-machine or scientific accuracy claim. One completed server trial advances41->42;software tests/requests/frames do not add runs. README now maps raw images/CSV/live JSON/normalized CSV/provenance/model results in plain language and corrects stale offline/sample-count wording. Source catalog57:official REST/messaging documentation consulted;authored notes/URLs/access precision retained,no source text/assets copied. Latest official snapshot34,matched persistence outcomes28303,MAE3.746387spaces;not neural/camera accuracy. Guide:docs/OFFLINE_JUPYTER_SETUP.md;pointer:reports/jupyter_server_latest.json. Next:combined relocated demo+installer acceptance and fresh legitimate labelled evidence;remaining manual/student/academic gates separate.

## 25 October 2026 / combined offline demonstration verified in a fresh copy

Combined selected local demo passes:419copied payload files,806,444,601bytes,including107original offline wheel archives (257,829,508bytes),their publisher metadata/full notices and frozen app/model/data assets. NEW .venv inside the copy installs no-index/hash-locked;all107expected versions verified,dependency check passes. Both actual hidden detector/export/semantic/archived forecast/cached live/SVD/progress/video routes pass. Actual copied-folder Jupyter kernel executes notebook08with inline plot;no stripped-magic-only claim. Both detector training-example counts agree68/32/0out of100,not accuracy. Normal Python fallback/non-loopback audits have zero denials;separate original-README/DNS probes correctly blocked. Existing-environment overwrite rejected without changing config. All payload hashes,original model/notebook/final claims and earlier demo bytes unchanged. Existing Windows/base Python/Tk reused;native extensionIO/physical offline,new-machine,visible/manual and student/official acceptance unverified. Selected package excludes full datasets/other7notebooks;rebuild environment after moving paths. Source catalog57;copying existing archives is not a new download. One completed combined trial advances42->43. Latest Singapore snapshot35:29466matched later baseline outcomes,MAE3.893063spaces;no neural/camera live accuracy. Main live history is newer than frozen bundle snapshot. Guide:docs/COMBINED_OFFLINE_DEMO_GUIDE.md;pointer:reports/offline_demo_latest.json. Next scientific priority:fresh legitimate independent labels;remaining manual/student/academic gates separate.

## 26 October 2026 / recovered CNR metadata qualification handoff

Official CNRpublisher HTTP page recovered after HTTPS failure;current links point to author HTTPS GitHub release. CSV18,132,695bytes/EXTZIP449,502,403bytes retained with exact receipts/local SHA;publisher digest absent.144,965EXTrecords map exactly to JPEG member names,9cameras/23dates.13/5/5global-date roles contain82,361train/30,525development/32,079reserved records;all cameras on each date stay together. No JPEG decompressed or model trained/scored. CSV fields were tokenized;occupancy values were not semantically used,and omitted from derived manifest. Database ODbLdeclared;individual image-content rights unqualified,soimages remain inspection-only under PROJECT_CONSTRAINTS rule5.7newsynthetic guard/parser tests and full191regressions pass. Temporary fixture permission errors and licence-download403preserved;primary licence read through web tool,no original licence HTML copy claimed. One metadata trial advances43->44;final images remain unopened/unclaimed. Usage-limit auto-review failure interrupted the documentation action before execution;no bypass or credit purchase. Handoff resumed after the known reset. Source catalog57updated in place;original models/packages intact. Next independent work:unused licensed PKLot date inventory and fresh reservations. Guide:docs/CNRPARK_DATA_QUALIFICATION.md.

## 26 October 2026 / licensed archive fresh-date metadata inventory

After the account reset,the missing CNRhandoff was recovered without repeating its model-free audit. A new bounded scan read only original PKLot tar headers:gzip decompression occurred to reach headers,but no JPEG pixels or XML labels were decoded/parsed.12,218valid paired frames/98camera-date groups,396invalid or inconsistent member metadata entries quarantined,no duplicate member names. Conservative prior model/manifest/layout/experiment-date exclusion leaves205provisional frames over6dates. Whole latest date/camera groups selected by metadata:PUCPR2012-10-23,UFPR042012-12-24,UFPR052013-04-08reserved in full171frames;first/last frames per group preselected for later6-frame final. Other3dates development-only. This is a metadata plan,not a qualified final evaluation:byte-duplicate/source/annotation audit still needed before modelling. All original weights and CNR32,079reserved images remain unchanged/unopened. No training or new accuracy. One inventory trial advances44->45;no counts per header/frame.191software tests retain prior executed scope. Latest actual Singapore snapshot resumed after gap:0new scores,30,614total,MAE4.391684spaces;missed targets remain unscored,new1191forecasts frozen. No camera/neural live accuracy. Next:bounded selected-member audit and frozen development hypothesis. See reports/fresh_pklot_data_latest.json;source catalog57unchanged. Full project/manual/physical/student/official completion unclaimed.

## 26 October 2026 / fresh development members and frozen classifier baseline

New licensed raw members qualified:36JPEG/XMLfiles copied unchanged from the existing archive,not newly downloaded. Cross-identity byte hashes checked against source receipts and selected members;no collision.12fixed development frames over3dates/2known cameras contain720explicit occupancy labels,no unknowns.6final frames over3whole camera/date groups are materialized only as raw byte copies/hashes;JPEG pixels not opened and XML labels not parsed. Final reservationv2 remains unclaimed/closed. Perceptual duplication not audited. Frozen original ResNet18crop classifier scores703/720correct(97.6389%)on DEVELOPMENT,17harderrors,2confident false-vacants,14uncertain at unchanged0.25/0.75bands. Per-date hard accuracies1.000/0.9625/0.93125. Coarse preset gate passes,but2of4confidentvacant predictions onUFPR052013-02-28are wrong,bothslot37at17:55/18:10;aggregate accuracy is not vacancy-safe precision. No new training,settings change,production promotion,final/live or end-to-end fused-pipeline accuracy. Two distinct recorded trials:member qualification46and fresh baseline47;not per-frame/crop counts.191software tests remain the prior regression evidence. Actual local-copy receipt times are logging times;copy-event times bounded by run start/end,not fabricated exact network downloads. Next:measure unchanged detector/classifier fusion on these development frames with per-date vacancy/error/uncertainty gates. Final6kept for a frozen qualified paired comparison. Guide:docs/FRESH_PARKING_DATA_GUIDE.md;pointer:reports/fresh_parking_baseline_latest.json.

## 26 October 2026 / unchanged app fusion on fresh development photos

Unchanged actual app fusion measured on the same 12 fixed DEVELOPMENT photos/720 explicit slot labels: fasterrcnn: 0 wrong empty/88 empty answers, 16 uncertain, 88 correct empty, gate True; maskrcnn: 1 wrong empty/88 empty answers, 16 uncertain, 87 correct empty, gate True. Gates were written before inference: fewer than2false-vacants, no per-date false-vacant regression, at most10%uncertainty, retain at least80%of88correct crop-only vacancies. Both existing detector options tested; no training/threshold/weight change or promotion. Faster flags both crop false-vacants as uncertain,not occupied; Mask flags only one. Ten false-occupied answers remain with either option. Mask Feb28vacancy precision is only2/3;Faster Feb28finds only2/6true vacancies despite zero observed wrong empty answers. Aggregate gate pass is not vacancy-safe certification. XML geometry was supplied without answer labels; this is not automatic learned space segmentation. Final6images/labels stay unopened/unclaimed; old finals remain consumed. All three production checkpoints and tracker source hashes unchanged. One completed comparison advances47->48; frames/tests/live collection do not add runs. Latest official Singapore snapshot38 adds1100matched earlier persistence outcomes,31714total,MAE4.623069spaces;1094newforecasts frozen. Restricted DNS failure retained; authorized retry succeeded. Immutable raw JSON, receipt URL/time/SHA, normalized CSV and cached app route validated; history duplicates0. No neural/camera live accuracy. Original full191regressions retain prior scope;14targeted product/holdout tests pass with zero failures/errors. Source catalog57 unchanged. Next: qualified training-only data expansion while final stays closed. Physical/manual/browser/student/official acceptance remains incomplete.

## 26 October 2026 / expanded occupancy training and real-engine development checks

Expanded frozen-ResNet18head trained on10,104explicit crops from170photos/32previously designated training dates,including958third-camera examples absent from the original classifier training. Validation45photos/12dates/2028labels kept globally separate;704training+396validation unknown labels excluded. All old/new final dates excluded;430source JPEG/XMLfiles copied locally with member/archive/source/checksum receipts,not network downloads. Camera/class-balanced AdamW warm-start head only; early stopping after8epochs selected epoch2 by prespecified macro-camera validation loss. Original classifier46/2028harderrors versus candidate12/2028(99.4083%development),confident false-vacants6->4,correct vacancies622->665,uncertain33->19;fresh720harderrors17->6. All preset classifier gates pass. Actual app engines with experiment-local candidate weights pass both detector development gates: Faster99correctvacancies/0wrongvacant/2wrongoccupied/14uncertain,Mask100/0/2/13;720labels,supplied geometry,2known cameras/3dates,not automatic space segmentation or final/live accuracy. No production promotion. Original3production weights,existing image-final claims and notebooks01-08unchanged. Best/full candidate,last optimizer/RNG and215feature chunks preserved;candidate checkpoint roundtrip passed.197full software tests pass. New pinned notebook09executes6codecells with one real inline learning-curve PNG and zero errors. Initial test import-path and notebook missing-pandas failures preserved;fixed using existing packages,no installation. Three completed distinct trials advance48->51(dataqualification,headtraining,pairedfusion),not perphoto/epoch. Latest officialSingapore39snapshots adds1048matched later baseline outcomes,32762total,MAE4.746963spaces;1316newforecasts frozen. Final6PKLotphotos remain closed/unclaimed. Next:one frozen paired original/candidate final protocol and durable claim before any final decoding. Physical/manual/browser/student/official acceptance remain incomplete.

## 26 October 2026 / once-only paired occupancy final and retained replacement failure

The frozen protocol/controller was committed as3b08e8f before any final pixels/XML labels were opened.206fullsoftware tests,including synthetic paired-controller/unknown-label cases,passed before final decode;real final claims unchanged during tests. Both original/candidate checkpoints,source/config/model hashes and passed development cards bound;paired binding receipt and durable whole-date claim flushed before callback. Six photos/3known camera-date groups supplied336explicit labels(236occupied/100vacant),0unknown;UFPR04group has56empty/0occupied so its occupied-case accuracy remains unmeasured. Forced classifier errors8->4(97.619->98.810percent),same for bothdetectors. Combined Faster original95correctempty/2wrongempty/4wrongoccupied/10review versus candidate99/0/0/8;Mask94/2/4/11versus98/0/0/9. Candidate is better overall but FAILS the frozen per-group correct-vacancy-retention check: rainy PUCPR14->13correctempty,13/14=92.857percent<95percent. Both final gatesFalse;no rule change,model promotion or universal/live accuracy claim. All3whole date groups now CONSUMED,including171sourceframes;older finals remain consumed. Original3production checkpoints/tracker unchanged. One final comparison advances51->52,not permodel/photo. Two-sheet Excel and tidy1344prediction CSV(4configs on336unique slots) preserve failed rule;11formula caches,boundary recalculation,ZIPCRC/source metrics and both previews checked. Native visible Excel not tested. Bundle-library junction initially denied in restricted call;authorized retry succeeded,no package installation/dependency mutation. Notebook09updated as archived training reader,6actualkernelcells/1PNG/zeroerrors,without retraining/finalinference;previous executed source preserved. Latest officialSingapore40snapshots adds1188matched earlier baseline outcomes,33950total,MAE4.790133spaces;1242newforecasts frozen. Missing targets unscored;aggregatefeed not camera truth. Source57unchanged. Next independent task:correct app archive-forecast LSTM mislabelling for the frozen group-relative report,without raw holdout access;continue legitimate new-source qualification. Physical/manual/browser/student/official completion remains unclaimed.

## 26 October 2026 / precise forecast variant labels and owned-snapshot exports

Both archived methods are LSTM variants. Display now distinguishes Original LSTM from Group-relative residual LSTM(trend-guarded/group-relative training),instead of using an ambiguous generic LSTM label for every report. Each keeps its own stored cohort,MAE,persistence comparison and actual source-time limitations. New Save forecast results route writes actual displayed PNG,CSV,reportJSON and checksum manifest;all identify method/run/park and sourceprediction SHA. Missing sensor timestamps/leads remain blank,not fabricated from grid targets. Plot and export snapshot are cleared on report or car-park changes. Actual hidden native Tk checks exercised both real archived reports:8original/75later windows for selectedBHMBCCMKT01;plot lines,text,CSV/JSON/export hashes agree. Normal raw/processed/split/network attempts0under Python audit;explicit raw-file negative probe blocked. No model inference/training/new scientific scoring;original204rowreportMAE121.210vs61.142persistence,and later1853rowreport31.724vs39.072remainunchanged,differentcohorts. All protected model/card/prediction/holdout hashes unchanged.213full software tests pass;new test fixtures are synthetic. One integration trial advances52->53,not perplot/test/export. Latest officialSingapore41snapshots adds1150matched later baseline outcomes,35100total,MAE4.804530spaces;1237newforecasts frozen. Source57unchanged. No occupancy model promotion:failed rainy-view final gate retained and all final groups remain consumed. Old combined offline package remains an older snapshot;nextrefresh is justified by this concrete application feature change. Visible/manual/physical/new-machine/student/official acceptance unclaimed. Guide:docs/FORECAST_REPORTS_GUIDE.md;pointer:reports/forecast_display_exports_latest.json.

## 26 October 2026 / forecast exports verified in the refreshed offline copy

The refreshed selected demo passes its frozen combined gate in415.75seconds:424payload files (807,000,528bytes),107original installer wheels and a NEW package-local environment with all107installed versions independently verified. Actual hidden native checks exercise both detectors on one training image,semantic preview,2D/3D teaching examples,SVD,two already-seen video frames,cached live data and both archived forecast variants. Original LSTM and Group-relative residual LSTM each retain their own plot legend,run/checkpoint/prediction identity and exact PNG/CSV/JSON exports. Report/park changes clear the previous plot/export. Export PNGs were visually inspected. A genuine copied-folder Jupyter kernel executes notebook08with one inline PNG;only08ofnine notebooks is included. Existing-environment overwrite is refused. Normal app Python socket attempts:zero;installer/Jupyter audit denials:zero. Separate deliberate original-project read/DNS probes are blocked. Python guards do not isolate native-extension IO or physically disconnect the laptop. All424payload hashes,protected model/claim bytes and all419earlier-package payload bytes remain unchanged. No model training,new scientific scoring,consumed final replay,new-machine or visible/manual/student acceptance. Prior213shared-runtime software tests remain separately dated. Counter53->54 counts one integration trial;wakeups37,next100-run live checkpoint100,no active jobs. Source catalog57unchanged;installer copying is not new acquisition. Offline cache is snapshot41/provider2026-10-26T10:29:36+08:00;main history has42snapshots/provider11:00:36+08:00. Main causal persistence scores36,258targets,MAE4.795797spaces;missing targets unscored,not neural/camera accuracy. Evidence:experiments/results/COMBINED-DEMO-20261026T025712811956Z/run.json;experiments/evidence/HEARTBEAT-20261026T025043Z/independent_checks.json. Start:docs/COMBINED_OFFLINE_DEMO_GUIDE.md. Next:legitimate fresh labels;failed occupancy final remains unpromoted.

## 26 October 2026 / new publisher-original parking archive verified

New SRC-DS-018 is the publisher repository bermalA/open-space-parking-dataset,not a CNR mirror. Its README explicitly declares author-created images/annotations and LICENSE declares dataset CC BY4.0. Pinned commit d4ea8d0afed823665c70102190641f2de28b6603 yields731photos/731matching label files (publisher518train/144valid/69test). A bounded94,163,307byte original archive was acquired;all1465file sizes/Git blob identities verified,102,520,255uncompressed bytes. No exact JPEG Git-blob duplicates found;this does not establish absence of near duplicates or source independence. Encoded image/label bytes were streamed/decompressed for hashes,but zero image pixels decoded and zero semantic annotation rows interpreted. Only three exact metadata files were extracted. Camera/capture dates,dimensions,geometry/exhaustiveness and source-content provenance are not independently verified. Publisher handle is recorded;paper citation incomplete. Image rights basis is this publisher declaration,not CNR terms. No training/scoring or benchmark admission. Original models/claims/earlier package remain unchanged. One completed asset-integrity trial advances54->55;wakeups38;catalog58;next100-run checkpoint100. Official Singapore snapshot43was collected at05:34UTC after a gap:0new matching later outcomes,36,258total,persistence MAE4.795797spaces.11,472expired targets remain unscored;matching coverage75.9648percent,not accuracy.1,159new forecasts frozen. Guide:docs/OPEN_SPACE_DATA_GUIDE.md;exact source URL/commit/local SHA and acquisition UTC in data/resource_receipts.jsonl;raw archive in data/raw/open_space_official/. Next:bounded train-only geometry/label/group admission,not automatic random-split benchmarking.

## 26 October 2026 / supplied space polygons and conservative source grouping

The first prespecified TRAIN syntax check failed because source labels are segmentation polygons,class plusXYvertices,often repeating the closing point;the strict five-token box reader correctly rejected them. Failure run OPEN-SPACE-TRAIN-INSPECTION-20261026T054147720575Z and original code/interrupted evidence retained. Its original interrupted pixel count0meant fully appended records;one TRAINimage actually decoded before parser failure,and terminal failure report corrects this. A separate strict polygon reader preserves raw rows/coordinates,handles a repeated closing vertex and tiny explicit rounding,and rejects nonfinite/outside/duplicate/conflicting/self-intersecting/zero-area geometry. After the concrete format change,the same four preselected TRAIN indices0/172/344/517(photo001/173/345/518)were inspected:4distinct1280x640photos,294polygons(235supplied occupied/59vacant),0rejected files/rounding corrections,0capture dates in EXIF. Actual contact-sheet review shows perspective parking outlines,day/night examples and visually related backgrounds. This is qualitative plausibility,not exhaustive annotation or model accuracy. Some scene areas outside supplied polygons also contain vehicles;do not assume the entire remainder is labelled background. No publisher valid/test pixels or semantic labels read. Entire source conservatively marked development-exposed in usagev2 because camera/session dates unknown;publisher test folders are not independent final groups. All227software tests pass,including14new synthetic parser/selection tests. Original model/claim bytes and source archive unchanged;no model training/scoring/promotion. Failed box stage55->56,corrected polygon inspection56->57;not perphoto/polygon/test. Wakeups39;58sources;next100-run checkpoint100;no active jobs. Live collection not due:latest05:34UTC43snapshots/36,258matched persistence targets/MAE4.795797spaces;nextafter06:04:21UTC. Models remain unchanged. Guide:docs/OPEN_SPACE_DATA_GUIDE.md;pointer:reports/open_space_training_inspection_latest.json.

## 26 October 2026 / complete TRAIN audit with quarantine and unknown-aware support

All518SRC-DS-018TRAIN photos and1036original member copies verified;72,701,375TRAIN bytes retained. 517pairs accepted syntactically,39,068source polygons(28,604occupied/10,464vacant);train328contains one5-token box row atline69inside a polygon file,so its ENTIRE69rows are quarantined without repair/partial salvage. All518images1280x640,0EXIF capture dates.0exactRGBduplicate groups,907pairs at frozen dHash<=8/256are similarity candidates,not confirmed duplicates or independent split groups. New source-support helper assigns known occupied1/vacant0only inside nonconflicting supplied polygons;unannotated or contradictory support255unknown. At diagnostic320x160,388accepted frames have some opposing-class raster overlap,74,632pixels out of10,771,213supplied-union pixels;maximum frame fraction1.731percent. Shared raster boundaries can contribute;this is not measured annotation error. Actual day/night support PNGs visually inspected. No region/background negative masks inferred. Source-wide group remains development-exposed;zero valid/test pixel/semantic target reads,though compressed archive bytes/headers are scanned for hashing/location. All233software tests pass(including6new synthetic coverage/hash tests). Original models/claims/archive untouched;no training/scoring/promotion. One audit57->58,wakeups40;source58,next100-run checkpoint100,no active jobs. Latest Singapore44snapshots add1,111causal baseline matches:37,369total,persistenceMAE4.859429spaces;1,183new forecasts frozen;missing targets unscored,not camera/neural accuracy. Next:bounded masked occupancy crop preparation and one explicitly DEVELOPMENT-ONLY source-balanced head trial with existing PKLot development labels;no final replay or app replacement. Derived CSVs/data locations:reports/open_space_train_audit_latest.json;guide:docs/OPEN_SPACE_DATA_GUIDE.md.

## 26 October 2026 / genuine source-balanced head training retained the warm comparison

Prepared16,448source TRAIN occupancy crops from517accepted photos with a label-blind32polygon/frame cap;96excluded(55native-side<12pixels,41unambiguous support<95percent),all retained with reasons. Gray127input outside unambiguous polygon support;source0occupied maps model1 and source1vacant maps model0.517NPZcachefiles/208,600,155bytes,source/row/crop hashes preserved. Genuine frozen-ResNet18 linear-head training used26,552crops(10,104original PKLot+16,448newsource),source-weighted.75/.25,camera/class-balanced,seed128,max6epochs/patience2. Original215feature chunks hash-verified;newsource517feature chunks retained;warm/original backbones verified identical. Two epochs completed in168.86seconds with early stopping. On SAME reused2,028PKLot DEVELOPMENT labels,last trained epoch errors12->20,confident false-vacant4->6,correct confident empty665->661,review19->20;macro loss.01942075->.02863934. Prespecified loss selection keeps epoch0warm comparison;selected12errors/4false-vacant,strict improvement gateFalse. All trained/best/last/checkpoint/cache states retained. This is a rejected transfer hypothesis,not improved final performance. Warm comparison was already a separate unpromoted research checkpoint;running app stilluses original model. No newsource validation/test semantics or consumed final data used. No night/new-park/live camera accuracy claim. Existing final failure/claims and original3production checkpoints unchanged.238software tests pass;crop59andtraining60are two completed trials,not perframe/epoch. Source58,wakeups41,next100-run checkpoint100,no active jobs. One-sheet Excel outputs/training_report_20261026T063846Z/Smart_Parking_Training_Study.xlsx compares warm/trained/retained results and data/source counts. Artifact-tool authoring with bundled runtime;4relevant formula caches,source counts,input perturb/restore,ZIPCRC and actual final preview verified;nativeExcel not tested. Archival exactcopy:reports/source_training_20261026/Smart_Parking_Training_Study.xlsx. OfficialSingapore45snapshots adds1,103causal persistence matches,38,472total,MAE4.859742spaces;1,300newforecasts;missing targets unscored,not neural/camera accuracy. Next:paired cached development regression analysis before any distinct bounded training hypothesis.

## 26 October 2026 / paired transfer diagnosis and rejected teacher-anchored study

Cached paired diagnosis on SAME2,028development slots:plain study corrected3forced mistakes but introduced11(12->20),added3false-vacant/removed1(4->6). UFPR05accounts9regressions/3corrections,PUCPR2regressions. Newsource TRAIN fit improves1,588->497errors and unweightedCE.294961->.076347on16,448SEEN examples;not generalization accuracy. One distinct frozen teacher-anchored head study usesKLstrength1/temperature2against warm predictions on original TRAIN only,sourceCE.75/.25,max6/patience2,seed128. Two epochs completed;lasttrained18errors/6false-vacant,macrodevelopmentCE.025601stillabove warm.019421. Prespecified CE selection retains epoch0warm12errors/4false-vacant;strict improvementFalse,no app promotion.20vs18is not isolated causal evidence because RNG consumption can differ. All failed/trained/optimizer/RNG/cache/curves preserved;original checkpoints/claims unchanged,no final or source018valid/test read. 245software tests pass;4new synthetic paired-identity and3teacher-loss tests. Diagnosis60->61,anchoredtraining61->62;not perepoch/frame/test. Wakeups42/source58/next100-run milestone100/no active jobs. New Excel comparison outputs/transfer_report_20261026T070847Z/Smart_Parking_Transfer_Comparison.xlsxrecords12/20/18/12onreused development,seen-training fit,source/data/run IDs and no final performance claim. Artifact-tool formulas6/source counts/input-change restore/ZIPCRC/date fit/actual preview verified;nativeExcel not tested. Earlier workbook and exact newarchive preserved. Singapore46snapshots adds1,171causal persistence matches,39,643total,MAE4.856746spaces;1,194newforecasts;missing targets unscored,not neural/camera accuracy. Next independent task:qualify captured Singapore history and reserve fresh FUTURE global time holdout before learned forecast work;stop similar linear-head grid attempts. Student guide:docs/TRANSFER_LEARNING_EXPLAINED.md.

## 26 October 2026 / Singapore causal history and reserved future forecasting period

Sealed46receipt-hash-bound snapshots before07:46:23UTC for a source-specific forecast study.111,458parsed rows yield56,136fresh observations;4,547observation-age and50,775source-lag records excluded,0exactduplicates/conflicting revisions among fresh candidates. Two known observations10-45minutes apart,same carpark/lot/capacity,form only causal features;first received fresh target20-45minutes later is used,no interpolation. Training labels must arrive before GLOBAL training cutoff21:27:05UTC25October. 18,393training windows across18origins/1,355series and9,202development windows across9origins/1,243series;many lots are not many independent days. Development actual target lead27.30-43.01minutes,not exact30. BEFORE fitting,reserved ALLcarparks future origin interval26October10:00UTCto27October10:00UTC,target/deliveryclosure27October10:51UTC. Future values unread/unconsumed;receipt availability,late-freeze,ledger hashes,target-free issuances,global overlap claims and failed-callback consumption covered by synthetic tests. Operational learned issuance/final scoring callback not yet built. One fixed non-neural ridge residual learner(strength.1,6causal features,training-only scaling)failed development:rawMAE7.738379vs6.957618persistence,macro-origin7.732101vs6.953844. Checkpoint roundtrip/bounds pass;no learned forecasts enabled,no final/neural/camera score. Model/source/predictions and rejected result retained. 260software tests pass. Admission62->63,learnedbaseline63->64;wakeups43/source58/next100-run milestone100/no activejobs. Currentmain Singapore47snapshots adds1,110previously frozen persistence matches:40,753total,MAE4.828111spaces,1,240newforecasts. Its07:55post-cutoff snapshot is excluded from the sealed model history;missingtargets unscored. Global rollingbaseline cohort differs from9,202development cohort. Original vision/occupancy/Birmingham/neural checkpoints and consumed finalclaims unchanged. Next:one MAE-aligned train-only hypothesis or continue collection;no grid/retrospective final. Guide:docs/SINGAPORE_FORECAST_STUDY.md.

## 26 October 2026 / MAE-aligned Singapore trend and frozen prospective issuer

A single MAE-aligned trend learner fitted alpha=0.3001851852 on the sealed 18,393 training windows. On the SAME 9,202 development windows it measured 6.309848 spaces MAE versus 6.957618 persistence, a 9.31% reduction; equal-origin MAE 6.306076 versus 6.953844. The rules were saved before fitting: at least 1% overall gain, macro-origin noninferiority, every origin regression <=0.5 spaces, physical bounds. All pass; two origins regress slightly, worst 0.425614. Only nine global development times; this is not live/final/neural/camera accuracy. No validation grid or refit. The prior ridge failure is preserved. Candidate checkpoint SHA b11dd08ff444affb92de3841a23ef6de0b63833d270f748df4ff654426e1851f. Research selection and issuer/config frozen at 08:16:03 UTC, before the unchanged ALL-carpark future origin interval 26 October 10:00 UTC–27 October 10:00 UTC. Actual pre-period smoke check returns not_started/zero issued; no real learned batches, outcomes, or final claims. Exclusive local-clock batches bind original receipts, two causal counts, model/config/reservation hashes; duplicates, stale/future inputs, changed capacity/checkpoints/batches and delayed writes are blocked. Local audit times are not external attestations. Final scoring callback remains unfinished; its matching/support/gates are already frozen in data/manifests/singapore_trend_issuance_v1.json. No real final scoring before 27 October 10:51 UTC. All 273 software tests pass, including six synthetic trend tests (100 seeded optimizer fixtures within one test) and seven issuance tests. One completed training/development experiment advances 64->65, wakeups 44, sources 58, next100-run checkpoint100, no active jobs. No network collection this wakeup: existing 47 snapshots/40,753 rolling persistence outcomes remain a different cohort. Original application models and consumed claims unchanged. Next: synthetic final callback + scoring-code freeze, then scheduled collection/real pre-target issuance with scripts/collect_singapore_study.py. No more fitting for this study. Guide: docs/SINGAPORE_FORECAST_STUDY.md; pointer: reports/singapore_forecast_study_latest.json.

## 26 October 2026 / frozen once-only Singapore final scorer

The once-only paired final scorer is implemented and frozen at08:53:02UTC, before reserved origins begin26October10:00UTC. Issuance config, candidate and final rules unchanged. It verifies committed ledger/model/config/receipt bindings without decoding targets, then claims the entire canonical source interval before opening semantic raw data (origin snapshots can also contain earlier targets). Raw context is reconstructed after claim, first received qualifying20-45minute target is used, changed capacities stop matching, missing targets remain unscored, and failed callbacks consume the period. Support/coverage and paired raw/macro/per-origin gates are frozen; zero baseline error cannot count as a positive relative gain. CSV/unmatched IDs/input hashes/claim outcomes/completion receipts preserved. Production CLI offers no historical-clock override; before27October10:51UTC it returnsnot_ready, and repeats of completed runs show archives. Actual smokecheck decoded0real targetJSON/created0real finalclaims/issued0learnedbatches. One separately recorded SYNTHETIC validation used seed133,14generated snapshots/12origins/60simulatedparks,700issued/688matched/12missing; full frozen numeric gates, manufactured slope arithmetic, early blocking and once-only behavior passed. These are software fixtures, not real-world forecasting performance. Actual fixture bytes/claims/logs retained underoutputs/singapore_final_validation with hashed inventory. 284software tests pass including11new final tests. One validation65->66, wakeups45/source58/next100-run checkpoint100/no activejobs. Official collection08:39UTC added snapshot48 and1,155previously frozen persistence matches:41,908total,MAE4.833015spaces;1,118new forecasts. Source receipt/hash/schema/bounds/duplicates/freshness and cached app-data path checked; manual UI not tested. Original model/checkpoint/consumed-claim hashes unchanged. No learned live/final/camera/neural accuracy measured and no app promotion. Next:read-only executed teaching notebook and sensible30minute collection; protect frozen sources and wait for actual future targets. Guide:docs/SINGAPORE_FORECAST_STUDY.md; frozen scorer:data/manifests/singapore_trend_scoring_v1.json.

## 26 October 2026 / executed read-only Singapore Jupyter lesson

Added notebook10_singapore_forecast_study.ipynb with seven actually executed Jupyter code cells and one inline development PNG. Reads only10hash-bound archived-development/frozen-metadata inputs; checks matching series/issue/targets and recomputes stored error arithmetic on the SAME9,202windows/nine collection times. Ridge7.738379vs6.957618persistence remains rejected; trend6.309848is development only. Synthetic toy prediction53.001852and80percentmatching example are explicitly teaching data. Receipt availability, train cutoff, two slightly worse origins, variable actual target leads, once-only future rules/licence and unassessed student questions are explained. Actual shared-venv kernel audits blocked two protected read probes, one study write and external DNS; no successful raw/growing/final reads or study writes. These are Python-level checks, not OS/physicaloffline/new-machine/browser/manual/mastery acceptance. Saved scientific PNG visually inspected. First restricted child timed out240seconds; owned processes were absent before host retry. Second host attempt failed firstcell becausepandaswasnotinstalled; replaced optional tables with escaped standardPython/JupyterHTML, installed0packages, successful host retry. Both interrupted attempts/protocols/source/diagnostics preserved and excluded from completed count; connection keys/runtime caches scopedignored. 291software tests pass including7new lesson fixtures. One completed lessonvalidation66->67,wakeups46/source58/next100-run checkpoint100/no activejobs. Official09:10collection adds snapshot49,1,016previously frozen persistence outcomes (42,924total,MAE4.839624spaces),1,256newforecasts. Raw URL/licence/receipt/hash/normalized history and cached-app schema/bounds/duplicates/freshness checked. Real learned study still has zero batches/claims/finalmetrics beforeitsoriginwindow; all frozen runtime/candidate/original weights/consumed claims unchanged. No app promotion. README stale six-final-untested statement corrected to the preserved consumed/failed occupancy replacement result. Existing424-file offline package and old notebooks/reports remain dated. Next:separate relocated read-only lesson pack and sensiblecollection; no fitting or early scoring. Evidence:reports/singapore_lesson_latest.json;guide:docs/SINGAPORE_FORECAST_STUDY.md.

## 26 October 2026 / relocated read-only lesson and resumed live collection

Built a separate read-only Singapore lesson copy:22payloadfiles/10,100,681bytes plus checksummanifest,10archived inputs, small statistical checkpoint, helper code and46original historical acquisition receipts with HDB/data.gov.sg attribution/licence. No raw/growing/final data, production neural weights, trainer/collector/scorer or runtime included. Actual relocated seven-cell Jupyter execution passed in the previously offline-installed local venv; helper origin is the copiedfolder and5dependency origins are inside that selectedvenv. File/socket audits and expectedprobes pass, PNG visually reviewed, every payloadbyte remains unchanged; launcher writes executed copies only. Verifier and publiclauncherhelp pass. This is not a new install, newmachine, physicaldisconnection, manualbrowser or studentmastery test. Existing424-file appbundle and originallesson remain untouched. 295software tests pass including4new package path/integrity fixtures. One relocatedvalidation67->68, completedwakeups47/source58, next100-run checkpoint100/no activejobs. Work spans coalesced heartbeat triggers; no unperformed iterations counted. Official09:43collection added snapshot50/1164previously frozen persistence matches; after no saved collections until11:39, snapshot51 adds0matches/1220newbaselineforecasts. Total44,088outcomes,MAE4.893781spaces; missingtargets stayunscored. The ongoing frozen learnedstudy issued0at11:39because previousfresh context was unavailable(1209excluded,6stale); no backdated origins or invented observations. Actualemptybatchfolders contain0files, globalfinalclaimabsent. Next legitimate context collection after12:09:26UTC. Candidate, issuer/scorer/configs, originalweights and consumedclaims unchanged; no learned interim/final/camera accuracy evaluated and no app promotion. Next:timely prospectiveissuance and metadata-only health checks, then publisher-backed fresh region/traffic segmentation-source qualification. Guide:docs/SINGAPORE_LESSON_PACKAGE.md; evidence:reports/singapore_lesson_package_latest.json.

## 26 October 2026 / first real pre-target batch and metadata-only health

The frozen issuer saved its first real batch: 1,110 forecasts issued 12:09:52.404825 UTC, committed 12:09:52.868374, receipted 12:09:52.907664; target window 12:29:52–12:54:52 UTC. This is pre-target logging evidence, not accuracy. The separate metadata-only health checker validates frozen model/config/batch/receipt identities, strict outcome-free schema, unique IDs, availability/issue/commit times, physical bounds and reproduction from saved inputs. Two original raw files are hashed once each, never decoded. Raw semantic context authentication is deliberately deferred to the once-only final callback, since an origin may also contain earlier targets. No learned error, matching coverage, final claim or app promotion. Routine CLI adds no trial count; first-integration record is one-time and repeat registration is blocked. All 302 software tests pass, including seven new synthetic health cases for no raw/target decoding, changed bytes, duplicate IDs, outcome smuggling, wrong predictions, invalid times and partial batches. One real metadata validation advances 68->69, completed wakeups48/source58/next100-run checkpoint100/no active jobs. Official snapshot52 at12:09 adds1,126previously frozen persistence matches:45,214total,MAE4.978878spaces;1,280newbaselineforecasts. Rolling baseline, historical development and new learned batch are different cohorts. Earlier collection gap stays unfilled. Raw/source/licence/receipt/normalized/cache/schema/bounds/freshness checks retained. All frozen candidate/issuer/scorer/reservation, original production weights and consumed claims unchanged; no learned interim/final/camera/neural score. Next:collect after12:39:49UTC, routine metadata health without new trial, then genuinely fresh publisher-qualified region/traffic annotations rather than repeated package checks. Guide:docs/SINGAPORE_ISSUANCE_HEALTH.md; current status:reports/singapore_forecast_study_latest.json.

## 26 October 2026 / fresh UVG data and retained annotation failures

Added publisher-qualified UVG traffic development assets (47,670,094 unchanged bytes), sealed whole HighwayDrive final reservation before any body download, and explicit safe annotation access/parser. HighwayView actual600frames/3840x2160/60fps,11109supplied observations/35tracks;all600maskCRC/headers checked. Initial RGB identity gate FAILED; separate fixed-eight-frame BGR correction146/147passes and also FAILED all-instance gate. Absent subpixel mask(frame121/track8,width0.17664px) remainsunknown;new adapter prevents false background/zero-IoU labels. Both failures/protocols/source snapshots preserved;no model inference/accuracy or production promotion. All317software tests pass. Two trials69->71,wakeups49/source60/next100-runcheckpoint100/noactivejobs. Latest53officialSingapore snapshots;2254learnedforecasts/2origins metadatahealthy, no learned target scoring. Rolling frozenpersistence46377matches/MAE5.045195spaces is a distinct cohort. Nextcollection after13:10:56UTC;learnedfinal closeduntil27October10:51UTC. Allproduction/frozen-study hashes and consumedclaims unchanged. Nextfreeze unchanged-detector positive-instance DEVELOPMENT comparison;HighwayDrivefinal unopened with no controller yet. Missinguniversitydocs/physicaloffline/manual/studentacceptance remainopen. Guide:docs/UVG_DEVELOPMENT_GUIDE.md;card:models/uvg_development_data_card.json.

## 26 October 2026 / measured real traffic development comparison

Measured both unchanged product detectors on11fixed HighwayView DEVELOPMENTframes:194suppliedcar/truckobservations(34tracks),153eligible(32tracks),41smallerexcludedfromgate,10trainobservationsoutsidescope. Default640 Faster88/153/Mask67/153;candidate960102/153and87/153. All-positive194recalls45.36->52.58percentand34.54->44.85percent. Zero-inclusive153MaskIoU0.342017->0.467224;matched-only0.781024->0.821670. Candidatepassesfrozenrelativegain/per-frame/per-class/timegates,butFAILSretainedabsolute75percent/0.5/mask-vs-fastergates;no apppromotion/finalaccess. Modeltimefactors1.373/1.647,notdeploymentFPS. Bothprotocols/code/input/weight/configbindings,seeds138,predictions/packedmasks andfailedgatesretained. Defaultexportpatherrorrepairedwithoutinference replay;interruptionpreserved. Independentartifactverificationreproduces306maskIoUs.324softwaretestspass;twoactualtrials71->73,wakeups50/source60,next100-runcheckpoint100/noactivejobs. Sourceannotationfailures/unknownsupportretained;oneoriginalabsentraster+fourresize-loss masksallbeloweligibilitygate. No exhaustiveprecision/mAP,parkingoccupancy,independentfinal/camerageneralizationclaim. Latest54officialSGsnapshots/3385learnedforecasts/3originsmetadatahealthy;no learnedtargetmetrics. Rollingpersistence47560matches,MAE5.095774spaces,distinctcohort. Nextcollectionafter13:41:07UTC;learnedfinalcloseduntil27October10:51UTC. Originalmodels/frozenSGmethods/consumedclaims unchanged. Nextboundedrawclass/scoremissdiagnostic orarchivedresultslesson;noresolutiongrid. Guide:docs/UVG_DETECTOR_DEVELOPMENT.md;card:models/uvg_detector_development.json.

## 26 October 2026 / class-error diagnosis and executed vision lesson

Prespecifiedoutputaudit6calls/3reusedHighwayViewDEVframes(52supplied/41eligibleobservations/model)reproducesallarchived960productoutputs. Unchangedheadscore0.05/NMS0.5/top150;notrawRPN/logits. Fastereligible26matched/8lowclassscore/2localization/5unresolved;Mask24/2/1/13plus1outsideclass. Fixedframe300truck25:Fastertruckscore0.813114/IoU0.964129,Masktrain0.682491/IoU0.979144;productcorrectlyexcludestrainclassbutlosesthismisclassifiedtruck. No classremapping/thresholdchange/causalclaim. Realtrainvisible;negativeevidenceunestablished. SeparateactualJupyterlesson11executes7cells/2archivedPNG/11boundinputs,zeroerrors. Threefile/write+oneDNSprobesdenied,successfulraw/growing/finalreads0,modelcalls0;sourcecells/PNGs/checksumsunchanged. Synthetictoyexplicit;studentmastery/physicaloffline/newmachine/manualbrowserunassessed. All336softwaretestspass;initialintegritytesttempACLfailurepreservedandfixturemovedtocheckedprojectscratch. Two distincttrials73->75,wakeups51/source60/next100-runcheckpoint100/noactivejobs. Earlier960candidateabsoluteadmissionstillfails;HighwayDrivefinalunopened/noapp promotion. Latest55officialSGsnapshots/4411genuinelearnedforecasts/4originsmetadatahealthy;no learnedtargetmetrics. Rollingpersistence48715matches,MAE5.120271spaces,distinctcohort. Nextcollectionafter14:11:37UTC;frozenlearnedfinalcloseduntil27October10:51UTC. Alloriginalmodels/frozenmethods/consumedclaimsunchanged. Nextboundednative-detailtilinghypothesiswithstrictsame-cohortgatesornewparkingregion-sourcequalification. Guide:docs/VISUAL_DETECTION_DIAGNOSTICS.md;notebook:notebooks/11_visual_detection_diagnostics.ipynb.

## Notebook-directory launch correction

Finalreviewfoundlesson11assumedkernelCWDwasprojectroot. Itnowfindsthenearestprojectfromrootornotebooks/. Originalroot-onlysource/executedbook/protocolretainedunchanged. Separateactualnotebooks-folderkernelregression VISION-LESSON-20261026T135823759379Z passes7cells/2PNGs/3file-write+1DNSdenials in3.937seconds;nofreshinference/raw/finalreads. This distinctlaunch-contextfixvalidationadvances75->76;wakeupcount51/source60/next100-runcheckpoint100/noactivejobs. Currentnotebook/cardpointtocorrectedexecutedversion. No studentmastery/physicaloffline/newmachineclaim.

## 26 October 2026 / native-detail crop comparison and retained admission failure

Onefixednative-detailcropDEVELOPMENTcandidatecompleted88cropcallsin400.593seconds,seed141,onidentical11HighwayViewframes. Original960full-frameoutputsretained. Faster102->139/153eligible(90.85percent),Mask87->113/153(73.86percent);all194matches146/113. Zero-inclusive153MaskIoU0.467224->0.599371;paired87referenceIoU0.821670->0.823097,all87retained. Relative/per-frame/per-class/pairedmask/runtimegatespass;FAILMaskabsolute75percentrecall,5ppFastergap,and+22eligible-unassignedbudget(+44/+59). Moreoutputsnotprecision;all194unassignedgrowth+37/+59. Descriptiveposthocknowntrainbboxoverlaproadlabels6->7Faster/8->9Maskon10trainobservations,notexhaustiveFP/newaccuracy/newtrial. No classremap/thresholdchange/app/finalpromotion. Independentarchiveverificationreproduces153maskIoUs/11bit-identicalreferenceprefixes;343softwaretestspassincluding7tilecases/50seededinversefixtures. Onecompletedtrial76->77,wakeups52/source60/next100-runcheckpoint100/noactivejobs. Originalweights/media/frozenSGmethods/consumedclaimsunchanged. Latest56officialSGsnapshots/5492genuinelearnedforecasts/5originsmetadatahealthy;no learnedtargetscoring. Rollingpersistence49788matches/MAE5.138467spaces,distinctcohort. Nextcollectionafter14:42:43UTC;learnedfinalcloseduntil27October10:51UTC. Nextunassigned/semanticconflictanalysisfromsavedartifactsorfreshparking-region/negative-sourcequalification;donotrepeatcropgrids. Guide:docs/UVG_NATIVE_DETAIL_GUIDE.md;card:models/uvg_tile_development.json.

## 26 October 2026 / rejected mask suppression and inspection-only export

Oneprespecifiedarchived-real-maskcomponentcandidatecompletedin0.968secondswithzeroneuralcalls. Same-classcontainment(.85mask/.8box/min16px)removed26cropadditionsfrom209totalpredictionsbutlost2correctcars:113->111/153eligibleand113->111/194all;car107->105/truck6unchanged. Zero-inclusiveMaskIoU0.599371->0.590373,paired113IoU0.811538->0.799354;preservation/qualitygatesFAIL. Frame361car18/frame600car19tightvalidoutputsreplacedbybroaderunmatchedboxes. AutomaticruleREJECTED;no threshold/classchange/appintegration/finalaccess. Derivedinspection-onlyfallbackretainsall209originalpredictions/masksunchanged,53reviewrecords/86flaggedoutputs/automaticremovals0,notnewaccuracyorconfirmedduplicates. Counterexamples/figuresandallfailedmetricsretained;153maskIoUsindependentlyrecomputed.355softwaretestspass(8automatic+4reviewcasesand25seededadjacent-maskfixtures). Onecompletedtrial77->78,wakeups53/source60/next100-runcheckpoint100/noactivejobs. Originalweights/frozenSGmethods/consumedclaimsunchanged. Latest57officialSGsnapshots/6630genuinelearnedforecasts/6originsmetadatahealthy;no learnedtargetscoring. Rollingpersistence50985matches/MAE5.137158spaces,distinctcohort. Nextcollectionafter15:13:14UTC;learnedfinalcloseduntil27October10:51UTC. Nextfreshparking-region/negative-sourcequalificationortraining-onlyPKLotregionhypothesis;stopheuristicgridsononeclip. Guide:docs/UVG_MASK_REVIEW_GUIDE.md;card:models/uvg_mask_duplicate_development.json.

## 26 October 2026 / bounded source qualification and failed view compatibility

Implemented bounded ZIP metadata and README validation with explicit individual-content admission guard. NDISPark official API declares ODC-BY database licence; individual image/annotation rights remain unqualified. Verified271entries/259JPEGnames(112TRAIN/30validation/117test),READMECRC61306bytes;no wholeZIP/MD5verification,completeJPEGacquisition,pixeldecode orsemanticlabelaccess. Initial65536byte tail includes39021noncentralbytes retainedopaque;notallacquiredbytesaremetadata. Primarylicencescope/READMEtest-count-only limitation documented. Separate offline revalidation0.203s passes6checks afterexplicitpriorresearch exposure;one completed trial. Independent prespecified PKLot TRAIN/DEV viewcheck10.016s uses6TRAINreferences/24DEVimages,zeroXML/final/neuralreads:1/16matchingcamera accepted,0/32wrong-camera accepted,48/48syntheticchangedview rejected. Usability gateFAIL;noapppromotion/thresholdretuning. CameraIDsnotmanualposecertification;syntheticfixturesnotrealrelocationtruth. Saveddiagnostic43/48matchingreferencepairs lackenoughmatches;causenotestablished. All369softwaretestspass(14new);originalZIPcommentfixturefailurepreserved. Originalproductionweights/frozenSGmethods/consumedclaimshashesunchanged. Two distincttrials78->80,wakeups54,62sources,next100-runcheckpoint100,noactivejobs. LatestofficialSGsnapshot58at17:09after146mingap:0newpersistence matches,total50985/MAE5.137158spaces;1327newbaselineforecasts. Learned0new(stalepriorcontext),6630genuineforecasts/6originsmetadatahealthy,unscoreduntil27Oct10:51UTC. Missing15:13/15:43/16:13/16:43observationsnotinvented;nextcollectionafter17:39:57.962120UTC. Guides:NDISPARK_QUALIFICATION.md;VIEW_COMPATIBILITY_STUDY.md. Genuineprojectcompletionstillpending.

## 26 October 2026 / complete export transactions and resumed issuance

Fixed concretepartial-exportbugs:injectedimageinterruptionleftpartialoverlay,unsupportedJSONleftorphanPNG,andNaNwaspreviouslypublished. Originalsource/reproductionretained. Imageandarchivedforecast exports nowpreflightstrictfiniteJSON/vector-countagreement,writeownsame-parentstaging,verifyPNGandpayloadhashes,publishcompletedirectorybyrename,andcleanonlyownedfilesonhandledfailure/cancellation. Existingexportsneverreplaced;previewhasseparatehash. Thirteensyntheticfault/integritycases pass;actualhiddenTkexports8original/75later-datearchivedwindows retainmethod/CSV/JSON/plot/provenance. Zeroforbiddennormalraw/processed/split/networkattempts;oneexplicitrawprobe denied. Actuallater-datePNGvisuallyreviewed. One10.070secondcompletedintegrationtrial80->81;notperfixture/window/test. Full382softwaretestspass. No model/accuracy/finalrescore/rawholdoutaccess,originalweights/frozenSGmethods/consumedclaims unchanged. Oldofflinepackagespreserveddonotcontainpatch;no power-loss/manualUI/newmachine/physicalofflineclaim. Wakeups55/source62/next100-runcheckpoint100/noactivejobs. Source-compliant17:40UTCofficialsnapshot59adds1178previouslyfrozenpersistenceoutcomes:52163total/MAE5.055691spaces;1219newbaselineforecasts. Learned1113newgenuinepre-targetforecasts,7743total/7originsmetadatahealthy;unscoreduntil27Oct10:51UTC. Nextcollectionafter2026-10-26T18:10:12.825280+00:00. Earliergapsremainmissing. Guide:RESULT_EXPORTS_GUIDE.md;exactprotocol:FORECAST-DISPLAY-EXPORT-20261026T174434533261Z.

## 26 October 2026 UTC / offline refresh remains incomplete after isolated bootstrap repair

A new451-file selected payload preserves an exact prior02:30UTCofficial snapshot whose receipt/provider predate reserved10:00UTCforecast origins;selector hashes opaque bytes,does not decode pendingtargets. Initialfreshcopyfailedensurepipbootstrap;originalchilddetailswerenotcaptured,causeunconfirmed. Revisedinstallerusesexplicitisolatedbootstrap,localTEMP/TMP,capturedlogs,no pipcache andexistingno-index/hashlock. Secondcopyfreshinstallandactualhiddenappchecks pass;Jupyterchecktimesout,andcleanupwaitalsoexpires. No completedkernel/notebookacceptance;INCOMPLETE remains,READYabsent. Independentdeferredcomponent5.094seconds passes13synthetictransactioncases,107exactversion/localdistributionchecks andexisting-venvoverwrite refusal. These fixtures/metadata are not model accuracy. CurrentpackageNOTpromoted;earlierverifiedpointer unchanged. Scopedcase-insensitiveCIMinventoryfound0matchingpackageprocessesat18:29UTC;noneforciblyterminated. DefaultCIMreadwasOS-denied;authorizedscoped elevatedverification succeeded,noapproval-review rejection. All388softwaretestspass(sixnewselector/environmentfixtures). Three completedtrials81->84:bootstrapfailure,partialbuild/Jupyterfailure,distinctdeferredcomponent;notperwheel/test/frame. Wakeups56/source62/next100-runcheckpoint100/noactivejobs. Originalweights/claims/frozenSGmethods unchanged;no finalreplay.60officialSGsnapshots;1082newrollingpersistenceoutcomes,53245total/MAE4.983567spaces;1141newbaselineforecasts.1001newgenuinelearnedforecasts,8744total/8originsmetadatahealthy,unscoreduntil27Oct10:51UTC;8loggedoriginsnotfinalmatchedcoverage. Nextcollectionafter2026-10-26T18:40:32.285498+00:00. Nextdiagnosekernelinexistingfreshenvwithnewboundedcontroller/phase+PIDevidence;do not reinstall/repeatdetectors. Studentguide:OFFLINE_REFRESH_EXPLAINED.md;mastery/physical/newmachine/manual/officialacceptance remainunassessed.

## 26 October 2026 UTC / copied notebook recovered with approved local loopback

Instrumented120-second diagnosticpreservesstack/phase/PIDevidence:importsfinish,butexecutionstallsbeforekernelstartinWindowsasyncio_fallback_socketpair.accept. Automaticdeadlineendeddiagnostic;CANCELmarkerwaswrittenAFTERitsfinishedtimestampanddidnotcausestop. ConservativependingPIDstatewasretained;latercase-insensitiveauthorizedCIMcheckfound0ownedprocesses. Separateprespecifiedapproved-local-loopbacktrial runsUNCHANGEDfrozencopiedverifier successfullyin18.187seconds:realcopiedkernel,5codecellsincluding1diagnostic,1inlinePNG,0savederrors;sourcecells/notebook/payloadunchanged. Controller/kernelPythonfallback/nonloopbackguarddenials0;localRPCallowed. No install/modelinference/fitting/finalorprospective-targetread inrevalidation. NewREVALIDATION_ACCEPTANCE linksprior107install/app/13faultcases/107versionproofsbyhash;initialfailedreportsremainfailedandINCOMPLETEmarkerretainedundernewname. NewREADY/latestpointerselect451-filecopywithtransactionalexports;olderpackages/pointers preserved. Notphysicaloffline,newmachine,visible/manual/student/officialacceptance.388softwaretestsremainpassed;two distincttrials84->86,notperphase/cell. Wakeups57/source62/next100-runcheckpoint100/noactivejobs. Sourcecompliant18:41officialsnapshot61adds1040rollingpersistenceoutcomes:54285total/MAE4.911725spaces;1262newbaselineforecasts.1030newgenuinelearnedforecasts,9774total/9originsmetadatahealthy,unscoreduntil27Oct10:51UTC;loggedoriginsnotmatchedfinalcoverage. Nextcollectionafter2026-10-26T19:11:01.539174+00:00. Resumeindependentvision/data/reportwork;do notrepeatready-packettestsforcounts.

## 27 October 2026 IST / current group-role audit and seven-page evidence addendum

Metadata-onlyauditreconcilesallsixearlierprovisionalPKLotgroups:3development-exposed/3consumedfinal/0unaccounted/0newqualifiedfinalgroups. Claimstatusconsumeswholecamera/dateeveniffailed;frozenunopenedreservationflagsdonotoverrideclaims. No pixels/XMLsemantics/archivebodies/modelcalls. Scopeonlyearlier6groups,notproofnofuturedataexists. Fournewsyntheticgroup-identity/claimtests;full392softwaretestspass. Createdseparate7-pagePDFaddendumwith17hash-boundsource snapshots,62sourceIDs,2saved-metriccharts;all7renderedpagesvisuallyreviewed,0out-of-margincharacters,requiredmetrics/pending/failuretextchecks pass. Itpreservesconditionalregion0.910vsresearchCNN0.803limits,failedrainyPUCPR13/14retention,realtraffic113/153maskadmissionfailure,Birminghamfinal31.72vs39.07MAE,andSGdevelopment6.310vs6.958withprospectiveperformanceunscored. Earlier12-pagev003PDF/TeX unchanged;newdocumentisanaddendum,notofficialsubmission. FirstauthoringattemptlackedmatplotlibinbundledPDFruntime;source/errorretained,chartsdelegatedtoexistingprojectruntimewithoutinstallingpackages. Internalrepairnotadditionaltrial. Two completedtrials86->88:updated-roleauditandfinalartifactQA;notperpage/hash/test/frame. Wakeups58/source62/next100-runcheckpoint100/noactivejobs.62officialSGsnapshots;19:12collectionadds1082rollingpersistenceoutcomes:55367total/MAE4.861091spaces;1091newbaselineforecasts.990newgenuinelearnedforecasts,10764total/10originsmetadatahealthy;nolearnedtargetmatching/error/coverageuntil27Oct10:51UTC. Nextcollectionafter2026-10-26T19:42:33.568681+00:00. NewPDFfreezes87trialsbeforeitsownQA;currentledger88. Rights/independentfreshvisionlabels andphysical/manual/newmachine/student/universityacceptance remainopen.

## 27 October 2026 IST / fresh licensed ACPDS development admitted; TEST remains closed

Author source SRC-DS-021 is pinned to repository revision17da2c8b33055be8019483260f0efbcbdfda0478. The paper explicitly grants MIT for dataset/code/models;notice retained. Whole author TEST/all lots/views/aliases was reserved before annotation decoding. Bounded ETag/HTTP206 acquisition verifies annotation ZIP descriptor,CRC and expanded size;380796292-byte wholearchive not downloaded/checksummed. TRAIN231images/7842spaces(3940occupied,3902vacant),VALID35/1904(831occupied,1073vacant),normalized coordinates0..1;no cross-partition duplicate filenames. Archive293image names leaves27 default-closed,not a decodedTESTlist. No pixels,models or TESTsemantics opened. Unique-lot separation is author evidence,not independent geolocation/date audit;no CCTV/automatic-region/generalization claim. Seven new synthetic admission tests;full399softwaretests pass. Two internal adapter-format repairs preserved:header-only ZIPflag8 rejection and integer-only rejection of explicit publisher booleans;original protocol plus chained pre-resumption amendments retained. They are one completed qualification trial88->89,not extra counts. Successful cached revalidation callback1.601seconds excludes earlier acquisition/discovery/repair work. SourceIDs63,wakeup59,next100-runcheckpoint100,noactivejobs. Latest actual Singapore22:39UTCsnapshot63;19:12->22:39gap remains missing.1199newpersistence forecasts/0newmatches;55367pastoutcomes/MAE4.861091spaces unchanged. Learned issuance0(newprevious-observation/staleness exclusions),10764forecasts/10origins metadatahealthy and unscored until27Oct10:51UTC. Nextcollectionafter2026-10-26T23:09:27.851456+00:00. Next implement bounded TRAIN/VALID image allowlist acquisition and geometry/class-convention audit before occupancy baseline;keep wholeTESTclosed. Originalweights/frozenmethods/claims/reports untouched;official/manual/student/physicaloffline acceptance remainsopen.

## 27 October 2026 IST / real ACPDS images qualified; unchanged classifier fails source-shift gates

Exact selective ZIP ranges acquired 3 seeded TRAIN and all 35 VALID photographs (51,978,829 network bytes); 38 original JPEGs decode at 4000 by 3000 with orientation 1. All supplied polygons validate using the author's normalized x*(W-1),y*(H-1) convention. All three TRAIN overlays were visually checked for coordinate/class convention; True marks occupied ground spaces and False vacant. Cars project beyond ground footprints and occlusions are visible; this is a possible source-shift factor, not a proven cause. No complete TEST member was acquired or decoded. Five new synthetic ZIP admission/range/descriptor/CRC/name/budget tests bring the full software suite to 404 passing tests.

The prespecified unchanged ResNet18 baseline evaluated all 1,904 labelled VALID spaces in 146.537 seconds: 1,704 correct (89.4958%), confusion [[961,112],[88,743]], image-average accuracy 90.6248%. Seventeen of 35 images fell below 90%. At the fixed .25/.75 uncertainty thresholds, 62 of 831 occupied spaces were confidently called vacant (7.461%), and 115 of 1,904 predictions were uncertain (6.040%). Overall accuracy, every-image accuracy and false-vacancy gates failed; the uncertainty gate passed. This is a crop-classifier development result with supplied geometry, not detector fusion, automatic segmentation, continuous camera or final-test accuracy. No weights, thresholds or production behavior changed. Runtime includes concurrent software-test CPU activity and is not a deployment speed benchmark.

Two distinct completed trials raised the counter from 89 to 91: real-image/geometry qualification (68.812 seconds) and unchanged cross-source baseline. No per-image/test/frame counts. Source IDs remain 63; wakeups completed 60; next separate 100-run live checkpoint is 100; no active jobs remain. The official 23:09 UTC Singapore snapshot is number 64, adding 1,132 rolling persistence outcomes (56,499 total; MAE 5.171330 spaces) and 1,276 baseline forecasts. Another 1,073 genuine learned forecasts were frozen, giving 11,837 forecasts and 11 origins with healthy receipts. Learned matching, coverage and error remain unscored until 27 October 10:51 UTC. Next collection after 2026-10-26T23:39:57.194205+00:00. All frozen methods, original weights, consumed claims and whole ACPDS TEST reservation remain unchanged.

Next acquire the remaining 228 TRAIN images with explicit resumable receipt verification, then prespecify one bounded TRAIN-only adaptation with PKLot development retention and validation early stopping. Do not adjust thresholds from this baseline or open TEST without a tested durable whole-partition claim. See docs/ACPDS_BASELINE_GUIDE.md. Official documents, student demonstration, visible manual dialogs, physical disconnection and new-machine acceptance remain open.

## 27 October 2026 IST / one bounded source-balanced head trial and complete TRAIN acquisition

All 231 ACPDS training images and 35 validation images are now qualified, with 7,842 training and 1,904 validation spaces. Routine resumable acquisition reused 38 receipted members and acquired 228 TRAIN members (295,388,491 new network bytes in 355.386 seconds). No additional experiment count was added for acquisition or individual images. All original bytes, exact range/ETag/CRC checks and provenance remain intact; whole TEST stayed closed. Ten new synthetic tests check receipt identity/hash/role reuse and paired vacancy retention. The full software suite passes 414 tests.

One prespecified experiment freezes the original ResNet18 backbone and fits its linear head with half the training loss mass from each source. It combines 7,842 ACPDS and 10,104 PKLot training spaces. Validation uses 1,904 ACPDS spaces and 2,028 reused PKLot development spaces, with no consumed camera/date overlap. The fixed selection rule blends per-image ACPDS and per-camera PKLot cross-entropy; epoch zero remains eligible. The trial completed 8 epochs and selected epoch 5. ACPDS hard accuracy changed from 89.4958% to 93.0672%, and confident false vacancies from 62 to 31 among 831 occupied spaces. PKLot development accuracy changed from 97.7318% to 99.4083%, with confident false vacancies 6 -> 2. Overall development gate: False. Failed checks: new_overall_accuracy, new_every_image_accuracy, new_false_vacancy. Exact counts, curves, predictions, per-image/camera results and identity-based per-date retention are preserved. No thresholds, production weights or final cohorts changed.

Feature extraction and training took 742.626 seconds in this invocation, with image checkpoints and saved optimizer/random state. Original ACPDS probabilities reproduced within 2.980232238769531e-07 before fitting; checkpoint state round-trip and unchanged backbone verified. These are development results with supplied polygons; no final, detector-fusion, continuous-camera or automatic-region claim follows. The separate candidate is models/checkpoints/acpds_balanced/ACPDS-BALANCED-HEAD-20261026T234728842213Z/candidate.pt. The completed counter increased 91 -> 92 for this one trial; wakeups completed 61, source IDs 63, next 100-run live checkpoint 100, no active jobs.

The actual 23:40 UTC Singapore observation is snapshot 65. It adds 1,136 rolling persistence outcomes (57635 total; MAE 5.388913 spaces) and 1,267 baseline forecasts. Another 1,129 genuine learned forecasts were frozen; 12966 forecasts across 12 origins have healthy receipts. Learned targets and matching/error/coverage remain closed until 27 October 10:51 UTC. Next collection after 2026-10-27T00:10:46.583246+00:00. Independent segmentation ground truth, physical/manual/new-machine/student demonstration and university documents remain open. See docs/ACPDS_ADAPTATION_PROTOCOL.md.

## 27 October 2026 IST / rejected raster translation and exact crop-cache validation

The first implementation candidate moved the polygon mask into a local drawing canvas. Five unit tests and 2,000 synthetic fixtures passed, but real TRAIN image GOPR6550.JPG, slot 9, differed in seven RGB channel values. The completed early-rejection trial is recorded as failed, with the original exception log, source, protocol and three finished image proofs (45 crops) preserved. No failed cache was selected. Its 6.928-second duration is the measured outer command wall time including startup. The small pixel difference was treated as an equivalence failure; no model was rerun to excuse it.

The revised helper retains the original full-size polygon mask and restricts only RGB paste/copy work to the bounding box. It checks all 9,746 real development crops across 266 images plus a new 2,000-case seed-158 synthetic suite. All real crops match the original bytes exactly; all cache files round-trip exactly. Measured crop-function time was 670.223 seconds for the reference and 51.699 seconds for the revision, a ratio of 12.96. The gate required at least two. Comparison order alternated, and image decoding, hashing and NPZ encoding were excluded from those function timers. Total invocation time was 761.462 seconds. These are process-local preparation timings, not full application inference performance or measured process RSS. A full-size mask allocation remains. Cache implementation gate=True.

The validated cache contains 7,842 TRAIN and 1,904 validation crops, with explicit labels, original image/layout hashes and per-crop/file SHA256. It occupies 99564816 compressed bytes. Candidate cache: data/processed/acpds_exact_crop_cache_v2/EXACT-CROP-CACHE-V2-20261027T001729204282Z/cache_manifest.json. It enables later bounded model work with unchanged crop inputs. The original application helper, production weights, best research checkpoint and every final reservation remain unchanged. Scientific accuracy was not evaluated; the earlier 93.0672%/31-false-vacancy model still fails source readiness.

Eight new synthetic regression/contract tests bring the full software suite to 422 passing tests. Two distinct implementation trials raise the completed counter 92 -> 94: one rejected translation and one revised full-mask/local-RGB validation. Individual fixture cases, crops and cache files are not runs. Wakeups completed 62, source IDs 63, next separate 100-run live checkpoint 100, no active jobs. Current primary CNR publisher access timed out and NDIS publisher text established no new content-rights grant; those source images remain unadmitted. No new source or model accuracy claim follows.

Official Singapore snapshot 66 adds 1,167 rolling persistence outcomes (58,802 total; MAE 5.571953 spaces) and 1,212 baseline forecasts. Another 1,113 genuine learned forecasts were frozen, giving 14,079 forecasts and 13 origins with healthy receipts. Learned targets, matching, coverage and error remain closed until 27 October 10:51 UTC. Next collection after 2026-10-27T00:41:09.473176+00:00. Next prepare hash-checked old PKLot RGB training/retention crops, then design one bounded last-block representation adaptation. Keep TEST closed and avoid repeating a parameter grid. See docs/EXACT_CROP_CACHE_GUIDE.md. Official/manual/student/physical-offline/new-machine acceptance remains open.

## 27 October 2026 IST / last-block adaptation improves accuracy but fails vacancy safety

Routine PKLot preparation verified all 12,132 crops byte-for-byte against the original function in 91.309 seconds. It matches the prior feature-row identities, includes 10,104 TRAIN and 2,028 reused development spaces, excludes consumed camera/date groups and keeps unknown labels excluded. It adds no experiment count. Four new synthetic tests verify exact batched normalization, trainable-parameter scope, frozen BN/lower state through a gradient step and invalid input/model refusal. All 426 software tests pass.

One bounded representation experiment warmed from the prior head, trained only layer4 convolution weights and fc, and froze every lower parameter and every BN affine/buffer. It completed four epochs in 467.112 seconds, within the 900-second invocation budget. Epoch three had the lowest prespecified validation loss; epoch four worsened and was not selected. Initial RGB probabilities matched the warm model within 1.1920928955078125e-07. Lower/BN state equality and saved-model round-trip passed. Training/validation cohorts, source balancing, crop inputs and thresholds stayed fixed.

ACPDS validation hard accuracy rose from 93.0672% to 95.8508% (1,825/1,904 correct), and confident false vacancies dropped 31 -> 14 among 831 occupied spaces. The remaining 1.6847% exceeds the frozen 1% limit. Two of 35 images remain below 90%: GOPR6593 38/43 (88.3721%) and GOPR6709 22/25 (88%). Source uncertainty is 87/1,904 (4.5693%). On reused PKLot development, accuracy rose 99.4083% -> 99.7041%, but confident false vacancies worsened 2 -> 5 while uncertainty fell 20 -> 0. Every previously correct confident vacancy stayed correct/confident. Aggregate accuracy gains therefore do not satisfy the safety gates. Failed checks: new_every_image, new_false_vacancy, old_false_vacancy. Overall development gate remains FALSE.

The separate candidate models/checkpoints/acpds_last_block/ACPDS-LAST-BLOCK-20261027T004612152849Z/candidate.pt has SHA256 7ea60239e81e83b4ba397c39498bb4c10861564bd63a6bf44d1eb75cedd85b2f. Both this checkpoint and the prior head remain preserved. Production weights and all final reservations remain unchanged; no detector-fusion, real-video, final-test or automatic-region accuracy is implied. One completed trial raises the counter 94 -> 95; epochs, crops and fixtures are not runs. Wakeups completed 63, source IDs 63, next separate 100-run live checkpoint 100, no active jobs. See docs/ACPDS_LAST_BLOCK_GUIDE.md.

Official Singapore snapshot 67 adds 1,125 rolling persistence outcomes (59,927 total; MAE 5.721895 spaces) and 1,273 baseline forecasts. Another 1,101 genuine learned forecasts were frozen, giving 15,180 forecasts and 14 origins with healthy receipts. Learned targets, matching, coverage and error remain closed until 27 October 10:51 UTC. Next collection after 2026-10-27T01:11:48.636856+00:00. Continue independent real-traffic/application/region-data work; avoid another parameter grid on this reused validation set. Official documents, physical/manual/new-machine and student acceptance remain open.

## 27 October 2026 IST / bounded occupancy assignment integrated

Qualified original-raster bounded slot bitmaps against independent dense reference:
2,000 generated cases, three TRAIN geometry cases with generated detector inputs,
and an isolated fixed 1920x1080/96-slot/24-box fixture all preserve exact output
dictionaries. Additional sampled peak RSS fell207,122,432->9,101,312bytes (95.6%)
on that fixture; retained slot bitmaps199,065,600->1,855,488bytes; assignment
8.351->0.165seconds. These are software fixtures, not camera accuracy or bounds
on model/MaskRCNN output memory. Qualification is frozen at145bdc7.

Working VisionEngine now delegates assignment to this qualified helper; original
dense reference remains. Six added contract tests bring the full suite to432/OK.
Actual FasterRCNN640+original classifier then processed three already exposed
4000x3000TRAIN photos/83spaces: identities, counts, ordered IDs, uncertainty rules,
unique vehicle support, unchanged model hashes and full-size RGB overlays pass.
Three detector and three classifier calls,15.814second worker duration, sampled
peak1,275,285,504bytes below1.5GiB cap. All three previews visually inspected.
No label accuracy, visibleGUI/native-dialog/newmachine/physicaloffline acceptance.

Parent reporting failed after successful inference on a duplicate duration field.
Original code/protocol/stdout/error/worker outputs remain immutable; separate
hash-checked recovery registers this same trial once with NO repeated inference.
Wall timestamps are explicitly derived from worker-file metadata and measured
duration; unavailable parent duration is not invented. Future runner repaired.
Two distinct trials95->97, not per case/frame/test/modelcall. Wakeups64/sourceIDs63,
next separate100-run live checkpoint100,noactivejobs. Original production weights,
frozenSGmethods and finalreservations unchanged. Last-block classifier remains
research only:source95.8508% hardaccuracy but14confidentfalsevacants>1%limit,
twoimagesbelow90%,oldfalsevacants2->5. No model promotion or new final access.

OfficialSGsnapshot68 at01:13:37UTC adds1,178rollingpersistenceoutcomes:
61,105total/MAE5.802520252025203spaces and1,140baselineforecasts. Another1,025
genuine learned forecasts give16,205forecasts/15origins/15receiptedbatches;no
learned target decoding/matching/coverage/error until27October10:51UTC. Next
collection after2026-10-27T01:43:37.918904+00:00; earlier gaps remainmissing.
Next preregister one fixed-threshold Faster/classifier DEVELOPMENT fusion study,
with memory/time caps and false-vacancy/uncertainty gates;avoid further optimizer
or threshold grids on35reusedVALID. Existing451-fileREADYofflinecopy predates
this patch;refresh at a new integration milestone. Guide:OCCUPANCY_MEMORY_GUIDE.md.
Official documents/manual/student/physicaloffline/newmachine acceptance open.

## 27 October 2026 IST / fixed-method detector fusion exposes review costs

One sealed development diagnostic processed all35already-exposed ACPDS VALID
photos/1904spaces (831occupied/1073vacant). Original and last-block classifier
scores were replayed from hash-bound earlier predictions,with exact supplied
slot geometry equality verified. No classifier forward/fitting. Actual unchanged
FasterRCNN640/confidence0.5 ran35times;application0.12overlap/0.25/0.75states stayed
fixed. Both methods reported independently,no winner/threshold chosen.

Original fusion reduced confident unsafe vacancy62->33 by sending29occupied
spaces to review,butalso38previouslycorrect vacantanswers to review. Uncertainty
182/1904=9.5588%;correctvacancyretention901/939=95.9531%,yet8imagesbelow90%.
The remaining33/831=3.9711%unsafevacancies exceed1%;readinessFAIL.
Research last-block fusion reduced unsafe vacancy14->3 (0.3610%of831) and
uncertainty155/1904=8.1408%,passing those absolute limits. However,57correct
vacancies were also sent to review:967/1024=94.4336%retention below95%,with
8imagesbelow90%;readinessFAIL. Warningsareuncertain,notcorrectoccupiedanswers.
Bothfailed results are preserved;no model/threshold/production promotion.

Seven sequential5photochildren checkpointed every frame;total183.217seconds,
maximum sampled workerRSS1297002496bytes below1.75GiBcap.35detector/0classifier
calls constitute one trial97->98,not perframe/method/batch. Five added meaningful
denominator/state/identity fixtures bring fullsuite437/OK7.000sec. Initial test
launcher omitted src importpath;error preserved,corrected launch passes without
changing sealed study code. Protocol prepared01:42UTC;actual inference started
03:39UTC after executiongap. Intermediate heartbeat triggers are not experiments.

Generated source-bound student explanation and3deterministic first-qualifying
diagnostic PNGs;all3visuallyinspected. Remainingunsafe example shows occlusion;
vacant-label example shows projected neighboring box overlapping supplied ground
polygon. These are observations,not independently verified labels or causalproof.
Labels retained. No final/video/exhaustivedetector/learnedregion/GUI/newmachine/
physicaloffline/studentmastery claim. See reports/acpds_fusion_ACPDS-FROZEN-FUSION-20261027T014230468943Z/EXPLANATION.md,
models/acpds_frozen_fusion.json and visual_review.json. Originalweights/frozenSG
methods/TESTreservations unchanged. Next geometry hypothesis should use admitted
TRAIN only;do not retune overlap/crop/model gates on35reusedVALID. Existing451file
offlineREADYcopy still predates memorypatch c004db7.

Source-compliant officialSGsnapshot69 at03:39:46UTC follows146.148minute gap;
no backfill.0newmatchedpersistenceoutcomes,61105total/MAE5.802520252025203spaces;
1299newbaselineforecasts.0newlearnedforecasts because prior context unavailable
or stale;16205forecasts/15origins/15receiptedbatches metadatahealthy. Learnedtarget
decoding/matching/coverage/error staysclosed until27Oct10:51UTC. Nextcollection
after2026-10-27T04:09:46.789307+00:00. Wakeups65/sourceIDs63/nextseparate100runlivecheckpoint100,
noactivejobs. Projectofficial/manual/physical/newmachine/student acceptance open.

## 27 October 2026 IST / reject bottom-center support on TRAIN geometry

Tested one fixed alternative to full-box overlap: floored bottom-center point
inside the original rasterized supplied bay; out-of-image point stays unknown,
with one detector per bay. No clipping, threshold variants, crop or model tuning.
Seed164 sampled24 of228admitted TRAIN photos after excluding3prior TRAIN API
previews. All images/labels participated in earlier representation training;
this is a component TRAIN diagnostic, not independent camera/model accuracy.
No classifier forwards or fitting; actual fixed Faster640/confidence0.5 ran24times.
No VALID/TEST photos or label semantics were read by this trial.

Across757bays (357occupied/400vacant), false support of vacant-label bays WORSENED
46->61, while supported occupied-label bays fell269->190. Only169of269originally
supported occupied bays retained support (62.8253%);100were lost and21new occupied
bays supported.20of24images fall below90%paired retention. Vacant support removed
on29old bays was outweighed by44new false supports. Cohort-size gate passes;
false-support reduction/globalretention/per-imageretention gatesFAIL. No support
never proves vacancy; occupied bay label does not verify physical vehicle identity.
Candidate remains separate research helper,not imported by production VisionEngine.
Do not sweep point shifts/thresholds against this rejection or retune35reusedVALID.

Six isolated4photochildren checkpointed each frame;112.642seconds total, maximum
sampled childRSS1283440640bytes below1.75GiBcap. Five meaningful support/identity/
boundary/denominator tests bring full suite442/OK7.317seconds. Three fixed-order
TRAIN crops and source-bound student explanation created; all3visuallyinspected.
They illustrate a removed warning,a lost occupied support and a new support whose
physical vehicle association is unverified; no relabeling/causalproof. See
reports/anchor_support_ANCHOR-TRAIN-20261027T041309240270Z/EXPLANATION.md and visual_review.json.
One completed experiment98->99,not perphoto/batch/test/preview;wakeups66/sourceIDs63,
noactivejobs. Originalweights/frozenSGmethods/finalreservations unchanged.

OfficialSGsnapshot70 at04:11:11UTC adds1163later rollingpersistence outcomes:
62268total/MAE5.791128669621635spaces and1204newbaselineforecasts.1113genuine
learned forecasts newlyfrozen give17318forecasts/16origins/16receiptedbatches;
metadatahealthy,learnedtargetdecoding/matching/coverage/error remainsclosed until
27Oct10:51UTC. Nextcollection after2026-10-27T04:41:11.029643+00:00;earlier146mingap notbackfilled.
Next update the outdated offline demonstration at a genuine application milestone,
using safe pre-origin snapshot selection and approved loopback for real copied
Jupyter;old postvalidators have date/package bindings and need a new parameterized
controller. Preserve old451-fileREADY/failures. At actual100completed trials perform
the separate required live checkpoint;pending100 now,no filler trial. Physical
offline/newmachine/manual/student/university acceptance remainsopen.

## 27 October 2026 IST / current copied package accepted and100-run checkpoint passed

New selected copy outputs/offline_demo_packages/COMBINED-DEMO-20261027T044747395249Z passes all5stages in299.063seconds:468payloadfiles/
809047000bytes,107original wheels/notices,NEW package-local environment installed
no-index/hash-locked,both actual hidden detector routes/exports/semantic separation/
archived forecast identities/SVD/video,copied notebook08actualkernel/1PNG,13synthetic
transaction fault cases and generic current-copy acceptance. FixedTRAIN sample
counts68occupied32vacant0uncertain/100 remain identical for bothdetectors;not new
accuracy. Current bounded occupancy_patches import/sourcehash verified. All107locked
versions match;existing environment overwrite refused. Normal Python audit denials0;
separate original-workspace/DNS negative controls blocked. Jupyter used approved
local loopback while external/fallback guards remained active;native extensionIO
and physical networking remain outside audit coverage.

Old451-fileacceptedpayload,READY/revalidationacceptance and originalfailed COMBINED
report all remain unchanged;previous pointers archived. Preflight initially assumed
oldpointer referenced COMBINED_VALIDATION;actualREADY explicitly references later
REVALIDATION_ACCEPTANCE,now verified by exact hash. Four new pure acceptance tests
bring suite446;initial Windows temporary-folder cleanup error preserved. Workspace
TEMP launch passes446/6.769sec;new reproducible run_project_tests.py passes446/9.283sec.
These are context repairs and softwarechecks,not extra experiments. New copy retains
safe pre-origin saved SGsnapshot26Oct02:30UTC;no pending learnedtargets packaged.
Onlynotebook08/selectedassets included;full datasets/10other notebooks/baseOS absent.

Fresh copy is completed trial100. Separately required LIVE-MILESTONE-100 checkpoint
is completed validation101:one fresh official acquisition viaexisting immutable raw/
receipt/history mechanism,at least60secs afterpriorpoll.2428rawlotrecords ->2423accepted
rows/2005parks,5invalid bounds excluded,0acceptedduplicates,43.460442sec providerage.
Normalized per-checkpointCSV round-trip/hash passes. ActualhiddenTk table2423rows,
filter1row andprovider/path/age-status checks pass. Backend callback receives those
actualacquiredrows without second poll;no modelcalls or cameraGT. LearnedMAE and
comparison remain unevaluated because finalstudy closed. Lastscheduledmilestone100
passed,next200;not100%accuracy/certification. Counter99->101 fromtwo actualtrials,
not per468files/107wheels/5phases/2423rows/testcase. Wakeups67/sourceIDs63/noactivejobs.

72officialSGsnapshots. Routine04:42acquisition froze1063learnedforecasts;milestone
04:54:19 froze1170more.19551forecasts/18origins/18receiptedbatches metadatahealthy,
no target decoding/matching/coverage/error. Rollingpersistence63461outcomes/MAE
5.768897433069129spaces;milestone added49later matches. Nextcollection after
2026-10-27T05:24:19.588132+00:00;this supersedes older routine due. Finalclosure27Oct10:51UTC unchanged.
Originalweights,frozenSGmethods,consumedclaims and bestresearchcheckpoints unchanged.
Next expand earlier six-group PKLot role audit to complete archive metadata before
fresh segmentation cohorts/pixel access,or update dated presentation/student materials.
Physicaloffline/newmachine/visiblemanual/student/university acceptance remainsopen.
See CURRENT_OFFLINE_PACKAGE.md;authoritative reports/offline_demo_latest.json.

## 27 October 2026 IST / full PKLot roles and retrospective consumption repair

Completed one metadata integrity audit over12218validatedpairs/98canonicalgroups.
Original3860376865compressedbytes/indexchecksum match;4.741seconds. No image
decoding/XMLsemanticlabels/modelcalls/network in normal audit;image/socket negative
controls blocked. Initial roles50TRAIN/15DEV/6durableconsumed/6historicaltestprotected/
21metadataexcluded are preserved in immutable run.json. Follow-up explicit modelcard
test-date evidence identified5originalsegmentationtestdates plus older vision and
known-camera completed tests lacking newer claims. Three records added NOW,
explicitlyretrospective andnot priorpreregistration. Current groupstatuses50TRAIN/
15DEV/17consumed/16metadataexcluded;no automaticnewTRAIN/final admission. Existing
guard blocks22newcanonical/folderalias probes;unrelatedTRAINcontrol allowed. Prior
claims untouched,no scoredtest/pixel/XML replay. Visioncurrentcode/manifesthashes
differ fromoldcard andremain disclosed;oldexplicitdates/completed360test-sample
record/preservedcheckpoint supportconservativeprotection. No metric score values
inspected;othermatched historicalevalcode/checkpointmetadata corroborateconsumption.

Zero known cross-group image-hash aliases in inspectedmetadata,not proofnoneexist
in wholearchive;no exhaustive new per-image hashing. Zero protected-role overlaps
in inspectedrolemanifests. Historical eligible_date flags never override current
closure.16remaininggroups stayquarantined;this is not globaldataexhaustion orfresh
final qualification. Five meaningfulsynthetictests bring fullsuite451/OK6.719sec.
Pre-run aliasflag correction preserved one unexecutedprotocol;0extra runs. Follow-up
protectionrecords/probes are part of this audit,0extra experimentcount. Counter101->102,
wakeups68/sourceIDs63/next100-runmilestone200/noactivejobs. Selected468-fileofflinecopy
and original/bestcheckpoints unchanged. Guide:PKLOT_ROLE_LEDGER_GUIDE.md;currentledger
models/pklot_current_role_ledger.json;immutableauditmodels/pklot_full_role_ledger.json.

73officialSGsnapshots.05:22checkwasnotdue anddidnotpoll;actual05:25:56UTCcollection
adds2273later rollingpersistenceoutcomes:65734total/MAE5.810965406030364spaces and1248
baselineforecasts.1163genuinelearnedforecasts newlyfrozen give20714forecasts/19origins/
19receiptedbatches metadatahealthy. Learnedtargetdecoding/matching/error/coverage stays
closed until27Oct10:51UTC. Nextcollection after2026-10-27T05:55:56.101845+00:00. Source licensedaggregate
availability,notcameraGT/BirminghamSGvalidation. Next prepare strongerregiondata using
existingTRAIN groups with explicit target semantics/byte-alias checks,or resolve
quarantined source roles/new rights-qualified data. No legacytrainer overwrite,
oldfinal reuse orautomaticadmission. Physical/manual/newmachine/student/official
acceptance remainsopen;datedPDF/presentation stillolder snapshots.


## 27 October 2026 / qualified region dataset and next bounded experiment

Run REGION-DATA-V2-20261027T054847435415Z qualified 230 real PKLot pairs:
200 TRAIN/30 development, three existing cameras, 50 TRAIN/15 DEV date groups.
Seed168 sampling4/2perdate, RGB256x144 and nearest-neighbor source-bay-union
masks. All12417archive JPEGs were hashed as opaque bytes before selected decode:
12417unique hashes,0exact cross-group aliases. All17consumedfinal and16unresolved
groups remain excluded;no new group admission or protected pixel/XML decoding.
No replacement sampling,230exact NPZ round trips,0cache errors;22,314,729cachebytes.
Measured phase duration72.303sec after initial input/archive checks.460raw-asset
receipts,per-member/cache/source/split hashes,immutable manifest and three visually
reviewed TRAIN overlays retained. No model calls,training,accuracy or promotion.
Provided polygons are bay footprints,not exhaustive parking facility/occupancy
truth;exact byte uniqueness does not establish perceptual independence.

Five split-admission tests cover closed/unknown/transitive aliases,DEV protection,
duplicate bytes and reproducible role-constrained sampling. Fullsuite456/OK6.798s.
Post-run integrity checks verify690asset hashes/460receipts,all frozen inputs and
114unique registry IDs. Completed trial102->103;not perimage/hash/fixture. Wakeups69,
sourceIDs63,noactivejobs;milestone100 passed,next200. Selected468-fileofflinecopy
and all original/best/failed checkpoints preserved. See REGION_DATASET_V2_GUIDE.md,
models/region_dataset_v2.json and result dataset_manifest.json. Next seal a bounded
frozen-ResNet18/decoder experiment and DEV gates before fitting;compare original
U-Net and conditional TRAIN-only camera template on the same30DEV images. Static
views can favor geometry priors. No recipe/gates sealed and no training started.
Fresh final qualification,physicaloffline/newmachine/visiblemanual/student/official
acceptance remain open;dated PDF/presentation still older snapshots.

The05:54:56UTC collection check correctly skipped before05:55:56due;actual05:56:09
acquisition made74officialSGsnapshots.1101genuinelearned forecasts newly committed:
21815total/20origins/20receiptedbatches,metadatahealthy.1185new persistenceforecasts
and1135later baselineoutcomes:66869total/MAE5.81039046493891spaces. No interim
learnedtarget/matching/error/coverage;final closed until27Oct10:51UTC(16:21IST).
Next historycollection AFTER2026-10-27T06:26:09.022140+00:00. Routine collection/health
is not an extra experiment orcameraaccuracy;Singaporeaggregate data is not cameraGT.


## 27 October 2026 / image-only FPN development trial and archived lesson

REGION-FPN-V1-20261027T061402381508Z trained one separately saved candidate using
200qualifiedTRAIN/30DEVimages. Frozen ImageNet ResNet18/allBN plus32channel feature
pyramid/decoder,seed169,weightedBCE+Dice,AdamW0.001/batch8,noaugmentation,4CPUthreads,
max8epochs/patience3. Epoch7 selected by equal-camera meanDEV IoU. Measured phase
afterinitialchecks8.990s,sampledRSSpeak1462673408bytes;256245760featuretensorbytes.
Perbatch cancellation/optimizer/RNG/order checkpoints,900secondlimit and earlystop
implemented;completedrun refusesrerun. Original/best/failed weights preserved.

Paired common-cache DEVELOPMENT macro-cameraIoU0.5819598228590831 versusoriginal
0.2871514278284487;Dice0.7344997485795348,worstimageIoU0.4524064935993707. Candidate
camera means PUCPR0.612145/UFPR040.573749/UFPR050.559986. Original common256x144RGB
cache ->192x112nativeinput ->probability commongrid,not replay of priorfinal/native
appinput benchmark. FourgatesFAIL:meanIoU>=.80,eachcamera>=.75,eachimage>=.65 and
no>.05camera regressionfromTRAINtemplate. Improvement>=.02andcamera nonregression
versusoriginalPASS. No threshold/gate relaxation or apppromotion. Supplied bay
footprints,familiarcameras/reusedDEV,not occupancy/exhaustivefacility/freshfinalGT.

TRAIN-template conditionalmeans1/.283890/1;two cameras haveidenticalTRAIN/DEVmask
geometry,notperfectsceneunderstanding. UFPR04has3TRAINpatterns56/8/8images;DEVuses
one8-examplepattern. PosthocTRAIN-only36x64maskreconstructionIoU.898799 isnotproven
architectureceiling/newtrial. Decliningloss andpatternimbalance are next hypotheses,
notcausalproof. Sealalongerbudgettrialseparatelybeforelater sampling/resolution
changes;retainalladmissiongates andfreshfinalrequirement. All17consumed/16quarantined
PKLotgroups,ACPDS27TESTandwholeHighwayDrive remainclosed. No protectedpixels/XML
decoded;backbone/BN/input/protectedhashes unchanged;normalforbiddenaccesses0,negative
cacheprobe blocked. SourcesSRC-DS-001/SRC-MOD-003(existingterms),0newsourceIDs.

460softwaretests/OK7.786s coverfrozenBN/weights,decodergradients,TRAIN-onlytemplates
andcamera-weightedmetrics. Threepostscoringworstimagepanels visuallyreviewed. Actual
notebook12executes6codecells/sixarchivedinputs/3inlinePNGs andsyntheticIoUteaching
fixture;raw/prospective-read,project-write andexternalDNSdenialcontrols pass. First
defaultcontextstalledbeforekernellaunch;only2verifiedownedprocesses stopped,source
anddiagnosticsretained;localretry passed. No modelcalls/freshaccuracy/extra trial
fromlesson/diagnostics. Usermanual/studentmastery/physicaloffline/newmachine/official
acceptance remainsopen. Selected468filedemo unchangedandstillonlynotebook08.
GuideREGION_FPN_EXPERIMENT_GUIDE.md;cardmodels/region_fpn_v1.json;actualcheckslinked
byreports/region_fpn_lesson_latest.json. Count103->104,wakeups70,63sourceIDs,noactive
jobs;lastrequired100-runcheckpointpassed,next200. DatedPDF/presentationolder.

One due officialSGacquisition06:27:16UTC ->75snapshots.1067newgenuinelearnedforecasts:
22882total/21origins/21receiptedbatches metadatahealthy.1219newpersistenceforecasts
and1102laterbaselineoutcomes ->67971scores/MAE5.792926395080255spaces. No interim
learnedtarget/matching/error/coverage;closure27Oct10:51UTC/16:21IST. Nextcollection
after2026-10-27T06:57:16.494271+00:00;no earlypoll/backfill/neural/cameraaccuracyclaim.


## 27 October 2026 / controlled longer image-only training

REGION-FPN-DURATION-20261027T064327135442Z changed only maxepochs8->32 andpatience3->6.
Seed169,architecture,uniformTRAINsampling,loss/optimizer/normalization/data/threshold
andsixadmissiongates fixed. OriginalV1driver/card/source/checkpoint preserved. First
eighttrainingloss/DEVmacroIoU values reproduceexactly:maximumdifferences both0.0.
Selectedepoch19,earlystopped25;measuredphaseafterinitialchecks16.696s,sampledRSSpeak
1462804480bytes. Perbatchcheckpoint/cancellation/RNG/order state and900secondlimit
retained;nooverlappingtrainer. One new completedtrial104->105,not perepoch/pair/plot.

Candidate macro-cameraDEV IoU.6361161784891378 versusV1.5819598228590831:gain
.05415635563005472 passesprespecifieddurationobjective>=.02. Dice.775435041273052,
worstimageIoU.4798861626028767. Camera meansPUCPR.711806/UFPR04.603953/UFPR05.592590.
Originalcommon-cacheU-Netmean.287151/conditionalTRAINtemplate.761297 unchanged.
29pairedDEVimagesimprove,oneUFPR052013-03-01image drops.0031373378004792IoU. ExactCSV
withsourceIDs/imagehashesandpostscoringonly-regressionpanel retained. Same-seed
reusedDEVhypothesis support,notmultiseed/unseencamera/freshfinalreliability. Four
admissionfailuresremain:meanIoU.80,eachcamera.75,eachimage.65andtemplateregression.05.
No threshold/gaterelaxation orapppromotion. Everyoriginal/best/failedweight preserved.

460softwaretests/OK7.539s. Two learning/cameracomparison plots andonepairedregression
panel visuallyreviewed;metrics/curves/predictions/controlchecks andsource/split/config
hashes preserved. SelectedcheckpointSHA74fd7780c30ff8bed50619a2a8ab597e5ab51a23e728dbe1d9e3d19f06838588.
All17consumed/16quarantinedPKLotgroupsandotherfinalsclosed;no protectedpixels/XML
decoded. No newsourceacquisition fortraining:SRC-DS-001/SRC-MOD-003existingterms.
GuideREGION_DURATION_EXPERIMENT_GUIDE.md;cardmodels/region_fpn_duration.json;fullreport
reports/region_duration_REGION-FPN-DURATION-20261027T064327135442Z/EXPLANATION.md.
Notebook12remainsunchangedearlier8epocharchive;accepted468fileappcopy unchanged,
stillnotebook08only. Studentmastery/physicaloffline/newmachine/visiblemanual/official
acceptanceopen;datedPDF/presentationolder. Count105,wakeups71,63sourceIDs,noactive
jobs,last100runlivecheckpointpassed,next200. Nextindependenthypothesis:finerRGB
residualdecoderwithsamecoarseinitialoutput/samplerRNGandunchangedqualitygates;code
notimplemented/sealedyet. TRAINpatternbalancinglater,separatefromspatialheadchange.
Longerbudgetaloneinsufficient;do not repeatidenticaldurationruns orrelaxthresholds.


27Oct09:10UTC resumed after account usage-limit approval-review failure interrupted the06:39 handoff. The blocked action had not executed;duration integrity now passes,first8trajectory exact. No retraining or extra trial counted. Actual newSGsnapshot76,zero newlearnedforecasts because1217origins lack eligible priorcontext and6stale atactualissue;22882logged/21origins unchanged. Baseline1222newforecasts,0newmatchedoutcomes,67971scores/MAE5.792926395080255 unchanged. No backfill of missedperiods;final10:51UTC remainsclosed. Nexthistorycollection after09:40:25.969291UTC. Count105/wakeups72,noactivejobs.


## 27 October 2026 / controlled RGB detail residual and preserved regressions

REGION-FPN-DETAIL-20261027T091901724291Z adds full-resolution normalizedRGB8channel
residual tocoarseFPN. Zero-initialized lastlayer preservesinitialcoarseoutput;extra
seed170fork leavescoarseinit/seed169samplerstream unchanged. Actualdurationreference
lastcheckpointRNG matchesindependentstream;all32epochorderhashes verified. Uniform
TRAINsampling,weightedBCE+Dice,optimizer,max32/patience6,threshold.5and6gatesfixed.
CameraIDsnotneuralinputs. Selectedepoch30of32;phase49.513sec,sampledRSS1452830720bytes.
Perbatchcheckpoint/cancel/900secondlimit andnewsealedexecutorguard retained.

Macro-cameraDEV IoU.6654007861570017 versusduration.6361161784891378:gain
.029284607667863893 passesprespecified>=.02objective. Dice.7962144543165345. But
worstimageIoU falls.4798861626028767->.40072563493056423.26pairsimprove/4regress;worst
UFPR052013-02-28drops.13658289898628473IoU. Camera means.750588/.644365/.601250. Four
admissionfailurespersist:mean.80,eachcamera.75,eachimage.65andtemplateregression.05.
No gate/thresholdrelaxation orapppromotion. Same-seed,reusedDEV,suppliedbayfootprints
notfinal/unseencamera/occupancy/exhaustivefacility truth. Reviewedworstcase visibly
missesprovidedbays;mean improvementdoesnotestablishindividualreliability.

463softwaretests/OK7.912s addzero-output/coarseweight/RNGidentity,finiteRGB/residual
gradients,andreferenceorderswithoutglobalRNGchanges. Learningcurve andworst-paired
postscoringpanel visuallyreviewed;all30pairCSV andtargetpixelstats retained. Against
suppliedmasks precision.738960/recall.843151,62403extra/32862missedpixels,area ratio
1.140998. No causalproof/calibrateduncertaintyclaim. Nextseparateunimplemented
hypothesis:boundedscore-gatedresidual,preservingotherrecipe/gates;lossablation or
TRAINpatternbalancing later. All17consumed/16quarantinePKLotgroupsandotherfinals
closed;protectedhashes/backbone/BNunchanged,normalforbiddenaccesses0,cacheprobeblocked.
SourcesSRC-DS-001/SRC-MOD-003existingterms;no newtrainingassetacquisition.

SelectedfailedcandidateSHA62a830f6a991cb468fc37aefce61647dbef2ba6d23907c616cb0faa843b109d4.
V1/duration/source/cards/best/failedweights preserved. Historicaldurationemitted a
copiedV1resumehint;noresumeoccurred. Newdetaildriverusesthecorrectselfcommandand
checkssealedexecutor. GuideREGION_DETAIL_EXPERIMENT_GUIDE.md,modelscardandreport
reports/region_detail_REGION-FPN-DETAIL-20261027T091901724291Z/EXPLANATION.md. Notebook12
remainsearlierboundV1archive;accepted468fileappcopy unchanged/stillnotebook08only.
No physicaloffline/newmachine/visiblemanual/studentmastery/officialacceptance.
One new trial105->106,72actualwakeups,63sourceIDs,noactivejobs,last100runlivecheckpoint
passed,next200. Prior105handoffrecovered/committed0806acd afterusage-limitreview
failure;no duplicateexperiment or missed-periodbackfill. Source76snapshots/22882
learnedforecasts/21origins unchangedafter09:10gapresumption,no eligiblepriorcontext
fornewlearnedforecast. Nexthistorycollection after09:40:25.969291UTC. Finallearned
target/matching/error/coverage closeduntil10:51UTC/16:21IST;notcameraGT/BirminghamSGvalidation.


## 27 October 2026 / bounded residual fails reliability;broader data next

REGION-FPN-BOUNDED-20261027T094324175595Z changesRGBmappingto.5*tanh(raw)*4*p*(1-p)
usingdetachedcurrent-coarsescorep,notcalibrateduncertainty. Allinitialparameters,
seed169/170,uniformTRAINsampler,loss/optimizer/max32patience6/threshold.5andsixgates
fixed. All32orderhashesmatchreference. Threeaddednumeric/modeltests bringfullsuite
466/OK7.680s. Pre-fitfiniteauditguardamendmentsealedbeforetraining;originalunexecuted
protocol/source retained,0extraexperiment. Selectedepoch32of32;phase50.331s,sampled
RSS1452507136bytes;perbatchcheckpoint/cancel/900seclimit retained.

Macro-cameraDEV IoU.6517000551396865 vsunbounded.6654007861570017;gain-.01370073101731517
fails>=.02. Worstpairedloss-.128913449530204 fails-.05nonregression objective.8pairs
improve/22regress. Worstimage.43257643029303566 vs.40072563493056423 improves,butfour
admissionfailuresremain(mean.80,eachcamera.75,eachimage.65,template-regression.05).
No gate/thresholdrelaxation,app/finalpromotion. Softwareauditmaxaddedlogit.499920577
<=.5and1070295strongcurrent-coarsesignspreserved. This isnotGT/earliermodelaccuracy;
softwarepropertycanholdwhileimagecomparisonsregress. PairedCSV/deltaplot/worstUFPR05
2013-02-26panel visuallyreviewed withpostscoringselection/source/scopeexplicit.
Cardmodels/region_fpn_bounded.json,guideREGION_BOUNDED_EXPERIMENT_GUIDE.md andreport
reports/region_bounded_REGION-FPN-BOUNDED-20261027T094324175595Z/EXPLANATION.md.
SelectedfailedSHA7834476ab1790536785da7b399c463f127d244780236caf17dd4438d8ffbadba.
Allprevious/best/failedweights/source/cards retained;encoder/BN/protectedhashes
unchanged,normalforbiddenaccesses0,unqualifiedcacheprobeblocked. One trial106->107,
73actualwakeups,63sourceIDs,noactivejobs,last100-runlivecheckpointpassed,next200.

NextpivotassessalreadyqualifiedACPDSdevelopmentregiondata beforemoreresidualgrids.
Metadata-onlyreview confirmsCOMPLETEmanifest data/processed/acpds_development_v1/
development_images.json SHA2e0705c8b1fa1089fff36be7ca663ca0e81fc05a92825f80775082eb8d3a13ed
has231TRAIN/35VALID/266frames. Earlierimagequalmanifesthas3TRAIN+35VALIDonly. Native
layoutsalreadyapplynormalizedW-1/H-1mapping;do notscaletwice. Existingrights/roles
SRC-DS-021MITgrant retained;all27TESTimages/lots/views/aliasesclosed. No newACPDS
images/labels/TESTsemanticread orregioncache/training inthismetadatareview. Proposed
letterbox/validmask/geometry/bytealias/receipt/cache qualification in
REGION_DATA_EXPANSION_PLAN.md isnotsealed/completed. Paddingvalidityisnotnegative
truthinunannotatedareas;suppliedbayunions notexhaustivefacility/occupancyGT.

One due09:41:02UTC officialSGacquisition ->77snapshots;1078genuinelearnedforecasts
newlycommitted ->23960forecasts/22origins/22receiptedbatches metadatahealthy.1202new
persistenceforecasts/1121laterbaselineoutcomes ->69092scores/MAE5.80722804376773spaces.
No interimlearnedtarget/matching/error/coverage;originperiodends10:00UTC andfinal
closure10:51UTC/16:21IST unchanged. NextcollectionAFTER10:11:02.311102UTC;no earlypoll,
backfill/refit/lateforecastrepair. AggregateavailabilitynotcameraGT/BirminghamSGvalidation.
Notebook12andaccepted468filecopy unchanged,stillnotebook08only. Physicaloffline/
newmachine/visiblemanual/studentmastery/officialacceptanceopen;datedPDF/presentationolder.


## 27 October 2026 / broader region data qualified and source-shift baseline

ACPDS-REGION-DATA-20261027T101700848553Z completed dataqualification108. All231TRAIN/
35DEV cached,266uniqueJPEGs/no exactalias to12417PKLotmembers,0errors. Everyimage/
layout/receipt/role/geometry/cachecheck passes. Native4000x3000all266;letterbox
192x144inside256x144with32sidepadding,RGBbilinear/masknearest/nativeW-1H-1already
applied. Occupancylabels excluded. NPZrgb/mask/valid;nonpadding27648pixels,cache
18231856bytes,validforegroundfraction.042065..497143;phase57.408s. Targetsupplied
bayunion,notexhaustivefacilitynegative/occupancytruth;validityonlypadding. Manifest
SHA84e99f49e42488985bea490c8ca8ce230dff844830c1f5a01eb9365c004e5937. FixedtwoTRAIN
overlaysvisuallyreviewed. Exacttargetpatterns231/35,0crossroleoverlap,notindependent
lots/pretrainingproof. Knownbytealiaschecksnottransformed/unacquiredTESTproof.

Padding-aware maskedBCE+Dice andIoU/Dice helpersimplemented:ignorepaddingoutputs,
zeroinvalidlogitgradients,knownsingle-pixelloss,nonemptyvalidity/emptybatch/target
validation andall-validmetricparity. Fullsuite470prefit/7.560s,then474/16.314safter
validityhelpers;4targetedvaliditytests passafteremptybatchguard. No helpermodel
training. Legacyunmaskedtrainers incompatible;futurematchedcontrolneedsloss/gradient
paritytest. TwoexistingTRAINsourceexamples notrepresentativeaccuracy orlabelaudit.

ACPDS-REGION-BASELINES-20261027T102856322278Z is completedvalidation109,not4model or
175frame-runs. Prespecifiedall35DEV/fourfrozenmodels/nonpaddingmetrics/threshold.5.
MeanIoU originalU-Net.325371/coarse.312125/RGBdetail.259695/bounded.310879;worst
.133651/.070336/.070568/.086255. Everymethodfailsmean.80/min.65referencegates.
Encoder35/model140imageforwards,phase6.055s,0modeltraining/rawimageaccess. Original
commonletterbox->192x112->probabilitycommongrid,notnativeappbenchmarkreplay. No
matchinggeometrytemplatefornewviews,N/A. PreviouslyexposedDEV/derivedpolygonlabels,
notfreshfinal/occupancyaccuracy. All35pairedCSV/plot/sourcehashes/EXPLANATION retained.
Familiar-camera gains didnottransfer;nextseal source-balancedmixed-data experiment
withsource-separatedvalidation/old-viewretentionbeforefitting,notresidualgrids.

SourceSRC-DS-021MIT2021MartinMareknotice,priorSRC-DS-001PKLotCCBY4.0andSRC-MOD-003
localacademicterms retained. TEST27/lots/views/aliasesandallotherfinalsclosed;no
TESTserde/pixels/sourceacquisition. Alloriginal/best/failedweights untouched.
Normalforbiddenaccesses0,unadmittedsource/rawnegativecontrolsblocked. Data/baseline
controllersbounded/cancellable,partialartifactsretained. GuideACPDS_REGION_DATA_GUIDE.md,
modelscardsandbaseline resultfolder. Trial107->109,wakeups74,63sourceIDs,noactive
jobs,last100-runlivecheckpointpassed,next200. Datasetarray/journal loops notruns.

Due10:14:43UTC sourcecollection78:originperiodclosed,0newlearnedforecasts.23960
logged/22origins/22receiptedbatches metadatahealthy,notfinalcoverage/accuracy.1305new
persistenceforecasts/1129lateroutcomes ->70221scores/MAE5.8642001680409spaces. Next
collectionAFTER10:44:43.957085UTC. Learnedfinaltarget/matching/error/coverage remains
closeduntil10:51UTC/16:21IST;thenfrozen score_singapore_study.py/globalonce-onlyclaim.
No refit/backdate/lateoriginrepair oraccountgapbackfill. AggregatefeednotcameraGT.
Notebook12andaccepted468filecopy unchanged,stillnotebook08only. Newdata/helpers/
baselinesnotpackaged. Physicaloffline/newmachine/manual/student/officialacceptance
open;datedPDF/presentationolder. Independentproject workcontinues.


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


## 2026-11-16 ACPDS TRAIN-only target-representation diagnostic(trial116)
Sealed protocol(seed187,32/231 ACPDS TRAIN masks,SRC-DS-021 only;DEV/TEST not opened). Fixed stride4 36x64 area-downsample,bilinear(align_corners=False) upsample,>=.5,scored on nonpadding pixels.
Result: mean valid IoU 0.966065,median 0.973524,min 0.905679,Dice 0.982639;32 distinct mask patterns/32 views;padding-edge share of errors 0.0105. PKLot TRAIN same scheme .899(NumPy port reproduced it exactly).
Conclusion(pre-registered rule): stride4 target representation is NOT the dominant ACPDS limit vs ~.534 DEV model IoU;no finer-output training hypothesis. Label reconstruction only,not model accuracy or a proven upper bound. Next: sealed TRAIN-only frozen-feature probe. Run ACPDS-TARGET-REPRESENTATION-20261116T093422210992Z.


## 2026-11-16 ACPDS TRAIN-only frozen-feature probe(trial117)
Sealed protocol(seed188,64/231 ACPDS TRAIN,4 image folds;DEV/TEST not opened). Frozen ImageNet ResNet18(SRC-MOD-003) layer1-4 at 36x64,per-cell L2 logistic C=1 unweighted,>=.5 after bilinear upsample,nonpadding scoring.
Result: held-out mean IoU 0.305441(min 0.000000,3 images 0),Dice 0.438330;positional prior 0.152692;cell AUROC 0.7544;all folds converged;61.3s on cloud CPU(Python 3.13.18,torch 2.15.0+cu132).
Pre-registered verdict: insufficient(<.55) -> supports one sealed encoder-adaptation hypothesis. Caveat: a per-cell linear probe is a weak test(trained decoders reach ~.53 DEV);not DEV/final accuracy. Run ACPDS-FEATURE-PROBE-20261116T094551398633Z.


## 2026-11-16 Windows verification and dependency audit (ENV-03)
Project runner scripts/run_project_tests.py on D:\deep learning\.venv (Python 3.12.10): Ran 506 tests OK (501 prior + 5 mask_reconstruction). Plain `unittest discover` without the runner fails one module import (test_acpds_admission needs PYTHONPATH=src);use the runner.
scripts/audit_dependencies.py -> models/dependency_audit.json: 118 installed packages,no version drift vs DEPENDENCY_INVENTORY/lock;24/24 offline wheels SHA256-exact;3/3 pretrained weights SHA256-exact;pip check clean. Licences are declared metadata,not legal review. Evidence: experiments/evidence/HEARTBEAT-20261116T091500Z/windows/.


## 2026-11-16 session close (trials 118-120)
Trial118 REGION-ENCODER-ADAPT-20261116T101716238167Z: sealed paired encoder adaptation(layer3/4,BN frozen) vs frozen control on the same mixed schedule;selected candidate round32 PKLot macro 0.7149 vs 0.5861, ACPDS mean 0.6172 vs 0.5827(+0.0345<.05) -> relative gate FAIL;both arms fail absolute gates;not promoted. Attempt1 crashed with Windows MemoryError after round30 (concurrent Singapore collection);resumed from last.pt under the same sealed protocol. Segmentation research frozen.
Trial119 MLP-CONTROLLED-20261116T102002732022Z: one-factor MLP study on real Birmingham windows(TEST unread);baseline balanced acc 0.9748 vs persistence 0.9236;real effects:optimizer=sgd,learning_rate=0.2,init_scale=3,normalization=off,l2=1e-3,dropout=0.2,batch_size=16;within noise:optimizer=nesterov,learning_rate=0.01,init_scale=0.1,batch_size=256.
Trial120 PERF-20261116T104423344985Z: CPU benchmark(PERF-01) see models/performance_benchmark.json.
New labs: neural_basics.py,learning_rules.py,Nesterov in mlp.py,notebook14(8/8 cells executed on Windows,0 errors). ETHICS_AND_DEPLOYMENT_LIMITS.md added. Singapore snapshots 10:09Z/10:36Z,1090 in-window scores,no backfill. Windows suite 521 tests OK.
