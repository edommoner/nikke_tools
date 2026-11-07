"""CPU-only, lossless migration of legacy benchmark captures; no GPU imports."""
import contextlib,datetime,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path

from portable_capture_storage import (archive_bundle,durable_mkdir,file_digest,regular_signature,
    require_space,restore_bundle,space_status,sync_directory,verify_bundle,write_synced_json,RESERVE_BYTES)

TARGETS=[
    ('enemy-target-scalar-benchmark-20261020T141034675819Z','portable-enemy-target-scalar-benchmark.json'),
    ('hp-basis-benchmark-20261020T112721901895Z','portable-mode-entry-hp-cache-benchmark.json'),
]


@contextlib.contextmanager
def locked(storage):
    # Lock outside the archive so it also covers initial manifest publication.
    storage=Path(storage);durable_mkdir(storage.parent)
    with (storage.parent/(storage.name+'.lock')).open('a+b') as f:
        if os.name=='nt':
            import msvcrt
            if not f.seek(0,os.SEEK_END):f.write(b'\0');f.flush()
            f.seek(0)
            try:msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
            except OSError:raise ValueError('Another storage operation is running')
        else:
            import fcntl
            try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise ValueError('Another storage operation is running')
        try:yield
        finally:
            if os.name=='nt':f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(f,fcntl.LOCK_UN)


def ensure_idle():
    try:lines=subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines()
    except (OSError,subprocess.CalledProcessError) as error:
        raise ValueError('Cannot observe benchmark/verification processes; storage operation stopped') from error
    pattern=r'(?:^|\s)(?:\S*/)?python\S*\s+(?:-\S+\s+)*(?:\S*/)?(?:benchmark-[\w-]+\.py|verify-portable[\w-]*\.py)\b'
    active=[line.strip() for line in lines if re.search(pattern,line)]
    if active:raise ValueError('Benchmark/verification process active: '+'; '.join(active))


def inside(root,relative):
    relative=Path(relative)
    if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe relative path')
    result=Path(root)/relative
    if not result.resolve().is_relative_to(Path(root).resolve()):raise ValueError('Path escapes root')
    return result


def strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,dict):
        for v in value.values():yield from strings(v)
    elif isinstance(value,list):
        for v in value:yield from strings(v)


def samples(value):
    if isinstance(value,dict):
        if all(k in value for k in ('captured','input_sha256','output_sha256')):yield value
        for v in value.values():yield from samples(v)
    elif isinstance(value,list):
        for v in value:yield from samples(v)


def evidence_size(evidence,name):
    if name=='readback.bin':return evidence['transport']['output_bytes']
    size=evidence['transport']['input_bytes']
    dispatches=evidence.get('dispatches',[])
    if dispatches:
        # Transport counts a 4-byte header per physical dispatch; input.bin
        # stores one logical header. Use the historical receipt, never today's ABI.
        if evidence.get('logical_input_hash')!='uint32 total count followed by all ordered program words; per-dispatch headers excluded':
            raise ValueError('Unknown batched input hash layout')
        if size!=sum(d['transport']['input_bytes'] for d in dispatches):raise ValueError('Batched transport byte count differs')
        if evidence['transport']['cases']!=sum(d['transport']['cases'] for d in dispatches):raise ValueError('Batched case count differs')
        size-=4*(len(dispatches)-1)
    return size


