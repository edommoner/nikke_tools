"""Read-only advisory cache snapshot; no driver, compiler or GPU imports."""
import hashlib,json
from pathlib import Path
from portable_metal_cache import verify

def probe(cache,transport,source,consumer):
    report=dict(schema='metal-cache-file-probe-v1',hit_snapshot=False,gpu_calls=0,compiler_calls=0,driver_calls=0,calculation_verified=False,context_current_verified=False,native_cache_revalidation_required=True)
    try:
        receipt=transport['pipeline_cache'];runtime=dict(metal_pipeline_cache_enabled=True,metal_pipeline_cache_required=receipt['required'])
        checked=verify(transport,runtime,source,consumer);key=checked['key'];report.update(key=key,reference_identity=receipt['identity'])
        _snapshot(cache,key,receipt['identity'],expected=dict(identity=receipt['identity'],archive_sha256=receipt['archive_sha256'],archive_bytes=receipt['archive_bytes']))
        report.update(hit_snapshot=True,archive_bytes=receipt['archive_bytes'],archive_sha256=receipt['archive_sha256'],reason=None)
    except (KeyError,TypeError,ValueError,OSError) as error:report['reason']=type(error).__name__+': '+str(error)
    return report


def _snapshot(cache,key,identity,*,expected=None):
    import re
    root=Path(cache);record=root/(key+'.json');archive=root/(key+'.metalarc')
    if root.is_symlink() or record.is_symlink() or archive.is_symlink():raise ValueError('Cache members must be ordinary files')
    before_record=record.stat();before_archive=archive.stat()
    if not 0<before_record.st_size<=65536 or not 0<before_archive.st_size<=512*1024**2:raise ValueError('Cache member size limit')
    metadata=json.loads(record.read_bytes())
    if not isinstance(metadata,dict) or set(metadata)!={'identity','archive_bytes','archive_sha256'}:raise ValueError('Invalid cache record')
    if metadata['identity']!=identity or type(metadata['archive_bytes']) is not int or metadata['archive_bytes']!=before_archive.st_size or not isinstance(metadata['archive_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',metadata['archive_sha256']):raise ValueError('Cache metadata mismatch')
    if expected is not None and metadata!=expected:raise ValueError('Cache metadata mismatch')
    digest=hashlib.sha256()
    with archive.open('rb') as stream:
        while chunk:=stream.read(1024**2):digest.update(chunk)
    if digest.hexdigest()!=metadata['archive_sha256']:raise ValueError('Cache archive hash mismatch')
    signature=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    if signature(before_record)!=signature(record.stat()) or signature(before_archive)!=signature(archive.stat()):raise ValueError('Cache changed during snapshot')
    return dict(archive_bytes=metadata['archive_bytes'],archive_sha256=metadata['archive_sha256'])


def probe_identity(cache,identity):
    """Inspect an exact requested identity without fabricating a native receipt."""
    from portable_metal_cache import key_for
    report=dict(schema='metal-cache-current-file-probe-v1',hit_snapshot=False,gpu_calls=0,compiler_calls=0,driver_calls=0,calculation_verified=False,context_current_verified=False,native_cache_revalidation_required=True)
    try:
        if not isinstance(identity,dict) or not identity or any(not isinstance(v,str) or not v for v in identity.values()):raise ValueError('Explicit string cache identity required')
        key=key_for(identity);report.update(key=key,requested_identity=identity)
        report.update(_snapshot(cache,key,identity),hit_snapshot=True,reason=None)
    except (KeyError,TypeError,ValueError,OSError) as error:report['reason']=type(error).__name__+': '+str(error)
    return report
