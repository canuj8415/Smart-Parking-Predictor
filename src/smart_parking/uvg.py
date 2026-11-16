"""Publisher-bound development access for the newly reserved UVG collection."""
import json
import math
from collections import Counter
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit
from .provenance import digest

COLLECTION = 'https://ultravideo.fi/UVG-VCM/'


def require_development(manifest_path, expected_sha256, url):
    if digest(manifest_path) != expected_sha256:
        raise ValueError('Whole-sequence source reservation changed')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['canonical_collection'] != COLLECTION:
        raise ValueError('Wrong canonical video collection')
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname is None or parsed.hostname.casefold() != 'ultravideo.fi'
            or parsed.username or parsed.password or parsed.port not in (None, 443) or parsed.query or parsed.fragment):
        raise ValueError('Only fixed publisher HTTPS asset URLs are admitted')
    path = unquote(parsed.path)
    if '..' in PurePosixPath(path).parts or '\\' in path:
        raise ValueError('Publisher asset path traversal rejected')
    parts = PurePosixPath(path).parts
    if len(parts) != 4 or parts[1].casefold() != 'uvg-vcm':
        raise ValueError('Unknown sequence asset path')
    sequence = next((item for item in manifest['sequences'] if item['name'].casefold() == parts[2].casefold()), None)
    if sequence is None or sequence['role'] != 'development':
        raise ValueError('Entire source sequence is reserved or unadmitted')
    if parts[3] not in sequence['assets'] or '_vis.' in parts[3]:
        raise ValueError('Unknown or annotated visualization asset is not a model input')
    return sequence


def validate_annotations(document, expected_frames):
    """Validate UVG v1 normalized objects without inventing absent negatives.

    Frame IDs are one based. Persistent IDs must retain class and color triplet.
    Publisher JSON color triplets are BGR relative to decoded RGB PNG planes.
    This validates supplied labels, not their exhaustiveness or video alignment.
    """
    if not isinstance(document, dict) or document.get('version') != '1.0':
        raise ValueError('Expected publisher annotation version 1.0')
    if set(document) != {'version', *(str(i) for i in range(1, expected_frames+1))}:
        raise ValueError('Annotation frame IDs must be complete and one based')
    tracks, classes, observations = {}, Counter(), 0
    required = {'class_name', 'class_id', 'track_id', 'mask_color',
                'x_min', 'y_min', 'x_max', 'y_max', 'polygon'}
    for frame in range(1, expected_frames+1):
        objects = document[str(frame)]
        if not isinstance(objects, list):
            raise ValueError('Frame annotations must be a list')
        seen_ids, seen_colors = set(), set()
        for obj in objects:
            if not isinstance(obj, dict) or set(obj) != required:
                raise ValueError('Unknown annotation object schema')
            for name in ('class_id', 'track_id'):
                if type(obj[name]) is not int or obj[name] < 0:
                    raise ValueError('Invalid object identity')
            color = obj['mask_color']
            if not isinstance(color, list) or len(color) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in color):
                raise ValueError('Expected three integer color channels')
            color = tuple(color)
            if obj['track_id'] in seen_ids or color in seen_colors:
                raise ValueError('Duplicate per-frame identity or color')
            seen_ids.add(obj['track_id']); seen_colors.add(color)
            if not isinstance(obj['class_name'], str) or not obj['class_name']:
                raise ValueError('Missing class name')
            identity = (obj['class_id'], obj['class_name'], color)
            if tracks.setdefault(obj['track_id'], identity) != identity:
                raise ValueError('Persistent identity changes class or mask color')
            polygon = obj['polygon']
            if not isinstance(polygon, list) or len(polygon) < 6 or len(polygon) % 2:
                raise ValueError('Expected at least three normalized polygon vertices')
            bounds = [obj[k] for k in ('x_min', 'y_min', 'x_max', 'y_max')]
            for value in bounds+polygon:
                if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError('Nonfinite or out-of-bounds normalized coordinate')
            xmin, ymin, xmax, ymax = bounds
            if xmin >= xmax or ymin >= ymax:
                raise ValueError('Degenerate bounding box')
            extrema = [min(polygon[::2]), min(polygon[1::2]), max(polygon[::2]), max(polygon[1::2])]
            if any(abs(a-b) > 2e-6 for a, b in zip(bounds, extrema)):
                raise ValueError('Bounding box disagrees with polygon extent')
            classes[obj['class_name']] += 1; observations += 1
    return dict(frames=expected_frames, object_observations=observations,
                unique_tracks=len(tracks), class_observations=dict(classes),
                coordinate_system='normalized [0,1], one-based frame IDs',
                exhaustive_ground_truth_established=False)


def instance_pixels(decoded_png, annotation_color):
    """Map publisher JSON BGR to a Pillow-decoded RGB(A) mask explicitly.

    Discovered on development data; never select channel order by model score.
    Transparent pixels cannot support an instance even if their RGB bytes match.
    """
    import numpy as np
    array = np.asarray(decoded_png)
    if array.dtype != np.uint8 or array.ndim != 3 or array.shape[2] not in (3,4):
        raise ValueError('Expected an RGB or RGBA uint8 decoded PNG')
    if len(annotation_color) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in annotation_color):
        raise ValueError('Expected publisher BGR integer triplet')
    pixels = np.all(array[:,:,:3] == np.asarray(annotation_color[::-1],dtype=np.uint8), axis=2)
    if array.shape[2] == 4:
        pixels &= array[:,:,3] > 0
    return pixels


def supported_instance_mask(decoded_png, annotation_color):
    """Absent raster support is unknown, never a negative or zero-IoU label."""
    pixels = instance_pixels(decoded_png, annotation_color)
    if not pixels.any():
        return None, 'unknown_no_raster_support'
    return pixels, 'provided_instance_pixels'
