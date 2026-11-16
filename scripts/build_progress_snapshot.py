"""Build a dated, source-traceable progress snapshot from saved evidence only."""
import csv,io,json,re,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest


def main():
    now=datetime.now(timezone.utc);folder=ROOT/'reports/progress'/now.strftime('%Y%m%dT%H%M%S%fZ');folder.mkdir(parents=True,exist_ok=False)
    inputs=[]
    def saved(path):
        p=ROOT/path;content=p.read_bytes();copy=folder/'inputs'/path;copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(content)
        inputs.append(dict(origin=path,snapshot=copy.relative_to(ROOT).as_posix(),sha256=digest(copy)))
        return json.loads(content) if p.suffix=='.json' else content.decode('utf-8-sig')
    state=saved('data/automation_state.json');vision=saved('models/vision_model_card.json')
    forecast=saved('models/forecast_final_evaluation.json');region=saved('models/region_stability_final.json')
    dev=saved('models/flow_continuation_development.json');final=saved('models/davis_sequence_final.json')
    live=saved('data/processed/singapore_prospective/summary.json')
    inventory=saved('data/dataset_inventory.json')
    sources=list(csv.DictReader(io.StringIO(saved('data/source_manifest.csv'))))
    experiments=list(csv.DictReader(io.StringIO(saved('experiments/EXPERIMENT_REGISTRY.csv'))))
    test_log='experiments/evidence/HEARTBEAT-20261025T151531Z/unit_tests.txt'
    tests=saved(test_log);match=re.search(r'Ran (\d+) tests',tests)
    if not match or not tests.rstrip().endswith('OK'):raise ValueError('Current software suite has not passed')
    count=int(match.group(1))
    completed=set(state['completed_run_ids']);assert len(completed)==state['completed_recorded_runs_since_schedule']
    assert len(sources)==len({r['source_id'] for r in sources})
    features=[
        dict(feature='Python desktop app',status='Working prototype',result='Images, layouts, saved forecasts, live readings and convolution lessons run locally.',next_action='Finish visible desktop, file-dialog and offline rehearsals.'),
        dict(feature='Real data and attribution',status='Collected and traceable',result='PKLot images, Birmingham records, DAVIS sequences and official Singapore observations have saved source records.',next_action='Use the Sources sheet. Some of the45catalog entries are research candidates, not acquired datasets.'),
        dict(feature='Vehicle detection',status='Works within tested scope',result='Pretrained Faster R-CNN/ResNet50 detects vehicles. One selected final car was matched in70/70frames.',next_action='Obtain fresh, exhaustively labelled traffic evidence for precision/mAP.'),
        dict(feature='Parking-region masks',status='Conditional result',result='Known-camera six-image final overlap is0.910. Two cameras use stored geometry, one uses the CNN.',next_action='Improve image-only/new-camera segmentation using fresh final groups.'),
        dict(feature='Slot occupancy',status='Trained and tested',result='Original classifier correctly labelled343of360held-out parking crops. Wider checks still include false vacancies.',next_action='Validate across more cameras/weather without replacing unknown labels.'),
        dict(feature='Historical availability',status='Candidate beats baseline',result='Frozen later-date candidate error31.72spaces versus39.07for persistence on1853windows.',next_action='Keep historical Birmingham findings separate from Singapore live forecasting.'),
        dict(feature='Vehicle crossing counts',status='More evidence needed',result='Development identity improved53/75to75/75frames. Final identity70/70, but zero labelled crossings prevented a recovery score.',next_action='Acquire fresh labelled positive-crossing sequences. Final DAVIS sequence is consumed; no rerun or promotion.'),
        dict(feature='Live availability feed',status='Public feed integrated',result=f"{live['scores_total']:,}later matched persistence outcomes, average error{live['baseline_mae_spaces']:.3f}spaces as of{live['checked_at']}.",next_action='Collect at the planned cadence. Missing targets remain unscored; this does not measure camera accuracy.'),
        dict(feature='Python/Jupyter learning',status='Seven lessons executed',result='Real data, detector, region/forecast limits, 2D/3D arithmetic, crossing setup and identity lessons are saved.',next_action='Practise explaining the results independently. Student mastery has not been assessed.'),
        dict(feature='Exports and offline use',status='Partly verified',result='Image/video exports and a network-disabled Python process were checked. Saved progress tables are available in the app.',next_action='Complete native save-dialog and physically disconnected/fresh-install tests.'),
        dict(feature='Report and university compliance',status='Unfinished',result='Report draft and14slide presentation exist. University documents, final compilation and rehearsal remain incomplete.',next_action='Finish report/presentation and check the missing official documents when supplied.'),
    ]
    metrics=[]
    def add(check,kind,unit,scope,limitation,source,evidence,*,numerator=None,denominator=None,value=None):
        if kind=='fraction':expected=numerator/denominator if denominator else None
        elif kind=='reduction':expected=(denominator-numerator)/denominator if denominator else None
        else:expected=value
        metrics.append(dict(check=check,kind=kind,numerator=numerator,denominator=denominator,value=expected,unit=unit,
            scope=scope,limitation=limitation,source_ids=source,evidence=evidence))
    cm=vision['classifier_metrics']['confusion_matrix'];correct=sum(cm[i][i] for i in range(len(cm)))
    add('Original occupancy crop accuracy','fraction','Fraction','Original held-out crops','360crops from the original limited camera/date split; not whole-project accuracy.','SRC-DS-001','models/vision_model_card.json',numerator=correct,denominator=vision['classifier_metrics']['samples'])
    add('Conditional parking-region overlap','scalar','IoU','Six later-date known-camera images','Two cameras use geometry only. Not automatic slot identities or pure neural performance.','SRC-DS-001;SRC-MOD-003','models/region_stability_final.json',value=region['final_evaluation']['hybrid']['overall']['pixel_iou'])
    fm=forecast['final_evaluation']['metrics']
    add('Historical candidate error','scalar','Spaces MAE','1853later-date Birmingham windows','Real target readings arrive10.02to29.12minutes later; correlated windows, not Singapore live.','SRC-DS-003','models/forecast_final_evaluation.json',value=fm['candidate_mae_spaces'])
    add('Historical persistence error','scalar','Spaces MAE','Identical1853later-date target rows','Same source/split/horizon as candidate; lower MAE is better.','SRC-DS-003','models/forecast_final_evaluation.json',value=fm['persistence_mae_spaces'])
    add('Historical improvement over persistence','reduction','Fraction','Reduction in MAE on identical targets','One frozen candidate; no claim of transfer to other sources.','SRC-DS-003','models/forecast_final_evaluation.json',numerator=fm['candidate_mae_spaces'],denominator=fm['persistence_mae_spaces'])
    for label,m in [('Original development identity',dev['baseline']['metrics']),('Candidate development identity',dev['metrics'])]:
        total=m['scored_visible_car_frames'];matched=round(m['dominant_track_fraction']*total)
        assert abs(matched/total-m['dominant_track_fraction'])<1e-12
        add(label,'fraction','Fraction','One car across75scored development frames','Reused development footage.75frames are not75independent cars.','SRC-DS-012;SRC-MOD-001','models/flow_continuation_development.json',numerator=matched,denominator=total)
    dm=dev['metrics'];tm=final['metrics']
    add('Development labelled crossing recovery','fraction','Fraction','One selected car, one image-line crossing','Label-assisted five-frame setup and moving camera; not a parking entrance benchmark.','SRC-DS-012;SRC-MOD-001','models/flow_continuation_development.json',numerator=dm['recovered_events'],denominator=dm['reference_events'])
    add('Final selected-car identity coverage','fraction','Fraction','One car across70scored final frames','The original tracker also achieved70/70. No final identity improvement is claimed.','SRC-DS-012;SRC-MOD-001','models/davis_sequence_final.json',numerator=round(tm['dominant_track_fraction']*tm['scored_visible_car_frames']),denominator=tm['scored_visible_car_frames'])
    add('Final labelled crossing recovery','fraction','Fraction','Zero labelled crossings of the frozen line','Not evaluable. Overall final gate failed; entire sequence consumed. One unmatched prediction cannot be graded using partial labels.','SRC-DS-012;SRC-MOD-001','models/davis_sequence_final.json',numerator=tm['recovered_events'],denominator=tm['reference_events'])
    add('Live-source persistence error','scalar','Spaces MAE',f"{live['scores_total']}matched later Singapore outcomes",'Persistence baseline only. Missing targets excluded, no neural/camera accuracy.','SRC-LIVE-001','data/processed/singapore_prospective/summary.json',value=live['baseline_mae_spaces'])
    cov=live['forecast_coverage']
    add('Live target matching coverage','fraction','Fraction','Matched / resolved frozen forecasts','This is data matching coverage, not prediction accuracy. Pending forecasts excluded from denominator.','SRC-LIVE-001','data/processed/singapore_prospective/summary.json',numerator=cov['scored'],denominator=cov['resolved_forecasts'])
    def readable(text):
        text=re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',text)
        return re.sub(r'\b([23]) D\b',r'\1D',text).replace('ResNet 50','ResNet50')
    for row in features:
        for key in ['result','next_action']:row[key]=readable(row[key])
    for row in metrics:
        for key in ['scope','limitation']:row[key]=readable(row[key])
    report=dict(schema_version=1,as_of=now.isoformat(),project_root=str(ROOT),completed_trials=len(completed),software_tests=count,
        features=features,metrics=metrics,sources=sources,experiments=[dict(r,counted_since_automation=r['experiment_id'] in completed) for r in experiments],
        live_as_of=live['checked_at'],live_summary=live,input_snapshots=inputs,
        definitions=dict(project_completion='No aggregate completion percentage is assigned. Each capability has its own evidence and remaining work.',
                         completed_trial='Completed uniquely recorded experiment or validation trial; frames, epochs, routine checks and report authoring are not counted.',
                         final_limit='Final vehicle-crossing gate did not pass; no universal accuracy or deployment claim.'))
    path=folder/'snapshot.json';path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    latest=ROOT/'reports/progress/latest.json';latest.write_text(json.dumps(dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(path)),indent=2)+'\n',encoding='utf-8')
    print(path)


if __name__=='__main__':main()
