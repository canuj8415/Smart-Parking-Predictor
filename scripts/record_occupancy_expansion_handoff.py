"""Save expansion training, real-engine validation and the next final-test step."""
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime,timedelta,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.holdouts import assert_holdout_closed
from smart_parking.live import get_live,URL,_observation_key

E=ROOT/'experiments/evidence/HEARTBEAT-20261026T011741Z'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,value):
    p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def append(p,title,text):
    p=ROOT/p;old=p.read_text(encoding='utf-8');assert title not in old
    p.write_text(old.rstrip()+'\n\n'+title+'\n\n'+text+'\n',encoding='utf-8')


def main():
    assert not (E/'handoff_checks.json').exists()
    state=read('data/automation_state.json');data=read('models/occupancy_expansion_data_card.json')
    train=read('models/occupancy_expansion_candidate.json');fusion=read('models/occupancy_expansion_fusion_candidate.json')
    assert state['completed_recorded_runs_since_schedule']==len(set(state['completed_run_ids']))==51
    assert state['scheduled_wakeups_completed']==33
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    assert train['validation_gate_passed'] and fusion['validation_gate_passed']
    assert train['final_images_or_labels_read']==fusion['final_images_or_labels_read']==0
    assert all(digest(ROOT/p)==h for card in [data,train,fusion] for p,h in card['source_hashes'].items())
    assert digest(ROOT/train['candidate_checkpoint'])==train['candidate_checkpoint_sha256']
    original=read('experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json')
    assert all(digest(ROOT/p)==h for p,h in original.items())
    final=ROOT/'data/manifests/pklot_fresh_final_v2.json'
    assert_holdout_closed(final,root=ROOT)
    assert digest(final)==train['closed_final_manifest_sha256']==fusion['closed_final_manifest_sha256']
    unchanged=[]
    for path in list((ROOT/'notebooks').glob('0[1-8]*.ipynb'))+list((ROOT/'data/holdout_claims').glob('*.json')):
        relative=path.relative_to(ROOT).as_posix()
        result=subprocess.run(['git','show','HEAD:'+relative],capture_output=True,check=True)
        raw=path.read_bytes()
        if result.stdout!=raw:
            assert relative=='notebooks/01_real_data_audit.ipynb'
            assert result.stdout.replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n')
            assert json.loads(result.stdout)==json.loads(raw)
            mode='JSON/source/output equal; observed working CRLF versus GitLF, bytes left untouched'
        else:mode='byte equal'
        unchanged.append(dict(path=relative,comparison=mode,working_sha256=digest(path),
            git_head_sha256=hashlib.sha256(result.stdout).hexdigest()))
    regressions=read(E/'regressions.json');lesson=read(E/'notebook_execution.json')
    assert regressions['tests_run']==197 and regressions['success']
    assert lesson['actual_jupyter_kernel'] and lesson['errors']==0 and lesson['inline_png_outputs']==1
    assert digest(ROOT/lesson['notebook'])==lesson['sha256']
    rows,meta=get_live(refresh=False);raw_path=Path(meta['path']);raw=read(raw_path)
    live=read('data/processed/singapore_prospective/summary.json');assert Path(live['snapshot_path'])==raw_path
    records=[json.loads(line) for line in (ROOT/'data/resource_receipts.jsonl').read_text(encoding='utf-8').splitlines()]
    receipt=next(r for r in reversed(records) if r['local_path']==raw_path.relative_to(ROOT).as_posix())
    assert receipt['source_url']==URL and receipt['sha256']==digest(raw_path)
    with (ROOT/'data/processed/singapore_live_observations.csv').open(encoding='utf-8',newline='') as stream:history=list(csv.DictReader(stream))
    keys=[_observation_key(r['car_park_id'],r['lot_type'],r['observed_at']) for r in history]
    assert len(keys)==len(set(keys)) and all(0<=r['available']<=r['capacity'] and r['capacity']>0 for r in rows)
    with (ROOT/'data/source_manifest.csv').open(encoding='utf-8-sig',newline='') as stream:assert len(list(csv.DictReader(stream)))==57
    snapshot_count=len(list(raw_path.parent.glob('*.json')))
    live_evidence=dict(**live,snapshot_count=snapshot_count,raw_sha256=digest(raw_path),source_url=URL,
        acquisition_receipt=receipt,valid_rows=len(rows),car_parks=len({r['car_park_id'] for r in rows}),
        history_duplicates=0,cached_app_route_passed=meta['cached'],scheduled_100_run_checkpoint=False,
        raw_lot_records=sum(len(p['carpark_info']) for item in raw['items'] for p in item['carpark_data']),
        scope='Prospective Singapore persistence only; not trained neural or camera accuracy')
    write(E/'live_checkpoint.json',live_evidence)
    brief=dict(training_run=train['run_id'],data_qualification_run=data['run_id'],fusion_run=fusion['run_id'],
        train_frames=170,validation_frames=45,training_crops=10104,validation_crops=2028,
        excluded_unknown_labels=1100,epochs_completed=train['epochs_completed'],selected_epoch=train['selected_epoch'],
        baseline=train['baseline']['overall'],candidate=train['candidate']['overall'],
        fresh12_baseline=train['fresh12_baseline'],fresh12_candidate=train['fresh12_candidate'],
        fusion={d:c['overall'] for d,c in fusion['detectors'].items()},
        classifier_development_gate_passed=True,fusion_development_gate_passed=True,
        candidate_checkpoint=train['candidate_checkpoint'],candidate_checkpoint_sha256=train['candidate_checkpoint_sha256'],
        final_images_or_labels_read=0,production_promoted=False,
        guide='docs/OCCUPANCY_TRAINING_GUIDE.md',notebook=lesson['notebook'])
    write('reports/occupancy_training_latest.json',brief)
    inventory=read('data/dataset_inventory.json');inventory['inventoried_at']=datetime.now(timezone.utc).isoformat()
    inventory['occupancy_expansion']=dict(data_qualification=data['summary'],training_result=brief)
    for item in inventory['datasets']:
        if item['source_id']=='SRC-DS-001':item['occupancy_expansion']=brief
        if item['source_id']=='SRC-LIVE-001':
            item.update(car_parks=live_evidence['car_parks'],observations=len(rows),provider_timestamp=meta['provider_timestamp'],
                raw_path=raw_path.relative_to(ROOT).as_posix(),snapshot_count=snapshot_count,
                prospective_baseline_scored_outcomes=live['scores_total'],prospective_baseline_mae_spaces=live['baseline_mae_spaces'],
                forecast_target_coverage=live['forecast_coverage'])
    write('data/dataset_inventory.json',inventory)
    next_poll=(datetime.fromisoformat(live['checked_at'])+timedelta(minutes=30)).isoformat()
    state.update(scheduled_wakeups_completed=34,last_updated_at=datetime.now(timezone.utc).isoformat(),
        occupancy_expansion=brief,last_live_baseline_score=dict(outcomes=live['scores_total'],mae_spaces=live['baseline_mae_spaces'],
            scope='Persistence only; no neural/camera accuracy',coverage=live['forecast_coverage']))
    state['next_actions']=[
        'Next freeze ONE paired original-versus-expanded-head final protocol on the6reserved PKLot photos/3whole camera-date groups. Bind both checkpoint hashes, both detector configs, geometry assumptions, original/candidate predictions and prespecified nonregression gates. Use holdouts.evaluate_final_once to durably claim the entire reserved groups BEFORE any pixels/XML labels are read. Do not spend final on a baseline-only or repeated study.',
        'Expanded candidate passes classifier gates on2028development labels and both actual detector-fusion gates on720fresh-development labels. Original classifier46->12harderrors;fresh17->6. Candidate combined Faster99correctvacants/0falsevacants/2falseoccupied/14uncertain;Mask100/0/2/13. These are development results, not final/live accuracy; no production promotion yet.',
        'Preserve best epoch2/full candidate checkpoint, last head/optimizer/RNG,215feature chunks,all curves and fixed source/date manifests. Training stopped after8epochs. Original3production checkpoints,core vision/tracker and notebooks01-08unchanged. No overlapping jobs. Notebook09actual kernel6codecells/1PNG/zeroerrors; no student mastery assumed.',
        'All earlier image/Birmingham/DAVIS final groups remain consumed. CNR144965metadata records qualified but image-content rights unqualified;32079reserved CNR images unopened. Final PKLot6remain closed/unclaimed;171source frames reserved in full. Extra data has704train+396validation unknown labels excluded,not labelled vacant; encoded-duplicate audit only.',
        f'Counter51; next separate100-run checkpoint100. OfficialSingapore{live["checked_at"]}:39snapshots,{live["scores_total"]}matched baseline outcomes,MAE{live["baseline_mae_spaces"]:.6f}spaces. Next sensible collection after{next_poll}; minimum1minute. Missing target windows unscored. Copied offline demo remains an older snapshot.',
        '197full software tests pass. Continue final evidence,then scoped app candidate integration if qualified; physical/new-machine offline,visible browser/manual,student rehearsal/mastery and official university-doc acceptance remain. Keep source57/430new local-copy receipts; no new image network downloads.'
    ]
    write('data/automation_state.json',state)
    title='## 26 October 2026 / expanded occupancy training and real-engine development checks'
    note='Expanded frozen-ResNet18head trained on10,104explicit crops from170photos/32previously designated training dates,including958third-camera examples absent from the original classifier training. Validation45photos/12dates/2028labels kept globally separate;704training+396validation unknown labels excluded. All old/new final dates excluded;430source JPEG/XMLfiles copied locally with member/archive/source/checksum receipts,not network downloads. Camera/class-balanced AdamW warm-start head only; early stopping after8epochs selected epoch2 by prespecified macro-camera validation loss. Original classifier46/2028harderrors versus candidate12/2028(99.4083%development),confident false-vacants6->4,correct vacancies622->665,uncertain33->19;fresh720harderrors17->6. All preset classifier gates pass. Actual app engines with experiment-local candidate weights pass both detector development gates: Faster99correctvacancies/0wrongvacant/2wrongoccupied/14uncertain,Mask100/0/2/13;720labels,supplied geometry,2known cameras/3dates,not automatic space segmentation or final/live accuracy. No production promotion. Original3production weights,existing image-final claims and notebooks01-08unchanged. Best/full candidate,last optimizer/RNG and215feature chunks preserved;candidate checkpoint roundtrip passed.197full software tests pass. New pinned notebook09executes6codecells with one real inline learning-curve PNG and zero errors. Initial test import-path and notebook missing-pandas failures preserved;fixed using existing packages,no installation. Three completed distinct trials advance48->51(dataqualification,headtraining,pairedfusion),not perphoto/epoch. Latest officialSingapore39snapshots adds1048matched later baseline outcomes,32762total,MAE4.746963spaces;1316newforecasts frozen. Final6PKLotphotos remain closed/unclaimed. Next:one frozen paired original/candidate final protocol and durable claim before any final decoding. Physical/manual/browser/student/official acceptance remain incomplete.'
    for path in ['docs/PROJECT_PROGRESS.md','docs/AUTONOMOUS_PROGRESS.md','docs/IMPLEMENTATION_STATUS.md','docs/TEST_RESULTS.md','docs/AI_ASSISTANCE_LOG.md']:
        append(path,title,note)
    append('docs/DATASET_PROVENANCE.md',title,'SRC-DS-001:430unchanged selected JPEG/XMLlocal archive-member copies with exact per-copy event bounds and logging receipts;170train/45validationframes,32/12globally separate dates. No network image acquisition,final decode or unknown-to-vacant relabel. Original byte duplicates across selected dates and train aliases of known protected/development dates rejected. Perceptual duplicates not audited. SRC-MOD-003original frozen features retained;class weights from training-only camera/class counts. No new sources;57catalog records. Live immutable raw JSON/receipt/normalized CSV and same-source prospective matching remain separate from image labels.')
    append('docs/UI_TEST_LOG.md',title,'Both actual VisionEngine.analyze detector routes exercised with experiment-local candidate classifier/provenance. Main app constructor/default checkpoint unchanged. Actual Jupyter notebook09tables/inline plot executed;no visible browser/manual/student UI rehearsal. Cached live route matched new saved JSON.')
    guide='''# What the extra training achieved

Imagine an attendant who learned from two parking-camera views. We now gave that attendant labelled practice photos from a third view too. We trained a separate candidate, while keeping the original app model intact.

| Data | Photos | Separate dates | Labelled spaces | Missing answers excluded |
|---|---:|---:|---:|---:|
| Training: practice with answers | 170 | 32 | 10,104 | 704 |
| Validation: choose and check the model | 45 | 12 | 2,028 | 396 |
| Final test: sealed exam | 6 | 3 camera/date groups | Still unknown | Not read |

Dates stay in one role. Different spaces in one photo and repeated photos of the same car park are related observations, not thousands of independent scenes. Missing labels never mean “empty.” All three camera views appear in training and validation.

The ResNet image features stayed fixed. Only its small final decision layer learned new weights. Training stopped after eight passes through the training data; the second pass performed best on validation. Continuing to reduce training loss made validation loss worse, which suggests overfitting. We kept the earlier checkpoint.

| Classifier on the same 2,028 validation spaces | Original | Candidate |
|---|---:|---:|
| Wrong forced yes/no answers | 46 | 12 |
| Forced yes/no accuracy | 97.73% | 99.41% |
| Confident wrong “empty” answers | 6 | 4 |
| Correct confident “empty” answers | 622 | 665 |
| Confident wrong “occupied” answers | 29 | 5 |
| Needs review | 33 | 19 |

Forced yes/no accuracy and review-band counts are different ways of examining the same predictions; do not add their counts together. On the smaller, recently selected 720-example development set, forced mistakes fell from 17 to 6. These are development results used to select the candidate, not its final-test accuracy.

We then loaded the candidate into the actual app engines for the same 12 development photos. The detector can flag a disagreement with the space classifier for review. Known slot geometry was supplied; this check does not prove automatic parking-space segmentation.

| Combined pipeline: 720 development spaces | Correct empty | Wrong empty | Wrong occupied | Needs review |
|---|---:|---:|---:|---:|
| Original + Faster R-CNN | 88 | 0 | 10 | 16 |
| Candidate + Faster R-CNN | 99 | 0 | 2 | 14 |
| Original + Mask R-CNN | 87 | 1 | 10 | 16 |
| Candidate + Mask R-CNN | 100 | 0 | 2 | 13 |

No wrong “empty” answers were observed in the candidate's combined check on these development photos. Other errors and review answers remain. This is not a promise about the next driver, another camera or live operation.

The candidate passed the checks fixed before training and before the combined evaluation. **It has not replaced the app model.** Next comes one frozen paired comparison with the six sealed final photos. Their pixels and answer labels remain unopened. A failed final evaluation would still consume those dates.

## Where the real data and results are

| Item | Saved location |
|---|---|
| Original licensed PKLot archive | `data/raw/pklot_subset/PKLot.tar.gz` |
| Selected training/validation JPEG/XML copies | `data/raw/pklot_occupancy_expansion_v1/` |
| Exact files, dates, roles, hashes and label counts | `data/manifests/occupancy_expansion_v1.json` |
| Source creator, URLs, terms and receipts | `data/source_manifest.csv`; `data/resource_receipts.jsonl`; `docs/THIRD_PARTY_SOURCES.md` |
| Data qualification | `models/occupancy_expansion_data_card.json` |
| Training, epoch curves, checkpoint and validation details | `models/occupancy_expansion_candidate.json`; its unique `experiments/results/` folder |
| Combined detector check | `models/occupancy_expansion_fusion_candidate.json` |
| Easy summary | `reports/occupancy_training_latest.json` |
| Executed Python/Jupyter lesson | `notebooks/09_occupancy_training_and_tradeoffs.ipynb` |

Open lesson09 to see the real learning curves, comparison tables, remaining errors and questions to practise explaining. It reads saved results rather than training again. No student answers or understanding have been assumed.

The Singapore live feed has its own raw JSON snapshots, normalized CSV history and later-observation forecast scores. It cannot grade camera detections or these occupancy labels. The existing Excel/PDF/slides and copied offline demonstration remain dated earlier snapshots.
'''
    path=ROOT/'docs/OCCUPANCY_TRAINING_GUIDE.md';assert not path.exists();path.write_text(guide,encoding='utf-8')
    append('docs/FRESH_PARKING_DATA_GUIDE.md',title,'A separate expanded head now passes development classifier and both actual detector-fusion gates. On720development labels,combined candidate Faster finds99correctempty/0wrongempty/2wrongoccupied/14uncertain;Mask100/0/2/13. Final6remain unopened,original app model unchanged. Read [the new plain-language training guide](OCCUPANCY_TRAINING_GUIDE.md) and notebook09for the full before/after tables and limits.')
    req=ROOT/'docs/REQUIREMENTS.csv'
    with req.open(encoding='utf-8-sig',newline='') as stream:r=csv.DictReader(stream);fields=r.fieldnames;requirements=list(r)
    for item in requirements:
        if item['requirement_id'] in {'CLS-02','CLS-03','OCC-01','DATA-02'}:
            item['actual_evidence']+='; models/occupancy_expansion_data_card.json; models/occupancy_expansion_candidate.json; models/occupancy_expansion_fusion_candidate.json; notebook09'
            item['test_result']+='; expanded head2028DEVELOPMENTharderrors46->12;combined720Faster99/0wrongempty/2wrongoccupied/14uncertain,Mask100/0/2/13;197software tests; final6closed,no app promotion'
            item['open_problems']+=';one frozen paired final still pending;known-camera/date-correlated/supplied-geometry scope; no live camera accuracy'
    with req.open('w',encoding='utf-8',newline='') as stream:w=csv.DictWriter(stream,fieldnames=fields,quoting=csv.QUOTE_ALL);w.writeheader();w.writerows(requirements)
    write(E/'handoff_checks.json',dict(completed_trials=51,wakeups_completed=34,no_active_jobs=True,
        classifier_and_both_fusion_development_gates_passed=True,production_promoted=False,
        final_pixels_or_labels_read=0,final_group_guard_passed=True,original_weights_and_tracked_artifacts_unchanged=unchanged,
        full_software_tests_passed=197,new_sources=0,source_records=57,local_archive_members_copied=430,
        next_100_run_live_checkpoint=100,latest_live_snapshots=snapshot_count,notebook_actual_kernel_executed=True,
        initial_handoff_check_failure='Strict byte comparison found notebook01workingCRLFversusGitLF; verified exact normalized bytes and parsed JSON equality,kept file bytes untouched. Other7originalnotebooks and finalclaimfiles byte-equal. No scientific/model check failure.'))
    print(json.dumps(dict(trials=51,training_run=train['run_id'],classifier_errors=[46,12],fusion_gates=True,
        final_closed=True,production_promoted=False),indent=2))


if __name__=='__main__':main()
