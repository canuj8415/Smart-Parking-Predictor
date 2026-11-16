# Desktop checks — 24 October 2026

The user explicitly renewed desktop-control authorization with “laptop is free
u can start again”. Checks used the computer-use skill against the actual Python
app on this laptop. These are observed UI checks, not an exhaustive UI test suite.

| Check | Observed outcome |
|---|---|
| Real sample and Faster R-CNN | 40 spaces: 35 occupied, 2 available, 3 uncertain; 35 vehicles detected |
| Mask R-CNN | Same slot counts; 38 vehicle detections and actual masks |
| Reload after analysis | Previously stale counts reproduced, fixed, then visually confirmed cleared |
| Change detection threshold | Readout updates; prior counts/overlay cleared until Analyze is clicked |
| Work in progress | Input/settings buttons disabled while inference runs; Stop video remains available |
| Learned space mask | Experimental purple region preview renders; IoU 0.252 limitation displayed |
| Historical forecast | Actual, LSTM and persistence curves render; MAE 121.21 versus 61.14 remains visible |
| Convolution lab | Six real-image/numeric teaching panels render with explanatory labels |
| Live refresh | Initial restricted process failed DNS; after reopening with network access, official refresh succeeded |
| Fresh live snapshot | 2,005 car parks; provider time 2026-10-24T18:55:36+08:00; original payload and receipt saved |
| Live search | HE12 filter displays its single record: capacity 105, occupied 2, available 103 |
| Saved snapshot | App reloads the acquired file with an explicit Saved/cached snapshot label |
| Sources and guide | Actual registry URLs, rights and local-storage paths render in the app |
| Status-bar layout | After reopening and rendering the convolution chart, numerical error message remains visible at the bottom |
| Export dialog | Open/cancel verified; automated typing into the native folder dialog did not reach its field, so no full dialog save pass claimed |

The live snapshot is `data/raw/singapore_live/20261024T105547434893Z.json`,
307,710 bytes, SHA-256
`b57b116c15e178b691f7acc524347d6a87b3de438a677cf98a98858d5c55dcbb`.
Its original URL, retrieval time, licence and provider time are recorded in
`data/resource_receipts.jsonl`. Normalized observations are appended to
`data/processed/singapore_live_observations.csv`.

Fixes also keep a separate analysis overlay when a semantic preview is displayed,
block canvas edits while a worker runs, improve control contrast, add a live-table
scrollbar and reserve the status bar before allocating chart space. The export
writer has a regression test verifying overlay pixels, separate preview pixels
and matching JSON. Synthetic test images are software fixtures, not model results.

Final automated verification: 23 tests pass; both saved notebooks retain executed
cells without error outputs. Evidence:
`experiments/evidence/FINAL-20261024T105548780114Z/`.
Model checkpoints and their reported evaluation scores were not changed.

Remaining checks include a full native export-dialog save, new-camera reliability,
original traffic video and physically disconnected operation. No physical camera,
entrance/exit counting or current camera-specific forecast is claimed.

## 25October2026 / actual forecast target times

Forecast tab wording/title now distinguishes30-minute grid targets from earlier real target readings. Automated software suite passes; this wake did not open the desktop or visually inspect the changed text. Existing native-save/offline limitations remain.

## 25 October 2026 / video-bound desktop entrance and exit setup

Hidden native Tk widget inspection passed: actual new tab, counting-line/reference-arrow canvas, busy-control states, explicit direction, setup-file save/reload methods and frame-event display. Native file dialogs were mocked. No screenshot/visual review, physical save-dialog interaction or human rehearsal claimed. See experiments/evidence/HEARTBEAT-20261025T090725Z/native_widget_checks.json. Real processing route separately validated on three licensed video samples; accuracy unmeasured.

## 25 October 2026 / clock coverage and one-time later-date forecast evaluation

Optional Later-date check added to historical forecast tab. Hidden native Tk/Matplotlib chart rendering passed for both actual archived reports; switching clears stale charts and round-trip restores original text. New label shows31.72/39.07MAE and actual10.0–29.1min lead, not live. No model rerun or raw final re-read for display. No screenshot/visible layout or physical-user acceptance claimed.

## 25 October 2026 / dated Excel report and Python progress exports

New saved-progress/source buttons:actual hidden native Tk display/export methods, JSON/CSV equality/checksums, source round-trip and busy-state checks pass. Folder chooser mocked; no visible screenshot/manual dialog/physical-offline/native Excel claim. Evidence:experiments/evidence/HEARTBEAT-20261025T151531Z/native_progress_checks.json.

