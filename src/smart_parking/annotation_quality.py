"""Diagnostic source-label coverage;unlabelled/conflicting pixels stay unknown."""
import math
import numpy as np
from PIL import Image, ImageDraw

UNKNOWN = 255


def occupancy_support(rows, size):
    """Return supplied vacancy0/occupancy1 support,unknown255 outside/at conflicts.

    This does not generate a parking-region/background segmentation target.
    Pixel coordinates use round(normalized*(dimension-1)) at the requested
    diagnostic resolution;shared rasterized edges can be marked conflicting.
    """
    if len(size) != 2 or any(type(v) is not int or v < 2 for v in size) or size[0]*size[1] > 25_000_000:
        raise ValueError('Invalid diagnostic raster dimensions')
    width, height = size
    layers = [Image.new('1', size), Image.new('1', size)]
    draws = [ImageDraw.Draw(layer) for layer in layers]
    for row in rows:
        label = row['class_id']
        if type(label) is not int or label not in {0, 1}:
            raise ValueError('Unknown source class')
        points = row['normalized_polygon']
        if not 3 <= len(points) <= 64 or any(len(p) != 2 or any(not math.isfinite(v) or not 0 <= v <= 1 for v in p) for p in points):
            raise ValueError('Invalid normalized polygon')
        coordinates = [(round(x*(width-1)), round(y*(height-1))) for x, y in points]
        draws[label].polygon(coordinates, fill=1)
    occupied, vacant = [np.asarray(layer, dtype=bool) for layer in layers]
    conflict = occupied & vacant
    target = np.full((height, width), UNKNOWN, dtype=np.uint8)
    target[occupied & ~conflict] = 1
    target[vacant & ~conflict] = 0
    union = occupied | vacant
    return target, dict(pixels=int(target.size), supplied_union_pixels=int(union.sum()),
        known_occupied_pixels=int((target == 1).sum()), known_vacant_pixels=int((target == 0).sum()),
        unknown_pixels=int((target == UNKNOWN).sum()), conflict_pixels=int(conflict.sum()),
        conflict_fraction_of_supplied_union=float(conflict.sum()/max(1, union.sum())))


def difference_hash(image):
    """256bit grayscale difference hash;similarity candidates are not identities."""
    values = np.asarray(image.convert('L').resize((17, 16), Image.Resampling.LANCZOS))
    bits = (values[:, 1:] > values[:, :-1]).ravel()
    result = 0
    for bit in bits:
        result = (result << 1) | int(bit)
    return f'{result:064x}'


def similar_pairs(records, maximum_distance=8):
    """All unordered small-dHash-distance pairs;never merge or assign splits."""
    if type(maximum_distance) is not int or not 0 <= maximum_distance <= 256:
        raise ValueError('Invalid Hamming-distance limit')
    if len({r['image'] for r in records}) != len(records):
        raise ValueError('Duplicate image identity')
    values = []
    for row in sorted(records, key=lambda r: r['image']):
        text = row['difference_hash256']
        if not isinstance(text, str) or len(text) != 64 or any(c not in '0123456789abcdef' for c in text):
            raise ValueError('Malformed difference hash')
        values.append((row['image'], int(text, 16)))
    pairs = []
    for index, (left, first) in enumerate(values):
        for right, second in values[index+1:]:
            distance = (first ^ second).bit_count()
            if distance <= maximum_distance:
                pairs.append(dict(left=left, right=right, hamming_distance=distance))
    return sorted(pairs, key=lambda r: (r['hamming_distance'], r['left'], r['right']))
