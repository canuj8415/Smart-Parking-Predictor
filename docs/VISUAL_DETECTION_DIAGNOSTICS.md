# Understanding the remaining traffic misses

The audit found a class error on the large truck. Mask R-CNN produced a closely aligned box but labelled it **train**. The unchanged product road-vehicle filter therefore removed it. Faster R-CNN labelled this supplied truck correctly. This explains an observed output signature; it does not establish why the neural network learned that error or justify changing every train into a truck.

## Fixed diagnostic scope

Run `UVG-OUTPUT-AUDIT-20261026T134257858034Z` was sealed before six model calls: two unchanged models on development frames 121, 300 and 541, internal maximum side 960, score gate 0.5 and same-class box IoU gate 0.5. It took 45.031 seconds. All reconstructed product detections reproduce the archived 960-setting predictions in identity/order, boxes and scores within the prespecified tolerances. Input images and supplied targets came from checksum-bound completed development artifacts; no raw video, final sequence or Singapore target was opened for this audit.

The retained records contain the final COCO detections before the app's class/score filters. The model heads still apply score threshold 0.05, NMS threshold 0.5 and a maximum of 150 detections. Thus these records are **not** raw RPN proposals, unfiltered logits or proof that the network never proposed an unresolved object.

Each model sees 52 supplied car/truck observations on these three reused frames, including 41 eligible observations and 11 smaller ones. These are selected development observations, not a new independent accuracy cohort. Diagnostic categories have a fixed priority and do not create additional matches.

| Eligible output signature | Faster R-CNN | Mask R-CNN |
|---|---:|---:|
| Matched at the existing operating point | 26 | 24 |
| Same-class aligned box below operating score | 8 | 2 |
| Same-class localization gap | 2 | 1 |
| Aligned other class outside product scope | 0 | 1 |
| Unresolved after model postprocessing | 5 | 13 |
| Total eligible supplied observations | 41 | 41 |

All 11 smaller observations per model are unresolved at this output stage. This is consistent with a detail/scale limitation but is not causal proof of the location of the failure inside the model. Lowering the app threshold cannot recover outputs already removed by the model head. Lower thresholds may also create new false positives; this provided-positive study has no exhaustive negative labels with which to establish their safety.

For fixed frame 300, supplied track 25:

- Faster R-CNN: `truck`, score 0.813114, box IoU 0.964129; retained by the product.
- Mask R-CNN: `train`, score 0.682491, box IoU 0.979144; excluded by the product.

A real train is visible on the bridge in this same clip. A global train-to-truck remap would therefore be an unsupported intervention. The detector benchmark's absolute quality gates remain failed, the app remains unchanged, and the entire HighwayDrive final sequence remains reserved and unopened. No final controller exists.

## Executed Jupyter explanation

`notebooks/11_visual_detection_diagnostics.ipynb` has seven actually executed code cells, two inline archived figures and no saved errors. It reads 11 hash-bound archived inputs: three reports, six diagnostic outputs and two derived PNGs. It explains eligible versus all supplied labels, matched-only versus zero-inclusive mask IoU, wrong-class localization and the danger of remapping classes. Its tiny constructed truck/train example is labelled synthetic teaching data and is not another experiment or real model prediction.

Validation `VISION-LESSON-20261026T134807223185Z` used the existing shared Python environment and a real Jupyter kernel. It completed in 4.000 seconds. Three protected file/write probes and one external-DNS probe were denied; successful raw/growing/final reads and model calls were zero. Cell sources remained unchanged, validation probes were removed, and both embedded PNGs are byte-identical to the previously reviewed archived figures. These are Python-level file/socket audits, not OS isolation, a physically disconnected test, a new machine, a manual browser rehearsal or student mastery.

The notebook's exact read-only manifest is `data/manifests/vision_diagnostics_lesson_v1.json`. The helper has no inference, training or acquisition entry point and admits only its fixed archived file set. Synthetic tests reject altered hashes, extra paths, missing archives and non-development manifests. An initial integrity-test fixture used an unwritable default temporary folder; its failure is preserved and the fixture now uses a checked project-local scratch directory. It did not change scientific results or add a completed trial.

Student questions ask why a well-placed box can fail same-class matching, why unknown truth masks differ from valid misses, and why these development findings do not authorize a final evaluation. Independent answers and presentation remain unassessed.

The source remains SRC-DS-019/SRC-DOC-021: Tampere University / Ultra Video Group, UVG-VCM, Partanen et al. (2026), CC BY 4.0; attribution and derivation notes accompany the figures. Original media, failed experiments, production weights and frozen Singapore methods are preserved. Current evidence pointers are `reports/uvg_output_audit_latest.json` and `reports/vision_diagnostics_lesson_latest.json`.

## Notebook-directory launch correction

Finalreviewfoundlesson11assumedkernelCWDwasprojectroot. Itnowfindsthenearestprojectfromrootornotebooks/. Originalroot-onlysource/executedbook/protocolretainedunchanged. Separateactualnotebooks-folderkernelregression VISION-LESSON-20261026T135823759379Z passes7cells/2PNGs/3file-write+1DNSdenials in3.937seconds;nofreshinference/raw/finalreads. This distinctlaunch-contextfixvalidationadvances75->76;wakeupcount51/source60/next100-runcheckpoint100/noactivejobs. Currentnotebook/cardpointtocorrectedexecutedversion. No studentmastery/physicaloffline/newmachineclaim.
