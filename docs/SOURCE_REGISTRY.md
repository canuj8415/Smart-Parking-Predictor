# Source registry

Canonical complete fields: `data/source_manifest.csv`. Actual asset-level access times, retrieval URLs, bytes, hashes and local paths: `data/resource_receipts.jsonl`.

| ID | Resource | Status | Local storage |
|---|---|---|---|
| SRC-DS-001 | [PKLot](https://web.inf.ufpr.br/luizoliveira/research-interests/pklot/) | downloaded | data/raw/pklot_subset/PKLot.tar.gz |
| SRC-DS-002 | [CNRPark+EXT](http://cnrpark.it/) | official archive/metadata acquired;images inspection-only | data/raw/cnrpark_official/ |
| SRC-DS-003 | [Parking Birmingham](https://archive.ics.uci.edu/dataset/482/parking+birmingham) | downloaded | data/raw/uci_parking_birmingham/parking-birmingham.zip |
| SRC-DS-004 | [COCO 2017](https://cocodataset.org/) | candidate | not downloaded |
| SRC-DS-005 | [Cityscapes](https://www.cityscapes-dataset.com/license/) | rejected | not downloaded |
| SRC-DS-006 | [MOT17](https://motchallenge.net/data/MOT17/) | rejected | not downloaded |
| SRC-DS-007 | [CARPK and PUCPR+](https://lafi.github.io/LPN/) | rejected | not downloaded |
| SRC-DS-008 | [VIRAT Ground Video release 2.0](https://viratdata.org/) | candidate | not downloaded |
| SRC-DS-009 | [KITTI Tracking](https://www.cvlibs.net/datasets/kitti/eval_tracking.php) | rejected | not downloaded |
| SRC-DOC-001 | [PyTorch C++ frontend](https://docs.pytorch.org/cppdocs/frontend.html) | used | not downloaded |
| SRC-DOC-002 | [LibTorch installation](https://docs.pytorch.org/cppdocs/installing.html) | used | not downloaded |
| SRC-DOC-003 | [PyTorch C++ training tutorial](https://docs.pytorch.org/tutorials/advanced/cpp_frontend.html) | used | not downloaded |
| SRC-DOC-004 | [DJL engines](https://djl.ai/docs/engine.html) | used | not downloaded |
| SRC-DOC-005 | [DJL PyTorch engine](https://djl.ai/engines/pytorch/pytorch-engine/) | used | not downloaded |
| SRC-DOC-006 | [OpenCV license page](https://opencv.org/license/) | used | not downloaded |
| SRC-DOC-007 | [PyTorch LICENSE](https://github.com/pytorch/pytorch/blob/main/LICENSE) | used | not downloaded |
| SRC-DOC-008 | [Learn the Basics: Python PyTorch](https://docs.pytorch.org/tutorials/beginner/basics/intro.html) | used | not downloaded |
| SRC-DOC-009 | [JupyterLab installation](https://jupyterlab.readthedocs.io/en/stable/getting_started/installation.html) | used | not downloaded |
| SRC-DOC-010 | [COCO terms](https://raw.githubusercontent.com/cocodataset/cocodataset.github.io/master/dataset/termsofuse.htm) | used | not downloaded |
| SRC-DOC-011 | [COCO official download definitions](https://raw.githubusercontent.com/cocodataset/cocodataset.github.io/master/dataset/download.htm) | used | not downloaded |
| SRC-DOC-012 | [deep-parking author repository README](https://github.com/fabiocarrara/deep-parking) | used | not downloaded |
| SRC-PAP-001 | [Deep Residual Learning for Image Recognition](https://arxiv.org/abs/1512.03385) | used | not downloaded |
| SRC-PAP-002 | [Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks](https://arxiv.org/abs/1506.01497) | used | not downloaded |
| SRC-PAP-003 | [You Only Look Once: Unified, Real-Time Object Detection](https://arxiv.org/abs/1506.02640) | used | not downloaded |
| SRC-PAP-004 | [Auto-Encoding Variational Bayes](https://arxiv.org/abs/1312.6114) | used | not downloaded |
| SRC-PAP-005 | [Long Short-Term Memory](https://direct.mit.edu/neco/article/9/8/1735/6109/Long-Short-Term-Memory) | used | not downloaded |
| SRC-PAP-006 | [U-Net: Convolutional Networks for Biomedical Image Segmentation](https://arxiv.org/abs/1505.04597) | used | not downloaded |
| SRC-PAP-007 | [Microsoft COCO: Common Objects in Context](https://arxiv.org/abs/1405.0312) | used | not downloaded |
| SRC-PAP-008 | [Deep learning for decentralized parking lot occupancy detection](https://github.com/fabiocarrara/deep-parking) | used | not downloaded |
| SRC-PAP-009 | [PKLot - A robust dataset for parking lot classification](https://web.inf.ufpr.br/luizoliveira/research-interests/pklot/) | used | not downloaded |
| SRC-LIVE-001 | [Singapore Carpark Availability](https://api.data.gov.sg/v1/transport/carpark-availability) | used | data/raw/singapore_live/ |
| SRC-MOD-001 | [Faster R-CNN ResNet50 FPN V2 COCO_V1](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.detection.fasterrcnn_resnet50_fpn_v2.html) | used | models/pretrained/fasterrcnn_resnet50_fpn_v2.pth |
| SRC-MOD-002 | [Mask R-CNN ResNet50 FPN COCO_V1](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.detection.maskrcnn_resnet50_fpn.html) | used | models/pretrained/maskrcnn_resnet50_fpn.pth |
| SRC-MOD-003 | [ResNet18 ImageNet1K V1](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet18.html) | used | models/pretrained/resnet18_imagenet.pth |
| SRC-DOC-013 | [TorchVision repository and pretrained-model disclaimer](https://github.com/pytorch/vision) | used | not downloaded |
| SRC-DOC-014 | [Singapore live API and licence](https://data.gov.sg/open-data-licence) | used | not downloaded |
| SRC-PKG-001 | [opencv-python-headless 4.13.0.92 Windows wheel](https://pypi.org/project/opencv-python-headless/4.13.0.92/) | used | dependencies/wheels/opencv_python_headless-4.13.0.92-cp37-abi3-win_amd64.whl |
| SRC-DOC-015 | [PKLot original laboratory page](https://web.inf.ufpr.br/vri/databases/parking-lot-database/) | used | not downloaded |
| SRC-PAP-010 | [Mask R-CNN](https://arxiv.org/abs/1703.06870) | candidate | not downloaded |

Documentation consulted in earlier sessions has date-only precision; acquisition receipts preserve actual times. Unknowns are not filled with guesses. See LICENSING_RECORD.md and THIRD_PARTY_SOURCES.md for use limits.


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

## 26 October 2026 / UVG development qualification

Sourcecatalog now60records. AddedSRC-DS-019(UVGdevelopmenttrafficassets) andSRC-DOC-021(primarypublishermetadata/licensing). Exactassetreceipts andboundaries:UVG_DEVELOPMENT_GUIDE.md.

## 26 October 2026 / real traffic development evidence

Catalogremains60sources. SRC-DS-019usageupdatedtoactualpairedresolutionDEVELOPMENTinferencewithfullfailedabsolutegatesretained. OfficialSingaporecollectionat13:11UTCusesexistingSRC-LIVE-001andoriginallicence/receipts. No newsourceID orfinalclaim.

## 26 October 2026 / diagnosis and archived vision lesson

60sourcesunchanged. SRC-DS-019usageextendstodistinctdevelopmentoutputdiagnosisandactualreadonlyJupyterlesson. Singapore55thsnapshot/newreceiptusesexistingSRC-LIVE-001licenceandminimuminterval;no learnedtargetscoring.

## 26 October 2026 / native-detail crop study

Sourcecatalog60unchanged. SRC-DS-019usageextendsnative-detailcropdevelopmenttrialwithallfailedadmissiongatesretained. Singapore56thsnapshotand5thlearnerbatchuseexistingSRC-LIVE-001receipts/licence;no learnedinterimaccuracy.

## 26 October 2026 / mask review safety evidence

60sourcesunchanged. SRC-DS-019usageaddsarchivedprediction-onlymaskcandidatewithfailedpreservationgatesandinspection-onlyexport. OfficialSingapore57thsnapshotand6thforecastbatchuseexistingSRC-LIVE-001receipts/licence;no learnedinterimaccuracy.

## Sources SRC-DS-020 and SRC-DOC-022 / 26 October

NDISParkofficialZenodo6560823/version1.0/DOI10.5281/zenodo.6560823:Ciampi,Santiago,Costeira,Gennaro,Amato. MetadataandexactREADMEonly;recordlicenceODC-BY,notCCBY. PrimaryODCAttribution1.0scope distinguishesdatabasefromcontents;individualimage/annotationrightsremainunqualified. See https://zenodo.org/records/6560823 and https://opendatacommons.org/licenses/by/1-0/ . Sourcecatalog62uniqueIDs;receiptregistrationUTCseparatefromoriginalrange/licenceUTC;APIcompletionbounded. Originaltailincludes39021opaque noncentralbytes;wholearchivechecksumunverified. Fullscopeandattribution:NDISPARK_QUALIFICATION.md.

## 27 October 2026 IST / current group-role audit and seven-page evidence addendum

62permanentIDsunchanged. Metadata-onlyreconciliationusesexistingmanifests/durableclaims,noimagecontentornewexternalacquisition. SRC-DS-001masterpermissionfieldcorrectsstaleinitial-discovery No data use yet placeholder;recordedCCBY4.0licence/actualpastuse unchanged. FrozenreportCSVsnapshotremainsexactasatinputfreeze;thismastercleanupislatersourcedmetadata,norewriteofearlierrecords.

## 27 October 2026 IST / fresh licensed ACPDS development admitted; TEST remains closed

SRC-DS-021 Martin Marek,Action-Camera Parking Dataset;official https://github.com/martin-marek/parking-space-occupancy ;author https://arxiv.org/abs/2107.12207 explicitly includes dataset in MIT grant. Saved primary documents/loader/licence/metadata with hashes:docs/source_evidence/acpds_20261026/. Per-range receipts:data/resource_receipts.jsonl. Source roles sealed before semantics. See docs/ACPDS_QUALIFICATION.md. 63unique source IDs. No author-reported 98% score claimed as local accuracy.

## 27 October 2026 IST / real ACPDS images qualified; unchanged classifier fails source-shift gates

SRC-DS-021 now includes 38 CRC-verified development JPEGs and an unchanged classifier DEVELOPMENT evaluation. All original bytes, exact UTC/range/ETag/SHA receipts and MIT notice are retained. Saved coordinate/visualization code evidence:docs/source_evidence/acpds_image_adapter_20261026/. The author's results are not local results; final pixels/labels remain closed. No new source IDs were added.

## 27 October 2026 IST / one bounded source-balanced head trial and complete TRAIN acquisition

SRC-DS-021 original author/MIT/pinned revision remain unchanged. All 266 development JPEGs now have receipted original files and qualified normalized polygons; 27 default-closed TEST names and whole publisher TEST remain unopened. Training/evaluation usage is ACPDS-BALANCED-HEAD-20261026T234728842213Z. Old PKLot caches are reused development retention data, not fresh final evidence. Candidate and failed gates are preserved without app promotion. 63 unique source IDs.

## 27 October 2026 IST / rejected raster translation and exact crop-cache validation

Source identities remain 63. SRC-DS-021 development imagery supports byte-equivalence validation and derived RGB cache only; publisher TEST remains closed. Original author/MIT attribution remains unchanged. Current CNR access timeout and NDIS page consultation did not establish new individual-content permission; data/resource rights statuses are unchanged. No new images, labels or rights from those two sources were admitted.

## 27 October 2026 IST / last-block adaptation improves accuracy but fails vacancy safety

SRC-DS-001/SRC-DS-021 received only existing TRAIN/development use in ACPDS-LAST-BLOCK-20261027T004612152849Z. Old RGB preparation is hash/label/role/identity checked. No final-source pixel/label access or new source/licence grant occurred. Both research candidates and their failed safety gates remain preserved; original source rights/attribution unchanged. 63 permanent source IDs.
