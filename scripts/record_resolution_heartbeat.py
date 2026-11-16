"""Record completed resolution study and inspection-only acquisitions; no training."""
import csv, hashlib, json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
RUN = 'REGION-TRANSFER-20261024T214740232123Z'
FOLDER = ROOT / 'experiments/results' / RUN
EVIDENCE = ROOT / 'experiments/evidence/HEARTBEAT-20261024T213922Z'
now = datetime.now(timezone.utc).isoformat()

def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def write(path, obj):
    (ROOT / path).write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')

def rows(path):
    with (ROOT / path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)

def table(path, fields, values):
    with (ROOT / path).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL if path == 'docs/REQUIREMENTS.csv' else csv.QUOTE_MINIMAL)
        writer.writeheader(); writer.writerows(values)

def append(path, heading, content):
    target = ROOT / path
    old = target.read_text(encoding='utf-8')
    if heading not in old:
        target.write_text(old.rstrip() + '\n\n## ' + heading + '\n\n' + content.strip() + '\n', encoding='utf-8')

r = read(FOLDER.relative_to(ROOT) / 'run.json')
summary = read('data/processed/singapore_prospective/summary.json')
acquisition = read('data/raw/metapklot_inspection/acquisition.json')
receipts = [json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text().splitlines()]
live_receipt = [x for x in receipts if x['source_id'] == 'SRC-LIVE-001'][-1]
raw = read(live_receipt['local_path'])
parks = raw['items'][0]['carpark_data']
live = dict(summary=summary, receipt=live_receipt,
            scored_issue_cohorts=sum(x['scored'] > 0 for x in summary['forecast_coverage']['cohorts']),
            car_parks=len(parks), observations=sum(len(x['carpark_info']) for x in parks))
write(EVIDENCE.relative_to(ROOT)/'live_checkpoint.json', live)
write(EVIDENCE.relative_to(ROOT)/'metapklot_inspection.json', acquisition)

expected = {
    'models/checkpoints/parking_unet.pt': '2fe3743e6cbec0a4f195292e62a37702c18d9a851af610b3e280ca54e7fc5feb',
    'models/checkpoints/lstm_30min.pt': '27dc324e0037a00147832dd1d84a3de1b75600e2600c9f429e47da84dac9bc39',
    'models/checkpoints/occupancy_resnet18.pt': '72272f0fccd1ca8da9d0fa2c0c78aef47b49c757954fdac6a93ef2266b4ee1a7',
}
checks = {}
for path, wanted in expected.items():
    actual = hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    assert actual == wanted, path
    checks[path] = actual
write(EVIDENCE.relative_to(ROOT)/'production_unchanged.json', checks)

fields, sources = rows('data/source_manifest.csv')
def source(**values):
    if not any(x['source_id'] == values['source_id'] for x in sources):
        sources.append({key: values.get(key, '') for key in fields})
source(source_id='SRC-DS-010', resource_type='dataset annotations; inspection only', resource='MetaPKLot PKLot UFPR04 vehicle annotations',
       original_creator='DSBD-Research; Paulo Lisboa de Almeida; Jeovane Honorio Alves; Luan Marko Kujavski; Paulo Luza Alves; Luiz Eduardo Oliveira',
       source_url=acquisition['source_url'], download_url=acquisition['assets'][0]['url'], access_date=acquisition['recorded_at'],
       access_time_precision='Asset receipt UTC timestamps', version=acquisition['revision'],
       license='Publisher README declares PKLot portion CC BY4.0; mixed repository has no blanket licence',
       permission='Public inspection acquisition; operational use pending exact file/scope verification', original_size='1426408 bytes archive; 97715961 bytes declared JSON member',
       local_location='data/raw/metapklot_inspection/', sha256=acquisition['assets'][0]['sha256'],
       purpose='Investigate vehicle ground-truth matching to existing PKLot development images', used_by='Metadata/rights audit only; no annotation parsing, training or scoring',
       modifications='Original archive and README/CITATION preserved; tar member headers inspected without extraction',
       attribution='Almeida and collaborators 2026; DOI10.1007/s00521-026-12398-0; pinned repository', status='inspection_archive_acquired',
       open_issues='Verify per-file rights, annotation rectangle/ROI, image identity and development-only filtering; do not expose closed final labels or silently repair raw dates')