## 25 October 2026 / relocated local demo and shutdown cleanup

Actual relocated hidden-native app workflows pass with mocked save dialogs. Both detector/semantic/forecast/cached-live/lab/progress routes tested under blocked Python networking and original-workspace fallback. Shutdown callback cleanup fixes observed stderr warning; strict second check has empty stderr. No visible/manual-dialog or physical-network acceptance claimed. See models/local_demo_package.json.

## 25 October 2026 / SVD lesson completed after usage-limit interruption

Actual hidden-native app rank switching,invalid/busy guards and2D/3D/SVD chart replacement pass; figures do not accumulate. Original input image unchanged. No visible/manual acceptance or detector score. See models/svd_lesson_validation.json.

## 25 October 2026 / refreshed relocated demo with live guards and Jupyter lesson

Refreshed copied app passes actual hidden-native detector/export/forecast/cached-live/SVD/progress/video routes; selected notebook08Python cells execute without original-source fallback or normal Python networking. Mocked dialogs and suppressed notebook display; visible/manual/fresh-offline/kernel acceptance unverified. Source outputs and empty stderr retained in the latest demo run.

## 25 October 2026 / existing-runtime startup preflight regression

New launcher passes discovery then delegates to the main entry point in the existing installed runtime. An actual hidden native window is created/updated/destroyed without model engine or image loading; exit0. This supplements the clean-venv missing-package negative control; no visible/manual/fresh-install or detector accuracy claim. Evidence:experiments/evidence/HEARTBEAT-20261025T201536Z/existing_startup_smoke.json.

## 25 October 2026 / verified fresh app-only offline dependency installation

Actual new-venv hidden-native detectors/paired exports/semantic/archived forecasts/cached live/SVD/video pass with networking blocked. Same frozen training prediction counts,not accuracy. No visible/manual/physical/new-machine/Jupyter acceptance. See models/offline_app_installation.json.

## 25 October 2026 / fresh offline Jupyter kernels verified

Actual fresh notebook kernels generate inline image outputs and both training-example overlays. JupyterLab browser/server,visible app layout/manual dialogs were not exercised. No physical-offline/new-machine claim.

## 25 October 2026 / local JupyterLab server route verified

Server/API/WebSocket route and inline PNG checked,including visual inspection of returned plot. No visible browser DOM/frontend-JavaScript/manual selection was tested. Server/kernel stopped cleanly;no UI process left open.

## 25 October 2026 / combined offline demonstration verified in a fresh copy

Actual hidden copied-folder app with freshly installed runtime exercises both models,exports,semantic separation,archived forecasts,cached live,SVD/progress and bounded video. Genuine copied-folder notebook kernel returns inline plot. Mocked dialogs;no visible browser/manual/physical/new-machine acceptance.

## 26 October 2026 / unchanged app fusion on fresh development photos

Actual VisionEngine.analyze backend paths for both detector options measured; offline get_live(refresh=False) route validated against new saved source bytes with network denied. No new desktop/browser/manual UI interaction in this wakeup.

## 26 October 2026 / expanded occupancy training and real-engine development checks

Both actual VisionEngine.analyze detector routes exercised with experiment-local candidate classifier/provenance. Main app constructor/default checkpoint unchanged. Actual Jupyter notebook09tables/inline plot executed;no visible browser/manual/student UI rehearsal. Cached live route matched new saved JSON.

## 26 October 2026 / once-only paired occupancy final and retained replacement failure

Actual VisionEngine paths run under frozenpairedprotocol,not a visible desktop rehearsal. Both Excel sheets visually reviewed and exported package/formula caches checked;nativeExcel not opened. Actual Jupyter archive-reader kernel works afterconsumption;no raw final pixels/inference replay.

## 26 October 2026 / precise forecast variant labels and owned-snapshot exports

Actual hidden native forecast widgets,real matplotlib plots and mocked export-folder dialogs checked for both saved reports. Real combobox park-change event invalidates old plot/export;save-before-show refused before directory dialog. Both export PNGs visually inspected;source curves/timestamps/metrics preserved. No visible window/manual dialog typing or new forecast score.

## 26 October 2026 / forecast exports verified in the refreshed offline copy

