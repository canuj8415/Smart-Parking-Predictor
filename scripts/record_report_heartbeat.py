"""Save dated report acceptance evidence and the continuation state once."""
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from smart_parking.live import parse_feed

E = ROOT / 'experiments/evidence/HEARTBEAT-20261025T161532Z'
P = ROOT / 'reports/technical_report_v003'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def write(path, value):
    (ROOT / path).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    if (E / 'checks.json').exists():
        raise RuntimeError('This dated heartbeat has already been recorded')
    now = datetime.now(timezone.utc).isoformat()
    checks = read(E.relative_to(ROOT) / 'pdf_checks.json')
    build = read(E.relative_to(ROOT) / 'report_build.json')
    state = read('data/automation_state.json')
    assert state['scheduled_wakeups_completed'] == 21
    assert state['completed_recorded_runs_since_schedule'] == len(set(state['completed_run_ids'])) == 34
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert sha('output/pdf/smart_parking_technical_report_v003.pdf') == checks['pdf_sha256']
    assert checks['pages'] == 12 and checks['input_records_verified'] == 15
    compile_result = {
        'checked_at': now, 'path': str(P), 'main_tex_sha256': build['main_tex_sha256'],
        'kind': 'success',
        'message': "The current source compiled successfully with the desktop editor's compiler.",
        'tool': 'mcp__codex_app__compile_latex_document',
        'standalone_pdf_exported_by_this_tool': False,
        'standalone_pdf_engine': 'ReportLab',
    }
    write(E.relative_to(ROOT) / 'updated_latex_compile.json', compile_result)
    pointer = dict(path='output/pdf/smart_parking_technical_report_v003.pdf',
                   sha256=checks['pdf_sha256'], pages=12, snapshot_as_of=build['as_of'],
                   source_project='reports/technical_report_v003',
                   main_tex_sha256=checks['main_tex_sha256'], content_sha256=checks['content_sha256'],
                   standalone_pdf_engine='ReportLab', latex_counterpart_compile_status='success',
                   guide='docs/TECHNICAL_REPORT_GUIDE.md',
                   evidence=str(E.relative_to(ROOT)).replace('\\', '/'),
                   official_submission_accepted=False, student_mastery_verified=False)
    write('reports/technical_report_latest.json', pointer)
    receipts = [json.loads(line) for line in (ROOT / 'data/resource_receipts.jsonl').read_text().splitlines()]
    receipt = next(row for row in reversed(receipts) if row['source_id'] == 'SRC-LIVE-001')
    assert sha(receipt['local_path']) == receipt['sha256']
    payload = read(receipt['local_path'])
    rows = parse_feed(payload)
    assert len({(r['car_park_id'], r['lot_type'], r['observed_at']) for r in rows}) == len(rows)
    assert all(0 <= r['available'] <= r['capacity'] for r in rows)
    live = read('data/processed/singapore_prospective/summary.json')
    assert live['scores_total'] == 21678 and live['scores_added'] == 1201
    raw_count = sum(len(park['carpark_info']) for item in payload['items'] for park in item['carpark_data'])
    write(E.relative_to(ROOT) / 'live_checkpoint.json', dict(
        summary=live, receipt=receipt, accepted_rows=len(rows), raw_lot_records=raw_count,
        invalid_capacity_excluded=raw_count-len(rows), duplicates=0, bounds_valid=True,
        interpretation='1201 previously frozen persistence forecasts matched later observations; no neural/camera accuracy'))
    inventory = read('data/dataset_inventory.json')
    inventory['inventoried_at'] = now
    for row in inventory['datasets']:
        if row['source_id'] == 'SRC-LIVE-001':
            row.update(car_parks=len({r['car_park_id'] for r in rows}), observations=len(rows),
                       raw_lot_records=raw_count, raw_path=receipt['local_path'],
                       provider_timestamp=receipt['provider_timestamp'],
                       snapshot_count=len(list((ROOT / 'data/raw/singapore_live').glob('*.json'))),
                       prospective_baseline_scored_outcomes=live['scores_total'],
                       prospective_baseline_mae_spaces=live['baseline_mae_spaces'],
                       forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json', inventory)
    state.update(last_updated_at=now, scheduled_wakeups_completed=22, technical_report=pointer,
                 pending_document_checks=[],
                 last_live_baseline_score=dict(outcomes=live['scores_total'], mae_spaces=live['baseline_mae_spaces'],
                     scope='Persistence only; not neural/camera accuracy', coverage=live['forecast_coverage']))
    state['next_actions'] = [
        'Seek genuinely fresh labelled fixed-camera positive-crossing evidence with a prespecified protocol. Final DAVIS car-roundabout has zero reference events, fails acceptance and remains wholly consumed. Do not retune or re-evaluate changed methods on consumed image/date/sequence groups.',
        'Local demo latest DEMO-BUNDLE-20261025T160503964992Z retains 184 verified assets,167 software tests. Installed runtime reused; hidden widgets/mocked dialogs/Python socket block only. Complete visible/manual-dialog, fresh installation and physical-offline acceptance without changing unrelated networking.',
        'Report v003:12-page ReportLab PDF, editable LaTeX counterpart compiles,15 pinned inputs/45-source snapshot. See reports/technical_report_latest.json and docs/TECHNICAL_REPORT_GUIDE.md. Update presentation only for material new results; student rehearsal,official template and university sources remain pending.',
        'Current ledger34 trials/167 tests; report compilation/render/provenance checks are not additional experiments. Earlier Excel15:32snapshot remains intentionally32/162. All original weights/failed studies and consumed reservations preserved; no active trainers.',
        'Next sensible official collection after16:23UTC observation:21678 matched persistence outcomes,MAE4.298828,6511 expired/1374 pending,76.90%resolved matching. Wait for future matching targets,do not poll per simulation. Counter34; separate100-run live milestone100.'
    ]
    write('data/automation_state.json', state)
    note = '''A current 12-page technical report v003 is saved at
output/pdf/smart_parking_technical_report_v003.pdf. It explains the Python/Jupyter
product, methods, real-data inventory, original and later measured results,
failed studies, qualified claims, convolution lessons, reproducibility and
remaining acceptance work. Source IDs, licensing limits and local data/CSV/raw
JSON paths are explicit. All45 source records and acquisition receipts are
snapshotted;15 exact inputs pinned. Earlier drafts and original evidence remain.

The old LaTeX draft and the new editable main.tex both return successful built-in
compiler diagnostics. The delivered standalone PDF is typeset with ReportLab
from the shared report_content.json; it is not a compiler-exported TeX PDF.
All12 rendered PDF pages were visually reviewed; extracted metrics, page bounds,
source/cache hashes and final-failure wording pass artifact checks. Bundled Python
has no Matplotlib, so figures are generated with existing project Python and
ReportLab runs in the bundled authoring runtime; no packages installed. An initial
literal-text assertion missed a PDF line wrap; whitespace-normalized check passes.

No new model inference/training or raw final evaluation occurred. Only a previously
seen development car-turn frame22 was opened for a labelled illustration; charts
use archived metrics/cached development observations. Counter remains34 unique
completed trials,167 previously passed software tests; report authoring checks
are not new experiment runs. No product runtime changed. No active jobs; next
separate100-run checkpoint100. Excel15:32snapshot remains intentionally32/162.

Actual16:23UTC authorized Singapore snapshot27 matches1201 earlier frozen
persistence targets:21678 total,MAE4.298828spaces,6511expired/1374pending,
76.90%resolved matching. Raw JSON,normalized observations,URL,time,SHA and schema/
bounds/duplicate checks retained. No camera/neural live accuracy. Source targets
must arrive later; no per-simulation polling. Full project,physical-offline/native
manual acceptance,student mastery,official academic template and fresh labelled
crossing evidence remain unfinished. See docs/TECHNICAL_REPORT_GUIDE.md.'''
    title = '## 25 October 2026 / current technical report and successful LaTeX compilation'
    for name in ['docs/PROJECT_PROGRESS.md', 'docs/AUTONOMOUS_PROGRESS.md', 'docs/TEST_RESULTS.md',
                 'docs/AI_ASSISTANCE_LOG.md', 'reports/PROGRESS_ADDENDUM_20261025.md']:
        path = ROOT / name
        text = path.read_text(encoding='utf-8')
        assert title not in text
        path.write_text(text.rstrip() + '\n\n' + title + '\n\n' + note + '\n', encoding='utf-8')
    path = ROOT / 'docs/IMPLEMENTATION_STATUS.md'
    text = path.read_text(encoding='utf-8').replace('Twenty-six authorized public snapshots acquired', 'Twenty-seven authorized public snapshots acquired')
    text = text.replace('Eighteen prospective persistence cohorts scored', 'Nineteen prospective persistence cohorts scored')
    text = text.replace('20,477 matched later outcomes, MAE4.344', '21,678 matched later outcomes, MAE4.299')
    text = text.replace('| Student mastery / final report | Not assessed / report draft sources saved | Editable technical report draft saved; compilation unconfirmed; 14slide presentation saved; official template, native rehearsal and learning/viva evidence remain |',
        '| Student mastery / final report | Not assessed / 12-page current technical draft reviewed | v003 PDF typeset with ReportLab; editable LaTeX counterpart compiles; 14slide presentation retained; official template, native rehearsal and learning/viva evidence remain |')
    path.write_text(text.rstrip() + '\n\n' + title + '\n\n' + note + '\n', encoding='utf-8')
    path = ROOT / 'docs/REQUIREMENTS.csv'
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle); fields = reader.fieldnames; requirements = list(reader)
    for row in requirements:
        if row['requirement_id'] == 'DOC-01':
            row.update(status='In progress', actual_evidence='reports/technical_report_latest.json; reports/technical_report_v003; docs/TECHNICAL_REPORT_GUIDE.md',
                       test_result='12-page standalone ReportLab PDF reviewed;15 input hashes/45 sources; editable LaTeX counterpart compiled successfully; not a TeX PDF export',
                       open_problems='Official university template/primary documents/student identity and independent student review remain absent; technical draft only',
                       next_action='Student review/rehearsal and official template mapping when documents supplied; preserve dated results and failed studies')
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader(); writer.writerows(requirements)
    write(E.relative_to(ROOT) / 'checks.json', dict(
        artifact=pointer, completed_trials=34, software_tests_previously_passed=167,
        new_model_experiments=0, active_jobs=[], raw_final_reread=False,
        final_counting_gate_passed=False, original_weights_unchanged=True,
        live_outcomes=21678, live_baseline_mae_spaces=live['baseline_mae_spaces']))
    print(json.dumps(pointer, indent=2))


if __name__ == '__main__':
    main()
