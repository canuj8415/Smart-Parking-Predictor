"""Offline display/export of a dated progress snapshot, never model evaluation."""
import csv,json
from datetime import datetime,timezone
from pathlib import Path
from .provenance import ROOT,digest


def load_progress(root=ROOT):
    root=Path(root).resolve();base=(root/'reports/progress').resolve()
    pointer=json.loads((base/'latest.json').read_text(encoding='utf-8'))
    path=(root/pointer['path']).resolve()
    if not path.is_relative_to(base):raise ValueError('Saved progress must stay inside the report folder')
    if digest(path)!=pointer['sha256']:raise ValueError('Saved progress checksum changed')
    report=json.loads(path.read_text(encoding='utf-8'))
    if report.get('schema_version')!=1 or not report.get('features') or not report.get('metrics'):
        raise ValueError('Saved progress report is incomplete')
    if datetime.fromisoformat(report['as_of']).tzinfo is None:raise ValueError('Progress snapshot needs an explicit timezone')
    return report


def progress_text(report):
    lines=['SAVED PROJECT PROGRESS',f"Snapshot: {report['as_of']}",
           'This saved summary does not train a model or refresh live data.',
           f"Recorded trials: {report['completed_trials']} | Software checks: {report['software_tests']}",
           'Working prototype. Final acceptance remains incomplete.','']
    for row in report['features']:
        lines += [f"{row['feature']} — {row['status']}",row['result'],'Next: '+row['next_action'],'']
    lines += ['DATA AND SOURCES','Original data: data/raw/','Prepared observations: data/processed/',
              'Exact trials: experiments/results/','Sources and licence records: data/source_manifest.csv',
              'Per-asset URL/time/checksum receipts: data/resource_receipts.jsonl',
              'Saved experiments include failures. Simulation/software fixtures are not camera accuracy.']
    return '\n'.join(lines)


def _safe_csv(value):
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')):return "'"+value
    return value


def export_progress(parent,report):
    folder=Path(parent)/datetime.now(timezone.utc).strftime('project_progress_%Y%m%dT%H%M%S%fZ')
    folder.mkdir(parents=True,exist_ok=False)
    (folder/'progress.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for key in ['features','metrics','sources','experiments']:
        rows=report.get(key,[])
        if not rows:continue
        columns=list(rows[0])
        with (folder/(key+'.csv')).open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
            writer.writerows({k:_safe_csv(row.get(k)) for k in columns} for row in rows)
    files={p.name:digest(p) for p in folder.iterdir() if p.is_file()}
    (folder/'export_metadata.json').write_text(json.dumps(dict(snapshot_as_of=report['as_of'],
        scope='Dated archived progress only; no model inference or live refresh',files=files),indent=2)+'\n',encoding='utf-8')
    return folder
