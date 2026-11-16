# What the new parking-image check measures

The source qualification admitted development annotations without opening the
publisher's test labels. This step acquires real development photographs and
checks the unchanged project's occupancy classifier on them. It uses the
author's 35 validation images and 1,904 labelled parking spaces. Three seeded
training photos provide a separate visual check of the format.

The original 4,000 by 3,000 JPEG files are preserved. A selective archive reader
requests only admitted development members, checks the server's archive identity,
validates exact byte ranges, and checks the ZIP descriptor, expanded size and CRC.
It refuses unlisted names, oversized members and ambiguous duplicate names.
No complete test-image member is requested or decoded.

The author's code scales normalized x coordinates by width minus one and y
coordinates by height minus one. We preserve this convention and the raw image
orientation. Supplied polygons describe parking spaces on the ground. A vehicle
can project outside its ground-space polygon or cover a neighbouring space in
an elevated camera image. The three training overlays visibly demonstrate this.
Their red True labels identify occupied spaces; green False labels identify
vacant spaces. This spot check does not independently verify every annotation.

The baseline keeps the original ResNet18 checkpoint and existing input pipeline:
mask outside a supplied polygon with grey, take its axis-aligned bounding crop,
resize to 96 by 96, and use the existing normalization. It does not fit a model,
rectify perspective, change thresholds or run a vehicle detector. A score of at
least 0.5 is a hard occupied prediction. Scores at most 0.25 are confident vacant
decisions; scores at least 0.75 are confident occupied decisions. Other scores
remain uncertain. These scores have not been calibrated as probabilities of
correctness on ACPDS.

Hard accuracy uses every labelled space. Selective accuracy uses only decisions
outside the uncertainty interval, so always read it with coverage. A false vacant
decision means an occupied space was offered as vacant. Its fraction of actual
occupied spaces and its fraction of vacant predictions answer different questions.
The report retains both denominators, the full confusion tables, calibration
diagnostics and results for each image. The image-average accuracy gives each
image equal weight; the aggregate accuracy gives each space equal weight.

The protocol freezes readiness gates before any validation predictions: at least
95% aggregate hard accuracy, at least 90% for every image, no more than 1% of
occupied spaces confidently called vacant, and at most 10% uncertain predictions.
Failing a gate is evidence to preserve, not a reason to adjust a threshold on the
same data. The exact outcome is in `reports/acpds_occupancy_latest.json`.

This is a development baseline using known space geometry. It does not measure
automatic bay discovery, parking-region segmentation, detector fusion, continuous
traffic-video reliability or final-test generalization. The author states that
publisher partitions use different parking lots; exact capture dates, independent
location verification and upstream pretraining overlap remain unknown. No local
result is the author paper's reported benchmark score.

A later candidate should fit only the training partition, use a prespecified
validation selection and check retention on the existing PKLot development data.
Do not run an open-ended crop or threshold search. Keep all 27 default-closed
test image names and the whole publisher test partition closed until a durable
whole-partition claim, a frozen selection and final evaluation gates are ready.
The original production classifier remains unchanged.

For a student explanation, identify the source of the polygons, explain why a
missing detection cannot prove vacancy, calculate one false-vacancy denominator,
and distinguish validation from an untouched final test. This guide is practice
material; it does not establish student mastery or university acceptance.
