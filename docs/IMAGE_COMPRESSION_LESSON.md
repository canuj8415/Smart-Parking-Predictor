# Rebuild a parking picture from fewer patterns

Open `notebooks/08_image_patterns_and_svd.ipynb`. In the Python app, load a
parking image, open Convolution lab, choose a number of patterns from1to160 and
press **Try image compression**. The convolution button restores the2D/3D view.

Imagine describing a photograph with broad shapes first, then adding details.
SVD separates a grid of image numbers into weighted patterns. Keeping fewer
patterns approximates the picture; it can blur a car edge into its shadow.
This does not train a detector or change how the main product detects vehicles.

The saved example is the existing PKLot **training** image selected by
`configs/demo_sample.json`. Its original bytes and checksum stay unchanged.
For this lesson only, the image becomes grayscale and is resized to256x160.
The actual saved comparison is under
`experiments/results/SVD-LESSON-20261025T191732227032Z/rank_comparison_reviewed.png`.
The earlier grid with overlapping row labels is preserved as an authoring failure;
the reviewed version changes layout only, without another model experiment.

With16patterns the three factors store6,672 numbers, versus40,960 numbers in
the grayscale grid. Using the same float64 number format, this is53,376 versus
327,680 bytes, or16.29%. This is **not** a comparison to the original JPEG file.
The mathematical reconstruction MSE is0.004653 on the0to1gray scale. It retains
98.63%of squared numerical energy; that is not98.63%vehicle accuracy.

With all160patterns, maximum reconstruction error is about2.05e-14, reflecting
floating-point arithmetic. The factors then occupy162.89%of the grayscale matrix
storage: a close reconstruction can use more storage. No compressed image codec,
detector improvement or parking accuracy has been evaluated. Numerical metrics
use the unclipped reconstruction; only displayed pictures clip values to0to1.

The library computes `U,S,Vh = numpy.linalg.svd(A, full_matrices=False)` and the
lesson rebuilds rank k as `(U[:,:k]*S[:k]) @ Vh[:k]`. Factor storage counts all
three arrays: `k*(height+width+1)` numbers. NumPy provides the solver; the project's
contribution is the lesson, accounting, checks, visualization and app/notebook
integration. [NumPy2.5 API, source SRC-DOC-018](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html).
Real photograph: Almeida et al., PKLot, source SRC-DS-001, CC BY4.0. Derived
grayscale/resized illustrations; no endorsement. Original source records and
receipts remain in `data/source_manifest.csv` and `data/resource_receipts.jsonl`.

Try changing16to8and predict which boundaries will disappear. Explain why all
patterns can take more memory, and why retained energy cannot prove occupancy
accuracy. The notebook's execution verifies software; independent answers,
student understanding and official university compliance remain unassessed.
