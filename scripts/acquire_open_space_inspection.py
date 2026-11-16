"""Acquire a pinned publisher archive, checking bytes without decoding images/labels."""
import csv
import hashlib
import json
import shutil
import sys
import tarfile
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from smart_parking.provenance import digest, receipt

SID = 'SRC-DS-018'
META = ROOT / 'data/manifests/open_space_publisher_metadata_20261026.json'
BUDGET = 160 * 1024**2


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def git_hash(body):
    return hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()


def main():
    state_path = ROOT / 'data/automation_state.json'
    state = json.loads(state_path.read_text())
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    start = datetime.now(timezone.utc)
    rid = 'OPEN-SPACE-ASSETS-' + start.strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT / 'experiments/results' / rid
    folder.mkdir(parents=True, exist_ok=False)
    metadata = json.loads(META.read_text())
    assert metadata['source_id'] == SID and not metadata['tree']['truncated']
    commit = metadata['commit']
    assert len(commit) == 40 and all(c in '0123456789abcdef' for c in commit)
    tree = metadata['tree']['tree']
    blobs = {x['path']: x for x in tree if x['type'] == 'blob'}
    assert len(blobs) == sum(x['type'] == 'blob' for x in tree)
    for name, row in blobs.items():
        path = PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts and '\\' not in name and ':' not in name
        assert row['mode'] == '100644' and row['size'] <= 4 * 1024**2
    assert sum(x['size'] for x in blobs.values()) <= BUDGET
    files = metadata['files']
    assert all(row['connector_utf8_matches_git_blob'] for row in files.values())
    assert 'All images and annotations were created by the authors.' in files['README.md']['text']
    assert 'Creative Commons Attribution 4.0' in files['LICENSE']['text']
    assert "names: ['space-occupied', 'space-vacant']" in files['data.yaml']['text']
    images = [x for x in blobs if x.lower().endswith('.jpg')]
    labels = {x for x in blobs if '/labels/' in x and x.endswith('.txt')}
    assert len(images) == len(labels) == 731
    assert {p.replace('/images/', '/labels/').rsplit('.', 1)[0] + '.txt' for p in images} == labels
    groups = defaultdict(list)
    for path in images:
        groups[blobs[path]['sha']].append(path)
    cross = [g for g in groups.values() if len({p.split('/')[0] for p in g}) > 1]
    assert not cross
    raw = ROOT / 'data/raw/open_space_official' / commit
    raw.mkdir(parents=True, exist_ok=False)
    archive = raw / 'publisher.tar.gz'
    partial = raw / 'publisher.tar.gz.partial'
    url = 'https://codeload.github.com/bermalA/open-space-parking-dataset/tar.gz/' + commit
    paths = ['scripts/acquire_open_space_inspection.py']
    source_hashes = {p: digest(ROOT / p) for p in paths}
    protected = json.loads((ROOT / 'experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json').read_text())
    for group in ['holdout_claims', 'forecast_holdout_claims', 'sequence_holdout_claims']:
        protected.update({p.relative_to(ROOT).as_posix(): digest(p) for p in (ROOT / 'data' / group).rglob('*.json')})
    protocol = dict(run_id=rid, started_at=start.isoformat(), seed=125, source_ids=[SID], commit=commit,
        hypothesis='A publisher-declared original CC-BY4.0 parking dataset can be pinned and byte-verified against its Git tree,with no image decode,target interpretation,training or scoring.',
        source_hashes=source_hashes, metadata_path=META.relative_to(ROOT).as_posix(), metadata_sha256=digest(META),
        protected_hashes=protected, byte_budget=BUDGET, maximum_download_seconds=300,
        gates=['Publisher explicitly declares original photos/annotations and CC-BY4.0', 'Pinned complete tree with safe regular-file paths',
            '731image/annotation pairs', 'No exact image Git-blob overlap across publisher splits', 'Every archive file matches publisher Git blob identity',
            'Zero image decoding,target interpretation,model use or final replay'],
        limitations=['Author identity is repository handle;paper citation incomplete', 'Unknown camera/capture dates and near duplicates;publisher random split not admitted as independent test',
            'Git blob SHA1 validates pinned file identity;archive SHA256 is local,not a publisher archive checksum',
            'Image dimensions/annotation geometry/exhaustiveness/content provenance not independently verified;no benchmark admission'])
    dump(folder / 'protocol.json', protocol)
    dump(folder / 'implementation_sources.json', {p: dict(sha256=h, source=(ROOT / p).read_text()) for p, h in source_hashes.items()})
    state['active_validation_jobs'] = [dict(run_id=rid, phase='bounded original archive acquisition')]
    dump(state_path, state)
    clock = time.monotonic()
    try:
        assert shutil.disk_usage(raw).free > BUDGET + 1024**3
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'SmartParkingAcademic/0.4'}), timeout=45) as response, partial.open('xb') as stream:
            expected = response.headers.get('Content-Length')
            if expected is not None and int(expected) > BUDGET:
                raise ValueError('Declared source archive exceeds byte budget')
            transferred = 0
            while chunk := response.read(1024**2):
                if (folder / 'CANCEL').exists() or time.monotonic() - clock > 300:
                    raise InterruptedError('Cancellable bounded acquisition stopped')
                transferred += len(chunk)
                if transferred > BUDGET:
                    raise ValueError('Source archive exceeds byte budget')
                stream.write(chunk)
                dump(folder / 'progress.json', dict(phase='download', bytes=transferred, elapsed_seconds=time.monotonic() - clock))
            if expected is not None and transferred != int(expected):
                raise ValueError('Incomplete source archive')
            final_url = response.url
        partial.replace(archive)
        acquisition = receipt(SID, archive, url, 'Pinned original publisher archive;byte-level qualification only,not model use',
            retrieval_url=final_url, licence='CC BY4.0,publisher README/LICENSE declarations', commit=commit,
            image_content_decoded=False, publisher_archive_checksum=None, checksum_basis='Local SHA256 plus every publisher Git blob SHA1')
        prefix = 'open-space-parking-dataset-' + commit + '/'
        seen = set()
        members = []
        with tarfile.open(archive, 'r:gz') as source:
            for info in source:
                if (folder / 'CANCEL').exists() or time.monotonic() - clock > 480:
                    raise InterruptedError('Cancellable bounded verification stopped')
                assert info.name.startswith(prefix) or info.name + '/' == prefix
                relative = info.name[len(prefix):]
                if info.isdir():
                    assert not relative or '..' not in PurePosixPath(relative).parts
                    continue
                assert info.isfile() and relative in blobs and relative not in seen
                expected_blob = blobs[relative]
                assert info.size == expected_blob['size']
                with source.extractfile(info) as stream:
                    body = stream.read(info.size + 1)
                assert len(body) == info.size and git_hash(body) == expected_blob['sha']
                seen.add(relative)
                members.append(dict(path=relative, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), git_blob_sha1=expected_blob['sha']))
                if relative in files:
                    assert body == files[relative]['text'].encode('utf-8')
                    with (raw / relative).open('xb') as target:
                        target.write(body)
                    receipt(SID, raw / relative, 'https://raw.githubusercontent.com/bermalA/open-space-parking-dataset/' + commit + '/' + relative,
                        'Exact pinned publisher rights/class metadata recovered from verified archive', acquisition_method='Extracted original member;not separately fetched',
                        commit=commit, publisher_git_blob_sha1=expected_blob['sha'])
        assert seen == set(blobs)
        assert all(digest(ROOT / p) == h for p, h in {**source_hashes, **protected}.items())
        summary = dict(files_verified=len(seen), images=len(images), labels=len(labels),
            publisher_image_split_counts=dict(Counter(p.split('/')[0] for p in images)), uncompressed_file_bytes=sum(x['bytes'] for x in members),
            archive_bytes=archive.stat().st_size, exact_duplicate_image_groups=sum(len(g) > 1 for g in groups.values()),
            exact_cross_split_duplicate_groups=len(cross), encoded_image_members_decompressed_for_hashing=len(images),
            image_pixels_decoded=0, semantic_label_rows_read=0, models_trained_or_scored=False, independent_benchmark_admitted=False,
            image_usage_permission_basis='Publisher explicit original-content and dataset CC-BY4.0 declarations;attribute handle and preserve licence',
            image_semantic_analysis_permitted_after_safe_admission=True, camera_date_or_near_duplicate_audit_complete=False,
            archive=archive.relative_to(ROOT).as_posix(), archive_sha256=digest(archive), commit=commit)
        report = dict(protocol, finished_at=datetime.now(timezone.utc).isoformat(), duration_seconds=time.monotonic() - clock,
            asset_integrity_gate_passed=True, summary=summary, acquisition_receipt=acquisition, members=members)
        dump(folder / 'run.json', report)
        dump(ROOT / 'models/open_space_asset_qualification.json', report)
        dump(ROOT / 'data/manifests/open_space_usage_qualification_v1.json', dict(source_id=SID, run_id=rid, commit=commit,
            archive=summary['archive'], archive_sha256=summary['archive_sha256'], usage_status='Inspection only until dimensions/labels/grouping audit',
            rights_basis=summary['image_usage_permission_basis'], image_analysis_authorized=True, model_training_admitted=False,
            independent_benchmark_admitted=False, source_camera_or_capture_dates='Unknown',
            image_pixels_decoded=0, labels_semantically_interpreted=0, source_splits='Publisher labels only;not trusted as independent groups'))
        registry = ROOT / 'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig', newline='') as stream:
            fields = csv.DictReader(stream).fieldnames
        row = dict(experiment_id=rid, run_type='New publisher asset/rights/integrity qualification;no model accuracy',
            started_at=protocol['started_at'], finished_at=report['finished_at'], source_ids=SID, split_ids='Publisher split names only;not benchmark-admitted',
            configuration=(folder / 'protocol.json').relative_to(ROOT).as_posix(), architecture='Byte-level Git-blob/archive validation;no model',
            random_seed=125, hardware='CPU;archive bytes only', execution_environment=sys.version.split()[0], training_duration=report['duration_seconds'],
            evaluation_metrics=json.dumps(summary), logs=folder.relative_to(ROOT).as_posix(), checkpoints='Original models unchanged',
            code_revision_basis='b1dba25 plus sealed source snapshot', implementation_sha256=source_hashes[paths[0]],
            conclusions='731publisher-original image/label pairs verified;CC-BY4.0declared;group/geometry audit pending,no accuracy')
        with registry.open('a', encoding='utf-8', newline='') as stream:
            csv.DictWriter(stream, fieldnames=fields).writerow({k: row.get(k, '') for k in fields})
        state = json.loads(state_path.read_text())
        state['completed_run_ids'].append(rid)
        state['completed_recorded_runs_since_schedule'] = len(set(state['completed_run_ids']))
        state['last_completed_run'] = rid
        print(json.dumps(dict(run_id=rid, summary=summary), indent=2))
    except BaseException as error:
        dump(folder / 'interrupted.json', dict(error=type(error).__name__, detail=str(error), completed_run_counted=False,
            partial_preserved=str(partial), original_archive_preserved=archive.exists()))
        state = json.loads(state_path.read_text())
        raise
    finally:
        state['active_validation_jobs'] = []
        dump(state_path, state)


if __name__ == '__main__':
    main()
