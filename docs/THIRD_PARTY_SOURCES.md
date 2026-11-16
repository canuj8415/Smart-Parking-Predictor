# What we used, who created it, and where it is stored

This is a locally built, AI-assisted student project. External models and data
are attributed separately from the models actually trained here. Full per-source
records are in `data/source_manifest.csv`; per-file retrieval timestamps, byte
counts, source URLs and SHA-256 values are in `data/resource_receipts.jsonl`.

| Resource | Original publisher / source | Actual use | Local storage |
|---|---|---|---|
| PKLot images and XML | Almeida et al.; UFPR, [original laboratory page](https://web.inf.ufpr.br/vri/databases/parking-lot-database/) | Real slot crops, occupied/vacant labels, original slot polygons; limited date-separated development subset | `data/raw/pklot_subset/PKLot.tar.gz`; selected original files below `data/raw/pklot_subset/PKLot/` |
| PKLot archive | [Official original download](https://www.inf.ufpr.br/lesoliveira/download/PKLot.tar.gz) | Full original compressed archive retained; working extraction includes 1,701 paired frames | Same folder; `acquisition.json` records selection, source and times |
| Birmingham occupancy | Daniel Stolfi/UCI; Birmingham City Council/NCP observations, [UCI 482](https://archive.ics.uci.edu/dataset/482/parking+birmingham) | Real historical forecasting; causal derived grid and chronological holdouts | `data/raw/uci_parking_birmingham/`; `data/splits/birmingham-global-days-v1/` |
| Singapore live availability | HDB/data.gov.sg, [official feed](https://api.data.gov.sg/v1/transport/carpark-availability) | Explicit online current-snapshot refresh, separately identified from the image camera and historical model | `data/raw/singapore_live/`; appended observations in `data/processed/singapore_live_observations.csv` |
| Faster R-CNN + ResNet50 FPN V2 | [TorchVision model publisher](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.detection.fasterrcnn_resnet50_fpn_v2.html) | Externally COCO-pretrained detector; this project did not train it | `models/pretrained/fasterrcnn_resnet50_fpn_v2.pth` |
| Mask R-CNN + ResNet50 FPN | [TorchVision model publisher](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.detection.maskrcnn_resnet50_fpn.html) | Externally COCO-pretrained vehicle instance segmentation; genuine pixel masks | `models/pretrained/maskrcnn_resnet50_fpn.pth` |
| ResNet18 ImageNet weights | TorchVision model weights | Frozen image features; this project genuinely trained a new occupied/vacant linear head on real PKLot crops | Original `models/pretrained/resnet18_imagenet.pth`; trained model `models/checkpoints/occupancy_resnet18.pt` |
| Python/PyTorch/TorchVision | Python Software Foundation; PyTorch/TorchVision contributors | Actual Python model definitions, training, inference and tensor demonstrations | Existing `D:\deep learning\.venv`; observed package metadata in `docs/DEPENDENCY_INVENTORY.json` |
| NumPy, Pillow, Matplotlib, Jupyter | Their respective open-source contributors | Handwritten MLP, images, plots and executed teaching notebooks | Same existing Python environment; pinned direct dependencies documented |
| Tkinter/Tcl/Tk | Python standard library and Tcl/Tk contributors | Local desktop user interface | Existing Python installation; app source `src/smart_parking/app.py` |
| OpenCV wheel | OpenCV team/PyPI wheel maintainers, [exact pinned release](https://pypi.org/project/opencv-python-headless/4.13.0.92/) | Optional local video-file decoding and writing; acquisition status must be checked | `dependencies/wheels/`; installed only to `dependencies/python/` if setup succeeds |
| Research articles and framework documentation | Original papers and official documentation | Architecture explanations, equations and API use; no paper scores attributed to this project | `reports/overleaf/references.bib`, `docs/LITERATURE_NOTES.md`, source registry |
| Codex assistance | OpenAI Codex, directed by the student | Assisted source research, implementation, test execution and documentation | `docs/AI_ASSISTANCE_LOG.md`, `docs/INDIVIDUAL_WORK_LOG.md` |

## Licensing and attribution

PKLot is CC BY 4.0 with the original dataset-paper attribution. UCI displays CC
BY 4.0 and also mentions the originating OGL; both source statements are retained.
Raw datasets and weight binaries have not been published or uploaded.

Contains information from **Carpark Availability**, accessed on **24 October
2026** from **HDB/data.gov.sg**, made available under the
[Singapore Open Data Licence version 1.0](https://data.gov.sg/open-data-licence).
The user explicitly authorized these terms, including the indemnity clause.
The application includes this attribution and does not imply government endorsement.

TorchVision code is BSD-3-Clause. Its publisher separately warns that pretrained
model terms may derive from training datasets. Local academic evaluation is the
current purpose; this record does not grant unrestricted commercial or model
redistribution rights. COCO/ImageNet origins are retained; consult source terms
before distributing any combined weights/application. No Ultralytics package or
YOLO weights were used. The selected official architecture option is Faster R-CNN
with ResNet, with Mask R-CNN for the separate instance-mask demonstration.

No private CCTV, credentials, paid services, protected feeds or personal accounts
were accessed. CNRPark and the other previously recorded candidate datasets were
not silently substituted into the acquired-data list.

## Derived data and experiment locations

- Occupancy crops: `data/processed/pklot_crops/`; mappings/labels/splits:
  `data/manifests/pklot_crops.csv` and `pklot_frames.csv`.
- Original layout geometry, without occupancy answers:
  `configs/layouts/`. Learned masks are separate outputs, not renamed polygons.
- Project-trained models: `models/checkpoints/`; small model cards: `models/`.
- Actual training curves, predictions, masks, reconstructed/synthetic VAE images
  and run settings: `experiments/results/<run_id>/`.
- Image/video user exports: chosen output folders or `outputs/`.
- Source/experiment CSV registries: `data/source_manifest.csv` and
  `experiments/EXPERIMENT_REGISTRY.csv`.

The source archive has an invalid date-folder label (`2013-14-16`). Those
observations are excluded from chronological image splitting instead of silently
inventing a corrected date. An interrupted preliminary training attempt was
stopped before final evaluation when this was discovered; the corrected run's
manifest and rejected-record reasons are retained.

The authorized Singapore source also supports a separate prospective persistence
baseline. Issue-time forecasts, later matched outcomes and actual elapsed horizons
are recorded under `data/processed/singapore_prospective/`. This is a non-neural
next-snapshot baseline with an explicit 20-45 minute target window; it is not
camera ground truth or demonstrated live neural forecasting accuracy. Collection
and causal scoring rules are documented in `docs/LIVE_EVALUATION_PROTOCOL.md`.


## SRC-VID-001 - acquired real-motion integration source

Street traffic, Editor (YouTube user Editor), recorded 28 May 2011; Wikimedia
Commons: https://commons.wikimedia.org/wiki/File:Street_traffic.webm
Description permalink: https://commons.wikimedia.org/w/index.php?title=File:Street_traffic.webm&oldid=1273823111
Original: https://upload.wikimedia.org/wikipedia/commons/7/70/Street_traffic.webm
Licence: CC BY 3.0 Unported, https://creativecommons.org/licenses/by/3.0/
Accessed 24 October2026 17:47:33UTC. Commons records licence review by McZusatz
on 3 February2013. Original YouTube source: https://www.youtube.com/watch?v=_7sCYyxw4Ic

Attribution: Street traffic, Editor, via Wikimedia Commons, CC BY 3.0. Derived
frames/overlays are modified for academic model evaluation. No endorsement.
Original recording is 26,490,572bytes; SHA256
e5facb24baf755f0c1193999d823e99f6032661ad2bdef5cc28cc1cbbfde03e2;
publisher SHA1 7f916030f14d84a65aa92077339f472897915fef verified.
Local: data/raw/wikimedia_street_traffic/Street_traffic.webm and acquisition.json.
Use: real-motion video integration only. No training, parking-space labels,
vehicle-box accuracy, tracking truth or entrance/exit evaluation. Derived JPGs
stay local under experiments/results/REAL-VIDEO-*/; source_attribution.json is
kept alongside them. No external publication performed.


## OpenCV registration references - SRC-DOC-016 / SRC-DOC-017

Read official installed-version4.13 documentation on24October2026:
- https://docs.opencv.org/4.13.0/dc/dc3/tutorial_py_matcher.html
- https://docs.opencv.org/4.13.0/d1/de0/tutorial_py_feature_homography.html

OpenCV contributors; public API/tutorial consultation, date-only access precision.
ORB binary descriptors use Hamming matching; robust findHomography returns inlier
support. Independent project implementation combines these APIs with documented
conservative bounds and same-camera training references. No tutorial text, code
excerpt or example images copied. Existing installed package/notices unchanged;
no new package, account, credentials or restricted data required. Documentation
content reuse rights are not asserted. Exact algorithm/settings/results are in
the registration run protocol; no independent final-test or camera identity claim.

## 25October2026 / higher-resolution region trial and annotation inspection

Primary sources consulted24October2026:
- MetaPKLot publisher https://github.com/DSBD-Research/MetaPKLot-Dataset and https://huggingface.co/datasets/DSBD-Research/MetaPKLot-Dataset ; pinned revision9218800c4eb2b7c1b17b51c8cdb07ad51686f8a2. PKLot-portion UFPR04 archive/README/CITATION receipts in data/resource_receipts.jsonl; originals in data/raw/metapklot_inspection/. No annotation JSON parsed, image acquired or model use. Verify exact-file rights and image/ROI correspondence before development-only extraction; no final labels.
- Associated publication metadata: Almeida, Alves, Kujavski, Alves and Oliveira, MetaPKLot: new challenges and protocols for vision-based parking lot management, Neural Computing and Applications38, article704(2026), DOI10.1007/s00521-026-12398-0. Metadata/repository review only, not full-paper methodological review.
- TRANCOS https://gram.web.uah.es/data/datasets/trancos/index.html ; scientific-research and DGT conditions, official SharePoint fetch failure; SRC-DS-011 candidate only, no download or use.
- KITTI https://www.cvlibs.net/datasets/kitti/user_submit.php requires registration/purpose declaration; existing SRC-DS-009 remains unacquired. CNRPark publisher site still unavailable; author repository links do not resolve source terms. No mirrors, account creation or gated downloads used.

MetaPKLot mixed-source README declares PKLot portion CC BY4.0, CNRPark-EXT ODbL1.0 and excludes redistribution of PLds images. Do not apply one licence to the whole repository. Publisher corrected-date mappings are only research notes; original PKLot files/manifests remain unchanged. Annotation rectangles bound label completeness; outside-ROI negatives are not assumed.44canonical source records; acquired archives are not automatically usable benchmark labels.

## 25October2026 / explicit gate counting and notebook04

SRC-VID-001 original Street traffic, Editor, Wikimedia Commons, CC BY3.0: https://commons.wikimedia.org/wiki/File:Street_traffic.webm . Additional derived overlays/notebook figures add detector boxes, gate and IDs, with attribution retained. Original recording/checksum unchanged; no endorsement. Real tracking outputs are predictions, not new ground truth.

## 25October2026 / presentation and practice guide

The presentation reuses existing SRC-DS-001PKLot photos/overlays under CC BY4.0, SRC-VID-001Street traffic by Editor under CC BY3.0, and the prior convolution lab figure with its explicitly synthetic numeric volume. Visible credits and speaker-note URLs remain attached. Actual asset hashes and bundled OpenAI presentation-tool provenance live in HEARTBEAT-20261025T000925Z/presentation_manifest.json. No new external image or dataset downloaded for the deck.

## 25October2026 / frozen occupancy and detector-fusion reliability

PKLot original source SRC-DS-001 reused under existing attribution/CC BY4.0. Primary publisher page https://web.inf.ufpr.br/vri/databases/parking-lot-database/ reviewed25October2026: general XML label description does not establish a default for absent attributes. Official https://www.inf.ufpr.br/lesoliveira/download/pklot-readme.pdf fetch timed out; no download/read claim. Local4selected original XMLs have396missing occupied attributes. No labels repaired/imputed; exact original files, crop transforms and attribution retained.

## 25 October 2026 / licensed labelled sequences and frame-index tracking

Primary DAVIS download page https://davischallenge.org/davis2017/code.html and official website licence schema reviewed25October2026. Official archive README/SOURCES preserved: aggregate CC BY-NC4.0, authors own sequences unless listed; car-turn/car-roundabout not external exceptions. Code repository BSD licence was not used as data permission. No third-party DAVIS code installed/copied; project-built bounded range decoder uses stdlibZIP/CRC. Exact URLs/times/ETag/ranges/member hashes in receipts;20MBoriginal subset, not full832MBarchive. Papers: Pont-Tuset et al.2017; Perazzi et al.2016. Foreground/reference and physical-fps limitations remain explicit.

## 25 October 2026 / live input quality and traffic-source admission

Source catalog now51 records, including SRC-DS-013..017 and SRC-PAP-011. See docs/TRAFFIC_SOURCE_ADMISSION.md and data/manifests/drive_thru_inspection_v1.json for exact primary URLs, partial-release restrictions, acquisition receipts and rejected uses. No model accuracy from these candidate assets.

## 25 October 2026 / SVD lesson completed after usage-limit interruption

Source catalog52. NumPy2.5SVD official technical reference SRC-DOC-018 supports the independent numerical lesson; no source text/code copied. PKLot training-image derivatives credited. Source14official HTML only, file-browser bundle403; no dataset labels/images acquired or use admitted. See docs/IMAGE_COMPRESSION_LESSON.md.

## 25 October 2026 / clear startup preflight and failed clean offline readiness gate

Source catalog53. SRC-PKG-002 captures exact PyPI release JSON and official PyTorch CPU indexes for existing pins;7metadata files,5core candidates,publisher hashes. No wheel assets downloaded or licence/closure/install acceptance claimed. See data/manifests/runtime_core_candidates_v1.json and per-URL resource receipts.

## 25 October 2026 / verified fresh app-only offline dependency installation

Source catalog54. SRC-PKG-003retains24official original wheel archives,publisher hashes/CRC and complete notices;33primary metadata acquisitions under SRC-PKG-002. Resolver no-download flag corrected append-only; network timestamps exactness limits explicit. Local academic installation only,no external redistribution clearance claim. See reports/offline_runtime/v1/WHEELHOUSE_MANIFEST.json and per-file receipts.

## 25 October 2026 / fresh offline Jupyter kernels verified

SRC-PKG-004adds83official immutable release JSON and83original wheel archives,49,287,471bytesof archives. Publisher hashes,ZIP CRC and complete embedded notices retained. Source catalog55;exact cache-copy times and resolver network-operation bounds preserved. Local academic use;no external redistribution clearance claim. See reports/offline_jupyter/v1/WHEELHOUSE_MANIFEST.json and append-only resource receipts.

## 25 October 2026 / local JupyterLab server route verified

Catalog57. SRC-DOC-019official Jupyter Server REST API and SRC-DOC-020official Jupyter messaging documentation consulted. Authored reference notes under data/research and append-only receipts retain exact URLs,local hashes and honest date-only consultation precision. Documentation rights not independently audited;reference only,no copied source content/assets/training use. Existing107wheel/notices profile unchanged.

## 25 October 2026 / combined offline demonstration verified in a fresh copy

Catalog57unchanged.419copied payload records preserve original hashes/source IDs,107original installer archives with full notices and107official per-release metadata files. No new package download or external publication. Wider source register is not an assertion that full datasets are included. Local academic use;external redistribution clearance remains unclaimed.

## 26 October 2026 / recovered CNR metadata qualification handoff

Official CNRpublisher HTTP page recovered after HTTPS failure;current links point to author HTTPS GitHub release. CSV18,132,695bytes/EXTZIP449,502,403bytes retained with exact receipts/local SHA;publisher digest absent.144,965EXTrecords map exactly to JPEG member names,9cameras/23dates.13/5/5global-date roles contain82,361train/30,525development/32,079reserved records;all cameras on each date stay together. No JPEG decompressed or model trained/scored. CSV fields were tokenized;occupancy values were not semantically used,and omitted from derived manifest. Database ODbLdeclared;individual image-content rights unqualified,soimages remain inspection-only under PROJECT_CONSTRAINTS rule5.7newsynthetic guard/parser tests and full191regressions pass. Temporary fixture permission errors and licence-download403preserved;primary licence read through web tool,no original licence HTML copy claimed. One metadata trial advances43->44;final images remain unopened/unclaimed. Usage-limit auto-review failure interrupted the documentation action before execution;no bypass or credit purchase. Handoff resumed after the known reset. Source catalog57updated in place;original models/packages intact. Next independent work:unused licensed PKLot date inventory and fresh reservations. Guide:docs/CNRPARK_DATA_QUALIFICATION.md.

## 26 October 2026 / new publisher-original parking archive verified

New SRC-DS-018 is the publisher repository bermalA/open-space-parking-dataset,not a CNR mirror. Its README explicitly declares author-created images/annotations and LICENSE declares dataset CC BY4.0. Pinned commit d4ea8d0afed823665c70102190641f2de28b6603 yields731photos/731matching label files (publisher518train/144valid/69test). A bounded94,163,307byte original archive was acquired;all1465file sizes/Git blob identities verified,102,520,255uncompressed bytes. No exact JPEG Git-blob duplicates found;this does not establish absence of near duplicates or source independence. Encoded image/label bytes were streamed/decompressed for hashes,but zero image pixels decoded and zero semantic annotation rows interpreted. Only three exact metadata files were extracted. Camera/capture dates,dimensions,geometry/exhaustiveness and source-content provenance are not independently verified. Publisher handle is recorded;paper citation incomplete. Image rights basis is this publisher declaration,not CNR terms. No training/scoring or benchmark admission. Original models/claims/earlier package remain unchanged. One completed asset-integrity trial advances54->55;wakeups38;catalog58;next100-run checkpoint100. Official Singapore snapshot43was collected at05:34UTC after a gap:0new matching later outcomes,36,258total,persistence MAE4.795797spaces.11,472expired targets remain unscored;matching coverage75.9648percent,not accuracy.1,159new forecasts frozen. Guide:docs/OPEN_SPACE_DATA_GUIDE.md;exact source URL/commit/local SHA and acquisition UTC in data/resource_receipts.jsonl;raw archive in data/raw/open_space_official/. Next:bounded train-only geometry/label/group admission,not automatic random-split benchmarking.

## 26 October 2026 / supplied space polygons and conservative source grouping

SRC-DS-018current usage:four preselected TRAIN images/294supplied polygon labels inspected;allsource conservatively development-exposed,not final-test eligible. Publisher rights/credit retained. Original archive and asset qualification stage unchanged. See usagev2 and docs/OPEN_SPACE_DATA_GUIDE.md.

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
