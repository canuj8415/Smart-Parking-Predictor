"""Persist the failed replacement gate honestly and keep final groups consumed."""
import csv
import json
import shutil
import sys
from datetime import datetime,timedelta,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.live import URL,get_live,_observation_key

E=ROOT/'experiments/evidence/HEARTBEAT-20261026T014742Z'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):
    p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def append(p,title,text):
    p=ROOT/p;old=p.read_text(encoding='utf-8');assert title not in old
    p.write_text(old.rstrip()+'\n\n'+title+'\n\n'+text+'\n',encoding='utf-8')


def main():
    assert not (E/'handoff_checks.json').exists()
    state=read('data/automation_state.json');final=read('models/occupancy_expansion_final.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==52
    assert state['scheduled_wakeups_completed']==34 and not state['active_training_jobs'] and not state['active_validation_jobs']
    assert final['all_final_groups_now_consumed'] and not final['paired_final_gate_passed'] and not final['production_promoted']
    assert sum(r['explicit_labels'] for r in final['support'])==336 and sum(r['unknown_labels'] for r in final['support'])==0
    for d,card in final['detectors'].items():
        assert [k for k,v in card['checks'].items() if not v]==['retain_correct_vacancies']
        group=next(r for r in card['per_group']['candidate'] if r['camera_id']=='pucpr')
        assert group['correct_vacant']==13
    try:assert_holdout_closed(ROOT/final['manifest'],root=ROOT)
    except ValueError as error:
        assert 'already started evaluation' in str(error);guard_note=str(error)
    else:raise AssertionError('Consumed final was incorrectly reopened')
    assert all(digest(ROOT/p)==h for p,h in final['source_hashes'].items())
    assert all(digest(ROOT/b['path'])==b['sha256'] for b in final['models'].values())
    original=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    assert all(digest(ROOT/p)==h for p,h in original.items())
    assert digest(ROOT/'src/smart_parking/flow.py')=='40f882044cfeadf05817584c9ead86964f2c6d2358a09da31256d27dd9d872b9'
    software=read(E/'pre_final_regressions.json');workbook=read(E/'workbook_checks.json');notebook=read(E/'notebook_archive_reader.json')
    assert software['success'] and software['tests_run']==206 and notebook['errors']==0
    assert workbook['typed_inputs_and_formula_caches_verified'] and digest(ROOT/workbook['workbook'])==workbook['sha256']
    archive=ROOT/'reports/occupancy_final_20261026';archive.mkdir(parents=True,exist_ok=False)
    for relative in [workbook['workbook'],workbook['csv']]:
        source=ROOT/relative;target=archive/source.name;shutil.copyfile(source,target);assert digest(source)==digest(target)
    rows,meta=get_live(refresh=False);raw_path=Path(meta['path']);live=read('data/processed/singapore_prospective/summary.json')
    assert Path(live['snapshot_path'])==raw_path
    receipts=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    receipt=next(r for r in reversed(receipts) if r['local_path']==raw_path.relative_to(ROOT).as_posix())
    assert receipt['source_url']==URL and receipt['sha256']==digest(raw_path)
    with (ROOT/'data/processed/singapore_live_observations.csv').open(encoding='utf-8',newline='') as stream:history=list(csv.DictReader(stream))
    keys=[_observation_key(r['car_park_id'],r['lot_type'],r['observed_at']) for r in history]
    assert len(keys)==len(set(keys)) and all(0<=r['available']<=r['capacity'] and r['capacity']>0 for r in rows)
    with (ROOT/'data/source_manifest.csv').open(encoding='utf-8-sig',newline='') as stream:assert len(list(csv.DictReader(stream)))==57
    snapshots=len(list(raw_path.parent.glob('*.json')))
    write(E/'live_checkpoint.json',dict(**live,snapshot_count=snapshots,raw_sha256=digest(raw_path),acquisition_receipt=receipt,
        valid_rows=len(rows),car_parks=len({r['car_park_id'] for r in rows}),history_duplicates=0,cached_app_route_passed=meta['cached'],
        separate_100_run_checkpoint=False,scope='Singapore persistence only; no neural or camera accuracy'))
    brief=dict(run_id=final['run_id'],frozen_revision=final['execution_frozen_revision'],scored_labels=336,photos=6,camera_date_groups=3,
        detectors={d:v['overall'] for d,v in final['detectors'].items()},paired_final_gate_passed=False,
        failed_rule='Per-group correct-vacancy retention: rainy PUCPR13/14=92.857percent, below frozen95percent requirement;both detectors',
        all_groups_consumed=True,production_promoted=False,original_checkpoint_unchanged=True,
        workbook=workbook['workbook'],workbook_sha256=workbook['sha256'],csv=workbook['csv'],
        archival_workbook=(archive/Path(workbook['workbook']).name).relative_to(ROOT).as_posix(),
        guide='docs/OCCUPANCY_FINAL_GUIDE.md')
    write('reports/occupancy_final_latest.json',brief)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=datetime.now(timezone.utc).isoformat()
    inventory['fresh_pklot_final_evaluation']=brief
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-001':item['fresh_final_evaluation']=brief
        if item['source_id']=='SRC-LIVE-001':item.update(car_parks=len({r['car_park_id'] for r in rows}),observations=len(rows),
            provider_timestamp=meta['provider_timestamp'],raw_path=raw_path.relative_to(ROOT).as_posix(),snapshot_count=snapshots,
            prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    state.update(scheduled_wakeups_completed=35,last_updated_at=datetime.now(timezone.utc).isoformat(),occupancy_final_evaluation=brief,
        latest_occupancy_workbook=workbook['workbook'],last_live_baseline_score=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],scope='Persistence only; no neural/camera accuracy',coverage=live['forecast_coverage']))
    next_poll=(datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    state['next_actions']=[
        'Keep original app occupancy model. Candidate final on336labels improves forced errors8->4,but FAILED frozen rainy-view retention13/14<95percent under BOTH detectors. Preserve this failed gate unchanged; no promotion,threshold waiver or new inference/tuning on these6photos or any of their3whole date groups. All171source frames in those groups consumed;older image/Birmingham/DAVIS finals also consumed.',
        'Next independent concrete fix: forecast_reports.load_forecast_report(LATER) correctly loads group-relative archived predictions,but app.py lines456/460still label every curve/MAE as LSTM. Expose the actual method name from each report,fix plot/text/export labels and add targeted report/native UI fixture checks. Read archived output JSON only;do not re-score/read raw consumed forecasting holdouts. Preserve original prediction bytes and model weights.',
        'Then pursue authoritative individual-image usage permission for CNR or another legitimate independently labelled parking source,without private accounts/CCTV or bypass. CNR144965metadata records/32079reserved images remain image-use-unqualified. Any new occupancy candidate must exclude all consumed groups and reserve genuinely fresh source groups before evaluation;do not tune to this final outcome.',
        'Excel outputs/parking_final_20261026T014742Z/Smart_Parking_Final_Comparison.xlsx has2sheets and11verified formula caches;final_slot_predictions.csv has1344config-level predictions for336unique source slots,not1344independent examples. Exact archive copies in reports/occupancy_final_20261026. Notebook09archive reader now executes afterfinalconsumption,training/curvesonly;no finalreplay.206fullsoftware tests pass.',
        f'Counter52; next separate100-run live checkpoint100; no active jobs. Singapore{live["checked_at"]}:40snapshots,{live["scores_total"]}matched persistence outcomes,MAE{live["baseline_mae_spaces"]:.6f}spaces;next sensible collection after{next_poll}. Missing targets unscored. Frozen offline demo remains an older snapshot;no neural/camera live accuracy.',
        'Project remains incomplete: source-qualified robustness/real traffic evidence and scoped physical/new-machine/visible browser/manual/student mastery/official university-doc acceptance pending. Preserve source57,allraws,best/failed checkpoints,receipts,final claims and dated reports.'
    ];write('data/automation_state.json',state)
    title='## 26 October 2026 / once-only paired occupancy final and retained replacement failure'
    note='The frozen protocol/controller was committed as3b08e8f before any final pixels/XML labels were opened.206fullsoftware tests,including synthetic paired-controller/unknown-label cases,passed before final decode;real final claims unchanged during tests. Both original/candidate checkpoints,source/config/model hashes and passed development cards bound;paired binding receipt and durable whole-date claim flushed before callback. Six photos/3known camera-date groups supplied336explicit labels(236occupied/100vacant),0unknown;UFPR04group has56empty/0occupied so its occupied-case accuracy remains unmeasured. Forced classifier errors8->4(97.619->98.810percent),same for bothdetectors. Combined Faster original95correctempty/2wrongempty/4wrongoccupied/10review versus candidate99/0/0/8;Mask94/2/4/11versus98/0/0/9. Candidate is better overall but FAILS the frozen per-group correct-vacancy-retention check: rainy PUCPR14->13correctempty,13/14=92.857percent<95percent. Both final gatesFalse;no rule change,model promotion or universal/live accuracy claim. All3whole date groups now CONSUMED,including171sourceframes;older finals remain consumed. Original3production checkpoints/tracker unchanged. One final comparison advances51->52,not permodel/photo. Two-sheet Excel and tidy1344prediction CSV(4configs on336unique slots) preserve failed rule;11formula caches,boundary recalculation,ZIPCRC/source metrics and both previews checked. Native visible Excel not tested. Bundle-library junction initially denied in restricted call;authorized retry succeeded,no package installation/dependency mutation. Notebook09updated as archived training reader,6actualkernelcells/1PNG/zeroerrors,without retraining/finalinference;previous executed source preserved. Latest officialSingapore40snapshots adds1188matched earlier baseline outcomes,33950total,MAE4.790133spaces;1242newforecasts frozen. Missing targets unscored;aggregatefeed not camera truth. Source57unchanged. Next independent task:correct app archive-forecast LSTM mislabelling for the frozen group-relative report,without raw holdout access;continue legitimate new-source qualification. Physical/manual/browser/student/official completion remains unclaimed.'
    for p in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md']:append(p,title,note)
    append('docs/PROJECT_CONSTRAINTS.md',title,'Fresh PKLot final6and all3whole groups are now CONSUMED:pucpr2012-10-23,ufpr042012-12-24,ufpr052013-04-08. Failed95percent rainy-view vacancy-retention gate is preserved;original app model retained. Do not evaluate/tune changed methods on these photos,aliases or any other same-group frame. Claims/immutable reservation and original/candidate results retained. Archived result display/export is allowed. Independent improvements need fresh final source groups.')
    append('docs/DATASET_PROVENANCE.md',title,'No new image acquisition. Previously qualified immutable JPEG/XMLbytes decoded only after frozen paired claim. Original explicit labels scored336,unknown0;geometry stripped of answer labels before inference. Future role is consumed-final,regardless of immutable reservation metadata saying originally unopened. Claim/outcome is authoritative. CSV duplicates336source slots across4clearly labelled detector/classifier configurations;no fictitious1344-ground-truth count.')
    append('docs/UI_TEST_LOG.md',title,'Actual VisionEngine paths run under frozenpairedprotocol,not a visible desktop rehearsal. Both Excel sheets visually reviewed and exported package/formula caches checked;nativeExcel not opened. Actual Jupyter archive-reader kernel works afterconsumption;no raw final pixels/inference replay.')
    guide='''# What the final parking test found

We opened the sealed exam once: six photos from three new dates on known camera views. They contained 336 labelled spaces: 236 occupied and 100 empty. Both the original model and the trained candidate answered the same questions with the same detector settings and supplied slot geometry.

| Final classifier result | Original | Candidate |
|---|---:|---:|
| Forced yes/no mistakes | 8 | 4 |
| Correct forced yes/no answers | 328 / 336 | 332 / 336 |
| Forced yes/no accuracy | 97.62% | 98.81% |

The combined app can say “needs review” instead of making a definite answer. Its counts below therefore measure a different result from forced yes/no accuracy.

| Combined final pipeline | Correct empty | Wrong empty | Wrong occupied | Needs review |
|---|---:|---:|---:|---:|
| Original with Faster R-CNN | 95 | 2 | 4 | 10 |
| Candidate with Faster R-CNN | 99 | 0 | 0 | 8 |
| Original with Mask R-CNN | 94 | 2 | 4 | 11 |
| Candidate with Mask R-CNN | 98 | 0 | 0 | 9 |

The candidate improved these overall totals. It still failed one rule fixed before opening the exam: on each camera/date, it had to keep at least 95% of the original model's correct empty-space answers. On the rainy PUCPR view, the original found all 14 empty spaces. The candidate found 13 and left one for review. That keeps 92.86%, below the fixed 95% requirement.

Imagine an attendant who avoids more wrong directions overall but overlooks one previously usable empty space in a rainy corner. Our replacement rules require both kinds of performance. **We kept the failed result and the original app model.** We have not lowered the rule after seeing the answers.

These six photos are related observations, not a universal benchmark. The UFPR04 photos show only empty spaces, so they cannot measure its occupied-case accuracy. Correct slot polygons were supplied; automatic space segmentation remains separate. Zero observed wrong-empty answers in this small candidate test does not promise zero future mistakes or live camera accuracy.

## Read the saved evidence

- Excel: `outputs/parking_final_20261026T014742Z/Smart_Parking_Final_Comparison.xlsx`. Results first; data, sources, paths and saved live-feed context second.
- CSV: the adjacent `final_slot_predictions.csv`. It has 1,344 prediction records because each of 336 source slots was checked under four model/detector configurations. These are not 1,344 independent labels.
- Full result: `models/occupancy_expansion_final.json`; exact per-frame outputs under its unique `experiments/results/` folder.
- Durable reservation and consumption records: `data/manifests/pklot_fresh_final_v2.json` and `data/holdout_claims/`.
- Training explanation and Jupyter lesson: `OCCUPANCY_TRAINING_GUIDE.md` and notebook09. The lesson now reads archived training results after the final has been consumed. It does not repeat training or final inference.

All three camera/date groups are now used, including other frames from those dates. We will not tune and test another version on them. Future model improvements need fresh final groups. The saved Excel/CSV can be reopened without repeating evaluation. A byte-identical archive copy is under `reports/occupancy_final_20261026/`.

The next independent fix is to label the app's archived forecasting methods correctly: its later-date report uses a group-relative predictor, while some current display text still says LSTM. The Singapore feed remains aggregate availability data, with its own JSON, CSV and forecast matching; it cannot grade camera recognition.
'''
    p=ROOT/'docs/OCCUPANCY_FINAL_GUIDE.md';assert not p.exists();p.write_text(guide,encoding='utf-8')
    for p in ['docs/OCCUPANCY_TRAINING_GUIDE.md','docs/FRESH_PARKING_DATA_GUIDE.md']:
        append(p,title,'Later final update:the6previously sealed photos are now consumed. Candidate forced errors8->4/336and combined totals improve,but the frozen rainy-view correct-vacancy-retention check fails13/14<95percent. Original app model kept. Earlier sealed statements describe their dated training/development stage. Read [the final-test guide](OCCUPANCY_FINAL_GUIDE.md) and the new Excel report;do not replay the final.')
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as stream:r=csv.DictReader(stream);fields=r.fieldnames;requirements=list(r)
    for item in requirements:
        if item['requirement_id'] in {'CLS-02','CLS-03','OCC-01','APP-02'}:
            item['actual_evidence']+='; models/occupancy_expansion_final.json; reports/occupancy_final_latest.json; docs/OCCUPANCY_FINAL_GUIDE.md'
            item['test_result']+=';one paired final336labels,errors8->4,finalgateFAILrainyretention13/14<95percent;originalappkept;206software tests;Excel/CSVverified'
            item['open_problems']+=';freshfinal3groupsnowCONSUMED,nochanged-methodretest;replacementgatefailed,newfinalsourcesrequired'
    with req.open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);w.writeheader();w.writerows(requirements)
    write(E/'handoff_checks.json',dict(completed_trials=52,scheduled_wakeups_completed=35,no_active_jobs=True,
        original_production_weights_unchanged=True,failed_final_gate_preserved=True,all_new_final_groups_consumed=True,
        consumed_guard_rejected_reopen=guard_note,software_tests_passed=206,notebook_archive_reader_executed=True,
        workbook_formula_and_visual_checks_passed=True,new_source_records=0,source_records=57,next_live_milestone=100,
        final_pixels_or_labels_replayed_after_frozen_evaluation=False))
    print(json.dumps(dict(trials=52,final_gate=False,original_app_kept=True,consumed_final_groups=3,workbook=workbook['workbook']),indent=2))


if __name__=='__main__':main()
