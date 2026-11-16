# Stored-layout view compatibility — rejected development study

The existing conditional region candidate uses stored TRAIN geometry for two stable cameras and a frozen CNN for the camera whose training masks vary. Correct camera selection and a compatible view are prerequisites. Matching dimensions or a camera name cannot establish that the camera has stayed in position.

`VIEW-COMPATIBILITY-20261026T172503270481Z` tested one fixed conservative image-matching hypothesis. Three TRAIN reference images per stable camera were selected without image labels: the first lexicographic frame on the first, middle and last training dates. The existing sealed broader-development manifest supplied 24 development images across three cameras. No current-frame XML, final image or final annotation was opened. Thirty distinct original images were decoded: six references and 24 development images. No neural inference or training occurred.

The pre-decoding protocol fixed ORB at 1,000 features and maximum side 640; Hamming ratio 0.75; RANSAC 3 pixels; at least 30 inliers with fraction 0.25 and spatial span 0.1 on each axis; median reprojection at most 2 pixels; maximum corner displacement 0.5% of the diagonal. Two of three references must support compatibility. No image warping or slot-coordinate adjustment is performed.

The usability gate required 80% acceptance of matching-camera pairs and at least 50% in each stable camera, zero wrong-camera acceptances, and 95% rejection of synthetic changed views. Results in 10.016 seconds:

| Cohort | Result |
| --- | --- |
| Real matching-camera pairs | 1 accepted / 16 (6.25%) |
| PUCPR / UFPR05 matching-camera acceptance | 0% / 12.5% |
| Real wrong-camera pairs | 0 accepted / 32 |
| Synthetic changed-view fixtures | 48 rejected / 48 |

**The development gate failed.** This checker is unsuitable for automatic stored-layout acceptance at this setting and is not connected to the app or region router. Rejecting nearly everything is not a useful camera-verification result. The entire failed protocol, code snapshots and per-reference decisions are retained. Thresholds were not retuned on these images.

Saved-decision diagnosis finds insufficient ratio-filtered matches in 43 of 48 matching-camera reference comparisons. All 96 wrong-camera reference comparisons likewise lack enough matches. Among the 144 transformed-reference comparisons, 136 lack enough matches and eight fail the geometry condition. This supports a feature-correspondence coverage problem; it does not establish its cause. The three synthetic transformations are a 5% horizontal shift, 5-degree rotation and horizontal flip of 16 matching-camera development images, with explicit generated borders. They do not replace real changed-camera observations.

Matching camera IDs are source group labels, not independent manual certification that every image has an identical pose. The study measures matching-camera usability, not authenticated camera identity, security, real relocation accuracy, occupancy or independent final generalization. Existing region final groups remain consumed. The earlier conditional region metrics and original production checkpoints remain unchanged.

Next: stop descriptor/threshold grids on this cohort. A different bounded approach should first establish a label-blind TRAIN-only static-background reference representation and reserve genuinely fresh groups before any final evaluation. App integration must continue to require explicit reviewed view/layout evidence until a candidate meets prespecified usability and mismatch gates.
