"""Correct a source-ID collision without rewriting immutable acquisition/run evidence."""
import csv,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD='SRC-DS-011';NEW='SRC-DS-012'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()

if __name__=='__main__':
    ledger=ROOT/'data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json';ledger.parent.mkdir(parents=True,exist_ok=True)
    if ledger.exists():raise FileExistsError('Source correction already recorded')
    with (ROOT/'data/source_manifest.csv').open(encoding='utf-8-sig',newline='') as s:sources=list(csv.DictReader(s))
    assert next(r for r in sources if r['source_id']==OLD)['resource']=='TRANCOS'
    assert not any(r['source_id']==NEW for r in sources)
    now=datetime.now(timezone.utc).isoformat();receipts=ROOT/'data/resource_receipts.jsonl';original_lines=receipts.read_text(encoding='utf-8').splitlines();corrections=[]
    already={json.loads(line)['corrects_receipt_sha256'] for line in original_lines if json.loads(line).get('record_type')=='source_id_correction' and json.loads(line).get('source_id')==NEW}
    for line in original_lines:
        r=json.loads(line)
        if r.get('source_id')==OLD and r.get('local_path','').startswith('data/raw/davis2017_') and hashlib.sha256(line.encode()).hexdigest() not in already:
            corrections.append(dict(**{k:v for k,v in r.items() if k!='source_id'},source_id=NEW,record_type='source_id_correction',original_source_id=OLD,correction_recorded_at=now,corrects_receipt_sha256=hashlib.sha256(line.encode()).hexdigest(),correction_reason='ID011 already denotes TRANCOS; DAVIS is ID012. Original acquisition time/bytes/checksum retained; no reacquisition.'))
    with receipts.open('a',encoding='utf-8',newline='\n') as s:
        for r in corrections:s.write(json.dumps(r)+'\n')
    # Preserve frozen v1 role/hash records; create explicitly corrected successors.
    parent=read('data/manifests/davis_car_sequences_v1.json');original_parent_sha=sha('data/manifests/davis_car_sequences_v1.json');parent['source_id']=NEW;parent['source_id_correction']='data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json';parent['supersedes_manifest_sha256']=original_parent_sha
    write('data/manifests/davis_car_sequences_v2.json',parent)
    final=read('data/manifests/davis_car_roundabout_final_v1.json');original_final_sha=sha('data/manifests/davis_car_roundabout_final_v1.json');final['source_id']=NEW;final['source_id_correction']='data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json';final['supersedes_reservation_sha256']=original_final_sha;final['parent_manifest_sha256']=sha('data/manifests/davis_car_sequences_v2.json')
    write('data/manifests/davis_car_roundabout_final_v2.json',final)
    state=read('data/automation_state.json');state['davis_sequences']['source_id']=NEW;state['davis_sequences']['final_manifest']='data/manifests/davis_car_roundabout_final_v2.json';write('data/automation_state.json',state)
    inv=read('data/dataset_inventory.json')
    for item in inv['datasets']:
        if item.get('source_manifest','').startswith('data/manifests/davis_'):
            item.update(source_id=NEW,source_manifest='data/manifests/davis_car_sequences_v2.json',reserved_final_manifest='data/manifests/davis_car_roundabout_final_v2.json',source_id_correction='data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json')
    write('data/dataset_inventory.json',inv)
    with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open(encoding='utf-8-sig',newline='') as s:r=csv.DictReader(s);fields=r.fieldnames;registry=list(r)
    for item in registry:
        if item['experiment_id'].startswith('DAVIS-'):
            item['source_ids']=item['source_ids'].replace(OLD,NEW)
            if 'source-ID collision corrected' not in item['conclusions']:item['conclusions']+='; source-ID collision corrected via DAVIS_SOURCE_ID_20261025.json; frozen evidence unchanged'
    with (ROOT/'experiments/EXPERIMENT_REGISTRY.csv').open('w',encoding='utf-8',newline='') as s:w=csv.DictWriter(s,fieldnames=fields);w.writeheader();w.writerows(registry)
    card=read('models/davis_foreground_development.json');original_ids=card.get('original_recorded_source_ids',card['source_ids']);card['source_ids']=[NEW if v==OLD else v for v in original_ids];card['original_recorded_source_ids']=original_ids;card['source_id_correction']='data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json';write('models/davis_foreground_development.json',card)
    # Current mutable sources use the correct ID; original sealed source snapshots stay intact.
    for name in ['inspect_davis_archive.py','acquire_davis_subset.py','audit_davis_subset.py','evaluate_davis_development.py','record_davis_heartbeat.py']:
        p=ROOT/'scripts'/name;text=p.read_text(encoding='utf-8');text=text.replace(OLD,NEW).replace('davis_car_sequences_v1.json','davis_car_sequences_v2.json').replace('davis_car_roundabout_final_v1.json','davis_car_roundabout_final_v2.json');p.write_text(text,encoding='utf-8')
    title='## 25 October 2026 / licensed labelled sequences and frame-index tracking'
    for name in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/PROJECT_CONSTRAINTS.md','docs/RESEARCH_LOG.md','docs/THIRD_PARTY_SOURCES.md','docs/AI_ASSISTANCE_LOG.md','docs/IMPLEMENTATION_STATUS.md','reports/PROGRESS_ADDENDUM_20261025.md']:
        p=ROOT/name;text=p.read_text(encoding='utf-8')
        if title in text:
            before,after=text.split(title,1);after=after.replace(OLD,NEW).replace('davis_car_sequences_v1.json','davis_car_sequences_v2.json').replace('davis_car_roundabout_final_v1.json','davis_car_roundabout_final_v2.json');p.write_text(before+title+after,encoding='utf-8')
    p=ROOT/'docs/LABELLED_SEQUENCE_GUIDE.md';text=p.read_text(encoding='utf-8').replace(OLD,NEW).replace('davis_car_sequences_v1.json','davis_car_sequences_v2.json').replace('davis_car_roundabout_final_v1.json','davis_car_roundabout_final_v2.json');p.write_text(text+'\nSource-ID correction: DAVIS is SRC-DS-012. Early acquisition/run records mistakenly\nused SRC-DS-011, which already belongs to TRANCOS. Those originals remain intact.\nThe explicit crosswalk and append-only receipt corrections are in\n`data/provenance_corrections/DAVIS_SOURCE_ID_20261025.json`; v2 manifests correct\nmetadata only, with identical original image/mask bytes and unchanged roles/results.\n',encoding='utf-8')
    write(ledger.relative_to(ROOT),dict(recorded_at=now,reason='Assistant assigned an already occupied permanent source ID before checking registry; detected at final integrity audit',incorrect_id=OLD,correct_id=NEW,existing_id011_resource_unchanged='TRANCOS; candidate only; no TRANCOS assets acquired',scope='Only DAVIS paths/artifacts in this wake; never reinterpret earlier TRANCOS references',original_receipts_preserved=True,append_only_receipt_corrections=len(already)+len(corrections),original_acquisition_manifest_sha256=sha('data/raw/davis2017_metadata/subset_acquisition.json'),original_v1_manifest_sha256=original_parent_sha,original_v1_reservation_sha256=original_final_sha,corrected_v2_manifest_sha256=sha('data/manifests/davis_car_sequences_v2.json'),corrected_v2_reservation_sha256=sha('data/manifests/davis_car_roundabout_final_v2.json'),original_image_mask_bytes_changed=False,metrics_or_roles_changed=False,frozen_protocols_and_source_snapshots_unchanged=True,correction_execution_repair='Initial correction stopped on Windows default cp1252 decoding of the UTF8 guide. Explicit UTF8 and idempotent receipt/registry updates allowed safe continuation; no duplicated correction receipts.'))
    print('Preserved original receipts/results; appended',len(corrections),'source-ID corrections; canonical DAVIS ID is',NEW)
