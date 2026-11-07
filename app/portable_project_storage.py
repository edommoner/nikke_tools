"""CPU-only reclamation of zero blocks in old, evidence-anchored buffers.

Unlike archival, raw paths, logical bytes, sizes and inodes remain available.
No GPU, compiler, evidence rewriting or calculation certification.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import time
import shutil

from portable_capture_storage import file_digest, sync_directory, write_synced_json
from portable_benchmark_storage import evidence_size, ensure_idle, locked
from portable_sparse_raw import scan, signature, CHUNK


def ensure_closed(path):
    result=subprocess.run(['/usr/sbin/lsof','-t','--',str(path)],capture_output=True,text=True)
    pids=set(result.stdout.split())-{str(os.getpid())}
    if result.returncode not in (0,1) or pids or result.stderr.strip():
        raise ValueError('Buffer is open or open-file observation failed: '+str(path))


def reclaim(path, receipt, *, apply=False,guard=None):
    """Only a recorded legacy input/readback, with full SHA checks both sides."""
    path=Path(path).absolute();receipt=Path(receipt).absolute()
    if sys.platform!='darwin':raise ValueError('Requires Darwin F_PUNCHHOLE')
    import fcntl
    if path.name not in ('input.bin','readback.bin'):raise ValueError('Not a legacy raw buffer')
    if any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('Symlinked raw path')
    if receipt.exists() or receipt.is_symlink():raise ValueError('Fresh receipt required')
    if receipt.resolve().is_relative_to(path.parent.resolve()):raise ValueError('Receipt must be outside capture')
    evidence=path.parent/'evidence.json'
    if evidence.is_symlink():raise ValueError('Symlinked evidence')
    with os.fdopen(os.open(evidence,os.O_RDONLY|os.O_NOFOLLOW),'rb') as source:
        evidence_bytes=source.read()
    evidence_sha=hashlib.sha256(evidence_bytes).hexdigest();e=json.loads(evidence_bytes)
    if not isinstance(e,dict):raise ValueError('Non-object historical evidence')
    key='input_sha256' if path.name=='input.bin' else 'output_sha256'
    digest=e[key];size=evidence_size(e,path.name)
    if type(size) is not int or size<=0 or not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Invalid evidence size/SHA')
    state=dict(schema=1,path=str(path),apply=apply,passed=False,gpu_calls=0,
               calculation_verified=False,raw_deleted=False,evidence_sha256=evidence_sha)
    # Reserve a failure receipt before touching allocation. Never replace it.
    with receipt.open('x') as report:
        json.dump(dict(state,status='started'),report);report.flush();os.fsync(report.fileno());sync_directory(receipt.parent)
        try:
            fd=os.open(path,(os.O_RDWR if apply else os.O_RDONLY)|os.O_NOFOLLOW)
            with os.fdopen(fd,'r+b' if apply else 'rb',buffering=0) as stream:
                fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
                before=os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_size!=size:
                    raise ValueError('Unique regular buffer with anchored size required')
                unit=os.fstatvfs(stream.fileno()).f_frsize
                if unit<=0 or 4096%unit:raise ValueError('Unsupported filesystem allocation unit')
                actual,ranges=scan(stream,size,4096)
                if actual!=digest:raise ValueError('Raw differs from historical evidence')
                if signature(os.fstat(stream.fileno()))!=signature(before):raise ValueError('Raw changed during scan')
                if (path.stat().st_dev,path.stat().st_ino)!=(before.st_dev,before.st_ino):raise ValueError('Raw path replaced')
                if file_digest(evidence)!=evidence_sha:raise ValueError('Evidence changed')
                if apply:
                    if guard is not None:guard(path)
                    for offset,length in ranges:
                        stream.seek(offset);remaining=length
                        while remaining:
                            # Narrow the non-cooperative writer race to one
                            # aligned chunk. Only quiescent, old files qualify.
                            at=stream.tell();b=stream.read(min(1024**2,remaining))
                            if not b or b!=bytes(len(b)):raise ValueError('Planned zero range changed')
                            fcntl.fcntl(stream,99,struct.pack('=IIqq',0,0,at,len(b)))
                            remaining-=len(b)
                    os.fsync(stream.fileno())
                stream.seek(0);after_digest,_=scan(stream,size,4096)
                after=os.fstat(stream.fileno())
                if after_digest!=digest or (after.st_dev,after.st_ino,after.st_size)!=(before.st_dev,before.st_ino,size):
                    raise ValueError('Post-reclamation raw verification failed')
                if (path.stat().st_dev,path.stat().st_ino)!=(before.st_dev,before.st_ino) or file_digest(evidence)!=evidence_sha:
                    raise ValueError('Raw path/evidence changed')
                if apply:os.utime(stream.fileno(),ns=(before.st_atime_ns,before.st_mtime_ns));os.fsync(stream.fileno())
                state.update(passed=True,raw_bytes=size,raw_sha256=digest,raw_inode=after.st_ino,
                    mtime_ns=before.st_mtime_ns,ctime_before_ns=before.st_ctime_ns,ctime_after_ns=os.fstat(stream.fileno()).st_ctime_ns,
                    allocated_before=before.st_blocks*512,allocated_after=after.st_blocks*512,
                    allocated_reclaimed=(before.st_blocks-after.st_blocks)*512,
                    zero_range_bytes=sum(length for _,length in ranges),full_hash_verified=True)
        except BaseException as error:
            state['error']=type(error).__name__+': '+str(error)
            raise
        finally:
            report.seek(0);json.dump(state,report,indent=2);report.write('\n');report.truncate();report.flush();os.fsync(report.fileno())
    sync_directory(receipt.parent)
    return state


def sweep(repository,storage,*,apply=False,limit=None):
    """Old primary-checkout captures only; never traverse live recovery worktrees."""
    repository=Path(repository).resolve();storage=Path(storage).resolve()
    root=repository/'research/portable-build'
    if root.is_symlink() or not root.is_dir():raise ValueError('Expected primary legacy capture directory')
    if storage.is_relative_to(root):raise ValueError('Receipts must be outside captures')
    with locked(storage):
        ensure_idle()
        storage.mkdir(exist_ok=True)
        rows=[];skipped=[];free_before=shutil.disk_usage(repository).free
        paths=[]
        for folder,dirs,files in os.walk(root,followlinks=False):
            folder=Path(folder)
            if '.git' in files or '.git' in dirs or folder.stat().st_dev!=root.stat().st_dev:
                skipped.append(dict(path=str(folder),reason='Worktree or different filesystem'));dirs[:]=[];continue
            dirs[:]=[d for d in dirs if not (folder/d).is_symlink()]
            paths.extend(folder/f for f in files if f in ('input.bin','readback.bin'))
        try:
          for path in sorted(paths):
            if path.name not in ('input.bin','readback.bin'):continue
            # Existing archived buffers stay absent. Do not synthesize metadata
            # for older unanchored/partial captures; keep those bytes untouched.
            epath=path.parent/'evidence.json'
            try:
                if any(p.is_symlink() for p in (path,*path.parents)) or not path.resolve().is_relative_to(root):raise ValueError('Symlinked or escaped raw path')
                s=path.lstat()
                if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1:raise ValueError('Non-unique regular file')
                if s.st_mtime>time.time()-24*3600:raise ValueError('Modified in last 24 hours')
                run=path.parent/'run.json'
                if run.exists() and json.loads(run.read_text()).get('status')!='finished':raise ValueError('Unfinished capture')
                if epath.is_symlink():raise ValueError('Symlinked evidence')
                e=json.loads(epath.read_text())
                if not isinstance(e,dict):raise ValueError('Non-object historical evidence')
                key='input_sha256' if path.name=='input.bin' else 'output_sha256'
                if key not in e:raise ValueError('Missing historical hash')
                digest=e[key]
                if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('Invalid historical hash')
                if evidence_size(e,path.name)!=s.st_size:raise ValueError('Historical size differs')
            except (OSError,KeyError,TypeError,ValueError) as error:
                skipped.append(dict(path=str(path.relative_to(repository)),reason=str(error)));continue
            # Readers may use sparse files without any restoration. Reprocessing
            # is byte-safe; omit nearly empty allocations to avoid useless scans.
            if path.lstat().st_blocks*512<1024**2:continue
            name=hashlib.sha256(str(path.relative_to(repository)).encode()).hexdigest()+'.json'
            receipt=storage/name
            if receipt.exists():
                try:old=json.loads(receipt.read_text())
                except ValueError:raise ValueError('Incomplete receipt; inspect before resuming: '+str(receipt))
                if not old.get('passed'):raise ValueError('Inspect failed receipt before retry: '+str(receipt))
                if apply and not old.get('apply'):raise ValueError('Use a fresh storage directory to apply a plan')
                rows.append(old);continue
            if apply:
                ensure_idle()
                ensure_closed(path)
            def guard(p):ensure_idle();ensure_closed(p)
            row=reclaim(path,receipt,apply=apply,guard=guard);rows.append(row)
            print(json.dumps(dict(path=str(path.relative_to(repository)),reclaimed=row['allocated_reclaimed'])),flush=True)
            if limit is not None and len(rows)>=limit:break
        finally:
          result=dict(schema=1,apply=apply,files=len(rows),skipped=skipped,
            reclaimed_bytes=sum(r['allocated_reclaimed'] for r in rows),
            zero_range_bytes=sum(r['zero_range_bytes'] for r in rows),
            free_bytes_before=free_before,free_bytes_after=shutil.disk_usage(repository).free,
            gpu_calls=0,raw_deleted=False,calculation_verified=False,
            finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
          write_synced_json(storage/('summary-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json'),result)
        return result