source(source_id='SRC-DS-011', resource_type='dataset candidate', resource='TRANCOS', original_creator='GRAM; University of Alcala; dataset authors',
       source_url='https://gram.web.uah.es/data/datasets/trancos/index.html', access_date='2026-10-24', access_time_precision='date only; primary site consulted',
       version='not acquired', license='Scientific research use; DGT terms also required; complete rights not verified', permission='No assets downloaded or used',
       original_size='Publisher describes1244images and46796vehicle points; no local assets', local_location='not downloaded',
       purpose='Potential vehicle-count evaluation; points do not provide boxes or masks', used_by='Candidate research only', modifications='None',
       attribution='Use publisher citation if acquired later', status='candidate', open_issues='Official SharePoint download failed; verify DGT reuse terms; no mirror substitution')
for item in sources:
    if item['source_id'] == 'SRC-DS-009':
        if '24Oct primary policy confirms' not in item['open_issues']:
            item['open_issues'] += '; 24Oct primary policy confirms registration/purpose declaration: https://www.cvlibs.net/datasets/kitti/user_submit.php; no bypass or acquisition'
    if item['source_id'] == 'SRC-DS-001':
        if 'higher-resolution region development' not in item['used_by']:
            item['used_by'] += '; higher-resolution region development trial on same train36/val6'
table('data/source_manifest.csv', fields, sources)

fields, registry = rows('experiments/EXPERIMENT_REGISTRY.csv')
if not any(x['experiment_id'] == RUN for x in registry):
    value = dict(experiment_id=RUN, run_type='Single-seed common-grid neural-region resolution contrast; final closed',
        started_at=r['started_at'], finished_at=r['finished_at'], source_ids='SRC-DS-001;SRC-MOD-003',
        split_ids='Known-camera train36/validation6; shared sealed final6 undecoded', configuration=str((FOLDER/'protocol.json').relative_to(ROOT)),
        architecture=r['architecture'], model_version=RUN, optimizer='Adam', learning_rate=.002, epochs=r['epochs_completed'], batch_size=4,
        random_seed=71, hardware='CPU4 threads; BLAS1/OMP2/MKL2', execution_environment='Python3.12.10; Torch2.14.0+cpu',
        training_duration=r['duration_seconds'], loss_curves=str((FOLDER/'curves.json').relative_to(ROOT)),
        evaluation_metrics=json.dumps(dict(common_grid=r['validation'], native_grid=r['native_validation'], gate_passed=False, final_images_decoded=0)),
        logs=str(FOLDER.relative_to(ROOT)), checkpoints=str((FOLDER/'candidate.pt').relative_to(ROOT)),
        code_revision_basis='36974e5 plus sealed protocol hashes and implementation_sources.json', implementation_sha256=r['code_sha256'],
        conclusions='Common192x112 IoU0.79629 vs0.77054; all three camera IoUs improve but aggregate and geometry-regression gates fail; no final decoding/promotion; checkpoint replay exact')
    registry.append({key: value.get(key, '') for key in fields})
table('experiments/EXPERIMENT_REGISTRY.csv', fields, registry)

inventory = read('data/dataset_inventory.json'); inventory['inventoried_at'] = now
for item in inventory['datasets']:
    if item['source_id'] == 'SRC-DS-001':
        item['resolution_contrast'] = dict(run_id=RUN, input_size=r['input_size'], evaluation_grid=r['evaluation_grid'],
            validation_iou=r['validation']['overall']['pixel_iou'], final_images_decoded=0, validation_gate_passed=False)
    if item['source_id'] == 'SRC-LIVE-001':
        item.update(car_parks=live['car_parks'], observations=live['observations'], provider_timestamp=live_receipt['provider_timestamp'],
            raw_path=live_receipt['local_path'], snapshot_count=len(list((ROOT/'data/raw/singapore_live').glob('*.json'))),
            prospective_baseline_scored_outcomes=summary['scores_total'], prospective_baseline_mae_spaces=summary['baseline_mae_spaces'],
            forecast_target_coverage=summary['forecast_coverage'])
if not any(x['source_id'] == 'SRC-DS-010' for x in inventory['datasets']):
    inventory['datasets'].append(dict(source_id='SRC-DS-010', status=acquisition['status'], files=acquisition['assets'],
        archive_members=acquisition['archive_members'], used_for_training=False, used_for_accuracy_evaluation=False,
        annotation_json_documents_parsed=0, images_downloaded=0, images_decoded=0, acquisition_receipt='data/raw/metapklot_inspection/acquisition.json'))
if 'TRANCOS' not in inventory['not_acquired']: inventory['not_acquired'].append('TRANCOS')
write('data/dataset_inventory.json', inventory)
state = read('data/automation_state.json')
assert state['completed_recorded_runs_since_schedule'] == 14
state.update(scheduled_wakeups_completed=7, last_updated_at=now, active_training_jobs=[])
state['best_development_region'] = dict(run_id=RUN, validation_iou=r['validation']['overall']['pixel_iou'],
    input_size=r['input_size'], evaluation_grid=r['evaluation_grid'], validation_gate_passed=False, production_promoted=False,
    fresh_final_images_decoded=0, fresh_final_manifest=r['fresh_final_manifest'])