def inventory(repository,storage,*,targets=TARGETS,progress=print):
    repository=Path(repository).resolve();storage=Path(storage).resolve()
    ensure_idle()
    if storage.exists():raise ValueError('Inventory destination already exists')
    rows=[];preserved={};references=[];snapshots={}
    for folder,report_name in targets:
        root=inside(repository/'research/portable-build',folder)
        if storage.is_relative_to(root):raise ValueError('Archive must be outside captures')
        report_path=inside(repository/'research',report_name);report=json.loads(report_path.read_text())
        if report.get('passed') is not True:raise ValueError('Completed passing report required')
        report_rel=report_path.relative_to(repository).as_posix();report_sha=file_digest(report_path)
        snapshots[report_rel]=report_path.read_text()
        preserved[report_rel]=report_sha
        lookup={}
        for entry in samples(report):
            captured=Path(entry['captured'])
            if not captured.is_absolute():captured=repository/captured
            key=captured.resolve().relative_to(root.resolve()).as_posix()
            if key in lookup:raise ValueError('Duplicate report capture')
            lookup[key]=entry
        captures=sorted(p.parent for p in root.glob('*/evidence.json'))
        if set(lookup)!={p.name for p in captures}:raise ValueError('Report/capture set differs')
        for capture in captures:
            evidence_path=capture/'evidence.json';e=json.loads(evidence_path.read_text())
            evidence_sha=file_digest(evidence_path)
            for name,key in [('input.bin','input_sha256'),('readback.bin','output_sha256')]:
                path=capture/name;signature=regular_signature(path)
                size=evidence_size(e,name);digest=e[key]
                if size!=signature['st_size'] or digest!=lookup[capture.name][key]:raise ValueError('Evidence/report anchor differs')
                if file_digest(path)!=digest or regular_signature(path)!=signature:raise ValueError('Raw differs from evidence or changed')
                rel=path.relative_to(repository).as_posix()
                rows.append(dict(path=rel,size=size,sha256=digest,stat=signature,
                    evidence=evidence_path.relative_to(repository).as_posix(),evidence_sha256=evidence_sha,
                    report=report_rel,report_sha256=report_sha,folder=folder,
                    selected=not capture.name.startswith('full-'),keep_reason='parity' if capture.name.startswith('full-') else None))
                progress('inventoried '+rel,flush=True)
        raw_paths={row['path'] for row in rows}
        for path in root.rglob('*'):
            if path.is_file() and path.relative_to(repository).as_posix() not in raw_paths:
                if path.is_symlink():raise ValueError('Symlink in capture')
                preserved[path.relative_to(repository).as_posix()]=file_digest(path)
    # Summary/progress/parity reports describe the same captures; they are
    # provenance, not consumers. Other references conservatively pin raw files.
    for path in sorted((repository/'research').glob('*.json')):
        text=path.read_text()
        relevant=[f for f,_ in targets if f in text]
        if not relevant:continue
        value=json.loads(text);rel=path.relative_to(repository).as_posix()
        associated=any(path.name in (r,r.replace('-benchmark.json','-benchmark-progress.json'),
                         r.replace('-benchmark.json','-parity.json')) for f,r in targets if f in relevant)
        preserved[rel]=file_digest(path);snapshots[rel]=text
        for s in strings(value):
            for folder in relevant:
                if folder not in s:continue
                tail=s.split(folder,1)[1].strip('/')
                references.append(dict(report=rel,value=s,provenance=associated))
                if not associated:
                    for row in rows:
                        if row['folder']==folder and (not tail or row['path'].split(folder+'/',1)[1].startswith(tail.rstrip('/')+'/') or row['path'].endswith('/'+tail)):
                            row.update(selected=False,keep_reason='external reference: '+rel)
    # Record static/dynamic path consumers for the operator. Dynamic reads must
    # restore first; the archival command never silently re-runs a GPU suite.
    consumers=[]
    for directory in ('research','scripts'):
        for path in sorted((repository/directory).glob('*.py')):
            for number,line in enumerate(path.read_text().splitlines(),1):
                if any(f in line for f,_ in targets) or (('captured' in line or 'replay_source' in line) and ("input.bin" in line or "readback.bin" in line)):
                    consumers.append(dict(path=path.relative_to(repository).as_posix(),line=number,text=line.strip()))
    try:commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repository,text=True).strip()
    except subprocess.CalledProcessError:commit=None
    manifest=dict(schema=1,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        repository=str(repository),source_commit=commit,files=rows,preserved=preserved,
        report_snapshots=snapshots,references=references,reader_sites=consumers,
        free_bytes_before=shutil.disk_usage(repository).free,gpu_calls=0,calculation_verified=False)
    storage.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.'+storage.name+'-inventory-',dir=storage.parent))
    try:
        write_synced_json(stage/'inventory.json',manifest)
        with (stage/'inventory.sha256').open('x') as f:
            f.write(file_digest(stage/'inventory.json')+'\n');f.flush();os.fsync(f.fileno())
        sync_directory(stage);os.rename(stage,storage);sync_directory(storage.parent)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return manifest


