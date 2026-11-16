# Research session log

## 24 October 2026 — Master Add-on 01 and Python correction

Read the add-on completely and preserved the original project scope. Reviewed
the existing plan and empty data/model state. The two university documents are
still unavailable; no claim of an official requirements audit is made.

Primary-source research covered PKLot, CNRPark+EXT, UCI Birmingham, COCO,
Cityscapes, MOT17, CARPK/PUCPR+, VIRAT and KITTI Tracking. Source IDs, exact URLs,
selection reasons, licensing uncertainties and rejection reasons are recorded
in SOURCE_REGISTRY.md and data/source_manifest.csv.

Selected **SRC-DS-003, UCI Birmingham**, for a small independent real-world
forecast-data track. The official page states CC BY 4.0, mentions original OGL
provenance and links directly to the downloaded archive. The archive and its
only CSV were inspected and hashed. Exact acquisition time:
2026-10-24T08:40:31.2044009+00:00 (14:10:31.2044009 Asia/Calcutta).
The official page was saved at 08:41:04.6181203 UTC for provenance review.

The first restricted shell download failed to resolve the host. The same public
download succeeded with authorized network access. No authentication, accounts,
EULAs, payments or certificate-verification bypasses were used.

CNRPark failed in the browsing tool and its direct HTTPS request failed during
TLS establishment. Author-repository links were confirmed, but its live license
and files remain unverified. No CNR archive was downloaded. PKLot's official
license/page was read; its advertised 4.6 GB archive was deferred while a small
source provides immediately testable data and the storage/toolchain plan remains
unsettled. No mirror or synthetic replacement was passed off as the original.

COCO is a candidate for genuine vehicle boxes and instance masks, with separate
image-license review. Cityscapes/CARPK/KITTI require user-side registration or
terms workflows, so none was accessed through those gates. VIRAT ground video
has a protection agreement; no agreement was accepted and no video acquired.
MOT17 was rejected as the immediate vehicle-flow source because its reviewed
benchmark is pedestrian focused.

Verified bibliographic metadata/abstracts for ResNet, YOLO, Faster R-CNN, VAE,
LSTM, U-Net and COCO. Author-provided PKLot/CNR bibliographic details were checked.
The resulting bibliography does not imply full-paper review, replicated paper
results, or acquired model weights.

An initial PowerShell preparation run validated the real CSV. The user then
explicitly requested **Python with Jupyter**. Its temporary preparation utilities
were replaced with reusable Python modules and scripts; no PowerShell dataset
implementation is retained. Existing Python/Jupyter packages were inspected and
reused without installation. The independent data tools may advance under the
add-on; model/application implementation still awaits the primary-source audit.

Python preparation found 35,717 original records from 30 entities, retained
35,116, quarantined 385 out-of-bounds records and removed 216 identical duplicate
copies in 160 duplicate-key groups. No conflicting valid duplicate groups were
found. Splits use 73 observed dates globally, with 51/10/12 dates assigned to
training/validation/test. No future observations were randomly moved into training.
Six data-integrity unit tests passed. No model training/evaluation occurred.

Open issues: source timestamp timezone/occupancy terminology, overnight gaps,
per-entity coverage, possible physical overlaps, image data acquisition and
segmentation labels, original OGL provenance, and official university requirements.

## Product implementation research and evidence — 24 October 2026

The user authorized the exact main-product implementation despite missing
university documents. Selected TorchVision Faster R-CNN/ResNet50 plus Mask R-CNN;
verified official API/weight metadata and code/pretrained-model licence distinction.
The user explicitly approved the Singapore public-feed licence. Two genuine
snapshots were acquired and stored with provider times; they are not camera outputs.

Small PKLot streaming prefixes had no matching image/XML pairs. Verified HTTP
ranges then completed the 3,860,376,865-byte original archive, yielding 1,701
paired working frames across 96 folder-date labels. An invalid calendar label
was quarantined. The fixed final vision development subset uses 60 frames from
20 valid dates, with 2,605/360/360 slot crops in train/validation/test.
The duplicate transfer chunks were removed only after the full original and
matching acquisition metadata were verified; the original archive remains local.

Real training and evaluation logs preserve an initial failed semantic model,
its corrected training protocol and a fresh semantic final holdout. The LSTM
loses to persistence; this is reported rather than tuned against the observed test.
External detector accuracy/mAP remains unmeasured because slot polygons are not
vehicle-box ground truth. All scientific figures/tables come from saved real runs.
The visual desktop check stopped on the user's Escape; subsequent checks were
headless or artifact inspections. Exact metrics and test limits: TEST_RESULTS.md.


## 24 October2026 - real-motion integration and learning handout

AI assistant researched the primary Commons description/licence, fetched the verified original public recording, implemented timestamp-based sampling and unknown-occupancy semantics, preserved the failed validation, completed the repaired real-motion trial and 44 software checks, continued prospective Singapore scoring, and authored/rendered/inspected a six-page beginner PDF using the PDF skill. No student-authored training or independent mastery is implied. See AUTONOMOUS_PROGRESS.md and SRC-VID-001 for exact evidence.


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

## 25October2026 / frozen occupancy and detector-fusion reliability

PKLot original source SRC-DS-001 reused under existing attribution/CC BY4.0. Primary publisher page https://web.inf.ufpr.br/vri/databases/parking-lot-database/ reviewed25October2026: general XML label description does not establish a default for absent attributes. Official https://www.inf.ufpr.br/lesoliveira/download/pklot-readme.pdf fetch timed out; no download/read claim. Local4selected original XMLs have396missing occupied attributes. No labels repaired/imputed; exact original files, crop transforms and attribution retained.

## 25 October 2026 / training-only robust forecast selection

Reused UCI Parking Birmingham SRC-DS-003 and existing official Singapore SRC-LIVE-001 with their recorded licences/receipts. No newly downloaded training dataset or new library. Training-only normalized group objective and blocked selection are project-designed; no external algorithm attribution invented. Later date reservation uses source identifiers/timestamps only; coverage and original-ingestion limitations recorded.

## 25 October 2026 / clock coverage and one-time later-date forecast evaluation

Reused SRC-DS-003 under existing UCI attribution/rights; no new source or library. Phase choice uses training coverage only. One-time temporal evaluation on previously unscored source dates retains initial-ingestion/blinding and variable-horizon limitations. Official Singapore remains distinct, with its authorized licence/receipts. No private video/CCTV, external publication or paid service used.

## 25 October 2026 / conditional known-camera region stability

Reused PKLot SRC-DS-001/UFPR/Almeida and colleagues under recorded CC BY4.0 plus existing ImageNet ResNet18 weights SRC-MOD-003. Project-designed stability routing; no externally attributed algorithm invented. Fitted camera geometry from141training masks/18dates; no final masks used for fitting/selection. Credited figure shows saved derived final images/masks only. Singapore source remains distinct.

## 25 October 2026 / licensed labelled sequences and frame-index tracking

Primary DAVIS download page https://davischallenge.org/davis2017/code.html and official website licence schema reviewed25October2026. Official archive README/SOURCES preserved: aggregate CC BY-NC4.0, authors own sequences unless listed; car-turn/car-roundabout not external exceptions. Code repository BSD licence was not used as data permission. No third-party DAVIS code installed/copied; project-built bounded range decoder uses stdlibZIP/CRC. Exact URLs/times/ETag/ranges/member hashes in receipts;20MBoriginal subset, not full832MBarchive. Papers: Pont-Tuset et al.2017; Perazzi et al.2016. Foreground/reference and physical-fps limitations remain explicit.
