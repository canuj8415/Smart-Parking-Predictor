# Proposed broader bay-footprint data qualification

This is a next-work plan,not a sealed experiment protocol or a claim of completed
region-mask preparation. Current PKLot image-only candidates fail four quality
gates despite several distinct controlled changes. Broader existing development
supervision is a higher-impact next step than a residual/threshold grid.

SRC-DS-021 ACPDS is already qualified for local attributed use:author Martin Marek,
pinned revision17da2c8b33055be8019483260f0efbcbdfda0478,recorded explicit MIT grant
and retained2021copyright/notice. The source-role manifest is
`data/manifests/acpds_source_roles_v1.json`,SHA256
`aab4890c3697fb3ce9117ee9220def3ecd131b372d0cfb96dd2b433c8b9ede1f`.
All27TESTimages,lots,views,aliases,annotations and derived representations remain
closed. The author claims unique split lots;independent location/date verification
and pretraining overlap remain unavailable. No final controller/claim is implemented.

Use the COMPLETE existing development image manifest:
`data/processed/acpds_development_v1/development_images.json`,SHA256
`2e0705c8b1fa1089fff36be7ca663ca0e81fc05a92825f80775082eb8d3a13ed`.
It contains231TRAIN/35validation frames,266total,with image/layout paths and hashes.
Its final_members_accessed field is0. The earlier
`experiments/results/ACPDS-IMAGES-20261026T231225302138Z/development_images.json`
contains only3TRAIN+35VALID images and is not the full inventory.

Prefer these admitted native-coordinate layout files;their polygons already
apply the publisher's normalized x*(W-1),y*(H-1) mapping. Do not scale them twice.
If original development annotations are needed,use the immutable development-only
derivative `experiments/results/ACPDS-DEVELOPMENT-20261026T224240258641Z/development_annotations.json`,
SHA256 `39534723e30bd162d26eece35da63ce58f336ee92575fcda9f78ce9b536885fc`.
Never json.loads the mixed original annotation body;the existing development_only
structural scanner excludes TEST semantics. No TEST pixel acquisition or decode.

Before decoding,seal a bounded data-only protocol with source IDs,seed,full image/
layout/receipt hashes,role/closure checks and code/config hashes. Verify current
TRAIN/VALID byte uniqueness and known protected aliases,including the existing
PKLot12417opaque JPEG hash table. Unknown ACPDS TEST byte aliases cannot be ruled
out from unacquired bodies;do not acquire TEST for this check or claim perceptual
independence. Preserve failures and do not silently resample rejected examples.

Target the union of supplied bay polygons with occupancy labels excluded from the
training target. Validate native polygon geometry and bounds,then exact cache
round trips and reproducible image/mask transforms. Outside supplied polygons
means outside the annotation union,not verified absence of every parking region.
The source is not exhaustive whole-facility semantic-mask truth.

Prespecify resize behavior before cache generation. Earlier qualified examples
are4:3;verify actual dimensions across the complete pool. Letterboxing to the
existing256x144 input is a reasonable proposal,with a separate
nonpadding-validity mask. Future loss/metrics must ignore padding consistently.
That validity mask does not establish negative truth in unannotated real image
areas. Existing PKLot16:9 caches can retain their geometry. Keep real observations,
derived supervision and synthetic transform fixtures distinct. Review fixed TRAIN
overlays and seal data-admission gates before any new neural fitting.

Retain source-separated validation and all earlier paired PKLot controls. A
camera-conditioned template has no matching geometry for arbitrary new views;
report it as inapplicable rather than invent a layout. Adding development data
does not make a result fresh final evidence. No new training/model promotion until
the derived dataset and a separate model recipe/gates are qualified and sealed.
