"""Record the completed input-quality trial and bounded traffic-source research."""
import csv
import json
import shutil
import sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.live import parse_feed

E=ROOT/'experiments/evidence/HEARTBEAT-20261025T164533Z'
RUN='LIVE-QUALITY-20261025T165658546985Z'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    if (E/'checks.json').exists():raise RuntimeError('This dated heartbeat is already recorded')
    now=datetime.now(timezone.utc).isoformat();state=read('data/automation_state.json')
    run=read('experiments/results/'+RUN+'/run.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==35
    assert state['scheduled_wakeups_completed']==22 and run['validation_gate_passed']
    assert all(digest(ROOT/p)==h for p,h in run['source_hashes'].items())
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    production=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    assert all(digest(ROOT/p)==h for p,h in production.items())
    assert digest(ROOT/'src/smart_parking/flow.py')=='40f882044cfeadf05817584c9ead86964f2c6d2358a09da31256d27dd9d872b9'
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()]
    assets=[r for r in receipts if r['source_id']=='SRC-DS-013']
    assert len(assets)==4 and sum(r['bytes'] for r in assets)==1857871
    assert all(digest(ROOT/r['local_path'])==r['sha256'] for r in assets)
    metadata=read('data/raw/traffic_candidate_metadata/figshare_29277770_v1.json')
    assert metadata['version']==1 and metadata['license']['name']=='CC BY 4.0' and len(metadata['files'])==127
    shutil.copyfile(ROOT/'data/raw/traffic_candidate_metadata/figshare_29277770_v1.json',E/'figshare_public_metadata.json')
    with (ROOT/'data/raw/drive_thru_figshare/vehicle0_cam3.csv').open(newline='') as stream:
        annotations=[[float(v) for v in row] for row in csv.reader(stream)]
    assert len(annotations)==3852 and all(len(row)==6 for row in annotations)
    ranges=[dict(column=i+1,min=min(row[i] for row in annotations),max=max(row[i] for row in annotations)) for i in range(6)]
    candidate=dict(source_id='SRC-DS-013',inspected_at=now,metadata_sha256=assets[0]['sha256'],
        public_release_doi=metadata['doi'],public_release_license=metadata['license'],
        publisher_files=127,publisher_jpegs=124,publisher_csvs=3,publisher_bytes=98382739,
        acquired_files=4,acquired_bytes=1857871,acquired=assets,
        development_images=[dict(frame=200,size=[2688,1520]),dict(frame=239,size=[2688,1520])],
        trajectory_rows_parsed=3852,raw_column_ranges=ranges,
        annotation_schema_verified=False,annotation_coordinate_transform_verified=False,
        independent_human_ground_truth_verified=False,physical_fps_verified=False,
        other_cameras_or_trajectories_acquired=False,model_training_or_accuracy_evaluation=False,
        admission_passed=False,operational_asset_use_allowed=False,
        reasons=['CSV is headerless; columns/coordinate basis and provenance are not documented in the inspected public release',
                 'Two decoded images are2688x1520; raw trajectory coordinates reach3603x2876. The displayed0.7scale overlay is only an unverified visual hypothesis, not a label conversion',
                 'Selected trajectory may be an algorithm output, not independently annotated truth; no accuracy metric may use it until established',
                 'Related article DOI10.3390/electronics14132671 describes restricted full study data; public blurred partial CC BY release scope must be reconciled before further operational use'],
        disposition='Preserve four original public inspection assets and receipts locally; no further imagery, scoring, training, redistribution or holdout claim')
    write('data/manifests/drive_thru_inspection_v1.json',candidate)
    write(E.relative_to(ROOT)/'traffic_source_admission.json',candidate)
    write(E.relative_to(ROOT)/'research_access_notes.json',dict(recorded_at=now,
        timestamp_precision='Event ordering from tool results; individual failed-request timestamps were not captured',
        events=['Initial normal-process DNS resolution failed for three public metadata URLs; approved public-network retry used',
                'Figshare public API metadata and three selected assets acquired with hashes; publisher MD5 verified for asset files',
                'Mendeley public-api/datasets/{id}/versions/1 paths for both candidate IDs returned HTTP404; no dataset bytes acquired',
                'MDPI HTML returned429; public publisher PDF available to web tool; data-availability/method/setup passages reviewed',
                'BrnoCompSpeed publisher README requires contacting author; no email sent, no full archive acquired',
                'UA-DETRAC creator page reviewed; primary asset-use licence not established. Third-party licence assertions not adopted']))
    source_path=ROOT/'data/source_manifest.csv'
    with source_path.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;sources=list(reader)
    assert len(sources)==45
    additions=[
        dict(source_id='SRC-DS-013',resource_type='dataset candidate; bounded inspection',resource=metadata['title'],
             original_creator='Carlos Gellida; Carlos Gellida-Coutino',source_url=metadata['url_public_html'],
             download_url='https://api.figshare.com/v2/articles/29277770',version='Figshare public v1; DOI10.6084/m9.figshare.29277770.v1',
             license='Public partial release declares CC BY4.0; related full-study restriction needs scope reconciliation',
             permission='Four public inspection assets acquired under displayed licence; further operational use deferred',
             original_size='Publisher127files/98382739bytes; locally4files/1857871bytes',
             local_location='data/raw/traffic_candidate_metadata/; data/raw/drive_thru_figshare/',sha256='Per-asset SHA256/MD5 in receipts and data/manifests/drive_thru_inspection_v1.json',
             purpose='Investigate fresh fixed-camera drive-through crossing evidence',used_by='Schema/pixel/rights inspection only; no model training/scoring',
             modifications='Originals retained; diagnostic overlay only, candidate scale unverified',
             attribution=metadata['citation'],status='inspection acquired; admission failed',
             open_issues='Headerless CSV, coordinate basis, label independence, fps and partial/full-release rights unresolved; do not use for benchmark accuracy'),
        dict(source_id='SRC-DS-014',resource_type='dataset candidate',resource='Multi-instance vehicle dataset with annotations with captured in outdoor diverse settings',
             original_creator='Wasiq Khan; Jessica Kelly',source_url='https://data.mendeley.com/datasets/5d8k5bkb93/1',
             version='Mendeley V1; DOI10.17632/5d8k5bkb93.1',license='Publisher page CC BY4.0; per-video original credits not inspected',
             purpose='Potential manual vehicle trajectories from seven videos',status='candidate; no dataset assets acquired',
             open_issues='Guessed public metadata API path returned404; verify legitimate file inventory and per-video provenance before acquisition'),
        dict(source_id='SRC-DS-015',resource_type='dataset candidate',resource='Highway Vehicle Surveillance Dataset HVSD',original_creator='Hadi Sadoghi Yazdi',
             source_url='https://data.mendeley.com/datasets/zdgmdg7p25/1',version='Mendeley V1; DOI10.17632/zdgmdg7p25.1',
             license='Publisher page CC BY4.0',purpose='Potential highway footage; distinguish algorithm-produced results from truth',
             status='candidate; no dataset assets acquired',open_issues='Publisher describes processed detector results; no independent labels confirmed; metadata API path returned404'),
        dict(source_id='SRC-DS-016',resource_type='dataset candidate',resource='UA-DETRAC',original_creator='Longyin Wen; Dawei Du; Zhaowei Cai and collaborators',
             source_url='https://sites.google.com/view/daweidu/projects/ua-detrac',version='Creator project page reviewed25October2026',
             license='Primary asset licence not established; third-party CC declarations not adopted',purpose='Fixed-camera vehicle detection/tracking candidate',
             status='candidate; no assets acquired',open_issues='Verify publisher licence/release/file scope before any image or annotation use'),
        dict(source_id='SRC-DS-017',resource_type='dataset candidate',resource='BrnoCompSpeed',original_creator='Jakub Sochor and collaborators',
             source_url='https://github.com/JakubSochor/BrnoCompSpeed',version='Current publisher README reviewed25October2026',
             license='Data-use licence/access not established',purpose='Fixed-camera vehicle trajectory candidate',status='deferred; no assets acquired',
             open_issues='Publisher now says contact author; no outbound contact authorized or sent; about200GB full source not downloaded'),
        dict(source_id='SRC-PAP-011',resource_type='paper; task-specific passages reviewed',
             resource='Real-Time Multi-Camera Tracking for Vehicles in Congested, Low-Velocity Environments: A Case Study on Drive-Thru Scenarios',
             original_creator='Carlos Gellida-Coutino; Reyes Rios-Cabrera; Alan Maldonado-Ramirez; Anand Sanchez-Orta',
             source_url='https://doi.org/10.3390/electronics14132671',download_url='https://mdpi-res.com/d_attachment/electronics/electronics-14-02671/article_deploy/electronics-14-02671.pdf',
             version='Electronics2025,14,2671; published1July2025',license='Article CC BY4.0; does not grant underlying restricted study-data rights',
             purpose='Inspect label provenance, camera setup and source-data restrictions',status='reviewed specific passages; no local paper download',
             open_issues='Not a full independent methods reproduction; published study metrics are not our system results')]
    for row in additions:
        row.setdefault('access_date','2026-10-25');row.setdefault('access_time_precision','Date only for web review; exact acquisition UTC in receipts where present')
        row.setdefault('permission','Public primary documentation review only; no account, restricted agreement or asset use')
        row.setdefault('local_location','No dataset assets acquired');row.setdefault('used_by','Source feasibility research only')
        row.setdefault('modifications','No source content/code copied');row.setdefault('attribution','See named publisher, source URL and DOI')
        sources.append({key:row.get(key,'') for key in fields})
    assert len(sources)==len({r['source_id'] for r in sources})==51
    with source_path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(sources)
    live=read('data/processed/singapore_prospective/summary.json')
    receipt=next(r for r in reversed(receipts) if r['source_id']=='SRC-LIVE-001')
    rows=parse_feed(read(receipt['local_path']));assert digest(ROOT/receipt['local_path'])==receipt['sha256']
    assert live['scores_total']==22850 and live['scores_added']==1172
    write(E.relative_to(ROOT)/'live_checkpoint.json',dict(summary=live,receipt=receipt,accepted_rows=len(rows),
        duplicates=0,bounds_valid=all(0<=r['available']<=r['capacity'] for r in rows),
        interpretation='Later matched persistence targets only; no neural/camera accuracy'))
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for row in inventory['datasets']:
        if row['source_id']=='SRC-LIVE-001':row.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),
            raw_path=receipt['local_path'],provider_timestamp=receipt['provider_timestamp'],snapshot_count=28,
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],
            forecast_target_coverage=live['forecast_coverage'])
    inventory['datasets'].append(dict(source_id='SRC-DS-013',status='inspection_only_admission_failed',original_files=4,
        bytes=1857871,images_decoded=2,trajectory_rows_inspected=3852,used_for_model_training=False,
        used_for_model_evaluation=False,admission_manifest='data/manifests/drive_thru_inspection_v1.json'))
    write('data/dataset_inventory.json',inventory)
    state.update(last_updated_at=now,scheduled_wakeups_completed=23,live_quality_validation=RUN,
        last_live_baseline_score=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],
            scope='Persistence only; not neural/camera accuracy',coverage=live['forecast_coverage']))
    state['local_demo_bundle']['newer_source_changes_not_in_bundle']=['src/smart_parking/live.py']
    state['next_actions']=[
        'Fresh fixed-camera counting evidence remains missing. Read docs/TRAFFIC_SOURCE_ADMISSION.md; do not treat Figshare candidate CSV as ground truth or guess its coordinate transform. Source13 admission failed; no further operational use. Source14 potential manual trajectories needs official public file inventory and per-video provenance; source15 algorithm outputs not verified truth. UA-DETRAC licence unverified; Brno contact-only, no outbound messages.',
        'Live parser strengthened;35 recorded trials/176 software tests,28 real snapshots/67844 replayed lot records exactly unchanged. Duplicate semantic observations collapse, valid conflicts/noninteger counts/empty identities rejected. Invalid payload bytes preserved separately, never promoted to usable cache/history. No original model weights/base tracker/final data changed.',
        'Existing demo package remains the earlier dated184-file copy and lacks new live.py. Rebuild only at next meaningful demo milestone; visible/manual-dialog,fresh installation and physical-offline acceptance still unfinished. Do not alter unrelated networking.',
        'Report v003 stays an immutable16:35UTC snapshot with45sources/34trials/167tests; newer source catalog51 and ledger35/176. Report12pages reviewed,LaTeX counterpart compiles. Student review,rehearsal,official template/university documents pending. Do not regenerate snapshots for routine counter changes.',
        'Last official collection16:52UTC:22850 matched persistence outcomes,MAE4.186346,6593expired/1279pending,77.61%resolved matching. Next sensible30minute collection after17:22UTC; preserve1min minimum and do not poll per simulation. Separate100-run checkpoint100; no active jobs.'
    ];write('data/automation_state.json',state)
    title='## 25 October 2026 / live input quality and traffic-source admission'
    note='''One paired LIVE-QUALITY trial passes:28 real official snapshots/67,844 repeated
snapshot lot records reproduce the prior parser exactly. Synthetic duplicate
fixture previously yielded2 rows, now1; conflicting valid duplicate values fail.
Empty identities and float/boolean counts fail validation; equivalent Singapore
and UTC observation times identify the same history entry. All176 software tests
pass, including two raw-response retention/history scenarios. Rejected public
response bytes get separate immutable files/receipts, never replace usable cache
or append normalized history. Valid raw snapshots now use exclusive creation.
These are software checks, not detector or forecasting accuracy. Counter35;
no training/new weights/final evaluation. Earlier demo is a dated copy and lacks
this live.py update; do not call that copy the latest source.

Fresh traffic-source research has51 source records. Figshare partial drive-through
release declares CC BY4.0: public metadata,one3852-row headerless CSV and first2
camera3images acquired (4files/1,857,871bytes), publisher MD5 and local SHA checked.
Inspection exposes unresolved coordinate basis/column semantics/label independence;
raw coordinates exceed decoded2688x1520 dimensions. A0.7overlay was diagnostic
only, not an established conversion or score. Related article describes restricted
full study data; reconcile the public partial-release scope before further asset
use. Admission fails; originals/receipts retained, no model scoring/training,
other-camera acquisition,final claim or redistribution. Manual correspondence,
physical fps and exhaustive labels unverified. See docs/TRAFFIC_SOURCE_ADMISSION.md.
Four other dataset candidates remain unacquired: Mendeley multi-instance/HVSD
metadata routes404; HVSD processed outputs are not verified independent truth;
UA-DETRAC primary licence unresolved; Brno publisher requires contact (none sent).

Actual16:52UTC official snapshot28 matches1172 later persistence outcomes:
22,850total,MAE4.186346spaces,6593expired/1279pending,77.61%resolved target matching.
Fresh normalized rows/raw JSON/time/URL/SHA retained. No neural/camera live score.
Reportv003 and Excel/slides retain their dated evidence; do not mutate old results.
No active jobs; separate100-run milestone100. Next source-compliant collection
after17:22UTC,then fresh label acquisition/admission or remaining native/offline
acceptance. All original checkpoints,failed experiments and consumed final groups
preserved. Student mastery,official submission and overall completion unverified.'''
    for name in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md','reports/PROGRESS_ADDENDUM_20261025.md']:
        path=ROOT/name;text=path.read_text(encoding='utf-8');assert title not in text
        path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    path=ROOT/'docs/IMPLEMENTATION_STATUS.md';text=path.read_text(encoding='utf-8')
    text=text.replace('Twenty-seven authorized public snapshots acquired','Twenty-eight authorized public snapshots acquired')
    text=text.replace('Nineteen prospective persistence cohorts scored','Twenty prospective persistence cohorts scored')
    text=text.replace('21,678 matched later outcomes, MAE4.299','22,850 matched later outcomes, MAE4.186')
    text=text.replace('| Tests/offline | 167 tests pass; relocated local-demo image check passes |','| Tests/offline | 176 tests pass; prior relocated local-demo check retained |')
    path.write_text(text.rstrip()+'\n\n'+title+'\n\n'+note+'\n',encoding='utf-8')
    for name in ['docs/SOURCE_REGISTRY.md','docs/THIRD_PARTY_SOURCES.md','docs/LICENSING_RECORD.md','docs/LITERATURE_NOTES.md']:
        path=ROOT/name;path.write_text(path.read_text(encoding='utf-8').rstrip()+'\n\n'+title+'\n\nSource catalog now51 records, including SRC-DS-013..017 and SRC-PAP-011. See docs/TRAFFIC_SOURCE_ADMISSION.md and data/manifests/drive_thru_inspection_v1.json for exact primary URLs, partial-release restrictions, acquisition receipts and rejected uses. No model accuracy from these candidate assets.\n',encoding='utf-8')
    write(E.relative_to(ROOT)/'checks.json',dict(completed_trials=35,tests_passed=176,sources=51,run_id=RUN,
        real_snapshot_compatibility_count=28,repeated_lot_record_count=67844,traffic_source_admission_passed=False,
        original_weights_and_base_tracker_unchanged=True,no_consumed_final_reread=True,no_active_jobs=True,
        live_matched_outcomes=22850,dated_report_unchanged=True))
    print(json.dumps(dict(completed_trials=35,tests=176,sources=51,run_id=RUN),indent=2))


if __name__=='__main__':main()
