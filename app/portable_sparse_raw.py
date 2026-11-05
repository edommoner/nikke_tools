"""Reclaim allocated zero blocks without changing ordinary raw file bytes.
Darwin F_PUNCHHOLE ABI: SDK sys/fcntl.h (99, two uint32 and two off_t).
No archive encoding, raw deletion, source execution, or proof promotion.
"""
import hashlib,json,os,stat,struct,sys
from pathlib import Path
from portable_capture_storage import anchor

BLOCK=64*1024
CHUNK=8*1024*1024
ZERO=bytes(BLOCK)
ZERO_CHUNK=bytes(CHUNK)


def scan(stream,size,block_size=BLOCK):
    digest=hashlib.sha256();ranges=[];start=None;offset=0;zero_block=bytes(block_size)
    while chunk:=stream.read(CHUNK):
        digest.update(chunk)
        for at in range(0,len(chunk),block_size):
            block=chunk[at:at+block_size];zero=len(block)==block_size and block==zero_block
            if zero and start is None:start=offset+at
            elif not zero and start is not None:ranges.append((start,offset+at-start));start=None
        offset+=len(chunk)
    if start is not None:ranges.append((start,offset-start))
    if offset!=size:raise ValueError('Raw length changed during scan')
    return digest.hexdigest(),ranges


def signature(value):
    return tuple(getattr(value,key) for key in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_nlink'))


def sparsify_raw(capture,receipt,check_records,*,apply=False,block_size=BLOCK):
    if type(block_size) is not int or block_size not in (4096,BLOCK):raise ValueError('Scan block must be4096 or65536 bytes')
    if sys.platform!='darwin':raise ValueError('Zero-block reclamation requires Darwin F_PUNCHHOLE')
    capture=Path(capture).resolve();receipt=Path(receipt).absolute()
    if receipt.is_symlink():raise ValueError('Fresh sparse receipt required')
    receipt=receipt.resolve()
    if receipt.exists():raise ValueError('Fresh sparse receipt required')
    if receipt.is_relative_to(capture):raise ValueError('Store receipt outside immutable capture')
    # Reserve the receipt before any mutation, including failures.
    with receipt.open('x') as report:
        state=dict(schema=1,operation='sparsify-raw',apply=apply,gpu_calls=0,calculation_verified=False,raw_deleted=False,passed=False)
        try:
            capture,size,digest,evidence_sha=anchor(capture,check_records)
            run=json.loads((capture/'run.json').read_text())
            if run.get('status')!='finished':raise ValueError('Only a finished capture may be sparsified')
            raw=capture/'readback.bin'
            artifacts=json.loads((capture/'artifacts.json').read_text())
            raw_records=[r for r in artifacts['files'] if r['path']=='readback.bin']
            if len(raw_records)>1 or not raw_records and artifacts.get('raw_included') is not False:raise ValueError('Missing or duplicate raw artifact policy')
            check_records(capture,raw_records)
            fd=os.open(raw,os.O_RDWR|os.O_NOFOLLOW) if apply else os.open(raw,os.O_RDONLY|os.O_NOFOLLOW)
            with os.fdopen(fd,'r+b' if apply else 'rb',buffering=0) as stream:
                import fcntl
                fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
                before=os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_size!=size:raise ValueError('Unique regular raw file with anchored size required')
                allocation_unit=os.fstatvfs(stream.fileno()).f_frsize
                if allocation_unit<=0 or block_size%allocation_unit:raise ValueError('Scan block must align to filesystem allocation unit')
                actual,ranges=scan(stream,size,block_size)
                if actual!=digest:raise ValueError('Raw differs from anchored SHA before reclamation')
                if signature(os.fstat(stream.fileno()))!=signature(before):raise ValueError('Raw changed during planning')
                if raw.stat().st_ino!=before.st_ino or raw.stat().st_dev!=before.st_dev:raise ValueError('Raw pathname changed')
                if apply:
                    for offset,length in ranges:
                        # Read each planned range again immediately before deallocation.
                        stream.seek(offset);remaining=length
                        while remaining:
                            chunk=stream.read(min(CHUNK,remaining))
                            if not chunk or chunk!=ZERO_CHUNK[:len(chunk)]:raise ValueError('Planned zero range changed; stop with original bytes retained')
                            remaining-=len(chunk)
                        fcntl.fcntl(stream,99,struct.pack('=IIqq',0,0,offset,length))
                    os.fsync(stream.fileno())
                stream.seek(0);after_digest,_=scan(stream,size,block_size);after=os.fstat(stream.fileno())
                if after_digest!=digest or after.st_size!=size or after.st_ino!=before.st_ino or (raw.stat().st_dev,raw.stat().st_ino)!=(before.st_dev,before.st_ino):raise ValueError('Raw byte/size/identity verification failed')
                # Recheck the original evidence and every recorded raw artifact.
                _,after_size,after_anchor,after_evidence=anchor(capture,check_records)
                if (after_size,after_anchor,after_evidence)!=(size,digest,evidence_sha):raise ValueError('Evidence anchor changed during reclamation')
                check_records(capture,raw_records)
                state.update(passed=True,capture=str(capture),raw_bytes=size,raw_sha256=digest,evidence_sha256=evidence_sha,
                             raw_inode=after.st_ino,scan_block_bytes=block_size,filesystem_allocation_unit=allocation_unit,zero_ranges=len(ranges),zero_range_bytes=sum(n for _,n in ranges),
                             allocated_before=before.st_blocks*512,allocated_after=after.st_blocks*512,
                             allocated_reclaimed=before.st_blocks*512-after.st_blocks*512,full_hash_verified=True)
        except BaseException as error:
            state['error']=type(error).__name__+': '+str(error)
            raise
        finally:
            json.dump(state,report,indent=2);report.write('\n');report.flush();os.fsync(report.fileno())
    return state
