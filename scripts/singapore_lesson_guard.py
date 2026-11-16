"""Project-file audit for a read-only lesson, not an OS security boundary."""
import atexit
import json
import os
import sys
from pathlib import Path


def path_decision(path, writing, root, scratch):
    if isinstance(path, int) or path is None:
        return None
    path = Path(os.fsdecode(path)).resolve()
    root, scratch = Path(root).resolve(), Path(scratch).resolve()
    if path.is_relative_to(scratch) or not path.is_relative_to(root):
        return None
    relative = path.relative_to(root)
    if writing:
        return 'Lesson may write only to its new execution scratch folder'
    parts = relative.parts
    if (len(parts) > 1 and parts[0] == 'data' and parts[1] in
            ['raw', 'processed', 'receipts', 'singapore_forecast_holdout_claims']):
        return 'Raw/growing observations, prospective batches and final claims are excluded from this lesson'
    if len(parts) > 1 and parts[0] == 'models' and parts[1] == 'checkpoints':
        return 'Lesson uses the archived statistical checkpoint, not mutable operational model paths'
    if (len(parts) > 2 and parts[0:2] == ('experiments', 'results')
            and parts[2].startswith('SG-FINAL-') and not parts[2].startswith('SG-FINAL-VALIDATION-')):
        return 'Actual final results are not lesson inputs'
    if parts and parts[0] == 'reports' and relative.name.startswith('singapore_final'):
        return 'Mutable final status/results are not lesson inputs'
    return None


def install(root, scratch, report_path):
    root, scratch = Path(root).resolve(), Path(scratch).resolve()
    reads = set(); denied = []
    def check(path, writing, event):
        reason = path_decision(path, writing, root, scratch)
        if reason:
            denied.append(dict(event=event, path=str(path), writing=writing, reason=reason))
            raise PermissionError(reason)
        if not writing and isinstance(path, (str, bytes, os.PathLike)):
            resolved = Path(os.fsdecode(path)).resolve()
            if resolved.is_relative_to(root) and not resolved.is_relative_to(scratch):
                reads.add(resolved.relative_to(root).as_posix())
    def audit(event, args):
        if event == 'open':
            mode, flags = args[1], args[2]
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            check(args[0], writing, event)
        elif event in ['os.listdir', 'os.scandir']:
            check(args[0], False, event)
        elif event in ['os.remove', 'os.rmdir', 'os.mkdir']:
            check(args[0], True, event)
        elif event == 'os.rename':
            check(args[0], True, event); check(args[1], True, event)
    sys.addaudithook(audit)
    def save():
        Path(report_path).write_text(json.dumps(dict(pid=os.getpid(), project_reads=sorted(reads), denied=denied,
            scope='Python file audit within project only; not an OS security boundary'), indent=2)+'\n', encoding='utf-8')
    atexit.register(save)
    return save
