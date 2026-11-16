# Understanding the new parking-region model

Imagine highlighting every parking space on a photograph. ResNet18 supplies
previously learned visual features: our borrowed eyes. A new decoder learns
where to put white paint. It also sees the picture's row and column coordinates.
That makes fixed views easier, but it may memorize a scene instead of learning
to handle every car park.

The decoder trained for 80 epochs on 36 real images. An epoch is one pass through
training examples, not an independent experiment. We kept the checkpoint from
epoch 79. Six separate development images checked progress. Those six are not
a final exam.

| Method on the same six development images | Region overlap, called IoU |
|---|---:|
| Earlier small candidate | 0.466 |
| New transfer candidate | 0.771 |
| Fixed map learned from training geometry | 0.768 |

An IoU of 1 means exact overlap and 0 means no overlap. These values are not
occupied-space accuracy percentages. The new model still paints broad bands and
merges some spaces. It failed our gate because some camera views fell too far
below the fixed map. We kept it out of the app.

Six fresh final images were reserved before training. Their bytes were hashed
for duplicate checks, but their pictures and answers were not decoded. Because
the gate failed, we did not peek at that exam. Failed attempts and best
checkpoints are retained.

Open **notebooks/03_region_transfer_and_live_coverage.ipynb**. Its six Python
cells have actually executed. They restore the selected predictions and show
real photos beside the masks. Explain why the white paint does not identify
individual spaces or say whether each space is occupied.

For live forecasting, imagine writing down 1,259 guesses and then missing the
later noticeboard update. A missing answer cannot count as a correct guess.
Our ledger now separates pending and expired guesses. At the latest saved
collection, 3,340 outcomes had matched and 1,562 older predictions had no eligible
matching outcome. The matching coverage is 3,340 / 4,902 = 68.14%, not forecasting
accuracy. The mean absolute error of 2.19 spaces describes only matched outcomes.
Singapore aggregate counts also do not prove that a camera sees cars correctly.

Try explaining: borrowed features versus trained decoder; development checks
versus a final exam; region overlap versus occupancy accuracy; missing outcome
versus zero prediction error.

Original photos and labels: PKLot, Almeida et al., UFPR, CC BY 4.0. Pretrained
ResNet18 origin and rights are recorded in the source/model documents. This is
AI-assisted teaching; your own understanding still needs practice and explanation.
