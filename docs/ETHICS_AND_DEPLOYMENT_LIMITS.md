# Ethics, privacy, bias and deployment limits (ETH-01)

Recorded 16 November 2026 from `data/source_manifest.csv`, `docs/LICENSING_RECORD.md`,
model cards and the experiment registry. This is a project record, **not legal advice or a
legal clearance**. University-specific rules are still unknown (AUD-01 blocked).

## 1. Permissions and data actually used

- All image and video data come from **published research datasets** or a public video under
  an open licence. No private cameras, no footage recorded by the project, no accounts,
  credentials, EULAs, payments or agreements were accepted.
- The only live source is the **Singapore car-park availability feed** (SRC-LIVE-001,
  Singapore Open Data Licence 1.0, authorised by the user). It is **aggregate lot counts**,
  not camera images, and is never presented as camera or segmentation accuracy.
- Rejected or deferred sources (Cityscapes, CARPK/PUCPR+, VIRAT, KITTI, MOT17, UA-DETRAC,
  BrnoCompSpeed) were not acquired, because their terms needed agreements, registration or
  were not established.

| Source (ID) | Licence as recorded | Obligation for this project |
|---|---|---|
| PKLot (SRC-DS-001) | CC BY 4.0 | Attribute; cite Almeida et al. 2015 |
| Parking Birmingham (SRC-DS-003) | CC BY 4.0 on UCI page; original OGL also mentioned | Attribute; verify OGL version before any redistribution |
| ACPDS (SRC-DS-021) | MIT (dataset, code, models per author paper) | Keep licence text and notice |
| Open-Space Parking (SRC-DS-018), UVG-VCM (SRC-DS-019) | CC BY 4.0 | Attribute |
| NDISPark (SRC-DS-020) | ODC-BY 1.0 at record level; per-image rights unqualified | Attribute; no blanket image licence assumed |
| DAVIS 2017 sequences (SRC-DS-012) | CC BY-NC 4.0 aggregate | **Non-commercial only**; exclude from any commercial use |
| Street traffic video (SRC-VID-001) | CC BY 3.0 | Attribute |
| Singapore feed (SRC-LIVE-001) | Singapore Open Data Licence 1.0 | Attribute; aggregate only |
| ResNet18 / Faster R-CNN / Mask R-CNN weights (SRC-MOD-001..003) | TorchVision BSD-3 code; weights inherit ImageNet/COCO terms | Local academic use only; **do not redistribute weights** |
| Python packages (SRC-PKG-001..004) | Per-wheel declared licences; notices retained | Keep notices with any package (see `models/dependency_audit.json`) |

## 2. Privacy

- Parking images can show **number plates, people and identifiable vehicles**. The system
  produces **slot occupancy, vehicle boxes/masks and counts only**. It does **not** read
  plates, identify people or link vehicles across cameras or days.
- Overlays and reports are saved **locally**. Nothing is uploaded or published by the app.
- For any real installation: get the site owner's permission, put up camera notices, blur
  plates and faces before storage, keep raw footage only as long as needed, and follow local
  data-protection law (in India, the Digital Personal Data Protection Act 2023).

## 3. Bias and representativeness

- **Few viewpoints.** PKLot covers three camera views (PUCPR, UFPR04, UFPR05). Most region
  models were trained mainly on these and transfer poorly to ACPDS views: best recorded
  ACPDS development IoU is about 0.53.
- **Development data reused.** ACPDS and PKLot development sets have been used across many
  trials, so their scores are optimistic and are not independent evidence.
- **Labels are partial.** Segmentation targets are the union of supplied bay polygons, not
  every parkable area; outside the union is unverified.
- **Conditions.** Weather, night, camera height and lot layout vary unevenly across sources.
  Failures by weather and view are recorded in the model cards, but coverage is incomplete.
- **Forecasts.** Birmingham data are from 2016 (UK); Singapore results describe one feed and
  period. Neither shows how forecasts would behave elsewhere.

## 4. Deployment limits

- **No universal accuracy claim.** Every number is tied to a named dataset, split and run.
- **Not validated on a real installation.** There is no ground truth from a camera at a site
  the project controls. Physical, manual and student acceptance tests remain open.
- **Promotion rules.** No candidate is promoted without passing sealed gates **and** fresh,
  qualified evidence. ACPDS TEST and the consumed Singapore final stay closed.
- **Human oversight.** The app shows uncertain, missing and stale states instead of guessing.
  It is for decision support, not automatic enforcement or charging.
- **Licence boundary.** Because of the DAVIS non-commercial terms and pretrained-weight
  terms, the current package is for **local academic use only**.

## 5. Open items

- Legal review of all terms (only declared licences were recorded).
- University ethics or data rules once the brief is available (AUD-01).
- Per-image rights for candidate sources that were not acquired.
