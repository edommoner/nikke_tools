"""Lossless local raw storage. Never compiles, dispatches or promotes GPU proof."""
import gzip,hashlib,json,os,shutil,stat,tempfile
from pathlib import Path

CHUNK=8*1024*1024
RESERVE_BYTES=20*1024**3


def sync_directory(path):
    if os.name!='nt':
        fd=os.open(path,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)


def durable_mkdir(path):
    path=Path(path)
    if path.exists():
        if not path.is_dir() or path.is_symlink():raise ValueError('Unsafe archive directory')
        return
    durable_mkdir(path.parent)
    path.mkdir();sync_directory(path.parent)


def space_status(path,needed=0,*,reserve=RESERVE_BYTES):
    if any(type(n) is not int or n<0 for n in (needed,reserve)):
        raise ValueError('Storage budget must use nonnegative integer bytes')
    probe=Path(path).resolve()
    while not probe.exists():probe=probe.parent
    free=shutil.disk_usage(probe).free
    return dict(passed=free>=needed+reserve,required_bytes=needed,reserve_bytes=reserve,free_bytes=free)


def require_space(path,needed,*,reserve=RESERVE_BYTES):
    result=space_status(path,needed,reserve=reserve)
    if not result['passed']:
        raise ValueError(f"Insufficient space: need {needed+reserve} bytes including reserve; available {result['free_bytes']}")
    return result


def require_raw_files(*paths):
    """Missing archived raw is a restore request, never a GPU retry trigger."""
    missing=[str(p) for p in paths if not Path(p).is_file()]
    if missing:
        raise FileNotFoundError('Missing raw: '+', '.join(missing)+
            '; restore archived bytes before audit/replay (archive-portable-benchmarks.py restore or nikke_gpu.py restore-raw). Do not rerun the GPU to recreate evidence.')


def benchmark_space_preflight(path,input_words,output_words,parity_cases,workloads,*,programs=1024,samples=4,variants=2):
    """Budget the entire uncompressed run, using its own ABI and case counts."""
    captures=variants*(len(parity_cases)+workloads*samples)
    cases=variants*(sum(parity_cases)+workloads*samples*programs)
    needed=4*cases*(input_words+output_words)+4*captures
    require_space(path,needed)
    return needed


def regular_signature(path):
    s=Path(path).lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1:
        raise ValueError('Expected a regular file with one hard link: '+str(path))
    return {k:getattr(s,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')}


def write_synced_json(path,value):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())


def verify_bundle(bundle,expected,*,expand=True):
    """Verify compressed bytes and, by default, expanded bytes without a GPU."""
    bundle=Path(bundle)
    if bundle.is_symlink():raise ValueError('Symlinked archive bundle')
    record=json.loads((bundle/'receipt.json').read_text())
    if record.get('schema')!=1 or record.get('anchor')!=expected:
        raise ValueError('Archive anchor mismatch')
    archive=bundle/'payload.gz'
    if archive.is_symlink() or archive.stat().st_size!=record['archive_bytes'] or file_digest(archive)!=record['archive_sha256']:
        raise ValueError('Compressed archive differs from receipt')
    if expand:decompress(archive,expected['size'],expected['sha256'])
    return record


def archive_bundle(source,bundle,expected):
    """Publish archive and receipt together. Caller serializes writers to bundle."""
    source=Path(source);bundle=Path(bundle)
    # Caller holds the migration lock. These staging directories never contain
    # originals; a SIGKILL may leave them behind before atomic publication.
    for orphan in bundle.parent.glob('.'+bundle.name+'-*'):
        if orphan.is_dir() and not orphan.is_symlink():shutil.rmtree(orphan)
    if bundle.exists():return verify_bundle(bundle,expected)
    before=regular_signature(source)
    if before['st_size']!=expected['size']:raise ValueError('Source size differs from anchor')
    # gzip can grow slightly on incompressible input. Do not assume a ratio.
    require_space(bundle.parent,expected['size']+expected['size']//100+1024**2)
    stage=Path(tempfile.mkdtemp(prefix='.'+bundle.name+'-',dir=bundle.parent))
    try:
        archive=stage/'payload.gz';h=hashlib.sha256()
        with source.open('rb') as r,archive.open('xb') as w:
            with gzip.GzipFile(filename='',fileobj=w,mode='wb',mtime=0) as z:
                for b in iter(lambda:r.read(CHUNK),b''):h.update(b);z.write(b)
            w.flush();os.fsync(w.fileno())
        if h.hexdigest()!=expected['sha256']:raise ValueError('Source hash differs from anchor')
        if regular_signature(source)!=before:raise ValueError('Source changed during archive')
        decompress(archive,expected['size'],expected['sha256'])
        record=dict(schema=1,anchor=expected,source_stat=before,
                    archive_bytes=archive.stat().st_size,archive_sha256=file_digest(archive),
                    gpu_calls=0,calculation_verified=False)
        write_synced_json(stage/'receipt.json',record);sync_directory(stage)
        if bundle.exists():raise ValueError('Bundle appeared during archive')
        os.rename(stage,bundle);sync_directory(bundle.parent)
        return record
    finally:
        if stage.exists():shutil.rmtree(stage)


def restore_bundle(bundle,expected,destination):
    """Restore exact bytes without overwriting an existing path."""
    bundle=Path(bundle);destination=Path(destination)
    verify_bundle(bundle,expected)
    if destination.exists() or destination.is_symlink():raise ValueError('Restore destination already exists')
    require_space(destination.parent,expected['size'])
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent,prefix='.raw-restore-',delete=False) as f:
            temporary=Path(f.name)
            decompress(bundle/'payload.gz',expected['size'],expected['sha256'],f)
            f.flush();os.fsync(f.fileno())
        os.link(temporary,destination);sync_directory(destination.parent)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
    return dict(restored=True,restored_bytes=expected['size'],gpu_calls=0,calculation_verified=False)


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
    require_space(archive.parent,size+size//100+1024**2)
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
    require_space(capture,size)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=capture,prefix='.raw-restore-',delete=False) as file:
            temporary=Path(file.name);decompress(archive,size,digest,file);file.flush();os.fsync(file.fileno())
        os.link(temporary,raw)
        return dict(restored=True,raw_bytes=size,raw_sha256=digest,gpu_calls=0,calculation_verified=False)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
