"""Python socket audit for local notebook checks, not an OS/network firewall.

Native extension networking is outside Python audit coverage. Jupyter/ZeroMQ
uses localhost; permit only literal loopback addresses in Python socket calls.
"""
import atexit,json,os,sys
from pathlib import Path

def install(path,loopback=False):
    events=[];allowed=0
    def audit(event,args):
        nonlocal allowed
        if event not in ('socket.connect','socket.bind','socket.getaddrinfo'):return
        address=args[0] if event=='socket.getaddrinfo' else args[1]
        host=address[0] if isinstance(address,tuple) else address
        if loopback and host in ('127.0.0.1','::1','localhost'):
            allowed+=1;return
        events.append(dict(event=event,host=str(host)))
        raise PermissionError('Offline validation blocks non-loopback Python socket access')
    sys.addaudithook(audit)
    def save():
        Path(path).write_text(json.dumps(dict(denied=events,allowed_loopback_events=allowed,pid=os.getpid(),
            scope='Python audit layer only; native extensions/physical networking not controlled'),indent=2)+'\n',encoding='utf-8')
    atexit.register(save)
    return save
