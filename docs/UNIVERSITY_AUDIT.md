# University document audit — awaiting primary sources

**Current user correction (24 October 2026):** Python with Jupyter is explicitly required by the user, superseding the earlier C/C++/Java instruction. This does not establish faculty approval. The two primary university documents remain missing. Master Add-on 01 authorizes independent dataset research, acquisition and preparation now.

Audit date: 24 October 2026, Asia/Calcutta.

## Sources actually available

The attachment `839fe2c8-a697-421e-b140-f004bca3ed62/Pasted text.txt`
contains the user's master brief. It is a secondary account of university rules.
No `.docx` files were found in the supplied attachment directory or beneath
`D:\deep learning`. The project directory was initially empty.

| Required source | Availability | Audit result |
|---|---|---|
| Deep Learning - PBL.docx | Missing | Not read; contents unverified |
| PBL Guidelines.docx | Missing | Not read; contents unverified |
| Faculty announcement/rubric | Mentioned in brief only | Marks and phase structure unverified |

## Exact wording supplied by the user, pending source verification

**Project 52: Smart Parking Occupancy and Vehicle Flow Predictor**

Industry Domain: Smart Cities

> Develop the main product to detect vehicles, segment spaces, classify occupancy and forecast availability, using YOLO/Faster R-CNN with ResNet; visualize representative 2D and, where appropriate, 3D convolution operations.

This quotation is reproduced from the user's brief, not independently checked
against a university document.

## Mandatory work claimed in the brief

- Individual work; reproducible C, C++, or Java implementation; native training.
- Neurons, from-scratch MLP, tensor mathematics, SVD, manual gradients and optimizers.
- Hebbian/modified Hebbian, competitive, error-correction and energy-based learning demonstrations.
- Controlled optimization, normalization, initialization and regularization experiments.
- Parking classification, detection, semantic and instance segmentation evidence.
- Representative 2D and conditionally applicable 3D convolution demonstrations.
- Sequential modelling, forecasting baselines and a generative component.
- At least two course-specified architecture benchmarks on suitable matching tasks.
- Real evaluation, reproducibility, offline functionality and independent modifications.
- Overleaf report, academic evidence and an individual contribution record.

The brief calls the listed foundations Unit I. It does not supply authoritative
Unit II–V definitions. Their exact mappings, evidence minima and exemptions
remain unresolved. No official phase-wise rubric has been created here.

## Distinguishing sources of requirements

`REQUIREMENTS.csv` uses these categories:

- **Reported university:** described as official in the brief; source audit pending.
- **User requirement:** explicitly requested product, learning or quality behavior.
- **User preference:** preferred implementation choice, subject to feasibility.
- **Optional:** expressly conditional capability such as a live camera.
- **Proposed enhancement:** an engineering choice suggested here, not a faculty rule.

All reported university rows must gain a document, page/section and exact wording
before they can be labelled officially verified.

## Questions to resolve from documents before asking faculty

1. Does “YOLO/Faster R-CNN with ResNet” allow either detector, or require both?
   Which two architectures must be compared, and on which tasks?
2. What exactly are the required Unit I–V artifacts? Are semantic and instance
   segmentation both mandatory for this particular project?
3. Is a pretrained detector/segmenter plus native-trained classifier acceptable?
   Which models must be trained, and are external conversion tools allowed?
4. What qualifies as 3D convolution evidence, and when is it applicable?
5. What counts as vehicle flow: occupancy changes, tracked movement, or
   independently verified entrance/exit crossing counts?
6. Is a clearly labelled simulation acceptable for sequence demonstrations when
   real temporal coverage is insufficient?
7. Is the report format prescribed? Confirm course code CSAI3027P, faculty,
   batch, deadline, phase dates, and actual phase-wise evaluation criteria.
8. Reconcile the reported 50% internal-assessment contribution and 50 marks per
   phase with the actual assessment scheme; do not infer a total.
9. Are cached third-party dependencies/pretrained weights allowed offline, and
   must a fresh build as well as execution work with the network disconnected?

## Audit completion procedure

Read every paragraph and table in both documents, including headers/footnotes
and embedded instructions. Extract Project 52 verbatim with location references.
Record common rules, the actual recommended eight-week sequence and each Unit's
evidence. Resolve conflicts by source authority and seek faculty clarification
only for questions the sources do not answer. Update each tracker row with source
locations and acceptance evidence before finalizing language or implementation.
