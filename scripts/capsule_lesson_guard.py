"""Python project-file boundary for a relocated read-only lesson;not OS isolation."""
import atexit,json,os,sys
from pathlib import Path


def path_decision(path,writing,root,scratch,blocked_project=None):
    if isinstance(path,int) or path is None:return None
    path=Path(os.fsdecode(path)).resolve();root=Path(root).resolve();scratch=Path(scratch).resolve()
    if path.is_relative_to(scratch):return None
    if path.is_relative_to(root):
        relative=path.relative_to(root);parts=relative.parts
        if writing:return 'Capsule payload is read-only;use execution scratch'
        if len(parts)>1 and parts[0]=='data' and parts[1] in ['raw','processed','receipts','singapore_forecast_holdout_claims']:
            return 'Raw,operational observations and final claims are outside lesson scope'
        if len(parts)>1 and parts[0]=='models' and parts[1] in ['checkpoints','pretrained']:
            return 'Model weights are outside lesson scope'
        if len(parts)>2 and parts[:2]==('experiments','results') and parts[2].startswith('SG-FINAL-'):
            return 'Real final-result reads are outside this capsule'
        return None
    if blocked_project is not None and path.is_relative_to(Path(blocked_project).resolve()):
        return 'Original-project fallback is blocked'
    return None  # External Python/runtime libraries remain available.


def install(root,scratch,report_path,blocked_project=None):
    root=Path(root).resolve();scratch=Path(scratch).resolve();reads=set();denied=[]
    def check(path,writing,event):
        reason=path_decision(path,writing,root,scratch,blocked_project)
        if reason:
            denied.append(dict(event=event,path=str(path),writing=writing,reason=reason));raise PermissionError(reason)
        if not writing and isinstance(path,(str,bytes,os.PathLike)):
            resolved=Path(os.fsdecode(path)).resolve()
            if resolved.is_relative_to(root):reads.add(resolved.relative_to(root).as_posix())
    def audit(event,args):
        if event=='open':
            mode,flags=args[1],args[2];writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            check(args[0],writing,event)
        elif event in ['os.listdir','os.scandir']:check(args[0],False,event)
        elif event in ['os.remove','os.rmdir','os.mkdir']:check(args[0],True,event)
        elif event=='os.rename':check(args[0],True,event);check(args[1],True,event)
    sys.addaudithook(audit)
    def save():
        Path(report_path).write_text(json.dumps(dict(project_reads=sorted(reads),denied=denied,pid=os.getpid(),
            blocked_original_project=str(blocked_project) if blocked_project else None,
            scope='Python project-file audit only;external runtime files/native extensions are not OS-isolated'),indent=2)+'\n',encoding='utf-8')
    atexit.register(save);return save
