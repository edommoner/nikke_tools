"""Byte-exact APFS compression of derived paired generation cache files.

No cache format, identity, shader, canonical reference or GPU operation changes.
"""
import hashlib,json,os,re,stat,subprocess,sys
from pathlib import Path
from portable_compile_cache import compile_claim
from portable_generation_cache import read_entry,key
from portable_capture_storage import space_status


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda:stream.read(8*1024**2),b''):h.update(b)
    return h.hexdigest()


def allocation(path):
    info=path.stat()
    if not hasattr(info,'st_blocks'):raise ValueError('Filesystem allocation reporting is unavailable on this platform')
    return info.st_blocks*512

def compressed(path):return bool(getattr(path.stat(),'st_flags',0)&getattr(stat,'UF_COMPRESSED',32))


def checked(path):
    if path.is_symlink() or not path.is_file() or re.fullmatch(r'[0-9a-f]{64}\.json',path.name) is None:raise ValueError('Regular keyed generation cache file required')
    value=json.loads(path.read_bytes());identity=value['identity']
    if identity.get('kind')!='paired-resident-slang-generation' or key(identity)!=path.stem:raise ValueError('Paired generation cache filename/identity mismatch')
    read_entry(path,identity)
    info=path.stat()
    return dict(key=path.stem,bytes=info.st_size,sha256=digest(path),allocated_bytes=allocation(path),compressed=compressed(path),inode=info.st_ino,device=info.st_dev,mtime_ns=info.st_mtime_ns)


def pack(source,destination):
    if sys.platform!='darwin':raise ValueError('Filesystem compression requires macOS APFS/HFS support')
    subprocess.run(['/usr/bin/ditto','--hfsCompression','--noclone',str(source),str(destination)],capture_output=True,check=True,timeout=30)


def compress_one(source,staging):
    source=Path(source);staging=Path(staging)
    with compile_claim(source,source.stem,description='Generation cache filesystem compression'):
        before=checked(source)
        if before['compressed']:return dict(before=before,after=before,status='already-compressed',logical_bytes_equal=True)
        pack(source,staging);candidate=checked(staging)
        if (candidate['bytes'],candidate['sha256'])!=(before['bytes'],before['sha256']):raise ValueError('Compressed candidate changed logical cache bytes; original preserved')
        if not candidate['compressed']:raise ValueError('Filesystem compression flag absent; original preserved')
        if checked(source)!=before:raise ValueError('Generation cache changed while staging; original preserved')
        if candidate['allocated_bytes']>=before['allocated_bytes']:
            staging.unlink();return dict(before=before,after=before,status='no-allocation-saving',logical_bytes_equal=True)
        # Cache readers see either complete byte-identical representation. A
        # cache inode may change; parity/source/capture files are never touched.
        with staging.open('rb') as stream:os.fsync(stream.fileno())
        os.replace(staging,source)
        after=checked(source)
        if (after['bytes'],after['sha256'])!=(before['bytes'],before['sha256']):raise ValueError('Compressed cache publication integrity failure')
        return dict(before=before,after=after,status='compressed',logical_bytes_equal=True)


def run(cache,output,*,apply=False):
    cache=Path(cache);output=Path(output)
    if type(apply) is not bool:raise ValueError('Explicit cache compression apply flag required')
    if sys.platform!='darwin':raise ValueError('Filesystem cache compression requires macOS APFS/HFS support')
    if cache.is_symlink() or not cache.is_dir():raise ValueError('Existing regular generation cache directory required')
    cache=cache.resolve();output=output.resolve()
    if cache.is_relative_to(output) or output.is_relative_to(cache):raise ValueError('Compression capture must be outside the cache')
    output.mkdir(parents=True,exist_ok=False)
    def write(name,value):(output/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    rows=[]
    try:
        files=sorted(cache.glob('*.json'))
        if not files:raise ValueError('No paired generation cache entries')
        if any(p.with_suffix('.claim').exists() for p in files):raise ValueError('Cache claim present; no compression started')
        before=[checked(p) for p in files]
        budget=space_status(output,max(r['bytes'] for r in before)+64*1024**2)
        write('plan.json',dict(cache=str(cache),entries=before,apply=apply,storage=budget,gpu_calls=0,calculation_verified=False))
        if not budget['passed']:raise ValueError('Insufficient staging budget and reserve')
        if apply:
            for path,entry in zip(files,before,strict=True):
                folder=output/'staging'/path.stem;folder.mkdir(parents=True)
                row=compress_one(path,folder/path.name)
                if row['before']!=entry:raise ValueError('Cache changed after inventory')
                rows.append(row)
                with (output/'entries.jsonl').open('a') as stream:stream.write(json.dumps(row,sort_keys=True)+'\n')
        after=[checked(p) for p in files]
        if [(r['key'],r['bytes'],r['sha256']) for r in before]!=[(r['key'],r['bytes'],r['sha256']) for r in after]:raise ValueError('Cache keys/bytes changed')
        result=dict(passed=True,apply=apply,entries=len(files),compressed_entries=sum(r['status']=='compressed' for r in rows),already_compressed_entries=sum(r['compressed'] for r in before),logical_bytes=sum(r['bytes'] for r in before),allocated_before=sum(r['allocated_bytes'] for r in before),allocated_after=sum(r['allocated_bytes'] for r in after),allocated_reclaimed=sum(r['allocated_bytes'] for r in before)-sum(r['allocated_bytes'] for r in after),all_keys_bytes_and_sha256_equal=True,artifacts_per_entry=4,cache_format_changed=False,cache_identity_changed=False,source_or_capture_files_modified=False,gpu_calls=0,compiler_calls=0,calculation_verified=False)
        write('result.json',result);return result
    except BaseException as error:
        write('failure.json',dict(error=type(error).__name__+': '+str(error),completed_entries=len(rows),gpu_calls=0,calculation_verified=False));raise
