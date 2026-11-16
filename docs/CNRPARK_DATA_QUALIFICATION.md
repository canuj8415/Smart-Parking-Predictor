# New CNR parking data: what is ready

The original project website is reachable through its published HTTP address,
although HTTPS requests failed. Its current download links point to the dataset
authors' HTTPS GitHub release. These are publisher links, not an unrelated mirror.
The original HTTP patch download failed; no access controls were bypassed.

| Item | Actual saved result |
|---|---|
| Official metadata | `data/raw/cnrpark_official/CNRPark+EXT.csv`,18,132,695bytes;157,549records across the preliminary and extended collections |
| Extended image archive | `data/raw/cnrpark_official/CNR-EXT-Patches-150x150.zip`,449,502,403bytes;retained intact for inspection |
| Extended metadata mapping | 144,965records,9cameras,23dates;exact match to144,965JPEG archive entries;no missing or unmapped JPEGs |
| Preliminary rows | 12,584A/Bcamera records excluded from this EXT-only study;their separate image archive was not acquired |
| Label-blind preparation | `data/splits/cnrpark-global-dates-v1/manifest.csv`;calendar/path/member checks,original CRC/size metadata and source-row lineage |
| Chronological roles | 82,361train-role records over13dates;30,525development-role records over5dates;32,079reserved records over5dates |
| Protected final dates | `data/manifests/cnrpark_final_dates_v1.json`;all camera views on each date stay together |
| Source and usage decision | `data/manifests/cnrpark_usage_qualification_v1.json`;SRC-DS-002in the source registry and per-file receipts |

These counts describe metadata preparation, not model accuracy. No JPEG member
was decompressed, no image was displayed and no classifier was trained/scored.
Archive member names/CRC/sizes were inspected; individual image integrity,
dimensions and annotation quality have not been verified. The publisher provides
no asset checksum in the release metadata; recorded SHA256values are local byte
fingerprints, not independently published checksums.

Dates are sorted globally, with cut points at `floor(0.6 * 23)` and
`floor(0.8 * 23)`. All nine cameras on a date share the same role. This prevents
the same day's overlapping camera views from appearing in different splits.
It is a chronological one-car-park protocol, not an unseen-camera benchmark.
The CSV parser tokenized source fields, but occupancy/occupant-change values were
not inspected, converted, scored or used for selection. They are excluded from
the derived manifest. The older audit field wording “targets parsed” refers to
semantic target use; it does not mean the raw CSV fields were never tokenized.

## Why images are not being used for a model yet

The [publisher page](http://cnrpark.it/) declares
[ODbL1.0](https://opendatacommons.org/licenses/odbl/1-0/) for CNRPark-EXT.
The licence distinguishes database rights from individual-content rights in
section2.4. No separate image-content licence was found in the homepage or archive.
Under this project's `PROJECT_CONSTRAINTS.md` rule5, image modelling therefore
remains unqualified. This is a project usage decision, not legal advice or a
blanket clearance for redistribution. Factual metadata work is recorded separately.

The new date guard checks frozen source/manifest/model/protocol bindings, writes
and flushes a canonical whole-date claim before a future evaluation callback,
and keeps dates consumed even if that callback fails. Renaming the local source
does not reopen a date. Seven synthetic software tests cover these behaviours;
all191current software tests pass. No real final claim has been created here.

Keep these images inspection-only unless their use is qualified from an
authoritative source. Meanwhile, independent model work can use genuinely unused
camera/date groups from the existing licensed PKLot archive, reserving new final
groups before any changed-method evaluation. Previously consumed PKLot,
Birmingham and DAVIS final groups remain unavailable for tuning or replay.

Attribution: Giuseppe Amato,Fabio Carrara,Fabrizio Falchi,Claudio Gennaro,
Carlo Meghini and Claudio Vairo;CNRPark/CNRPark-EXT research team. The
[author repository](https://github.com/fabiocarrara/deep-parking) links the research;
the [official archive release](https://github.com/fabiocarrara/deep-parking/releases/tag/archive)
provides the preserved files. No source images were redistributed or published.

## 26 October 2026 / new publisher-original parking archive verified

A separate source SRC-DS-018 explicitly declares original photos/labels and CC BY4.0. Its731pairs are acquired/byte-qualified,with model/group admission pending. See docs/OPEN_SPACE_DATA_GUIDE.md. This does not alter the CNR image-content decision:all CNR images remain unopened and not model-authorized.
