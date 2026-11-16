"""Bind an editable counting line to one local video and its decoded first frame."""
import json
from copy import deepcopy
from pathlib import Path
from .flow import GateCounter
from .provenance import digest


def video_preview(source):
    """Read a file, never a camera index or network stream."""
    import cv2
    from PIL import Image
    import hashlib
    path = Path(source).resolve()
    if not path.is_file():
        raise ValueError('Choose an existing local video file')
    source_hash = digest(path)
    capture = cv2.VideoCapture(str(path))
    try:
        ok, frame = capture.read()
        if not ok:
            raise ValueError('The video has no readable first frame')
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if image.width * image.height > 25_000_000:
            raise ValueError('Resize video below 25 megapixels per frame')
    finally:
        capture.release()
    if digest(path) != source_hash:
        raise ValueError('Video changed while its preview was being read')
    return image, dict(source_path=str(path), source_sha256=source_hash,
                      image_size=list(image.size),
                      first_frame_rgb_sha256=hashlib.sha256(image.tobytes()).hexdigest())


def make_setup(identity, line, entry_direction):
    # Requiring an explicit direction prevents guessing which side is an entrance.
    gate = GateCounter(image_size=identity['image_size'], line=line,
                       entry_direction=entry_direction).config
    return dict(schema_version=1, video=deepcopy(identity), gate=gate,
                accuracy_evaluated=False,
                scope='Predicted crossings of a user-defined line; no occupancy or live availability inferred')


def validate_setup(setup, identity):
    if setup.get('schema_version') != 1:
        raise ValueError('Unsupported counting setup version')
    for key in ('source_sha256', 'image_size', 'first_frame_rgb_sha256'):
        if setup.get('video', {}).get(key) != identity.get(key):
            raise ValueError('Counting setup belongs to a different video or decoded view')
    gate = GateCounter(**setup['gate']).config
    if gate.get('time_unit')=='frames':raise ValueError('Desktop video requires a seconds-based gate setup')
    if gate['image_size'] != identity['image_size']:
        raise ValueError('Counting line dimensions differ from the video')
    return gate


def run_configured_flow(setup, output, engine, *, max_frames=30, callback=None, cancel=None):
    """Bounded, cancellable file-only execution shared by desktop and validation."""
    from .video import process_video
    if not isinstance(max_frames, int) or isinstance(max_frames, bool) or not 1 <= max_frames <= 240:
        raise ValueError('Choose between 1 and 240 processed frames')
    source = Path(setup['video']['source_path']).resolve()
    _, identity = video_preview(source)
    gate = validate_setup(setup, identity)
    folder = Path(output)
    if folder.exists() and any(folder.iterdir()):
        raise ValueError('Choose a new or empty results folder to preserve previous results')
    folder.mkdir(parents=True, exist_ok=True)
    manifest = deepcopy(setup)
    manifest.update(max_processed_frames=max_frames, sample_interval_seconds=.5,
                    detector_identity=dict(name=engine.model_name, weight_sha256=engine.weight_sha256,
                                           resolution=engine.resolution), source_verified_before=True,
                    status='running')
    def save_manifest():
        (folder/'source_and_gate.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    save_manifest()
    cancelled = False
    def should_cancel():
        nonlocal cancelled
        cancelled = bool(cancel and cancel())
        return cancelled
    try:
        result = process_video(str(source), engine, None, folder, every_seconds=.5,
                               max_frames=max_frames, confidence=.5, flow_config=gate,
                               callback=callback, cancel=should_cancel)
    except Exception as error:
        if cancelled and str(error)=='Video contained no decodable processed frames':
            result=dict(processed_frames=0,decoded_frames=0,occupancy_evaluated=False,
                        flow_enabled=True,flow_diagnostics=None,
                        claims='Cancelled before any processed frame; no crossing predictions')
        else:
            manifest.update(status='failed',error=str(error));save_manifest()
            raise
    unchanged = digest(source) == identity['source_sha256']
    manifest['source_verified_after'] = unchanged
    manifest['status'] = 'invalid_source_changed' if not unchanged else 'cancelled' if cancelled else 'completed'
    save_manifest()
    if not unchanged:
        raise ValueError('Video changed during processing; results retained but invalid')
    result['cancelled'] = cancelled
    (folder/'events.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
