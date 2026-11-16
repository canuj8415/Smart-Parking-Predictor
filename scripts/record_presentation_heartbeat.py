"""Persist the presentation milestone; artifact work never inflates model runs."""
import csv,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def write(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def rows(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f);return r.fieldnames,list(r)
def table(path,fields,values):
    with (ROOT/path).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL if path=='docs/REQUIREMENTS.csv' else csv.QUOTE_MINIMAL);w.writeheader();w.writerows(values)
def append(path,text):
    title='25October2026 / presentation and practice guide'
    p=ROOT/path;old=p.read_text(encoding='utf-8')
    if title not in old:p.write_text(old.rstrip()+'\n\n## '+title+'\n\n'+text.strip()+'\n',encoding='utf-8')

if __name__=='__main__':
    now=datetime.now(timezone.utc).isoformat()
    evidence=read('experiments/evidence/HEARTBEAT-20261025T000925Z/presentation_manifest.json')
    live_evidence=read('experiments/evidence/HEARTBEAT-20261025T000925Z/live_checkpoint.json');live=live_evidence['summary'];receipt=live_evidence['receipt']
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=now
    for item in inventory['datasets']:
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=live_evidence['accepted_car_parks'],observations=live_evidence['accepted_lot_observations'],raw_lot_records=live_evidence['raw_lot_records'],
            provider_timestamp=receipt['provider_timestamp'],raw_path=receipt['local_path'],snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    state=read('data/automation_state.json');assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==16
    state.update(scheduled_wakeups_completed=10,last_updated_at=now,active_training_jobs=[],active_validation_jobs=[])
    state['presentation']=dict(path=evidence['final_path'],sha256=evidence['sha256'],slides=14,guide='docs/PRESENTATION_PRACTICE_GUIDE.md',
        artifact_checks_passed=True,all_rendered_slides_reviewed=True,native_powerpoint_opened=False,student_rehearsal_verified=False,official_template_compliance_verified=False)
    state['last_live_baseline_score']=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only;7scored issue cohorts; target matching is not accuracy.',coverage=live['forecast_coverage'])
    state['next_actions']=[
        'Next wake collect one official snapshot for1267forecasts frozen00:10UTC and70remaining23:40entries; score actual later valid targets only. Counter16; next separate100-run milestone100. Presentation authoring/checks are not model experiments.',
        'Resume core reliability work: broader legitimate development data for region segmentation/occupancy and a prespecified forecast robustness hypothesis using actual target times. Existing region0.79629 and forecast20.9015 candidates still fail gates. Keep shared final6closed and avoid repeated tuning on small reused validation sets.',
        'MetaPKLot remains inspection-only; no annotation JSON parsed. Verify exact-file rights/ROI/image identity before approved-development-only filtering, excluding consumed/reserved final frames.',
        'Gate counter needs independently labelled positive/negative crossing footage and a desktop editor. Existing real0crossing run establishes export consistency only; preserve all failures and sources.',
        '14slide walkthrough v002 and plain-language practice guide are ready as dated development materials. Native PowerPoint rehearsal, student unaided practice, official template reconciliation, report compilation, native export save and physical/fresh offline validation remain pending.'
    ]
    write('data/automation_state.json',state)
    overview='''Created reports/presentations/smart_parking_walkthrough_v002.pptx:
14editable slides with speaker notes,6native tables,1native chart and an embedded
workbook. Real PKLot/output/video images carry credits; the3Dnumeric volume is
explicitly synthetic. Source URLs, model/run caveats and AI assistance appear
in notes/on slides. Companion docs/PRESENTATION_PRACTICE_GUIDE.md explains each
section in everyday language and proposes an8-10minute practice route. No timed
human rehearsal, student mastery or official-template compliance is claimed.

Final PPTX SHA256bc82cf12417612e6fd8e7b072535a34a37a1c48c68b1f349f71115917fdfae68,
2,119,461bytes. Documented finalizer passed package/layout/font/import/native
chart-workbook checks. All14slides rendered and individually reviewed in the
first final version; v002changes only the sixth title and its revised render
was inspected, with the other13rendered images byte-identical. Native Microsoft
PowerPoint opening remains unverified. Original v001retained. Chart values use
six decimals for workbook portability; full original model metrics unchanged.
Failed font-environment/table-policy/precision/temp-replacement attempts and
their resolutions are recorded, with no failed model result concealed.

The bundled @oai/artifact-tool2.8.105and Presentations skill authored this local
artifact. Runtime paths/version and source/image hashes are in the presentation
manifest. No Python dependency, model weights, training code or raw source data
changed. Prior81software checks remain the latest runtime suite; no unnecessary
rerun. Three production hashes verified unchanged. Artifact work does not add
model trials: counter stays16, next100-run milestone100; no jobs active.

Thirteenth official live snapshot00:10:03UTC added1080later matched outcomes and
1267frozen forecasts.12310issued/7874scored across7scored issue cohorts,
persistenceMAE3.2025654spaces.3099expired missing targets,70in-window and1267
before-window as of collection. Matching7874/10973=71.76%of resolved entries,
not accuracy. RawJSON/normalized history/receipt/checksum preserved. No neural
Singapore, camera or flow accuracy claim. A frozen00:10summary accompanies the
deck, so later live updates cannot silently alter its historical snapshot.

Final report compilation, official university documents, stronger region and
forecast validation, labelled parking video, native-save/offline acceptance and
student practice remain unfinished. Resume core development next wake; exact
actions in data/automation_state.json.'''
    for p in ['docs/AUTONOMOUS_PROGRESS.md','docs/PROJECT_PROGRESS.md','reports/PROGRESS_ADDENDUM_20261025.md']:append(p,overview)
    append('docs/TEST_RESULTS.md','Presentation v002passed documented package/layout/font/import and native chart/workbook checks;6tables/1chart/14notes verified and displayed metrics checked against saved JSON. All14rendered slides reviewed, revised6separately;13others byte-identical. Native PowerPoint rehearsal not tested. Python runtime/model code unchanged, so prior81software checks were not repeated. Evidence: experiments/evidence/HEARTBEAT-20261025T000925Z/.')
    append('docs/AI_ASSISTANCE_LOG.md','AI assistant used the Presentations skill and bundled @oai/artifact-tool2.8.105 to author/validate a14slide local walkthrough, notes and plain-language practice guide. Actual source/model records and credited existing scientific images support it. Full source/tool/runtime/image hashes and failed authoring attempts remain in presentation_manifest.json/authoring_attempts.json. No student authorship/mastery or native PowerPoint rehearsal is implied. Parking product remains Python/Jupyter; authoring scripts only produce teaching artifacts.')
    append('docs/THIRD_PARTY_SOURCES.md','The presentation reuses existing SRC-DS-001PKLot photos/overlays under CC BY4.0, SRC-VID-001Street traffic by Editor under CC BY3.0, and the prior convolution lab figure with its explicitly synthetic numeric volume. Visible credits and speaker-note URLs remain attached. Actual asset hashes and bundled OpenAI presentation-tool provenance live in HEARTBEAT-20261025T000925Z/presentation_manifest.json. No new external image or dataset downloaded for the deck.')
    fields,sources=rows('data/source_manifest.csv')
    for s in sources:
        if s['source_id'] in {'SRC-DS-001','SRC-DS-003','SRC-LIVE-001','SRC-VID-001'} and 'presentation v002' not in s['used_by']:s['used_by']+='; attributed development presentation v002 and practice guide'
    table('data/source_manifest.csv',fields,sources)
    fields,requirements=rows('docs/REQUIREMENTS.csv')
    for q in requirements:
        if q['requirement_id']=='DEMO-01':q.update(status='In progress',actual_evidence='reports/presentations/smart_parking_walkthrough_v002.pptx; docs/PRESENTATION_PRACTICE_GUIDE.md; launch_parking.cmd',
            test_result='14slide editable deck/notes checked; package/render/native-table/chart validations pass; proposed8-10minute practice route',open_problems='No timed human rehearsal, presentation recording, native PowerPoint check or verified student mastery',next_action='Practise from verified features; record unaided explanations and demo after offline/native acceptance')
        if q['requirement_id']=='LEARN-01' and 'PRESENTATION_PRACTICE_GUIDE' not in q['actual_evidence']:q['actual_evidence']+='; docs/PRESENTATION_PRACTICE_GUIDE.md; 14slide walkthrough v002'
    table('docs/REQUIREMENTS.csv',fields,requirements)
    p=ROOT/'docs/IMPLEMENTATION_STATUS.md';s=p.read_text(encoding='utf-8').replace('Twelve authorized public snapshots acquired','Thirteen authorized public snapshots acquired').replace('Six prospective persistence cohorts scored','Seven prospective persistence cohorts scored').replace('6,794 matched later outcomes, MAE2.639','7,874 matched later outcomes, MAE3.203')
    s=s.replace('official report/template, presentation and learning/viva evidence remain','14slide presentation saved; official template, native rehearsal and learning/viva evidence remain')
    p.write_text(s,encoding='utf-8');append('docs/IMPLEMENTATION_STATUS.md','Presentation walkthrough v002and practice guide ready as dated development materials; native PowerPoint/human rehearsal and official template remain pending. Runtime code unchanged, prior81software checks retained; counter stays16. Latest live7874matched outcomes/MAE3.20257,71.76%resolved matching at00:10UTC. Core model acceptance limitations remain.')
    print(json.dumps(dict(wakeups=10,recorded_trials=16,presentation=evidence['final_path'],live_scores=live['scores_total']),indent=2))