state['last_live_baseline_score'] = dict(outcomes=summary['scores_total'], mae_spaces=summary['baseline_mae_spaces'],
    scope='Persistence only; five scored issue cohorts; coverage is target matching, not accuracy', coverage=summary['forecast_coverage'])
state['next_actions'] = [
    'Collect one authorized official snapshot next wake;1245forecasts frozen21:41UTC and86remaining21:11entries need later source-consistent targets. Never invent missing outcomes. Next separate100-run milestone100; current14.',
    'Higher-resolution common-grid IoU0.79629 improves all three cameras but still fails aggregate/geometry-regression gates. Keep all candidates and production unchanged; avoid repetitive threshold/loss sweeps on six development frames.',
    'SRC-DS-010 pinned UFPR04 vehicle annotation archive acquired for inspection only. Before parsing labels, verify exact-file licence/scope; design streaming metadata/development-only filtering excluding all reserved/consumed finals, verify original image identity and annotation ROI. No detection or mask accuracy yet.',
    'Shared final6 stays closed. Use overlap-aware evaluate_final_once only for a frozen validation-qualified method. Atomic checkpoint saves now protect prior complete files on interrupted writes; no active trainers.',
    'Continue independent forecast robustness, labelled parking-video/flow, application native-save/fresh-offline validation and report/presentation/student materials. Existing report/notebook/Excel/PDF remain dated snapshots; compilation and official university requirements unconfirmed.'
]
write('data/automation_state.json', state)

