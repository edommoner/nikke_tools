"""Audit optional exact-source Metal pipeline receipts, without external cache IO."""
import hashlib,json,re

def digest(data):return hashlib.sha256(data).hexdigest()
def key_for(identity):
    return digest(json.dumps(identity,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())

def verify(transport,runtime,source,consumer,*,entry='portableEvents'):
    receipt=transport.get('pipeline_cache')
    enabled=runtime.get('metal_pipeline_cache_enabled',False)
    required=runtime.get('metal_pipeline_cache_required',False)
    if receipt is None:
        if enabled or required:raise ValueError('Missing Metal pipeline cache receipt')
        return dict(enabled=False,hit=False)
    if not enabled:raise ValueError('Unexpected Metal pipeline cache receipt')
    if not isinstance(receipt,dict) or type(receipt.get('schema')) is not int or receipt['schema']!=1:
        raise ValueError('Invalid Metal pipeline cache schema')
    for name in ['enabled','required','hit','native_archive_miss_rejected']:
        if type(receipt.get(name)) is not bool:raise ValueError('Invalid Metal pipeline cache flag')
    if not receipt['enabled'] or receipt['required']!=required or not receipt['native_archive_miss_rejected'] or required and not receipt['hit']:
        raise ValueError('Metal pipeline cache native hit requirement failed')
    identity=receipt.get('identity')
    expected=dict(schema='1',source_sha256=digest(source),consumer_sha256=digest(consumer),
        entry=entry,resident_stride=str(transport.get('runtime_stride_bytes',0)),
        threads_per_threadgroup='1',math_mode='safe',registry_id=str(transport['registry_id']),
        device=transport['device'],os_build=transport.get('pipeline_os_build'))
    if not isinstance(expected['os_build'],str) or not expected['os_build'] or identity!=expected or receipt.get('key')!=key_for(expected):
        raise ValueError('Metal pipeline cache identity mismatch')
    if type(receipt.get('archive_bytes')) is not int or receipt['archive_bytes']<=0 or not isinstance(receipt.get('archive_sha256'),str) or not re.fullmatch('[0-9a-f]{64}',receipt['archive_sha256']):
        raise ValueError('Invalid Metal archive content identity')
    seconds=receipt.get('archive_compile_seconds')
    if type(seconds) not in (int,float) or not 0<=seconds<1e9 or receipt['hit'] and seconds!=0:
        raise ValueError('Invalid Metal archive compile timing')
    return dict(enabled=True,hit=receipt['hit'],required=required,key=receipt['key'],
        native_archive_miss_rejected=True,external_cache_read=False,calculation_verified=False)