The refreshed selected demo passes its frozen combined gate in415.75seconds:424payload files (807,000,528bytes),107original installer wheels and a NEW package-local environment with all107installed versions independently verified. Actual hidden native checks exercise both detectors on one training image,semantic preview,2D/3D teaching examples,SVD,two already-seen video frames,cached live data and both archived forecast variants. Original LSTM and Group-relative residual LSTM each retain their own plot legend,run/checkpoint/prediction identity and exact PNG/CSV/JSON exports. Report/park changes clear the previous plot/export. Export PNGs were visually inspected. A genuine copied-folder Jupyter kernel executes notebook08with one inline PNG;only08ofnine notebooks is included. Existing-environment overwrite is refused. Normal app Python socket attempts:zero;installer/Jupyter audit denials:zero. Separate deliberate original-project read/DNS probes are blocked. Python guards do not isolate native-extension IO or physically disconnect the laptop. All424payload hashes,protected model/claim bytes and all419earlier-package payload bytes remain unchanged. No model training,new scientific scoring,consumed final replay,new-machine or visible/manual/student acceptance. Prior213shared-runtime software tests remain separately dated. Counter53->54 counts one integration trial;wakeups37,next100-run live checkpoint100,no active jobs. Source catalog57unchanged;installer copying is not new acquisition. Offline cache is snapshot41/provider2026-10-26T10:29:36+08:00;main history has42snapshots/provider11:00:36+08:00. Main causal persistence scores36,258targets,MAE4.795797spaces;missing targets unscored,not neural/camera accuracy. Evidence:experiments/results/COMBINED-DEMO-20261026T025712811956Z/run.json;experiments/evidence/HEARTBEAT-20261026T025043Z/independent_checks.json. Start:docs/COMBINED_OFFLINE_DEMO_GUIDE.md. Next:legitimate fresh labels;failed occupancy final remains unpromoted.

## 26 October 2026 / supplied space polygons and conservative source grouping

Actual generated TRAIN-only contact sheet visually inspected:four source photos with supplied polygon outlines,sourcefile/preview hashes in the recorded inspection. No app-window/manual/student acceptance or model predictions. The main app/offline package was not changed.

## 26 October 2026 / complete TRAIN audit with quarantine and unknown-aware support

Generated TRAIN-only train001/day and train518/night source-support PNGs visually inspected. These are supplied-label diagnostics with unknown areas gray,not model predictions or app/manual acceptance. Existing app/offline package unchanged.

## 26 October 2026 / genuine source-balanced head training retained the warm comparison

Actual16-crop source-label gallery and final one-sheet Excel preview visually inspected. Timestamp formatting corrected and final report rerendered. No app UI/nativeExcel/manual/student acceptance claimed.

## 26 October 2026 / paired transfer diagnosis and rejected teacher-anchored study

New one-sheet Excel comparison rendered and visually reviewed. Date/time display fitted and rerendered. No main-app/manual/nativeExcel/student acceptance claimed.

## 26 October 2026 / executed read-only Singapore Jupyter lesson

Actual saved lesson10 development PNG visually inspected: labels, method values, nine UTC timestamps, two regressions, threshold and scope footnote readable. Actual kernel and HTML-table escaping tests pass; no manual notebook-browser/native-app/student rehearsal performed.

## 26 October 2026 / relocated read-only lesson and resumed live collection

Relocated-environment saved development PNG visually inspected and readable. Actual kernel, payload verifier and launcher help pass. No manual notebook-browser/native-app/new-machine/physical-disconnection/student rehearsal claimed.

## 26 October 2026 / UVG development qualification

Development video/polygon contact sheet frames1/300/600 visually inspected;supplied polygons align with visible vehicles/train. This is annotation QA, no app/native/manualUI or exhaustivealignment acceptance. All600frames decoded locally;no modelpredictions or finaldata.

## 26 October 2026 / real traffic development evidence

VisuallyreviewedactualMaskRCNNframe300modelboxoverlay andfixedthree-panelgroundtruth/640/960maskcomparison;large-truckmissvisibleinbothsettings. Reviewedaggregatecomparisonchartforreadabledenominators/gates/limits. No manualapp/nativeUI/browser/studenttest performed.

## 26 October 2026 / diagnosis and archived vision lesson

ActualJupyterkernelrenderslesson11sevenoriginalcodecells/twoinlinePNGs,zerosavederrors;embeddedPNGbytesidenticaltopreviouslyvisuallyreviewedfigures. No manualnotebookbrowser/nativeUI/studentpresentationornewmachine/physicalofflineacceptanceperformed.

## 26 October 2026 / native-detail crop study

