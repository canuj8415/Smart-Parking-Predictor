# Current project decisions and session handoff

1. Continue Project 52; do not replace its scope with a generic notebook demo.
2. **Python with Jupyter notebooks is the user's current explicit choice.** It
   supersedes the earlier C/C++/Java instruction. Keep reusable `.py` modules
   behind teaching notebooks. Do not switch back without a user instruction.
3. The university `.docx` files are still absent. Do not invent their contents,
   official unit mappings, deadlines, rubric or language approval. Audit them
   completely when supplied before claiming official compliance. The latest user instruction explicitly authorizes implementing the supplied main-product definition now; do not keep model work blocked on the missing files.
4. Master Add-on 01 authorizes independent public research, appropriate data
   acquisition and reproducible preparation now. Continue useful independent
   work without repeatedly asking the student to find resources.
5. Every source needs permanent ID, creator, URL, actual access evidence, rights,
   version/unknowns, purpose, provenance and local hashes where applicable.
   Unknown asset-use permissions mean no asset use until verified. Do not accept
   restricted-source agreements, create accounts or bypass access controls.
6. Use actual observations; distinguish real data, synthetic test fixtures,
   simulations, generated imagery and pretrained outputs. Do not fabricate model
   scores, timestamps, student contributions or mastery.
7. Hold out grouped image data and chronological forecasting data. Fit learned
   preprocessing on training data only. No final holdout tuning. Do not join
   unrelated image cameras to Birmingham histories as if they were one lot.
8. Keep raw archives immutable. Record transformation lineage and source rows.
   Model/application claims require executed evidence, not generated code alone.
9. Record every training/evaluation run with unique IDs, data/split/config/model/
   code provenance and genuine measured results. Data-validation runs are labelled
   separately. Never overwrite old experiment evidence.
10. Build for eventual offline use and independent explanation/modification.
    Cached execution alone does not prove a disconnected demonstration.

## Current verified checkpoint

Python 3.12.10 and existing JupyterLab 4.6.3 work. The UCI Birmingham source was
downloaded and inspected. Six data unit tests pass, five notebook cells executed,
and repeated preparation is byte-identical. No model was trained. Existing
PyTorch is CPU-only despite the laptop's NVIDIA GPU. See TEST_RESULTS.md,
SOURCE_REGISTRY.md and experiments/evidence for exact evidence.

Next: student opens the real-data notebook and explains chronological splitting;
obtain/audit university files; resolve image-source access and legitimate mask
annotations; then implement the explicit NumPy baseline and main models.

## New verified product milestone

The exact user-supplied main product is now implemented as a Python desktop app
and executed Jupyter notebook. Read IMPLEMENTATION_STATUS.md, TEST_RESULTS.md,
THIRD_PARTY_SOURCES.md and current model cards before resuming. Earlier statements
about zero models or no images describe previous checkpoints only. The user
approved the Singapore public feed terms and later stopped computer-use input
with Escape; do not resume desktop control without renewed user direction.

The user subsequently supplied that renewed direction (“laptop is free u can
start again”). Desktop QA resumed under it; see UI_TEST_LOG.md. The earlier stop
and authorization history remain recorded.


## Final reservation and traceability update (25October2026)

The region training CLI now requires --holdout-manifest pointing to an existing
sealed reservation and never loads final images/labels. Use holdouts.evaluate_final_once
for an eventual selected frozen final evaluation: prior claims, even failed or
interrupted, consume overlapping frames. The six currently reserved final frames
remain unclaimed and undecoded. Before changing a trained controller, preserve its
recorded source bytes/commit; actual source snapshots accompany these studies.
Runtime pixel/config/model hashes support traceability, not camera authentication.

## 25October2026 / higher-resolution region trial and annotation inspection

MetaPKLot SRC-DS-010 archive is inspection-only. Preserve pinned original bytes and mixed-source rights distinctions; operational annotation use requires file/scope/ROI/image matching verification and exclusion of consumed/reserved final frames. KITTI registration and unresolved TRANCOS/DGT terms are not bypassed. Higher-resolution candidate still fails acceptance; retain closed final and production checkpoints.

