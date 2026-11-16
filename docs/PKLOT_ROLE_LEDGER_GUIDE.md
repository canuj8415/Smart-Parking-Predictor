# Whole-archive PKLot roles and historical test protection

This metadata audit accounts for all 12,218 paired files in the previously
validated archive index, spanning 98 camera/date groups. It re-hashed the original
3,860,376,865 compressed bytes and verified the existing index checksum. It did
not decompress image formats, parse XML labels, run a model or change weights.
The initial audit took 4.741 seconds. Old rejected member metadata stays rejected.

| Current conservative status | Groups |
|---|---:|
| Training exposure already recorded | 50 |
| Development exposure already recorded | 15 |
| Historical final consumption now durably recorded | 17 |
| Earlier conservative metadata exclusions, still quarantined | 16 |

No new training or final groups were admitted. The earlier inventory's boolean
eligible_date is historical: its six provisional groups later became three
development groups and three consumed final groups. A missing newer claim is
not evidence that an older test was never used. The immutable initial audit
retains its pre-repair counts; the separate consumption supplement gives the
current table. See current_group_roles.csv in the completed audit folder.

The follow-up found five original weighted-segmentation test dates among the
metadata exclusions. Completed original vision and known-camera segmentation
tests also predated newer durable claim handling. Three consumption attestations
were therefore recorded at the actual current time, explicitly retrospective.
They are not presented as preregistrations made before those old evaluations.
All original artifacts and earlier claim files remain unchanged. Existing guard
checks reject 22 canonical/archive-folder alias probes, with a separate unrelated
training-group control allowed. Those probes use labelled synthetic guard
manifests and never open an image. No new experiment count is assigned to them.

For the original vision record, the current code and manifest byte hashes differ
from those recorded historically. This mismatch is retained explicitly; it was
not repaired by inventing an old matching version. The historical card's explicit
test-date map, completed 360-test-sample record and preserved checkpoint justify
conservative whole-date protection. Weighted-segmentation and known-camera
evaluation code hashes match their records. Only metadata and field presence,
not metric score values, were inspected for this consumption repair.

Known image-hash metadata produced no cross-group byte aliases, but most archive
images were not newly hashed individually. This is not proof of no duplicate
images throughout the archive. Future selected TRAIN data need a byte-alias
qualification before decoding; unknown groups remain quarantined. Camera aliases
parking2/pucpr, parking1a/ufpr04 and parking1b/ufpr05 are canonicalized. A consumed
or historical test role overrides later role labels, including failed evaluations.

Five synthetic role/alias/path tests bring the software suite to 451 passing tests.
One planned protocol was replaced before execution to separate an actual hash
alias from a merely protected seed group. Its source/protocol remain preserved,
and it contributes zero trial count. The completed audit is one recorded trial;
the archive frames, checksum chunks and synthetic probes are not separate runs.

A student should explain why an image filename, folder alias or absent claim
cannot make old test data fresh. Explain the difference between prior training
exposure, development decisions, consumed final evaluation and uncertain metadata.
Student independent understanding has not been assessed. Supplied bay polygons
are not automatically exhaustive whole-facility segmentation ground truth.
