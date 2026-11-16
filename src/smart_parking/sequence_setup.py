"""Label-assisted development gate placement using only five setup frames.

This is an operator-setup analogue, not learned automatic entrance discovery.
"""
import math
from statistics import median
from .flow import GateCounter


def setup_gate(setup_rows, image_size, object_id=1):
    """Place one vertical gate ahead of the initial horizontal foreground motion."""
    if [r['frame_index'] for r in setup_rows] != list(range(5)):
        raise ValueError('Pass exactly setup frames 0 through 4; later frames forbidden')
    width, height = image_size
    boxes = []
    for row in setup_rows:
        objects = [o for o in row['objects'] if o['object_id'] == object_id]
        if len(objects) != 1:
            raise ValueError('Setup requires the same labelled object in all five frames')
        box = objects[0]['box']
        if len(box) != 4 or not all(math.isfinite(x) for x in box):
            raise ValueError('Invalid setup box')
        if not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height):
            raise ValueError('Setup box outside view')
        boxes.append(box)
    centres = [(b[0] + b[2]) / 2 for b in boxes]
    motion = centres[-1] - centres[0]
    if abs(motion) < 2:
        raise ValueError('Initial horizontal motion below two pixels; gate unavailable')
    if width < 50 or height < 50:
        raise ValueError('Setup view too small for fixed 24-pixel margins')
    offset = max(24., .5 * median(b[2] - b[0] for b in boxes))
    x = round(min(width - 25, max(24, median(centres) + (offset if motion > 0 else -offset))))
    config = GateCounter(image_size=image_size, line=[[x, 24], [x, height - 25]],
                         time_unit='frames', max_gap_frames=1).config
    return config, dict(setup_frames=list(range(5)), object_id=object_id,
                        initial_horizontal_displacement_pixels=motion,
                        offset_pixels=offset, gate_x=x,
                        rule='Median setup x plus initial-motion sign times max(24, half median setup box width), clipped to 24-pixel margins',
                        uses_labelled_setup=True, automatic_entrance_discovery=False)
