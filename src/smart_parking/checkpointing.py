"""Replace a checkpoint only after a complete, flushed temporary write."""
import os,tempfile
from pathlib import Path
import torch

def save_checkpoint_atomic(payload,target):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    descriptor,name=tempfile.mkstemp(prefix=target.name+'.tmp-',suffix='.pt',dir=target.parent)
    os.close(descriptor);temporary=Path(name)
    try:
        with temporary.open('wb') as stream:
            torch.save(payload,stream);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,target)
    finally:temporary.unlink(missing_ok=True)
