"""Exact-source saved module/JIT CUBIN admission; no compiler or driver calls."""
import hashlib,json
from pathlib import Path
from portable_compile_cache import quoted_headers
from portable_compiler_certificate import full_family
from portable_device_linker import validate_cubin

PROVIDER='saved-module-jit-cubin'
STAGE='cuda_linked_artifact_receipt'


def digest(raw):return hashlib.sha256(raw).hexdigest()


def key(identity):return digest(json.dumps(identity,sort_keys=True,separators=(',',':')).encode())


def admission(current,linked,producer,compiler,receipt,anchors):
    if current.get('purpose','sealed')!='sealed' or not full_family(linked.get('suite'),linked.get('golden',{}).get('baseline_suite')) or linked.get('purpose')!='compiler-diagnostic':raise ValueError('Saved CUBIN requires sealed battle and full compiler packages')
    baseline=current['golden'];certificate=linked['golden']
    if not baseline['source_sha256'] or any(value!=baseline['source_sha256'] for value in (certificate['source_sha256'],producer['source_sha256'],compiler['source_sha256'])):raise ValueError('Saved CUBIN source closure mismatch')
    if any(value!=baseline['generated_normalized'] for value in (certificate['generated_normalized'],producer['generated_normalized'],compiler['generated_normalized'])):raise ValueError('Saved CUBIN generated baseline mismatch')
    if producer['producer_package_id']!=linked['package_id'] or compiler['generated_sha256']['cuda']!=producer['cuda_sha256']:raise ValueError('Saved CUBIN full producer mismatch')
    upstream=compiler['compile_artifact'];identity=upstream['identity']
    if identity['artifact']!='ptx' or identity['source_sha256']!=producer['cuda_sha256'] or not identity['headers'] or not identity['compiler_files']:raise ValueError('Saved CUBIN compiler identity incomplete')
    if upstream['key']!=key(identity):raise ValueError('Saved CUBIN upstream compiler key mismatch')
    link_identity=receipt['identity']
    if link_identity['provider']!='diagnostic-nvjitlink' or link_identity['artifact']!='diagnostic-jit-linked-cubin' or receipt['key']!=key(link_identity):raise ValueError('Saved CUBIN linker identity mismatch')
    result=dict(schema=1,provider=PROVIDER,artifact='cubin',source_sha256=producer['cuda_sha256'],source_closure=baseline['source_sha256'],generated_normalized=baseline['generated_normalized'],headers=identity['headers'],upstream_compile=identity,link_identity=link_identity,anchors=anchors)
    return dict(identity=result,key=key(result),artifact_bytes=receipt['artifact']['bytes'],artifact_sha256=receipt['artifact']['sha256'],enabled=True,reused=True)


def read_verified(receipt,source,artifact):
    if not valid_receipt(receipt):raise ValueError('Invalid saved CUBIN receipt')
    source=Path(source);raw=source.read_bytes();identity=receipt['identity']
    if digest(raw)!=identity['source_sha256']:raise ValueError('Saved CUBIN exact CUDA source mismatch')
    headers={str(p.resolve()):digest(p.read_bytes()) for p in quoted_headers(raw)}
    if headers!=identity['headers']:raise ValueError('Saved CUBIN prelude/header mismatch')
    image=Path(artifact).read_bytes();metadata=validate_cubin(image)
    if metadata['sha256']!=receipt['artifact_sha256'] or metadata['bytes']!=receipt['artifact_bytes']:raise ValueError('Saved CUBIN artifact changed')
    return image,receipt


def valid_receipt(receipt):
    try:
        identity=receipt['identity']
        return bool(identity['schema']==1 and identity['provider']==PROVIDER and identity['artifact']=='cubin' and receipt['key']==key(identity) and receipt.get('enabled') is True and receipt.get('reused') is True and type(receipt['artifact_bytes']) is int and receipt['artifact_bytes']>0 and len(receipt['artifact_sha256'])==64 and all(c in '0123456789abcdef' for c in receipt['artifact_sha256']))
    except (KeyError,TypeError,ValueError):return False


def valid_marker(row):return row.get('stage')==STAGE and row.get('state')=='verified' and valid_receipt(row.get('receipt',{}))
