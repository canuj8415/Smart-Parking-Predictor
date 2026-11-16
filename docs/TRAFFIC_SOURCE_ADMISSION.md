# Fresh traffic evidence: what is usable

The next counting study needs fresh fixed-camera footage, known timing, usable
vehicle identities/boxes or independently labelled crossing events, and clear
rights. A download is not automatically a valid accuracy benchmark. None of the
candidates below has yet passed this project's operational admission checks.

## SRC-DS-013: public partial drive-through release

Primary publisher: [Figshare v1](https://doi.org/10.6084/m9.figshare.29277770.v1),
Carlos Gellida and Carlos Gellida-Coutiño. Public API:
https://api.figshare.com/v2/articles/29277770 . The public record declares CC BY
4.0 and explicitly describes a partial release; full data depend on commercial
agreements. It lists 124 JPEGs and 3 trajectory CSVs, 98,382,739 bytes total.

Only four inspection assets were acquired: the 42,502-byte metadata JSON,
324,811-byte `vehicle0_cam3.csv`, and camera3 frames200/239 (740,524/750,034
bytes). Originals are under `data/raw/traffic_candidate_metadata/` and
`data/raw/drive_thru_figshare/`; exact URLs/timestamps/SHA256 and asset publisher
MD5 are in `data/resource_receipts.jsonl` and
`data/manifests/drive_thru_inspection_v1.json`. No other camera or trajectory
values were opened. This is not a final holdout reservation.

The CSV has 3,852 headerless six-value rows. Its coordinate basis and final
column semantics are not established by the inspected metadata. Two images
decode as2688x1520 while raw coordinates reach3603x2876. The diagnostic overlay
compares candidate scale factors; an apparent visual match does not establish a
transform. Do not multiply labels by0.7, clip them, or call them ground truth to
produce a score. Their manual versus algorithm-output provenance is also unclear.

Associated primary article, SRC-PAP-011:
[Gellida-Coutiño et al., Electronics2025,14,2671](https://doi.org/10.3390/electronics14132671).
Its data-availability section says the full underlying study data cannot be
publicly disseminated. The relationship between that restriction and the blurred
public partial release needs verification. The article's detector/tracker
performance is not our system's performance. Only setup, method, evaluation and
data-availability passages were reviewed; no full reproduction is claimed.

Decision: preserve the original bounded inspection assets/receipts, and defer
further operational asset use. No inference, training, accuracy evaluation,
publication, redistribution or extra footage acquisition. No permission request
or author message has been sent. Continue independent product work meanwhile.

## Other candidates researched, with no assets acquired

- SRC-DS-014: [Khan/Kelly multi-instance vehicle dataset](https://data.mendeley.com/datasets/5d8k5bkb93/1),
  DOI10.17632/5d8k5bkb93.1, publisher page CC BY4.0. It describes manually
  annotated frames from seven Creative Commons videos. Need official downloadable
  file inventory, per-video credits, temporal identity/schema and rights checks.
- SRC-DS-015: [HVSD](https://data.mendeley.com/datasets/zdgmdg7p25/1),
  Hadi Sadoghi Yazdi, DOI10.17632/zdgmdg7p25.1, publisher CC BY4.0. The description
  includes processed algorithm results. Those are not independent truth. Guessed
  public metadata API routes for both Mendeley records returned404; do not infer
  that the datasets themselves are unavailable or gated.
- SRC-DS-016: [UA-DETRAC creator page](https://sites.google.com/view/daweidu/projects/ua-detrac).
  Appropriate vehicle-tracking subject matter, but a primary asset-use licence
  was not established. Third-party or mirror licence declarations do not resolve
  that. No dataset bytes acquired.
- SRC-DS-017: [BrnoCompSpeed publisher repository](https://github.com/JakubSochor/BrnoCompSpeed).
  Current README directs download requests to an author; legacy full source is
  described as about200GB. No contact, account creation or archive acquisition.

Next: investigate SRC-DS-014's official public file inventory and original-video
credits without login; verify independent labels and source-consistent coordinate
mapping before acquisition/evaluation. If unsuitable, continue another legitimate
source or the remaining application acceptance work. Existing consumed DAVIS,
parking-image and Birmingham finals remain closed to changed-method tuning.
