"""Label-only coarse mask reconstruction (NumPy port of torch area/bilinear).

Reproduces F.interpolate(mode='area') to an exact integer-factor grid followed by
F.interpolate(mode='bilinear', align_corners=False) back to full size and a >=0.5
threshold. Coarse cell means are multiples of 1/factor**2 and bilinear weights are
multiples of 1/(2*factor), so float64 arithmetic gives the torch float32 values exactly.
This measures how well one interpolation scheme re-represents TARGET masks; it is not
model accuracy, a prediction on unseen images, or a proven architecture upper bound.
"""
import numpy as np


def area_downsample(masks, factor):
    masks = np.asarray(masks)
    if masks.ndim != 3 or factor < 1 or masks.shape[1] % factor or masks.shape[2] % factor:
        raise ValueError('N,H,W input with H and W divisible by an integer factor required')
    n, h, w = masks.shape
    return masks.astype(np.float64).reshape(n, h // factor, factor, w // factor, factor).mean((2, 4))


def _axis_weights(out_size, in_size):
    scale = in_size / out_size
    src = (np.arange(out_size) + .5) * scale - .5
    src = np.maximum(src, 0.)  # torch clamps negative source coordinates to zero
    low = np.minimum(np.floor(src).astype(int), in_size - 1)
    high = np.minimum(low + 1, in_size - 1)
    frac = src - low
    return low, high, frac


def bilinear_upsample(coarse, size):
    coarse = np.asarray(coarse, dtype=np.float64)
    if coarse.ndim != 3:
        raise ValueError('N,h,w coarse input required')
    height, width = size
    y0, y1, fy = _axis_weights(height, coarse.shape[1])
    x0, x1, fx = _axis_weights(width, coarse.shape[2])
    top = coarse[:, y0][:, :, x0] * (1 - fx) + coarse[:, y0][:, :, x1] * fx
    bottom = coarse[:, y1][:, :, x0] * (1 - fx) + coarse[:, y1][:, :, x1] * fx
    return top * (1 - fy)[None, :, None] + bottom * fy[None, :, None]


def reconstruct(masks, factor=4, threshold=.5):
    masks = np.asarray(masks)
    if masks.dtype != np.bool_:
        raise ValueError('Boolean target masks required')
    rebuilt = bilinear_upsample(area_downsample(masks, factor), masks.shape[1:])
    return rebuilt >= threshold
