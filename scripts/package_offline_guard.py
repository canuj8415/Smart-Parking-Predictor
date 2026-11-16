"""Python audit for copied-demo checks; not a native-extension/OS firewall."""
import atexit,json,os,sys
from pathlib import Path
def install(root,report):
    root=Path(root).resolve();original=Path(json.loads((root/'BUNDLE_SCOPE.json').read_text(encoding='utf-8'))['original_project_root']).resolve()
    denied=[];loopback=0
    def audit(event,args):
        nonlocal loopback
        if event in ('socket.connect','socket.bind','socket.getaddrinfo'):
            address=args[0] if event=='socket.getaddrinfo' else args[1]
            host=address[0] if isinstance(address,tuple) else address
            if host in ('127.0.0.1','::1','localhost'):loopback+=1;return
            denied.append(dict(event=event,host=str(host)));raise PermissionError('Offline demo permits localhost Python sockets only')
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            path=Path(os.fsdecode(args[0])).resolve()
            if path.is_relative_to(original) and not path.is_relative_to(root):
                denied.append(dict(event=event,path=str(path)));raise PermissionError('Original project fallback denied')
    sys.addaudithook(audit)
    def save():
        Path(report).write_text(json.dumps(dict(denied=denied,allowed_loopback_events=loopback,pid=os.getpid(),
            scope='Python sockets/file-open only;native extensions/physical networking outside coverage'),indent=2)+'\n',encoding='utf-8')
    atexit.register(save);return save
