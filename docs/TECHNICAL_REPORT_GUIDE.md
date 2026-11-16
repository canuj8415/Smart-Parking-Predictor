# Read the current technical report

Open `output/pdf/smart_parking_technical_report_v003.pdf` for the 12-page technical
draft. Start with the system overview, then read data/provenance, model methods,
measured results, live evidence, lessons, and remaining limitations. Think of the
system as a parking attendant: camera models find cars, configured space shapes
define bays, the occupancy classifier checks those bays, and historical patterns
help estimate later availability. Singapore provides separate official aggregate
space counts; it does not mark cars in our camera pictures.

`reports/technical_report_latest.json` identifies the current PDF and its checksum.
`reports/technical_report_v003/report_inputs.json` pins 15 exact input records.
`source_manifest_snapshot.csv` in that folder preserves all 45 source entries;
`resource_receipts_snapshot.jsonl` preserves acquisition URL, time, local path,
licence and checksum records. Their original live registers remain under `data/`.

Original pictures/annotations are under `data/raw/pklot_subset/`; the original
Birmingham CSV is `data/raw/uci_parking_birmingham/dataset.csv`, with separate
prepared splits under `data/splits/birmingham-global-days-v1/`. Singapore raw JSON
is under `data/raw/singapore_live/`; normalized history is
`data/processed/singapore_live_observations.csv`; frozen prospective forecasts,
later matched scores and coverage summary are under
`data/processed/singapore_prospective/`. Detailed exact paths are in the report
and dataset inventory. DAVIS selected sequence originals remain under
`data/raw/davis2017_subset/`; whole final sequences already consumed stay closed
to tuning. Do not treat development illustrations as new independent evidence.

The delivered PDF is generated with ReportLab. The editable LaTeX counterpart
`reports/technical_report_v003/main.tex` uses the same shared structured content
and figures and successfully compiles with the desktop editor; its preview may
have a different layout. It is not the source engine of the delivered PDF.
Earlier `reports/overleaf/smart_parking_draft/` is retained unchanged and also
compiles. Exact diagnostic proof and all 12 reviewed page images are under
`experiments/evidence/HEARTBEAT-20261025T161532Z/`.

Measured strengths and limits both matter: the historical candidate beats
persistence on its specified later-date cohort; conditional region masks need
known-camera setup; the final flow sequence has no positive labelled crossing,
so counting accuracy is not evaluable and that acceptance gate failed. Neither
software tests nor aggregate live counts prove universal camera accuracy.

This is an AI-assisted technical draft. Official university documents, student
details, independent understanding/viva, visible manual dialogs and fresh offline
installation acceptance remain unfinished. The dated Excel and slide files keep
their own earlier evidence cutoffs; use the current ledger for later updates.
