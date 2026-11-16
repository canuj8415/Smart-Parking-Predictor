"""One bounded real training-image numerical lesson and hidden-native app check."""
import csv,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from smart_parking.provenance import digest
from smart_parking.decomposition import image_factors,rank_report,reconstruct,plot_decomposition


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text(encoding='utf-8'))
    if state['active_training_jobs'] or state['active_validation_jobs']:raise RuntimeError('Another job is active')
    started=datetime.now(timezone.utc);run='SVD-LESSON-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False)
    sample=json.loads((ROOT/'configs/demo_sample.json').read_text(encoding='utf-8'))
    assert sample['split']=='train' and digest(ROOT/sample['image'])==sample['image_sha256']
    files=['scripts/validate_svd_lesson.py','src/smart_parking/decomposition.py','src/smart_parking/app.py','tests/test_decomposition.py']
    hashes={p:digest(ROOT/p) for p in files};ranks=[1,8,24,48,96,160]
    protocol=dict(run_id=run,started_at=started.isoformat(),seed=116,source_ids=['SRC-DS-001','SRC-DOC-018'],
        hypothesis='A bounded real-image SVD lesson reconstructs the full teaching matrix numerically, shows decreasing approximation error as rank grows, and reports complete equal-dtype factor storage without implying detector accuracy or JPEG compression.',
        image=sample['image'],image_sha256=sample['image_sha256'],split='Existing training-only demonstration image; no final images/labels',
        sample_config_sha256=digest(ROOT/'configs/demo_sample.json'),source_hashes=hashes,
        teaching_transform='PIL grayscale then bilinear resize256x160, normalize/255, float64; originals unchanged',ranks=ranks,
        gates=['Full-rank maximum error<1e-10','Squared residual agrees with discarded singular-value energy within1e-9',
               'MSE nonincreasing across ranks','Actual U/S/Vh float64 entry storage counted, including expansion',
               'Hidden-native ranks16/48, invalid-rank/busy guards and 2D/3D/SVD chart switching work without accumulating figures'],
        model_training_performed=False,model_accuracy_evaluated=False,
        limitations=['One training image: numerical teaching experiment, not an independent parking benchmark',
                     'Resizing/grayscale discard detail before SVD; no downstream vehicle accuracy measured',
                     'Equal-dtype factor memory is not source JPEG or saved-file compression',
                     'Hidden native widgets, not visible/manual student acceptance'])
    dump(folder/'protocol.json',protocol)
    dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'))];dump(state_path,state);clock=time.perf_counter()
    try:
        with Image.open(ROOT/sample['image']) as source:image=source.convert('RGB')
        factors=image_factors(image);reports=[]
        for rank in ranks:
            if (folder/'CANCEL').exists():raise InterruptedError('Cancellation requested')
            report=rank_report(factors,rank)
            assert abs(report['mse']*factors['input'].size-report['discarded_energy'])<1e-9
            reports.append(report)
        assert reports[-1]['max_absolute_error']<1e-10
        assert all(a['mse']>=b['mse']-1e-14 for a,b in zip(reports,reports[1:]))
        assert reports[-1]['factor_to_original_float64_ratio']>1
        with (folder/'observations.csv').open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(reports[0]));writer.writeheader();writer.writerows(reports)
        fig,axes=plt.subplots(2,3,figsize=(11,6.2))
        for ax,rank,row in zip(axes.flat,ranks,reports):
            ax.imshow(np.clip(reconstruct(factors,rank),0,1),cmap='gray',vmin=0,vmax=1)
            ax.set_title(f'{rank} patterns; MSE {row["mse"]:.5f}\nFactor storage {row["factor_to_original_float64_ratio"]:.1%}');ax.axis('off')
        fig.suptitle('One real training picture: more patterns retain more detail')
        fig.text(.5,.015,'PKLot / Almeida et al., CC BY4.0. Derived grayscale/resized reconstructions. Storage uses equal numeric formats; not JPEG size or accuracy.',ha='center',fontsize=8)
        fig.tight_layout(rect=(0,.04,1,.96));fig.savefig(folder/'rank_comparison.png',dpi=130);plt.close(fig)
        fig,_=plot_decomposition(image,16);fig.savefig(folder/'lesson_view.png',dpi=120);plt.close(fig)
        from smart_parking.app import ParkingApp
        app=ParkingApp();app.withdraw();errors=[];infos=[]
        try:
            app.image=image.copy()
            with patch('smart_parking.app.messagebox.showerror',side_effect=lambda *args:errors.append(args)),patch('smart_parking.app.messagebox.showinfo',side_effect=lambda *args:infos.append(args)):
                app.svd_rank.set('16');app.show_svd();app.update_idletasks();assert app.svd_report['rank']==16
                assert len(plt.get_fignums())==1
                app.svd_rank.set('48');app.show_svd();app.update_idletasks();assert app.svd_report['rank']==48
                assert len(plt.get_fignums())==1
                for value in ['0','161','2.5','bad']:
                    app.svd_rank.set(value);app.show_svd()
                assert len(errors)==4 and app.svd_report['rank']==48
                app.busy=True;app.show_svd();app.busy=False;assert len(infos)==1
                app.show_lab();app.update_idletasks();assert len(plt.get_fignums())==1
                app.svd_rank.set('16');app.show_svd();app.update_idletasks();assert len(plt.get_fignums())==1
                assert 'not JPEG size or detection accuracy' in app.status.get()
            assert np.array_equal(np.asarray(app.image),np.asarray(image))
        finally:app.destroy();plt.close('all')
        assert digest(ROOT/sample['image'])==sample['image_sha256']
        assert all(digest(ROOT/p)==h for p,h in hashes.items())
        metrics=dict(full_rank_max_error=reports[-1]['max_absolute_error'],rank16=rank_report(factors,16),
                     rows=len(reports),hidden_native_checks_passed=True,accumulating_chart_figures=False,
                     scientific_accuracy=None)
        report=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,
                    metrics=metrics,rank_reports=reports,validation_gate_passed=True)
        dump(folder/'run.json',report);dump(ROOT/'models/svd_lesson_validation.json',report)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=run,run_type='Real training-image numerical SVD lesson/native integration',started_at=protocol['started_at'],finished_at=report['finished_at'],
                 source_ids='SRC-DS-001;SRC-DOC-018',split_ids=protocol['split'],configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),
                 architecture='NumPy reduced SVD, no neural model',model_version='No trained model',epochs=0,batch_size=1,random_seed=116,
                 hardware='CPU',execution_environment=sys.version.split()[0],training_duration=report['duration_seconds'],evaluation_metrics=json.dumps(metrics),
                 logs=folder.relative_to(ROOT).as_posix(),checkpoints='No new weights',code_revision_basis='1db3108 plus sealed sources',
                 implementation_sha256=hashes[files[0]],conclusions='Numerical/native teaching gates pass; no model accuracy or JPEG compression claim')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=json.loads(state_path.read_text(encoding='utf-8'));state['completed_run_ids'].append(run)
        state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']));state['last_completed_run']=run
        print(json.dumps(dict(run_id=run,metrics=metrics),indent=2))
    except BaseException as error:
        dump(folder/'interrupted.json',dict(error=str(error),completed_run_counted=False));state=json.loads(state_path.read_text(encoding='utf-8'));raise
    finally:state['active_validation_jobs']=[];dump(state_path,state)


if __name__=='__main__':main()
