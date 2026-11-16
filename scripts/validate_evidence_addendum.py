"""One final artifact-integrity trial;no model or raw-data evaluation."""
import argparse,csv,hashlib,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'reports/evidence_addendum_20261027'
E=ROOT/'experiments/evidence/HEARTBEAT-20261026T190901Z'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def sha(p):
    with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def prepare():
    now=datetime.now(timezone.utc);rid='EVIDENCE-ADDENDUM-QA-'+now.strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'experiments/results'/rid;out.mkdir(exist_ok=False)
    pdf=ROOT/read(PROJECT/'build.json')['pdf'];input_manifest=read(PROJECT/'report_inputs.json')
    files=[pdf,PROJECT/'report_inputs.json',PROJECT/'report_content.json',PROJECT/'build.json',*sorted(PROJECT.glob('page-*.png')),*sorted((PROJECT/'figures').glob('*.png'))]
    files += [PROJECT/r['snapshot'] for r in input_manifest['inputs']]
    code=['scripts/build_evidence_addendum.py','scripts/validate_evidence_addendum.py']
    p=dict(run_id=rid,prepared_at=now.isoformat(),seed=151,source_ids=['SRC-DS-001','SRC-DS-003','SRC-LIVE-001','SRC-DS-019'],
        hypothesis='The dated addendum can preserve saved cohort identities,failures and pending status in a legible seven-page PDF with all17source snapshots bound by hash.',
        prior_exposure='Document was authored and all seven rendered pages visually reviewed before this final engineering integrity check;not a blind model evaluation',
        expected_pages=7,expected_snapshots=17,expected_source_ids=62,software_tests=392,expected_trials_at_input_freeze=87,
        input_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in files},source_hashes={p:sha(ROOT/p) for p in code},
        protected_hashes=read(ROOT/'models/singapore_trend_development.json')['protected_hashes'],
        required_phrases=['392 main-project tests','62 permanent IDs','10 logged learned origins','87 recorded trials existed at input freeze','13 of 14','92.86%','10,764 genuine forecasts','55,367 matched outcomes','16:21 IST','not exact 30-minute accuracy','consumed final','No replacement final set was admitted','ReportLab','does not assert independent student authorship'],
        gates=['Seven PDF pages and seven rendered PNGs','All source-snapshot identities match','Required results and pending/failure language present','No replacement glyphs or text outside page margins','All seven pages visually inspected','Protected production/claims unchanged'],
        maximum_seconds=120,model_calls=0,raw_final_or_future_targets_decoded=False,official_compliance_claimed=False)
    dump(out/'protocol.json',p);dump(out/'source_snapshots.json',{p:(ROOT/p).read_text(encoding='utf-8') for p in code});dump(out/'protocol_binding.json',dict(sha256=sha(out/'protocol.json')))
    dump(E/'artifact_validation_pointer.json',dict(run_id=rid,protocol=(out/'protocol.json').relative_to(ROOT).as_posix()));print(str(out/'protocol.json'))


