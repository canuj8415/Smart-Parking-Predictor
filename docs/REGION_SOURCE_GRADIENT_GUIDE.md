# Source-gradient diagnostic

The planned hypothesis was NOT supported at the selected mixed decoder:
3/8 gradient pairs opposed each other (threshold at least4),
and 0/8 predicted local PKLot loss growth
under the equal-source raw-gradient direction (threshold at least1).

| Fixed checkpoint | Opposing pairs | Mean cosine | Median ACPDS/PKLot gradient norm | Predicted PKLot first-order worsening |
|---|---:|---:|---:|---:|
| PKLot-only control | 8/8 | -0.578627 | 15.573627 | 7/8 |
| Mixed | 3/8 | 0.068482 | 1.385872 | 0/8 |

Mean TRAIN loss: control PKLot0.522271/ACPDS3.106375;
mixed PKLot0.614926/ACPDS0.720300.
The imbalance is present at the fixed PKLot-only checkpoint. These two endpoints do
not establish when or why the earlier AdamW training lost development performance.
Gradient direction, magnitude, nonlinear finite steps, momentum and model capacity
can differ. No claim of causal explanation or guaranteed retention follows.

The experiment fixed eight pairs of fourPKLot and fourACPDS TRAIN images, selected
without replacement using seed178:32images per source. Existing selected weights,
frozen encoder/BN,nonpadding loss and class weight4.593998 stayed fixed. All64caches
were TRAIN;DEV/raw-source negative access controls blocked before file reads.
No optimizer,weight updates,DEV/final images,threshold searches or new accuracy scores.
The entire two-checkpoint diagnostic is one trial;16pairs/32gradient evaluations/
64encoder image forwards are not32or64runs. Phase duration1.924s,
sampled peak processRSS0.615GB.

Cosine is the angle-like alignment of two flattened decoder gradients. A negative
dot product means one source's immediate descent direction opposes the other's.
For direction d=-(g_PK+g_AC)/2,the local PKLot loss derivative is g_PK dot d.
A positive derivative means local first-order loss growth,not a measured finite-step
or development-image regression. Undefined zero-gradient cosine remains missing.

An independent software prototype removes the auxiliary gradient component opposing
PKLot and caps its norm at the PKLot gradient norm. Its known-plane/zero/invalid-vector
tests and512seed179random-vector properties pass. It has NOT trained a model or entered
the app. Its float64 first-order geometry does not guarantee finite-step loss,AdamW
behavior or held-out quality. Next experiment must be sealed separately with matched
warm starts/optimizer/batches/budget,retained source-quality gates and fresh final
qualification before promotion. Do not retry this hypothesis on different samples.

Sources: SRC-DS-001,PKLot/Almeida etal./UFPR,CC BY4.0;SRC-DS-021,ACPDS/MartinMarek,
explicit MIT2021 grant;SRC-MOD-003,existing ImageNet ResNet18 under recorded local
academic terms. TRAIN examples were already used in fitting;this is not independent
generalization evidence. Near-duplicate/location/date/pretraining independence remains
unknown;provided bay unions are not exhaustive facility or occupancy truth.
All original,best and failed checkpoints and consumed final boundaries are preserved.


487 full software tests passed in7.177sec. Archive audit:105bound hashes,64TRAIN caches,16journal rows, sampling and all saved summaries/geometry consistent;completed protocol refuses rerun;zero new model calls by audit. Actual cancel/resume execution remains untested.