def load_inventory(storage,repository=None):
    storage=Path(storage).resolve();path=storage/'inventory.json'
    if file_digest(path)!=(storage/'inventory.sha256').read_text().strip():raise ValueError('Inventory changed')
    manifest=json.loads(path.read_text())
    if manifest['schema']!=1:raise ValueError('Unknown inventory schema')
    repository=Path(repository or manifest['repository']).resolve()
    return repository,manifest


def check_preserved(repository,manifest):
    for path,digest in manifest['preserved'].items():
        if file_digest(inside(repository,path))!=digest:raise ValueError('Preserved evidence/source/report changed: '+path)


def expected(row):
    return {k:row[k] for k in ('path','size','sha256','evidence_sha256','report_sha256')}


def bundle_path(storage,row):
    return inside(Path(storage)/'bundles',row['path']+'.bundle')


def journal(storage,event,row,**extra):
    path=Path(storage)/'events.jsonl'
    # Preserve a torn last write for inspection, then continue with valid JSONL.
    # Complete corrupt records stop the operation rather than being discarded.
    if path.exists():
        data=path.read_bytes();offset=0
        for line in data.splitlines(keepends=True):
            try:json.loads(line)
            except (ValueError,UnicodeDecodeError):
                if line.endswith(b'\n') or offset+len(line)!=len(data):raise ValueError('Corrupt migration journal')
                digest=hashlib.sha256(line).hexdigest();backup=Path(storage)/('incomplete-event-'+digest+'.json')
                if not backup.exists():write_synced_json(backup,dict(offset=offset,hex=line.hex()))
                with path.open('r+b') as f:f.truncate(offset);f.flush();os.fsync(f.fileno())
                break
            offset+=len(line)
        else:
            if data and not data.endswith(b'\n'):
                with path.open('ab') as f:f.write(b'\n');f.flush();os.fsync(f.fileno())
    with path.open('a') as f:
        f.write(json.dumps(dict(event=event,path=row['path'],utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra))+'\n');f.flush();os.fsync(f.fileno())
    sync_directory(storage)


def plan(storage,*,repository=None,workload=None):
    """Validate anchors and bytes without writing bundles or removing raw files."""
    repository,manifest=load_inventory(storage,repository)
    ensure_idle();check_preserved(repository,manifest)
    rows=[]
    for row in manifest['files']:
        if not row['selected'] or (workload and Path(row['path']).parent.name!=workload):continue
        source=inside(repository,row['path']);bundle=bundle_path(storage,row)
        if source.exists():
            before=regular_signature(source)
            if before['st_size']!=row['size'] or file_digest(source)!=row['sha256'] or regular_signature(source)!=before:
                raise ValueError('Raw differs from inventory or changed')
        elif source.is_symlink():raise ValueError('Dangling source symlink')
        elif not bundle.exists():raise ValueError('Neither original nor archive exists')
        if bundle.exists():verify_bundle(bundle,expected(row))
        rows.append(dict(path=row['path'],size=row['size'],original_present=source.exists(),archive_present=bundle.exists()))
    return dict(passed=True,apply=False,files=rows,selected_files=len(rows),
                selected_raw_bytes=sum(r['size'] for r in rows),gpu_calls=0,calculation_verified=False)


