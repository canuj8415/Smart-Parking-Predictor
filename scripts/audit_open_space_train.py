"""Bounded all-TRAIN source quality audit;no valid/test decode or model use."""
import csv
import hashlib
import io
import json
import shutil
import sys
import tarfile
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from smart_parking.annotation_quality import occupancy_support, difference_hash, similar_pairs
from smart_parking.parking_labels import parse_space_polygons, training_inspection_selection
from smart_parking.provenance import digest


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    started = datetime.now(timezone.utc)
    state_path = ROOT / 'data/automation_state.json'
    state = json.loads(state_path.read_text())
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    rid = 'OPEN-SPACE-TRAIN-AUDIT-' + started.strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT / 'experiments/results' / rid
    folder.mkdir(parents=True, exist_ok=False)
    source = json.loads((ROOT / 'models/open_space_asset_qualification.json').read_text())
    metadata = json.loads((ROOT / source['metadata_path']).read_text())
    usage = json.loads((ROOT / 'data/manifests/open_space_usage_qualification_v2.json').read_text())
    assert usage['image_analysis_authorized'] and usage['project_role'] == 'development_exposed'
    assert digest(ROOT / source['metadata_path']) == source['metadata_sha256']
    archive = ROOT / source['summary']['archive']
    assert digest(archive) == source['summary']['archive_sha256']
    images = sorted(x['path'] for x in metadata['tree']['tree'] if x['type'] == 'blob' and x['path'].startswith('train/images/') and x['path'].endswith('.jpg'))
    assert len(images) == 518
    identities = {x['path']: x for x in source['members']}
    wanted = set(images) | {p.replace('/images/', '/labels/').rsplit('.', 1)[0]+'.txt' for p in images}
    assert len(wanted) == 1036 and wanted.issubset(identities)
    byte_budget = 128*1024**2
    assert sum(identities[p]['bytes'] for p in wanted) < byte_budget
    preview_names = {x['path'] for x in training_inspection_selection(metadata['tree']['tree'])}
    paths = ['scripts/audit_open_space_train.py','src/smart_parking/annotation_quality.py','src/smart_parking/parking_labels.py','tests/test_annotation_quality.py']
    hashes = {p: digest(ROOT / p) for p in paths}
    protected = source['protected_hashes']
    assert all(digest(ROOT / p) == h for p, h in protected.items())
    protocol = dict(run_id=rid, started_at=started.isoformat(), seed=127, source_ids=['SRC-DS-018'],
        hypothesis='All518publisher TRAIN photos can be byte-bound,decoded,and audited for strict polygon validity,label coverage and similarity candidates while keeping unannotated/conflicting areas unknown and other publisher folders unexamined semantically.',
        source_commit=source['commit'], source_archive=source['summary']['archive'], source_archive_sha256=digest(archive),
        source_hashes=hashes, protected_hashes=protected, source_role='development_exposed', canonical_group='SRC-DS-018:whole-publisher-collection',
        selected_images=images, selected_image_manifest_sha256=hashlib.sha256('\n'.join(images).encode()).hexdigest(),
        selected_original_byte_budget=byte_budget, maximum_seconds=600, similarity_hamming_threshold=8,
        coverage_raster=[320,160], preview_images=sorted(preview_names),
        gates=['1036TRAIN member payloads match pinned source identities','Every TRAIN photo has safe JPEG dimensions/retained source metadata',
            'Strict polygon errors quarantine the entire label file,without repairs or imputation','Unannotated/conflicting class support stays255unknown',
            'Near-image hash matches are candidates,never automatic duplicate removal or independent splits','No valid/test pixel decode,target interpretation,model use or final replay',
            'Protected source/model/claim bytes unchanged'],
        limitations=['Syntactic quality is not manual annotation accuracy/exhaustiveness','320x160raster shared boundaries can create diagnostic conflicts',
            'Source grouping remains unknown;whole collection development-exposed','No valid independent final cohort created','No parking/background segmentation negatives inferred'])
    dump(folder / 'protocol.json', protocol)
    dump(folder / 'implementation_sources.json', {p: dict(sha256=h,source=(ROOT/p).read_text()) for p,h in hashes.items()})
    original_copies = ROOT / 'outputs/open_space_train_audit' / rid / 'originals'
    assert shutil.disk_usage(ROOT).free > byte_budget + 1024**3
    original_copies.mkdir(parents=True, exist_ok=False)
    derived = ROOT / 'data/splits/open-space-train-audit-v1' / rid
    derived.mkdir(parents=True, exist_ok=False)
    state['active_validation_jobs'] = [dict(run_id=rid,phase='TRAIN-only original member copy and quality audit')]
    dump(state_path,state)
    clock = time.monotonic()
    frames = []; polygons = []; quarantine = []; copied = set(); candidates = []
    total_bytes = 0
    try:
        prefix = 'open-space-parking-dataset-'+source['commit']+'/'
        with tarfile.open(archive,'r|gz') as stream:
            for member in stream:
                if (folder/'CANCEL').exists() or time.monotonic()-clock > 600:
                    raise InterruptedError('Bounded TRAIN-only audit cancelled/timed out')
                if not member.name.startswith(prefix):
                    continue
                name = member.name[len(prefix):]
                if name not in wanted:
                    continue
                assert member.isfile() and name not in copied and member.size == identities[name]['bytes']
                with stream.extractfile(member) as source_file:
                    body = source_file.read(member.size+1)
                assert len(body) == member.size and hashlib.sha256(body).hexdigest() == identities[name]['sha256']
                total_bytes += len(body)
                assert total_bytes <= byte_budget
                path = original_copies/name
                path.parent.mkdir(parents=True,exist_ok=True)
                with path.open('xb') as target:target.write(body)
                copied.add(name)
        assert copied == wanted
        for index,name in enumerate(images):
            if (folder/'CANCEL').exists() or time.monotonic()-clock > 600:
                raise InterruptedError('Bounded TRAIN-only audit cancelled/timed out')
            label_name = name.replace('/images/','/labels/').rsplit('.',1)[0]+'.txt'
            record = dict(image=name,annotation=label_name,source_image_sha256=identities[name]['sha256'],
                source_label_sha256=identities[label_name]['sha256'],publisher_split='train',project_group=protocol['canonical_group'])
            try:
                with Image.open(original_copies/name) as original:
                    assert original.format == 'JPEG' and 0 < original.width*original.height <= 25_000_000
                    exif = original.getexif()
                    record.update(width=original.width,height=original.height,capture_date_exif=str(exif.get(36867) or exif.get(306) or ''),
                        exif_orientation=exif.get(274))
                    image = original.convert('RGB')
                record.update(rgb_pixels_sha256=hashlib.sha256(image.tobytes()).hexdigest(),difference_hash256=difference_hash(image))
                text = (original_copies/label_name).read_text(encoding='utf-8')
                record['label_source_rows'] = sum(bool(x.strip()) for x in text.splitlines())
                labels = parse_space_polygons(text)
                target,coverage = occupancy_support(labels,tuple(protocol['coverage_raster']))
                record.update(status='accepted_syntax',polygons=len(labels),coverage=coverage,
                    occupied_polygons=sum(x['class_id']==0 for x in labels),vacant_polygons=sum(x['class_id']==1 for x in labels),
                    rounding_clipped_polygons=sum(x['rounding_clipped'] for x in labels),error=None)
                for label in labels:
                    polygons.append(dict(image=name,annotation=label_name,source_line=label['source_line'],class_id=label['class_id'],
                        class_name=label['class_name'],source_text=label['source_text'],source_line_text_sha256=hashlib.sha256(label['source_text'].encode()).hexdigest(),
                        normalized_polygon=json.dumps(label['normalized_polygon'],separators=(',',':')),normalized_area=label['normalized_area'],
                        source_image_sha256=identities[name]['sha256'],source_label_sha256=identities[label_name]['sha256']))
                if name in preview_names:
                    support = np.full((*target.shape,3),128,dtype=np.uint8)
                    support[target==1]=[239,150,40];support[target==0]=[30,155,100]
                    canvas=Image.new('RGB',(640,200),'white')
                    canvas.paste(image.resize((320,160)),(0,25));canvas.paste(Image.fromarray(support),(320,25))
                    draw=ImageDraw.Draw(canvas);draw.text((5,5),Path(name).name+' | Supplied class support; no model predictions',fill='black')
                    draw.text((5,186),'Orange occupied | Green vacant | Gray unknown/outside/conflict',fill='black')
                    canvas.save(folder/(Path(name).stem+'_support.png'))
            except (ValueError,AssertionError,OSError) as error:
                record.update(status='quarantined',error=type(error).__name__+': '+str(error))
                quarantine.append(dict(image=name,annotation=label_name,error=record['error'],source_label_sha256=identities[label_name]['sha256']))
            frames.append(record)
            dump(folder/'progress.json',dict(phase='TRAIN-only quality audit',images_processed=index+1,total_images=len(images),quarantined=len(quarantine)))
        candidates=similar_pairs([x for x in frames if 'difference_hash256' in x],8)
        accepted=[x for x in frames if x['status']=='accepted_syntax']
        pixels=defaultdict(list)
        for row in frames:
            if 'rgb_pixels_sha256' in row:pixels[row['rgb_pixels_sha256']].append(row['image'])
        exact=[g for g in pixels.values() if len(g)>1]
        write_csv(derived/'polygons.csv',polygons,['image','annotation','source_line','class_id','class_name','source_text','source_line_text_sha256','normalized_polygon','normalized_area','source_image_sha256','source_label_sha256'])
        write_csv(derived/'similarity_candidates.csv',candidates,['left','right','hamming_distance'])
        dump(derived/'frames.json',frames);dump(derived/'quarantine.json',quarantine)
        summary=dict(train_images_audited=len(frames),train_original_members_verified=len(copied),train_original_bytes=total_bytes,
            accepted_image_label_pairs=len(accepted),quarantined_image_label_pairs=len(quarantine),accepted_polygons=len(polygons),
            occupied_polygons=sum(x['class_id']==0 for x in polygons),vacant_polygons=sum(x['class_id']==1 for x in polygons),
            quarantined_source_label_rows=sum(x.get('label_source_rows',0) for x in frames if x['status']=='quarantined'),
            dimensions=dict(Counter(str(x.get('width'))+'x'+str(x.get('height')) for x in frames)),
            capture_dates_present=sum(bool(x.get('capture_date_exif')) for x in frames),
            rounding_clipped_polygons=sum(x.get('rounding_clipped_polygons',0) for x in accepted),
            exact_rgb_duplicate_groups=len(exact),exact_rgb_duplicate_extra_images=sum(len(g)-1 for g in exact),
            low_dhash_distance_candidate_pairs=len(candidates),similarity_hamming_threshold=8,
            frames_with_diagnostic_class_conflicts=sum(x['coverage']['conflict_pixels']>0 for x in accepted),
            diagnostic_conflict_pixels=sum(x['coverage']['conflict_pixels'] for x in accepted),
            diagnostic_unknown_pixels=sum(x['coverage']['unknown_pixels'] for x in accepted),
            outside_or_conflicting_support_policy='255unknown,never inferred vacant or background',
            publisher_valid_test_pixels_and_semantic_labels_read=0,source_group='SRC-DS-018:whole-publisher-collection',
            independent_final_eligible=False,model_training_admitted=False,model_training_or_scoring=False,
            region_background_negative_labels_created=False,source_integrity_gate_passed=True,
            all_train_annotation_files_valid=not quarantine)
        assert len(frames)==518 and all(name.startswith('train/') for name in copied)
        assert all(digest(ROOT/p)==h for p,h in {**hashes,**protected}.items())
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-clock,
            audit_completed=True,summary=summary,quarantine=quarantine,exact_rgb_duplicate_members=exact,
            closest_similarity_candidates=candidates[:20],original_copies=original_copies.relative_to(ROOT).as_posix(),
            derived_files={p.relative_to(ROOT).as_posix():digest(p) for p in sorted(derived.iterdir())},
            preview_files={p.relative_to(ROOT).as_posix():digest(p) for p in folder.glob('*_support.png')},
            semantic_read_scope='Only TRAIN payloads explicitly extracted for decoding/target interpretation;whole compressed archive bytes and all headers scanned for integrity/location')
        dump(folder/'run.json',report);dump(ROOT/'models/open_space_train_audit.json',report)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=rid,run_type='All-TRAIN source quality/quarantine/similarity audit;no model score',started_at=protocol['started_at'],finished_at=report['finished_at'],
            source_ids='SRC-DS-018',split_ids='All518publisher TRAIN images;whole source development-exposed',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),
            architecture='Strict polygon parser;unknown-aware class support;256bit diagnostic dHash;no model',random_seed=127,hardware='CPU',execution_environment=sys.version.split()[0],
            training_duration=report['duration_seconds'],evaluation_metrics=json.dumps(summary),logs=folder.relative_to(ROOT).as_posix(),checkpoints='Original models/claims unchanged',
            code_revision_basis='238dc86 plus sealed source snapshot',implementation_sha256=hashes[paths[0]],
            conclusions='TRAIN source audited;invalid files quarantined;unknown and conflicting support retained;similarity candidates not benchmark splits;no training/scoring')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=json.loads(state_path.read_text());state['completed_run_ids'].append(rid)
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=rid
        print(json.dumps(dict(run_id=rid,summary=summary),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=type(error).__name__,detail=str(error),train_members_copied=len(copied),frames_recorded=len(frames),
            completed_run_counted=False,originals_preserved=True))
        state=json.loads(state_path.read_text());raise
    finally:
        state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':main()
