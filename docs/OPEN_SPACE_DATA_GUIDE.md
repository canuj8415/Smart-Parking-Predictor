# Another parking dataset: what we actually collected

Current status: all518TRAIN photos checked;517image/label pairs passed the
format checks,one mixed-format file quarantined. The accepted CSV contains
39,068supplied space outlines. Two development-only training studies used the same16,448selected crops.
Neither beat the starting comparison. The app stayed unchanged.

Think of this as receiving a new workbook of parking photographs. We have
checked that every delivered file matches the publisher's fixed version. We
have not yet marked an AI exam using those photographs.

| Item | Verified result |
|---|---|
| Publisher | [bermalA/open-space-parking-dataset](https://github.com/bermalA/open-space-parking-dataset) |
| Fixed version | `d4ea8d0afed823665c70102190641f2de28b6603` |
| Publisher declaration | Authors created the photos and annotations; dataset licensed CC BY4.0. The publisher's personal name and full paper citation are absent. |
| Original download | `data/raw/open_space_official/d4ea8d0afed823665c70102190641f2de28b6603/publisher.tar.gz` |
| Download size | 94,163,307 bytes |
| Local SHA256 | `3485666aabd201284a4eb5778229b829bbbd6aa3c7527ae57f1db31afc99aed1` |
| Files | 731 JPEG photos,731 matching annotation files,README,LICENSE and data.yaml:1,465 files |
| Published folders | 518train,144valid,69test images |
| Classes declared | `0: space-occupied`, `1: space-vacant`; YOLO format |
| Exact file check | Every size and Git blob identity agrees with the pinned publisher tree |
| Original preservation | Archive retained intact; only three exact metadata files extracted |
| Attribution | bermalA/open-space-parking-dataset (2025),Open-Space Parking Occupancy Dataset,CC BY4.0; incomplete associated-paper citation recorded |

The checksum above identifies our saved archive. The publisher Git tree
independently binds each contained file using Git's SHA1 blob format; it does
not provide an independent SHA256 for the compressed archive.

For the integrity check,encoded image and label bytes were decompressed and
hashed. At that initial integrity stage,no image pixels were decoded or label rows
interpreted. The later training-only inspection below opened four photos. No
model was trained or scored,and no original final test was replayed. There are no
exact JPEG-byte duplicates across folders. Visually similar or neighbouring
photographs can still exist.

Before model use,we need to check image sizes,what the polygon annotations actually
cover,and whether nearby photos share a camera or capture session. Those
details are unknown. Folder names such as "test" do not establish independence.
Initial visual/annotation inspection must use explicitly selected publisher
training examples. No validation/test-image selection by model outcome is
allowed. This entire collection is now conservatively development-exposed. Future
final evaluations must use fresh independent data elsewhere,with a frozen
group protocol and a durable once-only claim.

This source's publisher declaration applies to this source. It does not settle
the separate CNR image-rights question. CNR images remain unopened.

Acquisition URLs,actual UTC times and hashes are in
`data/resource_receipts.jsonl`;publisher tree/text evidence is in
`data/manifests/open_space_publisher_metadata_20261026.json`;the usage decision
is in `data/manifests/open_space_usage_qualification_v1.json`. The latest
qualification report is linked by `reports/open_space_data_latest.json`.
Original metadata files beside the archive preserve the publisher's wording.

New images are preparation for further work. They do not add an accuracy score
or change the running app's selected model.

## 26 October 2026 / supplied space polygons and conservative source grouping

We opened four TRAIN photos chosen before looking at their contents:train001,173,345and518. Each is1280x640. Their files contain294parking-space polygons:235labelled occupied and59labelled vacant. They are perspective outlines,not ordinary rectangular boxes. Think of tracing the painted shape of each parking bay. Some photos show daylight and one shows night. The initial box-reader failure is saved;the new polygon reader and all227software tests pass. These numbers count supplied annotations,not correct AI predictions. There are no capture dates in these four images’EXIF. Their related backgrounds mean the whole source is conservatively development material. The publisher’s validation/test photos remain unopened,but cannot be called an independent exam for this project. At that four-photo inspection stage,we had not checked every annotation or trained a model with this source. Unannotated scene regions are not automatically empty/background labels. Current source decision:`data/manifests/open_space_usage_qualification_v2.json`. Visual evidence:`experiments/results/OPEN-SPACE-TRAIN-INSPECTION-20261026T054402004396Z/contact_sheet.png`. Next:broader TRAIN-only quality audit and a clear training plan with fresh independent final data elsewhere.

The zero validation/test-read figure counts member payloads opened for image
decoding or semantic label interpretation. The compressed archive was read for
checksums,and its member headers were scanned to locate the four TRAIN pairs.
That does not mean the other original bytes were never touched.

## 26 October 2026 / complete TRAIN audit with quarantine and unknown-aware support

We checked all518photos in the publisher’s TRAIN folder.517photo/label pairs passed the strict format checks,containing39,068supplied parking-space outlines. One file mixes a rectangular-box row into polygon labels;the whole file and its69rows are set aside unchanged. This is like setting aside a worksheet with a different answer format rather than guessing how to mark it. All photos are1280x640 and none supplies an EXIF capture date. There are907visually similar hash-pair candidates;these are leads for checking,not907proven duplicates. No exact decoded-photo duplicates were found within TRAIN. Gray in the new coverage pictures means unknown:outside labelled spaces or where opposite labels overlap. We do not tell the model that an unlabelled street or bay is empty. These pictures are label diagnostics,not AI answers. The actual accepted polygon CSV is `data/splits/open-space-train-audit-v1/OPEN-SPACE-TRAIN-AUDIT-20261026T061416550627Z/polygons.csv`;it retains source image,file hashes,row text,class and original polygon coordinates. The frame/quarantine/similarity files beside it preserve rejected files and screening results. Exact copied TRAIN originals are under `outputs/open_space_train_audit/OPEN-SPACE-TRAIN-AUDIT-20261026T061416550627Z/originals`. Publisher validation/test photos stay unopened semantically;allsource remains development material. Next:prepare small masked occupancy crops and test a bounded training idea against existing development data. This audit adds no model accuracy. Current decision:`data/manifests/open_space_usage_qualification_v3.json`.

## 26 October 2026 / genuine source-balanced head training retained the warm comparison

A separate experimental model trained on26,552small parking-space pictures:10,104from PKLot and16,448from the new source. After two learning passes,it made20mistakes on the same2,028development examples,versus12for its starting comparison. Wrong confident-empty decisions rose4to6. The fixed selection rule kept the starting comparison checkpoint. The running app was not replaced. New-park/night accuracy was not tested. Excel report: outputs/training_report_20261026T063846Z/Smart_Parking_Training_Study.xlsx. Crop records: data/processed/source_occupancy_crops/SOURCE-CROPS-20261026T064244765369Z/manifest.json. Original archives,excluded samples,caches and failed trained checkpoints remain preserved. Current source decision:usagev4. Next:inspect paired development mistakes before another distinct training idea.

## 26 October 2026 / paired transfer diagnosis and rejected teacher-anchored study

A teacher-retention penalty was tested after paired error diagnosis. The plain study made20development mistakes and this second study18,while the starting comparison made12. Both were rejected. Better fit on already-seen training examples is not an independent score. See docs/TRANSFER_LEARNING_EXPLAINED.md and outputs/transfer_report_20261026T070847Z/Smart_Parking_Transfer_Comparison.xlsx. Source usagev5retains the development-only restriction and all earlier records.
