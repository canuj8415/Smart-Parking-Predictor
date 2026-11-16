"""One-use whole-sequence claims, without invented capture dates or fps.

Only metadata is read here. A durable claim precedes the loader callback; any
callback failure consumes all reserved source/sequence groups. Source identity
is the canonical collection URL, independent of a local source-catalog ID.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from .provenance import ROOT, digest


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Sequence asset outside project root')
    return path.relative_to(root).as_posix().casefold()


def reservation_sequences(manifest, parent_manifest, *, root=ROOT):
    """Check full membership against the sealed parent, without opening assets."""
    root = Path(root).resolve()
    reserved, parent = _read(manifest), _read(parent_manifest)
    if digest(parent_manifest) != reserved['parent_manifest_sha256']:
        raise ValueError('Parent manifest checksum changed')
    if reserved['source_id'] != parent['source_id']:
        raise ValueError('Reservation and parent source identity differ')
    sequences = reserved['reserved_sequences']
    if not sequences or any(not isinstance(s,str) or not s.strip() for s in sequences):
        raise ValueError('Missing reserved sequence identities')
    if len({s.casefold() for s in sequences}) != len(sequences):
        raise ValueError('Duplicate reserved sequence identity')
    rows = reserved['frames']
    expected = [r for r in parent['frames'] if r['sequence'] in sequences]
    if not rows or rows != expected or {r['sequence'] for r in rows} != set(sequences):
        raise ValueError('Reservation must contain complete parent sequence membership')
    paths, hashes = [], []
    for sequence in sequences:
        group = [r for r in rows if r['sequence']==sequence]
        if [r['frame_index'] for r in group] != list(range(len(group))):
            raise ValueError('Reserved sequence frame indices must be complete and consecutive')
    for row in rows:
        if row['role'] != 'reserved_final':
            raise ValueError('Reserved sequence contains non-final frame roles')
        for key in ['image','annotation']:
            paths.append(_inside(root, row[key]))
            value=row[key+'_sha256']
            if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError('Invalid sealed sequence asset checksum')
            hashes.append(value)
    if len(paths) != len(set(paths)):
        raise ValueError('Duplicate reserved asset path')
    return rows, paths, hashes, sequences


def assert_sequence_closed(manifest, parent_manifest, collection_identity, *, receipt_dir=None, root=ROOT):
    if not isinstance(collection_identity,str) or not collection_identity.strip():
        raise ValueError('Canonical collection identity required')
    rows, paths, hashes, sequences = reservation_sequences(manifest,parent_manifest,root=root)
    groups={(collection_identity.casefold(),s.casefold()) for s in sequences}
    folder=Path(receipt_dir or ROOT/'data/sequence_holdout_claims')
    for marker in folder.glob('*.claim.json'):
        claim=_read(marker)
        if groups & {tuple(g) for g in claim['source_sequences']}:
            raise ValueError('Whole source sequence overlaps an already started evaluation')
        if set(paths)&set(claim['asset_paths']) or set(hashes)&set(claim['asset_sha256']):
            raise ValueError('Sequence assets overlap an already started evaluation')
    return rows


def evaluate_sequence_once(manifest, parent_manifest, selection, protocol, run_id, evaluate, *,
                           collection_identity, expected_manifest_sha256,
                           expected_selection_sha256, receipt_dir=None, root=ROOT):
    """Load final pixels only inside evaluate(rows), after a flushed claim exists."""
    root=Path(root).resolve()
    if digest(manifest)!=expected_manifest_sha256:
        raise ValueError('Sequence reservation checksum changed')
    if digest(selection)!=expected_selection_sha256:
        raise ValueError('Frozen selection checksum changed')
    selected=_read(selection)
    if selected.get('counting_final_qualified') is not True or selected.get('metrics',{}).get('reference_events',0)<1:
        raise ValueError('A passed positive-reference counting validation gate is required')
    if digest(protocol)!=selected['protocol_sha256']:
        raise ValueError('Frozen protocol checksum changed')
    if selected['collection_identity']!=collection_identity:
        raise ValueError('Frozen collection identity changed')
    for field in ['source_hashes','checkpoint_hashes']:
        if not selected.get(field):
            raise ValueError('Frozen implementation and checkpoint checksums required')
        for relative, checksum in selected[field].items():
            _inside(root,relative)
            if digest(root/relative)!=checksum:
                raise ValueError('Frozen implementation or checkpoint checksum changed')
    folder=Path(receipt_dir or ROOT/'data/sequence_holdout_claims')
    folder.mkdir(parents=True,exist_ok=True)
    lock=folder/'claim.lock'
    descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    os.close(descriptor)
    try:
        rows=assert_sequence_closed(manifest,parent_manifest,collection_identity,receipt_dir=folder,root=root)
        _,paths,hashes,sequences=reservation_sequences(manifest,parent_manifest,root=root)
        groups=sorted((collection_identity.casefold(),s.casefold()) for s in sequences)
        identity=hashlib.sha256(json.dumps(groups).encode()).hexdigest()
        marker=folder/(identity+'.claim.json')
        claim=dict(run_id=run_id,started_at=datetime.now(timezone.utc).isoformat(),
            status='started; entire sequences consumed even on callback failure',
            source_sequences=groups,asset_paths=paths,asset_sha256=hashes,
            manifest_sha256=expected_manifest_sha256,selection_sha256=expected_selection_sha256,
            protocol_sha256=selected['protocol_sha256'],source_hashes=selected['source_hashes'],
            checkpoint_hashes=selected['checkpoint_hashes'])
        with marker.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(claim,stream,indent=2)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        lock.unlink(missing_ok=True)
    try:
        result=evaluate(rows)
    except BaseException as error:
        outcome=dict(status='failed; original whole-sequence claim remains consumed',
                     error=type(error).__name__,detail=str(error))
        marker.with_suffix('.outcome.json').write_text(json.dumps(outcome,indent=2),encoding='utf-8')
        raise
    marker.with_suffix('.outcome.json').write_text(json.dumps(dict(status='completed; whole sequences consumed'),indent=2),encoding='utf-8')
    return result
