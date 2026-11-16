"""Four fixed TRAIN examples: dimensions/EXIF/label parsing,never model scoring."""
import csv
import hashlib
import io
import json
import sys
import tarfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from smart_parking.parking_labels import parse_space_polygons, training_inspection_selection
from smart_parking.provenance import digest


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def main():
    started = datetime.now(timezone.utc)
    state_path = ROOT / 'data/automation_state.json'
    state = json.loads(state_path.read_text())
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    rid = 'OPEN-SPACE-TRAIN-INSPECTION-' + started.strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT / 'experiments/results' / rid
    folder.mkdir(parents=True, exist_ok=False)
    source = json.loads((ROOT / 'models/open_space_asset_qualification.json').read_text())
    metadata = json.loads((ROOT / source['metadata_path']).read_text())
    usage = json.loads((ROOT / 'data/manifests/open_space_usage_qualification_v1.json').read_text())
    assert usage['image_analysis_authorized'] and source['asset_integrity_gate_passed']
    assert source['commit'] == usage['commit'] == metadata['commit']
    assert digest(ROOT / source['metadata_path']) == source['metadata_sha256']
    archive = ROOT / source['summary']['archive']
    assert digest(archive) == source['summary']['archive_sha256']
    selection = training_inspection_selection(metadata['tree']['tree'], count=4)
    identities = {x['path']: x for x in source['members']}
    assert all(x['path'].startswith('train/images/') and x['annotation'].startswith('train/labels/') for x in selection)
    source_paths = ['scripts/inspect_open_space_training.py', 'src/smart_parking/parking_labels.py', 'tests/test_parking_labels.py']
    hashes = {p: digest(ROOT / p) for p in source_paths}
    protected = source['protected_hashes']
    assert all(digest(ROOT / p) == h for p, h in protected.items())
    protocol = dict(run_id=rid, source_ids=['SRC-DS-018'], started_at=started.isoformat(), seed=126,
        hypothesis='Four label-blind preselected TRAIN photos have safe dimensions and parsable finite in-bounds YOLO-space polygons;inspect available capture metadata without assuming independent test groups.',
        source_commit=source['commit'], archive=source['summary']['archive'], archive_sha256=digest(archive),
        parent_qualification_run=source['run_id'], source_hashes=hashes, protected_hashes=protected,
        selection=selection, selection_rule='Lexically sorted publisher TRAIN images at indices0,floor517/3,floor1034/3,517;no labels/pixels/model outputs consulted',
        gates=['Exactly four prespecified TRAIN images,zero valid/test image or label reads', 'Verified encoded members match qualified parent identities',
            'JPEG dimensions <=25million pixels', 'Strict two-class normalized polygon parsing with explicit tiny-rounding handling',
            'Source rows and originals retained;no model inference/training or accuracy', 'Protected models/claims unchanged'],
        limitations=['Four development-inspection photos only,not all731image integrity/quality', 'Polygon labels are supplied geometry,not independently verified pixel masks',
            'Missing capture metadata stays unknown;no independent split admission', 'Visual review remains separate from syntactic parsing',
            'Any source inspection can make its whole unknown camera/session group development;do not assume remaining publisher test independent'])
    dump(folder / 'protocol.json', protocol)
    dump(folder / 'implementation_sources.json', {p: dict(sha256=h, source=(ROOT / p).read_text()) for p, h in hashes.items()})
    state['active_validation_jobs'] = [dict(run_id=rid, phase='prespecified TRAIN geometry inspection')]
    dump(state_path, state)
    clock = time.monotonic()
    outputs = ROOT / 'outputs/open_space_inspection' / rid
    outputs.mkdir(parents=True, exist_ok=False)
    records = []
    decoded = 0
    touched = []
    panels = []
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
    small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 13)
    counts = Counter()
    try:
        prefix = 'open-space-parking-dataset-' + source['commit'] + '/'
        with tarfile.open(archive, 'r:gz') as stream:
            for item in selection:
                if (folder / 'CANCEL').exists() or time.monotonic() - clock > 180:
                    raise InterruptedError('Bounded inspection cancelled/timed out')
                bodies = {}
                for name in [item['path'], item['annotation']]:
                    member = stream.getmember(prefix + name)
                    assert member.isfile() and member.size == identities[name]['bytes']
                    with stream.extractfile(member) as source_file:
                        body = source_file.read(member.size + 1)
                    assert hashlib.sha256(body).hexdigest() == identities[name]['sha256']
                    destination = outputs / 'originals' / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with destination.open('xb') as target:
                        target.write(body)
                    bodies[name] = body
                    touched.append(name)
                with Image.open(io.BytesIO(bodies[item['path']])) as original:
                    assert original.format == 'JPEG' and 0 < original.width*original.height <= 25_000_000
                    exif = original.getexif()
                    capture = {key: str(exif[tag]) if tag in exif else None for tag, key in
                        [(36867, 'DateTimeOriginal'), (306, 'DateTime'), (271, 'Make'), (272, 'Model'), (274, 'Orientation')]}
                    image = original.convert('RGB')
                    decoded += 1
                parse_error = None
                try:
                    labels = parse_space_polygons(bodies[item['annotation']].decode('utf-8'))
                except ValueError as error:
                    labels = []
                    parse_error = str(error)
                for label in labels:
                    counts[label['class_name']] += 1
                width, height = image.size
                preview = image.copy()
                preview.thumbnail((800, 600))
                canvas = Image.new('RGB', (840, 680), '#f5f6f8')
                canvas.paste(preview, (20, 65))
                draw = ImageDraw.Draw(canvas)
                draw.text((20, 10), 'TRAIN inspection | ' + Path(item['path']).name, fill='black', font=font)
                draw.text((20, 36), f'{width}x{height} | {len(labels)} supplied polygons | No model predictions', fill='#333333', font=small)
                for i, label in enumerate(labels, 1):
                    points = [(20+x*preview.width, 65+y*preview.height) for x,y in label['normalized_polygon']]
                    color = '#f39a23' if label['class_id'] == 0 else '#168b62'
                    draw.line(points+points[:1], fill=color, width=2)
                    draw.text((points[0][0]+1, points[0][1]+1), str(i), fill=color, font=small)
                draw.text((20, 655), 'Orange: supplied occupied | Green: supplied vacant | Supplied polygons, not model predictions', fill='#333333', font=small)
                preview_path = folder / (Path(item['path']).stem + '_labels.png')
                canvas.save(preview_path)
                panels.append(canvas)
                records.append(dict(image=item['path'], annotation=item['annotation'], publisher_split='train',
                    source_image_sha256=identities[item['path']]['sha256'], source_label_sha256=identities[item['annotation']]['sha256'],
                    width=width, height=height, mode='RGB', jpeg_exif=capture, polygons=len(labels), label_parse_error=parse_error, labels=labels,
                    rgb_pixels_sha256=hashlib.sha256(image.tobytes()).hexdigest(), source_copies=(outputs/'originals').relative_to(ROOT).as_posix(),
                    preview=preview_path.relative_to(ROOT).as_posix(), preview_sha256=digest(preview_path)))
        assert len(records) == 4 and len(touched) == 8
        assert all(p.startswith('train/') for p in touched)
        assert all(digest(ROOT / p) == h for p, h in {**hashes, **protected}.items())
        sheet = Image.new('RGB', (1680, 1360), 'white')
        for index, panel in enumerate(panels):
            sheet.paste(panel, ((index % 2)*840, (index // 2)*680))
        sheet.save(folder / 'contact_sheet.png')
        summary = dict(train_images_pixel_decoded=4, train_label_files_interpreted=4, publisher_validation_or_test_files_read=0,
            polygons=sum(x['polygons'] for x in records), class_counts=dict(counts),
            label_files_rejected=sum(x['label_parse_error'] is not None for x in records),
            rounding_clipped_boxes=sum(r['rounding_clipped'] for x in records for r in x['labels']),
            capture_datetime_present=sum(bool(x['jpeg_exif']['DateTimeOriginal'] or x['jpeg_exif']['DateTime']) for x in records),
            technical_training_sample_gate_passed=all(x['label_parse_error'] is None for x in records), semantic_visual_review_completed=False,
            independent_benchmark_admitted=False, model_training_admitted=False, model_training_or_scoring=False,
            pixel_segmentation_ground_truth_created=False, originals_preserved=True)
        report = dict(protocol, finished_at=datetime.now(timezone.utc).isoformat(), duration_seconds=time.monotonic()-clock,
            summary=summary, records=records, exact_read_members=touched,
            contact_sheet=(folder/'contact_sheet.png').relative_to(ROOT).as_posix())
        dump(folder / 'run.json', report)
        dump(ROOT / 'models/open_space_training_inspection.json', report)
        registry = ROOT / 'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig', newline='') as source_file:
            fields = csv.DictReader(source_file).fieldnames
        row = dict(experiment_id=rid, run_type='Preselected TRAIN image/label admission inspection;no model score',
            started_at=protocol['started_at'], finished_at=report['finished_at'], source_ids='SRC-DS-018',
            split_ids='Four fixed publisher TRAIN images only;no independent split admitted',
            configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(), architecture='Strict YOLO polygon parser and image/EXIF checks;no model',
            random_seed=126, hardware='CPU', execution_environment=sys.version.split()[0], training_duration=report['duration_seconds'],
            evaluation_metrics=json.dumps(summary), logs=folder.relative_to(ROOT).as_posix(), checkpoints='Original checkpoints/claims unchanged',
            code_revision_basis='8d15743 plus frozen source snapshot', implementation_sha256=hashes[source_paths[0]],
            conclusions='Four preselected TRAIN files audited;parse failures retained,visual meaning/grouping remain unqualified,no model/benchmark admission')
        with registry.open('a', encoding='utf-8', newline='') as target:
            csv.DictWriter(target, fieldnames=fields).writerow({k: row.get(k, '') for k in fields})
        state = json.loads(state_path.read_text())
        state['completed_run_ids'].append(rid)
        state['completed_recorded_runs_since_schedule'] = len(set(state['completed_run_ids']))
        state['last_completed_run'] = rid
        print(json.dumps(dict(run_id=rid, summary=summary), indent=2))
    except BaseException as error:
        dump(folder / 'interrupted.json', dict(error=type(error).__name__, detail=str(error), completed_run_counted=False,
            touched_members=touched, inspected_train_pixels=decoded, originals_preserved=True))
        state = json.loads(state_path.read_text())
        raise
    finally:
        state['active_validation_jobs'] = []
        dump(state_path, state)


if __name__ == '__main__':
    main()
