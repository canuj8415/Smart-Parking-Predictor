# Practising the Smart Parking walkthrough

Open `reports/presentations/smart_parking_walkthrough_v002.pptx`. It has 14 slides
and speaker notes. The route below aims for about 8–10 minutes; this is a practice
plan, not a measured rehearsal. The slides describe a development build as of
25 October 2026. Later model or live-feed results may differ.

## Slides 1–2: what the project tries to do

Imagine a parking attendant. First, the attendant notices a vehicle. Next, they
recognise the marked parking area. Then they check whether a particular space
has a vehicle in it. After watching the car park over time, they might estimate
how many spaces will be available later.

The project gives these jobs different names: detection, segmentation,
occupancy classification and forecasting. Explain them separately. A high score
for one job does not automatically make the other jobs accurate.

Practice question: Can the program see a car that is driving past a parking
space without that space being occupied? Yes. Finding a vehicle and assigning
it to a parking space are separate decisions.

## Slide 3: where the real data comes from

PKLot supplies parking photographs and annotations. UCI Birmingham supplies
historical counts. The official Singapore HDB feed supplies timestamped
availability records. A licensed street recording supplies moving video input.
These locations and time periods differ.

Original files stay in `data/raw/`. Derived live history goes to
`data/processed/singapore_live_observations.csv`. The source manifest identifies
each external resource. The receipt ledger records actual download URLs, times,
sizes and checksums. A checksum acts like a fingerprint for a file: it helps
detect a changed file but cannot prove that its labels are correct.

Practice question: Does the Singapore feed tell us whether a box around a car in
the PKLot photograph is correct? No. It provides aggregate availability counts,
with no matching camera labels.

## Slide 4: a saved image result

Point to the vehicle boxes and then the configured parking spaces. This saved
example contains 100 configured spaces. The program predicted 68 occupied,
32 vacant and zero uncertain spaces. These are outputs from one image, rather
than a verified score for every car park.

An uncertain result means the available evidence does not support a confident
decision. That is useful: a missing vehicle detection alone should not make the
program promise a free space.

## Slide 5: what the classifier score means

The small test set contains 360 individual parking-space crops. The classifier
got 343 correct, which gives 95.28% accuracy. The table also shows the mistakes:
13 vacant crops became occupied predictions, and four occupied crops became
vacant predictions.

The four false-vacant cases matter because they could send a driver toward an
occupied space. This score covers the selected test crops. It does not establish
accuracy on a different camera, weather condition or whole parking image.

Practice calculation: add 91 and 252 to find the correct predictions. Divide
343 by 360 and multiply by 100 to reproduce the accuracy.

## Slide 6: how the region model is doing

Imagine colouring the parking region on a photograph. Intersection over Union
(IoU) measures how much the predicted colouring overlaps the annotated region.
Perfect agreement gives 1.0.

On the same six development frames, the earlier transfer model reached about
0.771 and the sharper-image candidate reached about 0.796. The new candidate
still misses the acceptance rules. A reserved final set remains closed. This
preserves a later check on genuinely unused images.

Practice question: Can we call 0.796 “80% project accuracy”? No. It is one region
overlap measure on a small development set, with separate acceptance failures.

## Slide 7: why a simple forecast is hard to beat

The baseline predicts that the last count stays the same. MAE means average
absolute error. If MAE is 10 spaces, the predictions miss the observed counts
by 10 spaces on average. Lower is better.

The original LSTM scored 121.21 spaces of error against the baseline's 61.14
on its final-test windows. It performed worse. A newer candidate scored better
overall on development data, but it harms some individual car parks and still
fails its acceptance rules. Those two rows use different splits, so they do
not prove the newer candidate would win on the final test.

## Slide 8: the two clocks

Use the teaching example. A prediction issued at 9:00 has a grid target of 9:30.
If the real reading used for that target came at 9:10, the score compares with a
reading only 10 minutes after issue.

The actual development readings were 19.3–29.4 minutes ahead. The code now
preserves those source times. The audit left the old model inputs, targets,
weights and aggregate scores unchanged.

## Slide 9: what the live check can tell us

The saved slide shows 7,874 later observations matched to forecasts frozen
earlier. The simple persistence baseline has MAE 3.203 parking spaces at this
snapshot. The number can change as new observations arrive.

The live check uses actual later readings from the same source and capacity.
Missing targets receive no invented scores. It does not establish Singapore
neural-model accuracy or camera detection accuracy.

## Slide 10: video counting

The counter places an imaginary line in the video. It tries to keep a vehicle's
identity and records a crossing after stable observations on both sides.
Occlusion, uncertain identity and long gaps can make it miss vehicles.

The saved real trial processed 25 frames at half-second spacing and predicted
zero crossings. The files agree with one another, but no human labels establish
whether those predictions are correct. A made-up example in notebook 04 shows
the counting rule producing an entry and exit. Keep these evidence types clear.

## Slide 11: convolution in plain language

A kernel is a small set of numbers that slides over an input. At each position,
it combines nearby values. The 2D example scans an image's height and width to
highlight edges. A 3D kernel also spans a depth or time dimension.

The 3D volume in this lesson is synthetic numerical teaching data. It is not a
trained 3D parking detector or a real parking video.

## Slides 12–14: demonstration, remaining work and authorship

Use the launcher, load the real sample and explain its outputs. Show the
forecast baseline and the timestamp on a saved live snapshot. Use the notebooks
for the arithmetic and experiments. A physically disconnected demonstration and
fresh offline setup still need validation.

Explain the remaining model and application gaps. Mention sources when showing
their data. The implementation and learning materials include AI assistance.
Describe your own contribution accurately and demonstrate understanding by
changing a safe example yourself.

## A short practice record

After practising, record the date, what you explained without help, the exact
notebook cell you changed, the result you expected, the result you observed and
what you still could not explain. Keep the attempt even if it fails. The current
project does not contain evidence of your independent mastery yet.

Suggested first task: in notebook 04, reverse the configured entry direction
for the synthetic example. Predict the labels before running it, then explain
why the labels change while the made-up vehicle positions stay the same.