VisuallyreviewedactualnativecropcomparisonchartandMaskframe300reference/additionboxoverlay;train-fragmentroadclasspredictionsvisible. Nomanualapp/browser/student/newmachine/physicalofflineacceptance. FiguresannotatedDEVELOPMENT/failure/scope.

## 26 October 2026 / mask review safety evidence

Visuallyreviewedfalse-suppressioncasefigures(frame361car18/frame600car19)withsuppliedlabelsandactualpredictedmasks/boxes,andthefailed-rulemetricchart. No actualapp/native/manualbrowser/student/newmachine/physicalofflineacceptanceperformed. ReviewexportisJSONresearchinspection,notproductionUI.

## 26 October 2026 / hidden app export transaction regression

ActualhiddenTkappdisplaysandsavesbotharchivedforecastmethods(8and75selectedwindows);legends/text/CSV/JSON/checksums andstale-selectionclearingpass. Controlleddirectorydialogpatchused,novisiblemanualdialogcontrol. Actualexportedlater-datePNGvisuallyinspected:title/axes/legendlegible.13syntheticfailure/cancellation/integritycasesseparatefromrealarchiveddisplay. No manualbrowser/student/newmachine/physicalofflineacceptance.

## 26 October 2026 UTC / offline refresh remains incomplete after isolated bootstrap repair

Secondfreshcopiedhiddenappcheckpassesexistingdetector/analysis-preview/archivedforecastexport/cachedlive/SVD/progress/video softwareflows. Newcopiedkernelcheckdidnotfinish;no notebookbrowser/manual/student/physical/newmachineacceptance.13deferredsynthetictransactionchecks passseparately. OlderREADYpackage remainsselected.

## 26 October 2026 UTC / copied notebook recovered with approved local loopback

ActualcopiedJupyterkernelexecutesunchangednotebook08plusdiagnosticcelland1PNGunderapprovedlocal-loopbackcontext. Copiedapp/failurecaseswereverifiedpreviouslyandnotreplayedhere. No visiblebrowser/manualdialog/student/newmachine/physicalofflineacceptance.

## 27 October 2026 IST / current group-role audit and seven-page evidence addendum

All7actualPDFpagePNGsreviewed:legibletables/plots,consistentheaders/footers,noclipping/overlap. PDFtextboundschecks pass. No newvisibleapp/browser/native-dialog/student/physicaloffline/newmachineacceptance.

## 27 October 2026 IST / real ACPDS images qualified; unchanged classifier fails source-shift gates

Visually reviewed all three prespecified TRAIN geometry overlays; no model or TEST overlay was viewed for this format check. This was source-image inspection, not a visible application, browser, manual-dialog, student, new-machine or physical-offline acceptance test.

## 27 October 2026 — API integration and rendered previews only

ASSIGNMENT-API-20261027T012959957197Z ran real FasterRCNN640 and original classifier on3previously exposed4KTRAIN photos,83spaces. API identity/count/state/modelhash/overlay contracts pass. All3downscaled PNG overlays visually inspected for intact rendering;this is not occupancy accuracy certification. No desktop control,visible native dialogs,physicaloffline,newmachine or student acceptance executed. Worker reporting error recovered once without rerunning inference. Software432/OK;full allocation guide OCCUPANCY_MEMORY_GUIDE.md.

## 27 October 2026 — scientific fusion examples, no desktop control

Three fixed-order diagnostic PNGs rendered and visually inspected:original unsafevacant warned,original unsafevacant remaining,research correctvacant senttoreview. Hashes,source/crop bounds,published labels,method states and supporting boxes retained in report manifest/visual_review.json. Observed occlusion/projection differences are not causal proof. No visible GUI/native-dialog/offline/newmachine/manual/student acceptance;software437/OK.

## 27 October 2026 — TRAIN geometry examples only

Three source-bound fixed-order PNGs visually reviewed:vacant support removed,occupied support lost,occupied support added. Supplied polygon,detector rectangle and yellow box-bottom proxy are visible with readable headers. New bay support does not verify correct physical vehicle association. Published labels unchanged;no visibleGUI/native-dialog/offline/newmachine/manual/student acceptance.442softwaretests pass;no production geometry change.

## 27 October 2026 — fresh current copy and milestone native callback

Actual hidden app in new468-filecopy runsbothdetectors,transactional PNG/CSV/JSON exports,semantic preview separation,archived forecast method identities,SVD/progress/video and cached pre-origin feed. Mocked dialogs,not visible manual acceptance. Actualcopied Jupyterkernel/1PNG passes with local loopback and unchanged external/fallback guards. Separate milestone100 main-app callback displays2423actual freshlyacquired rows/filter1/provider/path/status,backend patched toavoid duplicatepolling. No camera accuracy/physicaloffline/newmachine/student/official acceptance.446softwaretests pass.