heading = '25October2026 / higher-resolution region trial and annotation inspection'
overview = '''Completed REGION-TRANSFER-20261024T214740232123Z: same36train/6development
images, architecture, seed71, augmentation and fixed positive BCE4.574; input
384x224 rather than192x112. Selected and scored projected logits on the SAME
192x112 truth grid, before sigmoid/threshold0.5. IoU0.7962915 vs0.7705360;
per-camera pucpr0.85596/ufpr040.67641/ufpr050.81643. Native-grid IoU0.79788
is secondary.80epochs, best69,427.51seconds. Acceptance FAILS: aggregate<0.80
and stable-camera drops>0.10 below train-only geometry. No final image/annotation
decoding, no production change, no unseen-camera or individual-slot claim.
All six saved common-grid masks exactly replay from the selected checkpoint;
truths match the reference. Protocol/code/data hashes, full source snapshot,
curves, native/common masks and visually checked comparison plot retained.

Checkpoint writes now save/flush/fsync a same-folder temporary then replace the
target. Fault-injected incomplete saves preserve the previous complete checkpoint;
temporary cleanup and successful load tested.66software checks pass, distinct
from model trials. All3production hashes verified unchanged. Counter14 completed
recorded runs; next100-run checkpoint100; no trainers active.

Tenth official Singapore snapshot21:41UTC added1115later matched outcomes and
1245frozen forecasts.5601scored across5issue cohorts; persistence MAE2.0114265
spaces.8607issued;1675expired missing targets,1245before-window and86in-window
as of collection. Target matching5601/7276=76.98%among resolved forecasts is
not accuracy. No invented missing scores or neural/camera live accuracy.

MetaPKLot SRC-DS-010: pinned UFPR04 vehicle-annotation archive1,426,408bytes
plus original README/CITATION acquired, Git-blob and SHA256 verified. Only tar
member headers inspected:97,715,961byte JSON not extracted/parsed. Zero images
downloaded/decoded; zero training/scoring use. Publisher declares PKLot portion
CC BY4.0 but repository contains mixed licences. Exact-file rights, source-image
identity, rectangle/ROI completeness and development-only filtering remain to
verify. Raw data dates/final reservations unchanged. TRANCOS SRC-DS-011 remains
unacquired: official download failed and DGT terms unresolved. KITTI registration
policy confirmed; no access controls bypassed.44source records now maintained.

Full next actions: data/automation_state.json. Report compilation/presentation,
official university documents, labelled parking-video/flow and physical native
save/offline/fresh-install validation remain unfinished. Earlier reports, Excel,
guide and notebook03 remain dated evidence snapshots.'''
append('docs/AUTONOMOUS_PROGRESS.md', heading, overview)
append('docs/PROJECT_PROGRESS.md', heading, overview)
append('reports/PROGRESS_ADDENDUM_20261025.md', heading, overview)
append('docs/TEST_RESULTS.md', heading, '''66software checks passed: new atomic interrupted-save/success tests and fixed rectangular common-grid projection/decoder tests. Evidence: experiments/evidence/HEARTBEAT-20261024T213922Z/. Selected higher-resolution checkpoint exactly reproduces all6common-grid masks. DevelopmentIoU0.79629 remains below acceptance; final6closed;3production hashes unchanged. Source archive inspection is not an accuracy trial.''')
append('docs/IMPLEMENTATION_STATUS.md', heading, '''Higher-resolution region developmentIoU0.79629 on common192x112 grid (native0.79788), gate failed; shared final6closed. Atomic checkpoint saves implemented;66software checks pass. Tenth live snapshot:5601matched persistence outcomes, MAE2.01143, resolved matching76.98%as of21:41UTC. MetaPKLot archive is inspection-only, no annotation parsing or model use. Remaining limitations above still apply.''')
append('docs/PROJECT_CONSTRAINTS.md', heading, '''MetaPKLot SRC-DS-010 archive is inspection-only. Preserve pinned original bytes and mixed-source rights distinctions; operational annotation use requires file/scope/ROI/image matching verification and exclusion of consumed/reserved final frames. KITTI registration and unresolved TRANCOS/DGT terms are not bypassed. Higher-resolution candidate still fails acceptance; retain closed final and production checkpoints.''')
research = '''Primary sources consulted24October2026:
- MetaPKLot publisher https://github.com/DSBD-Research/MetaPKLot-Dataset and https://huggingface.co/datasets/DSBD-Research/MetaPKLot-Dataset ; pinned revision9218800c4eb2b7c1b17b51c8cdb07ad51686f8a2. PKLot-portion UFPR04 archive/README/CITATION receipts in data/resource_receipts.jsonl; originals in data/raw/metapklot_inspection/. No annotation JSON parsed, image acquired or model use. Verify exact-file rights and image/ROI correspondence before development-only extraction; no final labels.
- Associated publication metadata: Almeida, Alves, Kujavski, Alves and Oliveira, MetaPKLot: new challenges and protocols for vision-based parking lot management, Neural Computing and Applications38, article704(2026), DOI10.1007/s00521-026-12398-0. Metadata/repository review only, not full-paper methodological review.
- TRANCOS https://gram.web.uah.es/data/datasets/trancos/index.html ; scientific-research and DGT conditions, official SharePoint fetch failure; SRC-DS-011 candidate only, no download or use.
- KITTI https://www.cvlibs.net/datasets/kitti/user_submit.php requires registration/purpose declaration; existing SRC-DS-009 remains unacquired. CNRPark publisher site still unavailable; author repository links do not resolve source terms. No mirrors, account creation or gated downloads used.

MetaPKLot mixed-source README declares PKLot portion CC BY4.0, CNRPark-EXT ODbL1.0 and excludes redistribution of PLds images. Do not apply one licence to the whole repository. Publisher corrected-date mappings are only research notes; original PKLot files/manifests remain unchanged. Annotation rectangles bound label completeness; outside-ROI negatives are not assumed.44canonical source records; acquired archives are not automatically usable benchmark labels.'''
for path in ['docs/SOURCE_REGISTRY.md','docs/THIRD_PARTY_SOURCES.md','docs/RESEARCH_LOG.md','docs/LITERATURE_NOTES.md']:
    append(path, heading, research)
append('docs/AI_ASSISTANCE_LOG.md', heading, '''AI assistant designed/implemented the common-grid resolution contrast and atomic checkpoint saving, ran the80epoch study and66software checks, replayed its checkpoint, researched primary annotation sources, acquired the pinned public inspection archive, maintained live collection/evidence and documentation. Student independent authorship/mastery is not implied. No final labels or new vehicle annotations were parsed/scored; failed gates and acquisition restrictions preserved.''')
fields, requirements = rows('docs/REQUIREMENTS.csv')
for item in requirements:
    if item['requirement_id'] == 'DATA-01':
        item['test_result'] = '44source records; original PKLot/UCI/live/video; MetaPKLot pinned inspection-only archive, no annotation parsing; TRANCOS unacquired'
    if item['requirement_id'] == 'SEG-02':
        if 'models/region_resolution_candidate.json' not in item['actual_evidence']:
            item['actual_evidence'] += '; models/region_resolution_candidate.json'
        item['test_result'] = 'Original finalIoU0.2518; higher-resolution common-grid developmentIoU0.79629 vs reference0.77054, gate FAILED; fresh final6closed'
table('docs/REQUIREMENTS.csv', fields, requirements)
print(json.dumps(dict(counter=14, source_records=len(sources), live=live['observations'], checkpoint_replay=read(FOLDER.relative_to(ROOT)/'checkpoint_replay.json')), indent=2))
