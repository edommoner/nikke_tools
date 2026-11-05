"""Lossless local raw storage. Never compiles, dispatches or promotes GPU proof."""
import gzip,hashlib,json,os,tempfile,shutil
from pathlib import Path

CHUNK=8*1024*1024


def space_status(path,needed=0,*,reserve=1024**3):
    """Shared budget-only check; no cleanup, compression or proof promotion."""
    if any(type(n) is not int or n<0 for n in (needed,reserve)):
        raise ValueError('Storage budget must use nonnegative integer bytes')
    probe=Path(path).resolve()
    while not probe.exists():probe=probe.parent
    free=shutil.disk_usage(probe).free
    return dict(passed=free>=needed+reserve,required_bytes=needed,reserve_bytes=reserve,free_bytes=free)


def file_digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(CHUNK),b''):h.update(b)
    return h.hexdigest()


def anchor(capture,check_records):
    capture=Path(capture).resolve();records=json.loads((capture/'artifacts.json').read_text())['files']
    evidence=[r for r in records if r['path']=='evidence.json']
    if len(evidence)!=1:raise ValueError('Unique raw evidence anchor required')
    check_records(capture,evidence)
    e=json.loads((capture/'evidence.json').read_text());size=e['transport']['output_bytes'];digest=e['output_sha256']
    if type(size) is not int or size<1 or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('Invalid raw anchor')
    return capture,size,digest,file_digest(capture/'evidence.json')


def decompress(archive,size,digest,target=None):
    h=hashlib.sha256();total=0
    with gzip.open(archive,'rb') as source:
        for b in iter(lambda:source.read(CHUNK),b''):
            total+=len(b)
            if total>size:raise ValueError('Archived raw exceeds anchored size')
            h.update(b)
            if target is not None:target.write(b)
    if total!=size or h.hexdigest()!=digest:raise ValueError('Archived raw differs from anchored bytes')


def archive_raw(capture,archive,check_records,*,remove_original=False):
    capture,size,digest,evidence_sha=anchor(capture,check_records);raw=capture/'readback.bin';archive=Path(archive).resolve()
    receipt=Path(str(archive)+'.json')
    if archive.exists() or receipt.exists():raise ValueError('Archive destination already exists')
    if archive.is_relative_to(capture):raise ValueError('Store archive outside immutable capture')
    before=raw.stat()
    if before.st_size!=size:raise ValueError('Raw size differs from evidence')
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=archive.parent,prefix=archive.name+'.',delete=False) as file:
            temporary=Path(file.name);h=hashlib.sha256()
            with raw.open('rb') as source,gzip.GzipFile(filename='',fileobj=file,mode='wb',mtime=0) as zipped:
                for b in iter(lambda:source.read(CHUNK),b''):h.update(b);zipped.write(b)
            file.flush();os.fsync(file.fileno())
        if h.hexdigest()!=digest:raise ValueError('Raw hash differs from evidence')
        decompress(temporary,size,digest)
        record=dict(schema=1,capture=str(capture),raw_bytes=size,raw_sha256=digest,evidence_sha256=evidence_sha,archive_bytes=temporary.stat().st_size,archive_sha256=file_digest(temporary),gpu_calls=0,calculation_verified=False)
        os.link(temporary,archive)
        with receipt.open('x') as file:json.dump(record,file,indent=2);file.write('\n');file.flush();os.fsync(file.fileno())
        after=raw.stat()
        if any(getattr(after,k)!=getattr(before,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')):raise ValueError('Raw changed during archive; original retained')
        if os.name!='nt':
            directory=os.open(archive.parent,os.O_RDONLY)
            try:os.fsync(directory)
            finally:os.close(directory)
        if remove_original:raw.unlink()
        return dict(**record,archive=str(archive),original_removed=remove_original)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def restore_raw(capture,archive,check_records):
    capture,size,digest,evidence_sha=anchor(capture,check_records);raw=capture/'readback.bin';archive=Path(archive).resolve()
    if raw.exists():raise ValueError('Raw destination already exists')
    record=json.loads(Path(str(archive)+'.json').read_text())
    if record['schema']!=1 or record['capture']!=str(capture) or record['raw_bytes']!=size or record['raw_sha256']!=digest or record['evidence_sha256']!=evidence_sha:raise ValueError('Archive anchor mismatch')
    if archive.stat().st_size!=record['archive_bytes'] or file_digest(archive)!=record['archive_sha256']:raise ValueError('Compressed archive differs from receipt')
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=capture,prefix='.raw-restore-',delete=False) as file:
            temporary=Path(file.name);decompress(archive,size,digest,file);file.flush();os.fsync(file.fileno())
        os.link(temporary,raw)
        return dict(restored=True,raw_bytes=size,raw_sha256=digest,gpu_calls=0,calculation_verified=False)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