27Oct2026 full-role audit:metadata/softwareguard work only;no nativeUI orimagepreview/newcamera/modelaccuracy acceptance. Existing468-filecopy acceptance remains separate.451softwaretests pass.


27Oct2026 region-data qualification:three source-bound TRAIN overlay PNGs visually inspected,one per camera,polygon alignment plausible. This is a dataset sanity check,not model accuracy or new visible GUI/manual/offline acceptance.456softwaretests pass;accepted468-filecopy unchanged. See REGION_DATASET_V2_GUIDE.md and result visual_review.json.


27Oct2026 FPN study:three worst DEVELOPMENT error panels visually reviewed,source/hash/selection/legends readable. New model reduces excess area but still misses bay boundaries;UFPR04 majority template visibly misaligns. Actual notebook12 six cells/three matching inline PNGs passed read-only/file/socket controls after preserved startup interruption/local retry. No visibleGUI/manual/newmachine/physicaloffline/student acceptance;app and acceptedcopy unchanged.460softwaretests pass.


27Oct2026 duration study:learning-curve andcamera-comparison scientificPNGs pluspost-scoringonly pairedregressionpanel visuallyreviewed,axes/legends/selection/source captions readable.29pairsimprove/1drops.003137IoU;no causalclaim. No newnativeGUI/manual/offline/studentacceptance. Notebook12andacceptedappcopy remain unchanged.460softwaretests.


27OctRGBdetail:learningcurve andpostscoringworstpairedchange PNGs visuallyreviewed,readableaxes/labels/source/scope.26improve/4regress;UFPR05worstpairvisiblymissesprovidedbays andloses.136583IoU. No causal/representativesample claim. No newnativeGUI/manual/physicaloffline/studentacceptance.463softwaretests;app/copy/notebook12 unchanged.


27OctboundedRGB:paired-delta plot andworstchangeUFPR052013-02-26panel visuallyreviewed,readableindex/limit/source/scope/errorlegends.8improve22regress;worstpairedloss.128913 retained. Softwarelogitbound notimageaccuracy. No newnativeGUI/manual/offline/studentacceptance.466tests;app/copy/notebook12unchanged.


27Octbroaderregiondata:twofixedTRAINoverlaysandfrozen4-modelsource-shiftbarplot visuallyreviewed,labels/padding/source/scopeclear. Geometryalignment sanityonly,notindependentannotationaudit;all35DEVmodelreferencegatesfail. No newnativeGUI/manual/offline/studentacceptance.474softwaretests+4targetedvaliditychecks,app/copy/notebook12unchanged.


27OctSingaporefinal: saved-metric comparison PNG visually reviewed; MAE units, failed +0.5-origin gate, coverage/missing targets, source licence and horizon readable. Archived rendering only; no new nativeGUI/manual/offline/student acceptance.475software tests pass.


27Octmixed-region: learning/source-delta figure and worst PKLot regression panel visually reviewed. Labels,gate lines,source scope and differing selected updates clear. Worst image chosen after scoring,not representative. No new nativeGUI/manual/offline/student acceptance.479softwaretests pass.


27Octsource-gradient diagnostic: cosine/norm-ratio plot visually reviewed,log-scale andfixedTRAINbatch/checkpoint labels clear. Unsupported hypothesis andnoncausal/raw-gradient scope explicit. No new GUI/manual/offline/student acceptance.487softwaretests pass.


27OctguardedSGD: learning/retention figure andlowestguardedACPDSquality panel visually reviewed. Shared550updates/selected325vs400/source/gate scopes clear. Worstimage chosen afterscoring,not representative. No newnativeGUI/manual/offline/studentacceptance.491softwaretests pass.


27Octdetailcapacity:curves andpostscoringworstACPDS panel visuallyreviewed;nearlyidenticalcurves/failinggain/source/selectedsteps clear. SamePNGs rendered inactual notebook13(twoinlineimages). No newnativeGUI/manual/offline/studentacceptance.495softwaretests pass.


27Octportablelesson13:actualrelocatedkernel fivecells/twoPNGs,sixinputs andfivefile/network probespass;inlinePNGhashesequalalreadyreviewedimages. No newnativeGUI/browser/manual/physicaloffline/studentassessment.501softwaretests pass.
