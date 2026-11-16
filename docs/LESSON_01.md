# Lesson 1 — from a parking photograph to a prediction

**Workflow update:** use Python/Jupyter. The independent data audit is implemented in `src/smart_parking/data.py` and `notebooks/01_real_data_audit.ipynb`; the neuron/MLP discussed here remains planned.

Mastery status: introduced only; student response and practical work pending.
No model has been trained and no code is being claimed as implemented.

## What the system does

Everyday explanation: imagine looking at a fixed parking camera and checking
each marked space. Our application will perform that check, display free,
occupied and uncertain spaces, then use a history of observations to estimate
later availability. An estimate can be wrong; the screen must show limitations.

Technical explanation: occupancy estimation combines camera-specific regions,
computer vision predictions and decision logic. Future availability is a
separate time-series regression problem. Classification, detection and
segmentation produce different kinds of outputs.

## How a picture becomes numbers

An RGB picture stores three color measurements per pixel: red, green and blue.
For an ordinary 8-bit image, each measurement ranges from 0 to 255.

A 2 × 2 RGB image has `2 × 2 × 3 = 12` scalar measurements. A later example crop
of 64 × 64 pixels would contain `64 × 64 × 3 = 12,288` values. These example
dimensions are for teaching, not selected production settings.

A tensor is an array with dimensions. Image input may be stored as height ×
width × channels; a CNN batch often uses batch × channels × height × width.
Changing dimension order does not change what a color means, but it changes
where the program finds each measurement. A wrong order can break predictions.

One simple scaling formula is `x = p / 255`, where `p` is an original color
measurement and `x` is its scaled value. For `p = 128`, `x ≈ 0.502`.
Later models may require additional channel normalization; the saved training
preprocessing must also be used during inference.

## What deep learning adds

Everyday explanation: instead of writing every rule about shadows and car
shapes ourselves, we show a model labelled examples and let training adjust its
internal settings. A label tells it whether a particular space was occupied.

Technical explanation: a neural network is a parameterized composition of
functions. Deep learning trains models with multiple transformation layers to
learn useful representations. A loss measures disagreement with labels;
optimization changes parameters to reduce training loss. Good training loss
alone does not prove performance on unseen cameras or days.

## One neuron, before a whole network

A neuron combines inputs, weights and a bias:

`z = w1*x1 + w2*x2 + b`

`p = sigmoid(z) = 1 / (1 + exp(-z))`

Here `x1` and `x2` are two numerical input features, `w1` and `w2` are learned
weights, `b` is a learned offset, `z` is the weighted score, and `p` is a value
between zero and one. `exp` is the exponential function.

Illustrative parking-feature example, not a trained model:

1. Suppose two scaled features are `x1 = 0.8` and `x2 = 0.2`.
2. Choose teaching weights `w1 = 2`, `w2 = -1`, and bias `b = -0.5`.
3. Compute `z = 2*0.8 - 1*0.2 - 0.5 = 0.9`.
4. Compute `p = 1/(1 + exp(-0.9)) ≈ 0.711`.
5. A teaching threshold of 0.5 would classify this example as occupied.

These arbitrary features/weights do not establish actual parking accuracy.
The output 0.711 is a model score, not evidence that 71.1% of similarly scored
real cases are occupied. That interpretation needs calibration evaluation.
If `w1` increases while `x1` stays positive, `z` and the sigmoid output increase.

Weights and bias are parameters learned from data. Learning rate, batch size
and architecture settings are hyperparameters chosen outside an update step.

## What we will implement first and why

After the source audit and toolchain check, we will implement this arithmetic
explicitly, then a small multilayer perceptron with handwritten gradients.
You will see how loss leads to weight changes. This makes backpropagation
inspectable before using a framework for the larger CNN, LSTM and VAE.

Planned code connection: the baseline's forward function will compute `z` and
sigmoid outputs; its backward function will compute derivatives; its optimizer
will change the stored weights. Those functions do not exist yet, so there is
no run command or code explanation to falsely present as verified.

## Revision and practice — answer before viewing a solution

Definitions: pixel = color measurements at a location; tensor = shaped numeric
array; parameter = learned value; inference = prediction using fixed weights;
training = updating weights using a loss.

Remember `z = sum(w_i*x_i) + b` and `sigmoid(z) = 1/(1+exp(-z))`.
Common mistakes: confusing one pixel with one color channel, mixing occupied
and vacant label meanings, treating a high score as calibrated confidence,
or claiming training merely because a pretrained model produced an output.

1. How many numerical channel values are in a 4 × 3 RGB image?
2. Using the same weights and bias, compute `z` when `x1 = 0.3` and `x2 = 0.7`.
   Is its sigmoid above or below 0.5? Explain without a calculator.
3. In your own words, explain why changing a weight differs from changing the
   decision threshold. Which change belongs to training?

Viva prompts: What does one neuron calculate? Why does a successful training
example not prove the system will work on an unseen camera?

Answers are deliberately withheld until the student attempts these questions.