## 25 October 2026 / training-only robust forecast selection

Forecast Dec12–19/2016 source rows are reserved by data/manifests/forecast_fresh_dates_v1.json. Do not use them for training/development/calibration. Legacy test loading is blocked; implement/test a durable overlap-aware one-time temporal claim before final evaluation. Freeze a suitable causal window protocol using training/development only first; missing admissible windows mean unavailable evidence. Original Dec8–11 final windows are already consumed. Current candidate passes reused-development gates only; production unchanged.

## 25 October 2026 / clock coverage and one-time later-date forecast evaluation

Forecast Dec12–19/2016 is now consumed under data/forecast_holdout_claims: one successful frozen evaluation, gate passed. Preserve immutable reservation and durable claims/outcomes. Never tune on or evaluate changed methods on these dates, even after code fixes. Original Dec8–11 also consumed. Displaying archived results is allowed; changed forecasting methods need genuinely fresh final data. Image final six remain separately closed.

## 25 October 2026 / conditional known-camera region stability

The six image-final frames and all3camera/date groups are now CONSUMED under data/holdout_claims. Image guard requires explicit group metadata and rejects same-day alternative frames. Do not tune on or evaluate changed vision methods on these groups. Use genuinely fresh groups for future changes. Conditional known-camera router passed; two cameras use stored geometry only, not image-based neural segmentation. Original production preview unchanged.

## 25 October 2026 / licensed labelled sequences and frame-index tracking

DAVIS car-roundabout is reserved as an entire sequence:75frames, pixels and annotation values unopened. Use a tested durable source/whole-sequence claim before final decoding; failure consumes it. Unknown source fps must remain unknown; frame-index mode does not create physical timestamps. Publisher foreground masks are partial traffic ground truth; no exhaustive precision/mAP/occupancy or parking entrance accuracy claim. Dataset aggregate CC BY-NC4.0, local noncommercial academic use with attribution; selected sequences absent from external-source exceptions.

## 25 October 2026 / positive image-line crossing and failed identity qualification

Current counting candidate fails dominant-identity gate; do not run final evaluation. Use sequence_holdouts.evaluate_sequence_once for any eventual frozen qualified final; canonical whole collection/sequence claims survive source-ID/path changes and failed callbacks. Car-roundabout remains unopened/unclaimed; no fabricated capture dates/fps. Positive development1/1crossing is label-assisted setup on a reused sequence and does not establish parking-entrance/exhaustive traffic accuracy.

## 25 October 2026 / identity-only continuation and whole-sequence final

DAVIS car-roundabout entire75frame source/sequence is now CONSUMED, including setup frames. Do not tune/re-evaluate changed methods on it. Original role manifest remains immutable; claim/outcome enforces consumption. Candidate differs from production tracker, no promotion. Partial foreground/image-plane/label-assisted setup scope; no physical fps/parking accuracy or universal claims. Preserve all failed experiments and selected snapshots; use fresh source/sequence groups for changed methods.

## 26 October 2026 / recovered CNR metadata qualification handoff

CNRimages remain inspection-only:individual-content scope unqualified.32079records across5global dates reserved;claim canonical whole dates before any qualified final evaluation. Continue independent licensed PKLot work;existing final groups remain consumed.

## 26 October 2026 / once-only paired occupancy final and retained replacement failure

Fresh PKLot final6and all3whole groups are now CONSUMED:pucpr2012-10-23,ufpr042012-12-24,ufpr052013-04-08. Failed95percent rainy-view vacancy-retention gate is preserved;original app model retained. Do not evaluate/tune changed methods on these photos,aliases or any other same-group frame. Claims/immutable reservation and original/candidate results retained. Archived result display/export is allowed. Independent improvements need fresh final source groups.

## 26 October 2026 / MAE-aligned Singapore trend and frozen prospective issuer

The Singapore trend coefficient, 46-snapshot historical split, candidate selection and issuance implementation/config are now FROZEN for the reserved ALL-carpark origin period 26 October10:00UTC to27 October10:00UTC. Do not refit or tune on post-cutoff data. Use fixed parameters with already available inference context only. Real forecast batches must be committed before targets; no backdating. No learned partial/final scoring before 27 October10:51UTC or outside the global durable once-only claim. Final callback remains to be implemented on synthetic fixtures under the already frozen scoring plan. Original production app unchanged; development pass is not final acceptance.

