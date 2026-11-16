# Literature review notes — initial, not full-paper reviews

Titles/authors/years and citation keys are in the checked bibliography. Entries
using arXiv are explicitly preprint citations, not fabricated venue records.
No paper benchmark is reported as a result measured by this project.

| Citation key | Verified source / contribution | Project use | Limits of current review |
|---|---|---|---|
| stolfi2017birmingham | UCI dataset page and DOI; real time-stamped occupancy observations | Independent forecast-data track | Timezone/original OGL wording and count terminology need clarification |
| almeida2015pklot | Original dataset page; occupied/vacant slot images | Classifier/mapping candidate | Dataset paper not fully read; archive uninspected |
| amato2017deep | Author repository bibliography; decentralized parking CNN study | Occupancy and cross-camera background | Repository metadata checked; publisher full text inaccessible |
| he2015resnet | Original arXiv metadata/abstract; residual learning | ResNet classifier/backbone rationale | Parking transfer must be measured; no weights acquired |
| ren2015faster | Original arXiv metadata/abstract; shared region proposals | Detector comparison rationale | Paper speed is not laptop speed; no reproduction |
| redmon2015yolo | Original arXiv metadata/abstract; unified single-pass detection | Detector comparison rationale | Does not license a modern YOLO implementation or its weights |
| kingma2013vae | Original arXiv metadata/abstract; variational inference and reparameterization | Compact generative lab | Full derivation and own experiment remain pending |
| hochreiter1997lstm | Publisher metadata/abstract; long-term sequence memory | LSTM fundamentals | Modern gate variants/forecasting performance need separate study |
| ronneberger2015unet | Original arXiv metadata/abstract; contracting/expanding segmentation architecture | Semantic segmentation candidate | Biomedical success does not establish parking accuracy |
| lin2014coco | Original arXiv metadata/abstract; per-instance annotations for scene understanding | Box/mask source candidate | Paper statistics differ from exact 2017 package counts; image licenses separate |
| he2017mask | Original arXiv metadata/abstract; instance-mask branch parallel to box recognition | Explains actual Mask R-CNN outputs | Publisher paper scores are not project measurements; no full-paper review or reproduction claimed |

Later full-paper notes should record split protocols, assumptions, domain gaps,
computational requirements, failure cases and relevant equations, not only
headline scores. A dedicated parking-forecasting paper still needs a full verified
bibliographic and methodological review before it is cited in the report.

## 25October2026 / higher-resolution region trial and annotation inspection

Primary sources consulted24October2026:
- MetaPKLot publisher https://github.com/DSBD-Research/MetaPKLot-Dataset and https://huggingface.co/datasets/DSBD-Research/MetaPKLot-Dataset ; pinned revision9218800c4eb2b7c1b17b51c8cdb07ad51686f8a2. PKLot-portion UFPR04 archive/README/CITATION receipts in data/resource_receipts.jsonl; originals in data/raw/metapklot_inspection/. No annotation JSON parsed, image acquired or model use. Verify exact-file rights and image/ROI correspondence before development-only extraction; no final labels.
- Associated publication metadata: Almeida, Alves, Kujavski, Alves and Oliveira, MetaPKLot: new challenges and protocols for vision-based parking lot management, Neural Computing and Applications38, article704(2026), DOI10.1007/s00521-026-12398-0. Metadata/repository review only, not full-paper methodological review.
- TRANCOS https://gram.web.uah.es/data/datasets/trancos/index.html ; scientific-research and DGT conditions, official SharePoint fetch failure; SRC-DS-011 candidate only, no download or use.
- KITTI https://www.cvlibs.net/datasets/kitti/user_submit.php requires registration/purpose declaration; existing SRC-DS-009 remains unacquired. CNRPark publisher site still unavailable; author repository links do not resolve source terms. No mirrors, account creation or gated downloads used.

MetaPKLot mixed-source README declares PKLot portion CC BY4.0, CNRPark-EXT ODbL1.0 and excludes redistribution of PLds images. Do not apply one licence to the whole repository. Publisher corrected-date mappings are only research notes; original PKLot files/manifests remain unchanged. Annotation rectangles bound label completeness; outside-ROI negatives are not assumed.44canonical source records; acquired archives are not automatically usable benchmark labels.

## 25 October 2026 / live input quality and traffic-source admission

Source catalog now51 records, including SRC-DS-013..017 and SRC-PAP-011. See docs/TRAFFIC_SOURCE_ADMISSION.md and data/manifests/drive_thru_inspection_v1.json for exact primary URLs, partial-release restrictions, acquisition receipts and rejected uses. No model accuracy from these candidate assets.
