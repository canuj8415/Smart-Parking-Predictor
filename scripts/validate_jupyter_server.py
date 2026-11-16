"""Bounded authenticated localhost JupyterLab/REST/WebSocket acceptance.

No visible browser automation; no final-data scoring; token stays in memory and
ignored local logs only. Existing isolated Jupyter installation is reused.
"""
import base64,csv,hashlib,json,os,runpy,secrets,socket,subprocess,sys,time,urllib.error,urllib.request,uuid
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def server(folder,port):
    from offline_jupyter_guard import install
    install(folder/'server_network.json',loopback=True)
    sys.argv=[str(ROOT/'scripts/start_jupyter.py'),'--no-browser','--offline','--port',str(port),
        '--notebook','08_image_patterns_and_svd.ipynb','--state-dir',str(ROOT/'outputs/server_checks'/folder.name/'state')]
    runpy.run_path(str(ROOT/'scripts/start_jupyter.py'),run_name='__main__')

def main():
    if len(sys.argv)>1 and sys.argv[1]=='--server':server(Path(sys.argv[2]),int(sys.argv[3]));return
    started=datetime.now(timezone.utc);run='JUPYTER-SERVER-'+started.strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True,exist_ok=False)
    state_path=ROOT/'data/automation_state.json';state=json.loads(state_path.read_text(encoding='utf-8'))
    assert not state['active_training_jobs'] and not state['active_validation_jobs']
    pointer=json.loads((ROOT/'reports/offline_jupyter_latest.json').read_text(encoding='utf-8'));python=ROOT/pointer['python']
    local=ROOT/'outputs/server_checks'/run;local.mkdir(parents=True,exist_ok=False)
    files=['scripts/validate_jupyter_server.py','scripts/start_jupyter.py','scripts/execute_notebook.py','scripts/offline_jupyter_guard.py',
        'notebooks/08_image_patterns_and_svd.ipynb','configs/demo_sample.json']
    hashes={p:sha(ROOT/p) for p in files}
    production=json.loads((ROOT/'experiments/evidence/HEARTBEAT-20261025T110727Z/production_unchanged.json').read_text(encoding='utf-8'))
    protected={p:sha(ROOT/p) for group in ['holdout_claims','forecast_holdout_claims','sequence_holdout_claims'] for file in (ROOT/'data'/group).rglob('*.json') for p in [file.relative_to(ROOT).as_posix()]}
    protected.update(production)
    # Ephemeral port reservation is advisory; a bind race must fail honestly.
    with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    protocol=dict(run_id=run,started_at=started.isoformat(),seed=122,source_ids=['SRC-PKG-004','SRC-PKG-003','SRC-DS-001'],
        hypothesis='The selected offline Jupyter environment serves local Lab/assets/notebook content and executes a fresh authenticated WebSocket kernel using the project interpreter.',
        source_hashes=hashes,protected_hashes=protected,python=pointer['python'],parent_installation_run=pointer['run_id'],port=port,
        gates=['Authenticated Lab HTML and local JavaScript asset200','Anonymous kernel API rejected','Project kernelspec points to selected interpreter',
            'Notebook source available through Contents API unchanged','Server-created kernel executes training-only SVD/2D/3D and returns inline PNG',
            'No non-loopback Python socket attempts','Kernel and owned server stopped; original files/weights/claims unchanged'],
        limitations=['No visible browser interaction or frontend JavaScript execution','Existing base Python/OS/assets reused',
            'Python audit layer is not an OS firewall; native ZeroMQ outside its coverage','No accuracy scoring or training'])
    dump(folder/'protocol.json',protocol);dump(folder/'implementation_sources.json',{p:dict(sha256=h,source=(ROOT/p).read_text(encoding='utf-8')) for p,h in hashes.items()})
    state['active_validation_jobs']=[dict(run_id=run,cancel_file=str(folder/'CANCEL'))];dump(state_path,state)
    token=secrets.token_hex(32);env=os.environ.copy();env.update(JUPYTER_TOKEN=token,JUPYTER_PLATFORM_DIRS='1',
        OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',NO_PROXY='127.0.0.1,localhost,::1',no_proxy='127.0.0.1,localhost,::1')
    base=f'http://127.0.0.1:{port}';process=None;kid=None;connection=None;checks={};failure=None;clock=time.perf_counter()
    def request(path,method='GET',data=None,auth=True):
        headers={'Authorization':'token '+token} if auth else {}
        if data is not None:headers['Content-Type']='application/json'
        req=urllib.request.Request(base+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers=headers)
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=15) as response:
            return response.status,response.read(12000001),response.headers.get('Content-Type','')
    try:
        with (local/'server_stdout.txt').open('w',encoding='utf-8') as out,(local/'server_stderr.txt').open('w',encoding='utf-8') as err:
            process=subprocess.Popen([str(python),'-I',str(Path(__file__).resolve()),'--server',str(folder),str(port)],cwd=ROOT,env=env,stdout=out,stderr=err)
            deadline=time.monotonic()+90
            while True:
                if process.poll() is not None:raise RuntimeError('Owned Jupyter server exited before readiness')
                if time.monotonic()>deadline or (folder/'CANCEL').exists():raise TimeoutError('Readiness deadline/cancellation')
                try:status,body,_=request('/api/kernelspecs');break
                except (urllib.error.URLError,TimeoutError):time.sleep(.4)
            specs=json.loads(body);spec=specs['kernelspecs']['smart-parking-python']['spec'];assert Path(spec['argv'][0]).resolve()==python.resolve()
            checks['selected_kernel']=dict(name='smart-parking-python',python=spec['argv'][0],correct=True)
            try:request('/api/kernelspecs',auth=False);raise AssertionError('Anonymous kernel API unexpectedly accepted')
            except urllib.error.HTTPError as error:assert error.code in (401,403);checks['anonymous_rejected']=error.code
            status,html,_=request('/lab/tree/notebooks/08_image_patterns_and_svd.ipynb');assert status==200 and b'jupyter-config-data' in html
            import re
            assets=re.findall(rb'<script[^>]+src="([^"]+\.js[^"]*)"',html)
            asset=next(a.decode() for a in assets if a.startswith(b'/static/lab/'))
            status,javascript,ctype=request(asset);assert status==200 and len(javascript)>100
            checks['lab']=dict(html_status=200,html_bytes=len(html),javascript_status=status,javascript_bytes=len(javascript),asset_path=asset,
                javascript_sha256=hashlib.sha256(javascript).hexdigest(),frontend_javascript_executed=False)
            status,body,_=request('/api/contents/notebooks/08_image_patterns_and_svd.ipynb?content=1')
            notebook=json.loads(body)['content'];original=json.loads((ROOT/'notebooks/08_image_patterns_and_svd.ipynb').read_text(encoding='utf-8'))
            assert len(notebook['cells'])==len(original['cells']) and all(a['source']==''.join(b['source']) if isinstance(b['source'],list) else a['source']==b['source'] for a,b in zip(notebook['cells'],original['cells']))
            checks['notebook_content']=dict(status=status,source_cells_match=True,original_sha256=hashes['notebooks/08_image_patterns_and_svd.ipynb'])
            status,body,_=request('/api/kernels','POST',dict(name='smart-parking-python',path=''));assert status==201;kid=json.loads(body)['id']
            # Startup hook covers user-code Python sockets in server-launched kernel.
            # Install directly in the first cell before any project/network use.
            import websocket
            session=uuid.uuid4().hex;msg=uuid.uuid4().hex
            connection=websocket.create_connection(f'ws://127.0.0.1:{port}/api/kernels/{kid}/channels?session_id={session}',
                header=['Authorization: token '+token],origin=base,timeout=10,http_no_proxy=['127.0.0.1','localhost'])
            code="""import sys,json,hashlib
from pathlib import Path
assert Path(sys.executable).resolve()==Path(EXPECTED_PYTHON).resolve()
sys.path.insert(0,str(Path.cwd()/'scripts'))
from offline_jupyter_guard import install
_save=install(AUDIT_PATH,loopback=True)
%matplotlib inline
import numpy as np,torch,cv2
assert all(Path(m.__file__).is_relative_to(Path(sys.prefix)) for m in [np,torch,cv2])
from PIL import Image
sys.path.insert(0,str(Path.cwd()/'src'))
from smart_parking.decomposition import image_factors,rank_report,plot_decomposition
from smart_parking.convolution import convolution_demo
sample=json.loads((Path.cwd()/'configs/demo_sample.json').read_text(encoding='utf-8'));assert sample['split']=='train'
image_path=Path.cwd()/sample['image'];assert hashlib.sha256(image_path.read_bytes()).hexdigest()==sample['image_sha256']
image=Image.open(image_path).convert('RGB');factors=image_factors(image);r=rank_report(factors,16)
conv=convolution_demo(image);assert conv['max_2d_error']<1e-5 and conv['max_3d_error']<1e-5
import matplotlib.pyplot as plt
fig,report=plot_decomposition(image,16);plt.show()
print('SERVER_CHECK:'+json.dumps(dict(python=sys.executable,rank16_mse=r['mse'],max_2d_error=conv['max_2d_error'],max_3d_error=conv['max_3d_error'],scope='Training-only compatibility; no accuracy')))
_save()
""".replace('EXPECTED_PYTHON',repr(str(python))).replace('AUDIT_PATH',repr(str(folder/'kernel_network.json')))
            dump(folder/'executed_cell.json',dict(source=code,sha256=hashlib.sha256(code.encode()).hexdigest(),split='train'))
            message=dict(header=dict(msg_id=msg,username='local-validation',session=session,msg_type='execute_request',version='5.3',date=datetime.now(timezone.utc).isoformat()),
                parent_header={},metadata={},channel='shell',content=dict(code=code,silent=False,store_history=False,user_expressions={},allow_stdin=False,stop_on_error=True),buffers=[])
            connection.send(json.dumps(message));reply=False;idle=False;outputs=[];deadline=time.monotonic()+180
            while not (reply and idle):
                if time.monotonic()>deadline or (folder/'CANCEL').exists():raise TimeoutError('Kernel deadline/cancellation')
                try:raw=connection.recv()
                except websocket.WebSocketTimeoutException:continue
                if not isinstance(raw,str):raise ValueError('Unexpected binary websocket protocol')
                event=json.loads(raw)
                if event.get('parent_header',{}).get('msg_id')!=msg:continue
                kind=event['header']['msg_type'];content=event['content']
                if kind=='execute_reply':assert content['status']=='ok';reply=True
                elif kind=='status' and content['execution_state']=='idle':idle=True
                elif kind in ('stream','display_data','execute_result','error'):
                    outputs.append(dict(type=kind,content=content));assert kind!='error',str(content)
            connection.close();connection=None
            png=next(o['content']['data']['image/png'] for o in outputs if 'image/png' in o['content'].get('data',{}))
            picture=folder/'server_inline.png';picture.write_bytes(base64.b64decode(png))
            metrics=json.loads(next(o['content']['text'].split('SERVER_CHECK:',1)[1].strip() for o in outputs if o['type']=='stream' and 'SERVER_CHECK:' in o['content']['text']))
            checks['websocket_kernel']=dict(status='passed',execute_reply_ok=reply,iopub_idle=idle,metrics=metrics,inline_png_sha256=sha(picture))
            dump(folder/'cell_outputs.json',outputs)
            assert request('/api/kernels/'+kid,'DELETE')[0]==204;kid=None
            assert request('/api/shutdown','POST',{})[0]==200
            process.wait(timeout=30);checks['shutdown']=dict(server_returncode=process.returncode,kernel_deleted=True)
    except Exception as error:failure=type(error).__name__+': '+str(error).replace(token,'[REDACTED]')
    finally:
        if connection is not None:connection.close()
        if process is not None and process.poll() is None:
            try:
                if kid:request('/api/kernels/'+kid,'DELETE')
                request('/api/shutdown','POST',{});process.wait(timeout=15)
            except Exception:
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,timeout=20);process.wait(timeout=20)
        logs={name:(local/name).read_text(encoding='utf-8',errors='replace').replace(token,'[REDACTED]') for name in ['server_stdout.txt','server_stderr.txt'] if (local/name).exists()}
        dump(folder/'redacted_server_logs.json',logs)
        networks={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in folder.glob('*_network.json')}
        unchanged=all(sha(ROOT/p)==h for p,h in {**hashes,**protected}.items())
        accepted=failure is None and unchanged and len(networks)==2 and all(not v['denied'] for v in networks.values()) and process.returncode==0
        result=dict(protocol,finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.perf_counter()-clock,checks=checks,
            failure=failure,network_audits=networks,original_assets_and_claims_unchanged=unchanged,local_server_gate_passed=accepted,
            owned_server_stopped=process is not None and process.poll() is not None)
        dump(folder/'run.json',result);dump(ROOT/'models/jupyter_server_acceptance.json',result)
        registry=ROOT/'experiments/EXPERIMENT_REGISTRY.csv'
        with registry.open(encoding='utf-8-sig',newline='') as stream:fields=csv.DictReader(stream).fieldnames
        row=dict(experiment_id=run,run_type='Local JupyterLab authenticated server and websocket kernel acceptance',started_at=protocol['started_at'],finished_at=result['finished_at'],source_ids=';'.join(protocol['source_ids']),
            split_ids='Training-only image; numeric3D fixture; no raw final groups',configuration=(folder/'protocol.json').relative_to(ROOT).as_posix(),architecture='Existing isolated Jupyter venv; server/REST/websocket',
            epochs=0,batch_size=1,random_seed=122,hardware='CPU; Windows; existing base Python',execution_environment=sys.version.split()[0],training_duration=result['duration_seconds'],
            evaluation_metrics=json.dumps(dict(local_server_gate_passed=accepted,failure=failure)),logs=folder.relative_to(ROOT).as_posix(),checkpoints='Original weights unchanged; no training',
            code_revision_basis='5bc812c plus sealed source snapshots',implementation_sha256=hashes[files[0]],conclusions='Server gate='+str(accepted)+'; no visible frontend/manual/physical/new-machine or accuracy claim')
        with registry.open('a',encoding='utf-8',newline='') as stream:csv.DictWriter(stream,fieldnames=fields).writerow({k:row.get(k,'') for k in fields})
        state=json.loads(state_path.read_text(encoding='utf-8'));state['completed_run_ids'].append(run);state['completed_recorded_runs_since_schedule']=len(set(state['completed_run_ids']))
        state['last_completed_run']=run;state['active_validation_jobs']=[];dump(state_path,state)
        print(json.dumps(dict(run_id=run,gate_passed=accepted,failure=failure,checks=checks),indent=2))

if __name__=='__main__':main()