## 26 October 2026 / frozen once-only Singapore final scorer

Singapore final scorer is now implemented and FROZEN by data/manifests/singapore_trend_scoring_v1.json. Do not modify frozen matching/gates/model/issuer/scorer for this interval. No real final semantic target/context decoding for evaluation before 27October10:51UTC and the durable global claim. Synthetic fixture successes are software evidence only. Failures consume; never repeat changed-method evaluation or repair late forecasts. Display archived completed results only. Real study remains unscored.

## 26 October 2026 / first real pre-target batch and metadata-only health

Metadata-only issuance health checks may run before final closure: validate logged fields and byte hashes without decoding raw context/targets or computing learned errors/coverage. Do not wire the new health helper into the frozen scientific controller, prefilter final forecasts based on outcomes, or repair/delete failed batches. The final raw-semantic check stays inside the once-only claimed callback. Routine health/collection does not create new experiment counts.

## 26 October 2026 / UVG development qualification

ENTIRE UVG HighwayDrive is reserved final across aliases/frames/representations;no finalbodydownload/decode. Finalcanonicalbundleclaimcontroller is notimplemented;DAVIScountadapter is unsuitable. HighwayView isdevelopmentexposed. Absent raster support isunknown,nevernegative/zero-IoUtruth;strict failedsourcegates mustremain. No occupancy/parking-region truth fromtrafficinstance masks.

## 26 October 2026 / real traffic development evidence

UVGcandidate960passesrelativegain/time/nonregressionchecksbutfailsabsoluteadmission. Do not openHighwayDrivefinalorchangeappsettingsfromthisresult. No exhaustiveprecision/mAP oroccupancyclaimfromprovidedtrafficinstances. Keep153eligibleand194all-observationdenominators,unknownrasterexclusions,trainoutsidescope andcorrelatedonecliplimitation.

## 26 October 2026 / diagnosis and archived vision lesson

Diagnostictrainlabelononesuppliedtruckdoesnotauthorizetrain-to-truckremappingorconfidencecutchanges. Savedoutputsarepost-NMS/headscore0.05/top150,notrawRPNproof. Lesson11isreadonlyarchivedDEVELOPMENT;synthetictoyexplicit,studentmastery/physicalofflineunassessed. Absolutevisiongatesremainfailed;wholeHighwayDrivefinalunopened.

## 26 October 2026 / native-detail crop study

Native-detailcroppingdoesnotauthorizeapppromotionorHighwayDrivefinalaccess:Maskrecall/gap/unassignedvolumegatesFAILED. No posthocgaterelaxation. Knowntrainclassconfusionspersist;unassignedoutputsnotverifiedFPandpositivecoverageisnotprecision. Originalthresholds/classes/weightsunchanged.

## 26 October 2026 / mask review safety evidence

Do notautomaticallyapplymaskcontainmentdeletion:actualDEVELOPMENTregressionlost2correctcarsandmaskquality;frozengatesFAILED. Currentmask_reviewAPIisinspection-only,preservesalloutputs/weights/classesandprovidesnooccupancystates. SourceHighwayDrivefinalunopened;overallnativecropadmissionstillfails. No thresholdgridtoerasefailure.


## 27 October 2026 / Singapore whole-interval final consumed

The canonical ALL-carpark origin interval26October10:00UTC to27October10:00UTC,
with targets through27October10:51UTC,is now CONSUMED by SG-FINAL-20261027T105114261864Z.
Completed claim/outcome and result are authoritative; immutable reservation text is historical.
Overall final gate FAILED despite15.53% lower paired MAE: worst-origin regression0.514513
exceeded frozen0.5spaces. Never tune/retest a changed method on this interval or its aliases,
repair late forecasts,backfill missed origins or relax the gate. Archived result display/audit
is allowed. A future method requires a separate prespecified protocol and fresh future interval.
No app-model promotion;aggregate availability is not camera ground truth.
