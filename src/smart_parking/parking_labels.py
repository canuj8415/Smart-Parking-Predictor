"""Strict publisher YOLO-space labels and label-blind TRAIN inspection selection.

Box and polygon formats remain distinct;neither proves annotation accuracy.
Empty annotation files do not establish exhaustive occupancy labels.
"""
import math
import re
from pathlib import PurePosixPath

CLASS_NAMES = {0: 'space-occupied', 1: 'space-vacant'}
ROUNDING_TOLERANCE = 1e-6


def parse_space_labels(text):
    """Parse exactly class,x-center,y-center,width,height; reject bad rows.

    A corner can exceed the image by at most 1e-6 after decimal serialization.
    Such corners are clipped explicitly and the original numbers are retained.
    Larger overflows,nonfinite values and duplicate rectangles fail the file.
    """
    if not isinstance(text, str):
        raise ValueError('Labels must be decoded UTF-8 text')
    rows = []
    seen = set()
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        tokens = line.split()
        if len(tokens) != 5 or tokens[0] not in {'0', '1'}:
            raise ValueError(f'Line {number}: expected integer class0/1 and four coordinates')
        try:
            center_x, center_y, width, height = map(float, tokens[1:])
        except ValueError as error:
            raise ValueError(f'Line {number}: nonnumeric coordinates') from error
        values = [center_x, center_y, width, height]
        if not all(math.isfinite(v) for v in values):
            raise ValueError(f'Line {number}: nonfinite coordinate')
        if not (0 <= center_x <= 1 and 0 <= center_y <= 1 and 0 < width <= 1 and 0 < height <= 1):
            raise ValueError(f'Line {number}: invalid normalized center/size')
        corners = [center_x-width/2, center_y-height/2, center_x+width/2, center_y+height/2]
        if any(v < -ROUNDING_TOLERANCE or v > 1+ROUNDING_TOLERANCE for v in corners):
            raise ValueError(f'Line {number}: rectangle exceeds image bounds')
        clipped = [max(0.0, min(1.0, v)) for v in corners]
        key = tuple(clipped)
        if key in seen:
            raise ValueError(f'Line {number}: duplicate rectangle or conflicting class')
        seen.add(key)
        label = int(tokens[0])
        rows.append(dict(source_line=number, source_text=line, class_id=label,
            class_name=CLASS_NAMES[label], normalized_center_size=values,
            normalized_xyxy=clipped, rounding_clipped=corners != clipped))
    return rows


def parse_space_polygons(text):
    """Parse class plus3..64XYvertices;retain originals and reject invalid rings.

    A repeated closing vertex is allowed once. Nonadjacent crossing/touching
    edges,duplicate interior vertices and zero-area polygons are rejected.
    """
    if not isinstance(text, str):
        raise ValueError('Labels must be decoded UTF-8 text')
    rows = []
    seen = set()
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        tokens = line.split()
        if tokens[0] not in {'0', '1'} or len(tokens) < 7 or len(tokens) % 2 != 1 or len(tokens) > 131:
            raise ValueError(f'Line {number}: expected class0/1 plus polygon XYvertices')
        try:
            values = list(map(float, tokens[1:]))
        except ValueError as error:
            raise ValueError(f'Line {number}: nonnumeric polygon coordinate') from error
        if not all(math.isfinite(v) and -ROUNDING_TOLERANCE <= v <= 1+ROUNDING_TOLERANCE for v in values):
            raise ValueError(f'Line {number}: nonfinite or outside polygon coordinate')
        points = [tuple(max(0.0, min(1.0, v)) for v in values[i:i+2]) for i in range(0, len(values), 2)]
        closing = len(points) > 1 and points[0] == points[-1]
        if closing:
            points.pop()
        if not 3 <= len(points) <= 64 or len(set(points)) != len(points):
            raise ValueError(f'Line {number}: duplicate or insufficient polygon vertices')
        area = abs(sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(points, points[1:]+points[:1])))/2
        if area <= 1e-10:
            raise ValueError(f'Line {number}: zero-area polygon')
        def cross(a, b, c):
            return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        def on_segment(a, b, c):
            return (abs(cross(a, b, c)) <= 1e-12 and min(a[0], b[0])-1e-12 <= c[0] <= max(a[0], b[0])+1e-12
                    and min(a[1], b[1])-1e-12 <= c[1] <= max(a[1], b[1])+1e-12)
        edges = list(zip(points, points[1:]+points[:1]))
        for i, (a, b) in enumerate(edges):
            for j, (c, d) in enumerate(edges):
                if j <= i+1 or (i == 0 and j == len(edges)-1):
                    continue
                opposite = cross(a, b, c)*cross(a, b, d) < 0 and cross(c, d, a)*cross(c, d, b) < 0
                if opposite or on_segment(a, b, c) or on_segment(a, b, d) or on_segment(c, d, a) or on_segment(c, d, b):
                    raise ValueError(f'Line {number}: self-intersecting polygon')
        # Canonical cyclic/reversed representation catches equivalent duplicate rings.
        ring = tuple(points)
        rotations = [ring[i:]+ring[:i] for i in range(len(ring))]
        reverse = tuple(reversed(ring))
        rotations += [reverse[i:]+reverse[:i] for i in range(len(reverse))]
        key = min(rotations)
        if key in seen:
            raise ValueError(f'Line {number}: duplicate polygon or conflicting class')
        seen.add(key)
        label = int(tokens[0])
        rows.append(dict(source_line=number, source_text=line, class_id=label, class_name=CLASS_NAMES[label],
            source_normalized_xy=values, normalized_polygon=[list(p) for p in points], closing_vertex_removed=closing,
            normalized_area=area, rounding_clipped=values != [max(0.0, min(1.0, v)) for v in values]))
    return rows


def training_inspection_selection(tree, count=4):
    """Choose uniformly spaced lexical TRAIN filenames without pixels or labels."""
    if type(count) is not int or count < 1:
        raise ValueError('Positive integer inspection size required')
    images = {}
    for row in tree:
        name = row['path']
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
            raise ValueError('Unsafe publisher path')
        if row.get('type') != 'blob' or not name.startswith('train/images/'):
            continue
        if len(path.parts) != 3 or path.suffix != '.jpg':
            raise ValueError('Unexpected TRAIN image identity')
        if name in images or not re.fullmatch('[0-9a-f]{40}', row['sha']):
            raise ValueError('Duplicate path or invalid Git identity')
        if type(row.get('size')) is not int or not 0 < row['size'] <= 4*1024**2:
            raise ValueError('Unexpected publisher image size')
        images[name] = row
    names = sorted(images)
    if len(names) < count:
        raise ValueError('Insufficient TRAIN images')
    indices = [0] if count == 1 else [i*(len(names)-1)//(count-1) for i in range(count)]
    return [dict(images[names[i]], selected_index=i, publisher_training_images=len(names),
        annotation=names[i].replace('/images/', '/labels/').rsplit('.', 1)[0]+'.txt') for i in indices]