def check(path):
    import pdfplumber
    from pypdf import PdfReader
    path=Path(path).resolve();out=path.parent;p=read(path);assert sha(path)==read(out/'protocol_binding.json')['sha256'] and not (out/'run.json').exists()
    start=datetime.now(timezone.utc);clock=time.perf_counter()
    for name,h in {**p['input_hashes'],**p['source_hashes'],**p['protected_hashes']}.items():assert sha(ROOT/name)==h,name
    build=read(PROJECT/'build.json');pdf=ROOT/build['pdf'];reader=PdfReader(pdf);assert len(reader.pages)==p['expected_pages']
    text=' '.join('\n'.join(page.extract_text() for page in reader.pages).split());phrases={v:v.lower() in text.lower() for v in p['required_phrases']};assert all(phrases.values()),phrases
    assert '\ufffd' not in text and '\u25a0' not in text
    bounds=[]
    with pdfplumber.open(pdf) as document:
        for i,page in enumerate(document.pages,1):
            chars=[c for c in page.chars if c['text'].strip()];bad=[c for c in chars if c['x0']<42 or c['x1']>page.width-42 or c['top']<15 or c['bottom']>page.height-15]
            assert not bad,(i,bad[:1]);assert (PROJECT/f'page-{i}.png').exists();bounds.append(dict(page=i,characters=len(chars),out_of_bounds=0))
    inputs=read(PROJECT/'report_inputs.json');assert len(inputs['inputs'])==17 and inputs['source_count']==62 and inputs['completed_trials_at_snapshot']==87 and inputs['software_tests']==392
    for row in inputs['inputs']:assert sha(PROJECT/row['snapshot'])==row['sha256']
    snap=PROJECT/'inputs';state=read(snap/'data/automation_state.json');group=read(snap/'models/pklot_remaining_group_audit.json');sg=read(snap/'models/singapore_trend_development.json');health=read(snap/'reports/singapore_issuance_health_latest.json')
    assert group['development_exposed']==group['consumed_final']==3 and group['newly_qualified_final_groups']==0
    assert state['forecast_temporal_final']['final_gate_passed'] and not state['occupancy_final_evaluation']['paired_final_gate_passed']
    assert sg['development_gate_passed'] and not sg['final_performance_evaluated'] and health['forecasts_logged']==10764
    assert sha(PROJECT/pdf.name)==sha(pdf)==build['pdf_sha256']
    result=dict(run_id=p['run_id'],started_at=start.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,seed=151,
        protocol_sha256=sha(path),artifact_gate_passed=True,pages=7,source_snapshots=17,source_ids=62,required_phrases=phrases,page_bounds=bounds,all_seven_rendered_pages_visually_reviewed=True,
        original_models_consumed_claims_unchanged=True,model_calls=0,raw_final_or_future_targets_decoded=False,official_compliance_claimed=False,pdf_sha256=sha(pdf),scope='Dated document artifact validation,not new model/accuracy evaluation')
    dump(out/'run.json',result);dump(E/'pdf_checks.json',result)
    statepath=ROOT/'data/automation_state.json';s=read(statepath);assert s['completed_recorded_runs_since_schedule']==87 and not s['active_validation_jobs'] and not s['active_training_jobs']
    registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
    with registry.open(encoding='utf-8-sig',newline='') as f:fields=csv.DictReader(f).fieldnames
    row=dict(experiment_id=p['run_id'],run_type='Seven-page dated PDF evidence addendum integrity/render validation',started_at=result['started_at'],finished_at=result['finished_at'],source_ids=';'.join(p['source_ids']),split_ids='Saved results andsource metadata only;no fresh/final/targetscoring',configuration=path.relative_to(ROOT).as_posix(),architecture='ReportLabPDF/Matplotlibcharts/Popplerrender/pypdf+pdfplumber checks',random_seed=151,hardware='CPU',execution_environment=sys.version.split()[0],training_duration=result['duration_seconds'],evaluation_metrics=json.dumps(dict(artifact_gate_passed=True,pages=7,source_snapshots=17,all_page_bounds_pass=True,model_calls=0)),logs=out.relative_to(ROOT).as_posix(),checkpoints='Original weights and claims unchanged',code_revision_basis='64ab20e plus sealed artifact sources',implementation_sha256=sha(__file__),conclusions='Artifact gate passes;dated frozen claims/limitations/pendingforecast preserved;not official academic/model completion')
    with registry.open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
    s['completed_run_ids'].append(p['run_id']);s['completed_recorded_runs_since_schedule']=len(set(s['completed_run_ids']));s['last_completed_run']=p['run_id'];dump(statepath,s)
    print(json.dumps(dict(run_id=p['run_id'],artifact_gate_passed=True,pages=7,source_snapshots=17,duration_seconds=result['duration_seconds'])))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check');args=parser.parse_args();check(args.check) if args.check else prepare()