def migrate(storage,*,repository=None,remove_original=False,workload=None,progress=print):
    repository,manifest=load_inventory(storage,repository);storage=Path(storage).resolve()
    ensure_idle();check_preserved(repository,manifest)
    # Only scratch restored copies live here; originals are in portable-build.
    for orphan in storage.glob('.restore-test-*'):
        if orphan.is_dir() and not orphan.is_symlink():shutil.rmtree(orphan)
    for row in manifest['files']:
        if not row['selected'] or (workload and Path(row['path']).parent.name!=workload):continue
        source=inside(repository,row['path']);bundle=bundle_path(storage,row)
        durable_mkdir(bundle.parent)
        if not source.exists():
            if source.is_symlink():raise ValueError('Dangling source symlink')
            verify_bundle(bundle,expected(row));journal(storage,'verified-absent',row)
            progress('already archived '+row['path'],flush=True);continue
        before=regular_signature(source)
        record=archive_bundle(source,bundle,expected(row))
        # A separate pass validates published bytes, not just the staging file.
        verify_bundle(bundle,expected(row));journal(storage,'verified',row,archive_bytes=record['archive_bytes'])
        # Real restoration is exercised for every file, using just one raw
        # temporary at a time. It is checked and removed before source removal.
        require_space(storage,row['size'])
        with tempfile.TemporaryDirectory(prefix='.restore-test-',dir=storage) as td:
            restored=Path(td)/'raw.bin';restore_bundle(bundle,expected(row),restored)
            if file_digest(restored)!=row['sha256']:raise ValueError('Restore test differs')
        if remove_original:
            ensure_idle()
            for path,key in ((row['evidence'],'evidence_sha256'),(row['report'],'report_sha256')):
                if file_digest(inside(repository,path))!=row[key]:raise ValueError('Evidence changed')
            if regular_signature(source)!=before or file_digest(source)!=row['sha256'] or regular_signature(source)!=before:
                raise ValueError('Source changed; original retained')
            free_before=shutil.disk_usage(repository).free
            source.unlink();sync_directory(source.parent)
            journal(storage,'removed',row,raw_bytes=row['size'],free_bytes_before=free_before,
                    free_bytes_after=shutil.disk_usage(repository).free)
        progress(('archived and removed ' if remove_original else 'archived, original kept ')+row['path'],flush=True)
    check_preserved(repository,manifest)
    return status(storage,repository=repository)


def restore(storage,path,*,repository=None):
    repository,manifest=load_inventory(storage,repository);ensure_idle();check_preserved(repository,manifest)
    rows=[r for r in manifest['files'] if r['path']==path]
    if len(rows)!=1:raise ValueError('Path is not in inventory')
    row=rows[0];result=restore_bundle(bundle_path(storage,row),expected(row),inside(repository,path))
    journal(storage,'restored',row)
    return result


def status(storage,*,repository=None,verify=False):
    repository,manifest=load_inventory(storage,repository);check_preserved(repository,manifest)
    archived=removed=raw_bytes=archive_bytes=0;kept=pending=0
    for row in manifest['files']:
        source=inside(repository,row['path']);bundle=bundle_path(storage,row)
        if bundle.exists():
            record=verify_bundle(bundle,expected(row),expand=verify)
            archived+=1;archive_bytes+=record['archive_bytes']
        if not source.exists():
            if not row['selected']:raise ValueError('Pinned original is missing')
            if not bundle.exists():raise ValueError('Neither original nor archive exists')
            removed+=1;raw_bytes+=row['size']
        else:
            if not row['selected']:kept+=1
            else:pending+=1
            if verify:
                if regular_signature(source)['st_size']!=row['size'] or file_digest(source)!=row['sha256']:
                    raise ValueError('Retained original changed')
    return dict(schema=1,inventory_sha256=file_digest(Path(storage)/'inventory.json'),
        total_binary_files=len(manifest['files']),archived_files=archived,removed_files=removed,
        kept_raw_files=kept,removed_raw_bytes=raw_bytes,archive_bytes=archive_bytes,
        pending_timing_raw_files=pending,raw_files_requiring_restore=removed,
        compressed_bytes_verified=True,
        net_file_bytes_saved=raw_bytes-archive_bytes,
        free_bytes_before=manifest['free_bytes_before'],free_bytes_now=shutil.disk_usage(repository).free,
        gpu_calls=0,calculation_verified=False,all_archives_verified=verify)


def storage_check(repository,*,needed=0,reserve=RESERVE_BYTES,storage=None,verify=False,require_archived=False):
    """Read-only check: free capacity, archive integrity and optional cleanup gate."""
    if (verify or require_archived) and storage is None:
        raise ValueError('--verify/--require-archived requires --storage')
    result=dict(space_status(repository,needed,reserve=reserve),gpu_calls=0,calculation_verified=False,
                archive_storage_checked=False)
    if storage is not None:
        archives=status(storage,repository=repository,verify=verify)
        result.update(archive_storage_checked=True,archives=archives)
        if require_archived and archives['pending_timing_raw_files']:
            result.update(passed=False,reason='Timing raw files remain; archive after measurement before completing cleanup')
    return result
