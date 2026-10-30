"""Exact-source saved module/JIT CUBIN admission; no compiler or driver calls."""
import hashlib,json
from pathlib import Path, PurePosixPath, PureWindowsPath
from portable_compile_cache import quoted_headers
from portable_compiler_certificate import full_family
from portable_device_linker import validate_cubin

PROVIDER='saved-module-jit-cubin'
STAGE='cuda_linked_artifact_receipt'


def digest(raw):return hashlib.sha256(raw).hexdigest()


def key(identity):return digest(json.dumps(identity,sort_keys=True,separators=(',',':')).encode())


def missing_identities(rows):
    """Lossless identities; FILETIME stays decimal text across Node/Python."""
    result=[]
    for row in rows:
        pid=row['pid'];path=row['path'];created=row['creation_filetime_ticks']
        if (type(pid) is not int or not 0<pid<=0xffffffff or not isinstance(path,str) or not path
                or type(created) is not str or not created.isascii() or not created.isdecimal()
                or str(int(created))!=created or not 0<int(created)<2**64):
            raise ValueError('Incomplete historical process identity')
        result.append(dict(pid=pid,path=path.lower(),creation_filetime_ticks=created))
    result.sort(key=lambda row:(row['pid'],row['path'],row['creation_filetime_ticks']))
    if len({(r['pid'],r['path'],r['creation_filetime_ticks']) for r in result})!=len(result):raise ValueError('Duplicate historical process identity')
    return result


def validate_history_binding(binding,*,portable=False):
    if (type(binding) is not dict or set(binding)!={'capture','observation_sha256','missing_identities','disposition'}
            or binding['disposition']!='retained-failure' or not isinstance(binding['capture'],str)
            or not (Path(binding['capture']).is_absolute() if not portable else
                    PurePosixPath(binding['capture']).is_absolute() or PureWindowsPath(binding['capture']).is_absolute())
            or type(binding['observation_sha256']) is not str
            or len(binding['observation_sha256'])!=64 or any(c not in '0123456789abcdef' for c in binding['observation_sha256'])
            or type(binding['missing_identities']) is not list or not binding['missing_identities']
            or any(type(r) is not dict or set(r)!={'pid','path','creation_filetime_ticks'} for r in binding['missing_identities'])
            or binding['missing_identities']!=missing_identities(binding['missing_identities'])):
        raise ValueError('Invalid historical link observation binding')


def retained_link_environment(capture,observation_raw,comparison,binding):
    """Bind one prior failure without upgrading its preservation outcome."""
    missing=comparison['missing_existing_processes']
    if binding is None:
        if missing:raise ValueError('Saved CUBIN link observation missing process')
        return None
    validate_history_binding(binding)
    if (not missing or comparison['all_monitored_processes_preserved'] is not False or comparison['termination_cause']!='unknown'
            or Path(binding['capture']).resolve()!=Path(capture).resolve()
            or binding['observation_sha256']!=digest(observation_raw)
            or binding['missing_identities']!=missing_identities(missing)):
        raise ValueError('Historical link observation binding mismatch')
    return dict(capture=str(Path(capture).resolve()),observation_sha256=digest(observation_raw),
                missing_identities=missing_identities(missing),preservation_verified=False,
                service_preservation_verified=comparison['identified_nikke_service_preservation_verified'],
                service_status_before=comparison['nikke_service_status_before'],service_status_after=comparison['nikke_service_status_after'],
                termination_cause='unknown',disposition='retained-failure')


def validate_historical_environment(history,*,portable=False):
    fields={'capture','observation_sha256','missing_identities','preservation_verified','service_preservation_verified',
            'service_status_before','service_status_after','termination_cause','disposition'}
    if (type(history) is not dict or set(history)!=fields or history['preservation_verified'] is not False
            or type(history['service_preservation_verified']) is not bool or history['termination_cause']!='unknown'
            or history['service_preservation_verified'] and 'unverified' in (history['service_status_before'],history['service_status_after'])
            or any(history[k] not in ('identified','absent','unverified') for k in ('service_status_before','service_status_after'))):
        raise ValueError('Historical failure cannot become preserved')
    validate_history_binding({k:history[k] for k in ('capture','observation_sha256','missing_identities','disposition')},portable=portable)


def exact_ptx_reuse(producer,compiler,original):
    """Bind two audited producers by actual bytes and complete compiler identity."""
    old,old_compiler,old_raw,current_raw=original
    if type(old_raw) is not bytes or type(current_raw) is not bytes or not old_raw or old_raw!=current_raw:
        raise ValueError('Saved CUBIN reuse requires identical original/current PTX bytes')
    if old['ptx']!=producer['ptx'] or digest(current_raw)!=producer['ptx']['sha256'] or len(current_raw)!=producer['ptx']['bytes']:
        raise ValueError('Saved CUBIN reuse PTX metadata mismatch')
    prior=old_compiler['compile_artifact'];now=compiler['compile_artifact']
    if prior['identity']!=now['identity'] or prior['key']!=now['key'] or prior['key']!=key(prior['identity']):
        raise ValueError('Saved CUBIN reuse compiler identity mismatch')
    for entry in (prior,now):
        if entry['artifact_sha256']!=digest(current_raw) or entry['artifact_bytes']!=len(current_raw):
            raise ValueError('Saved CUBIN reuse compiler artifact mismatch')
    if old_compiler['generated_sha256']['cuda']!=old['cuda_sha256'] or prior['identity']['source_sha256']!=old['cuda_sha256']:
        raise ValueError('Saved CUBIN reuse original CUDA identity mismatch')
    return dict(original_producer=old,current_producer=producer,ptx_sha256=digest(current_raw),
        ptx_bytes=len(current_raw),compiler_key=now['key'])


def admission(current,linked,producer,compiler,receipt,anchors,*,sealed_producer=None,ptx_reuse=None,historical_environment=None):
    baseline=current['golden'];source_owner=linked;certificate=linked['golden']
    reuse=None
    if ptx_reuse is not None:
        if sealed_producer is None:raise ValueError('PTX reuse requires an audited current sealed producer')
        reuse=exact_ptx_reuse(producer,compiler,ptx_reuse)
    if sealed_producer is None:
        if current.get('purpose','sealed')!='sealed' or not full_family(linked.get('suite'),certificate.get('baseline_suite')) or linked.get('purpose')!='compiler-diagnostic':raise ValueError('Saved CUBIN requires sealed battle and full compiler packages')
    else:
        certificate=sealed_producer['golden'];source_owner=sealed_producer
        if any(p.get('purpose','sealed')!='sealed' or p.get('selected_cases') for p in (current,linked,sealed_producer)) or certificate!=baseline or type(certificate.get('entries')) is not list or not certificate['entries'] or not certificate.get('input_sha256') or not certificate.get('output_sha256'):
            raise ValueError('Saved CUBIN requires the exact independently sealed battle producer')
        if anchors.get('producer_manifest_sha256')!=producer.get('producer_manifest_sha256') or not producer.get('producer_manifest_sha256') or anchors.get('package_id')!=linked['package_id'] or anchors.get('link_receipt_key')!=receipt['key']:
            raise ValueError('Saved CUBIN sealed producer anchors mismatch')
        linked_producer=receipt['identity'].get('origin',{}).get('object_receipt',{}).get('identity',{}).get('origin',{}).get('producer')
        if linked_producer!=(reuse['original_producer'] if reuse is not None else producer):raise ValueError('Saved CUBIN linked object producer mismatch')
    if not baseline['source_sha256'] or any(value!=baseline['source_sha256'] for value in (certificate['source_sha256'],producer['source_sha256'],compiler['source_sha256'])):raise ValueError('Saved CUBIN source closure mismatch')
    if any(value!=baseline['generated_normalized'] for value in (certificate['generated_normalized'],producer['generated_normalized'],compiler['generated_normalized'])):raise ValueError('Saved CUBIN generated baseline mismatch')
    if producer['producer_package_id']!=source_owner['package_id'] or compiler['generated_sha256']['cuda']!=producer['cuda_sha256']:raise ValueError('Saved CUBIN full producer mismatch')
    upstream=compiler['compile_artifact'];identity=upstream['identity']
    if identity['artifact']!='ptx' or identity['source_sha256']!=producer['cuda_sha256'] or not identity['headers'] or not identity['compiler_files']:raise ValueError('Saved CUBIN compiler identity incomplete')
    if upstream['key']!=key(identity):raise ValueError('Saved CUBIN upstream compiler key mismatch')
    link_identity=receipt['identity']
    if link_identity['provider']!='diagnostic-nvjitlink' or link_identity['artifact']!='diagnostic-jit-linked-cubin' or receipt['key']!=key(link_identity):raise ValueError('Saved CUBIN linker identity mismatch')
    result=dict(schema=1,provider=PROVIDER,artifact='cubin',source_sha256=producer['cuda_sha256'],source_closure=baseline['source_sha256'],generated_normalized=baseline['generated_normalized'],headers=identity['headers'],upstream_compile=identity,link_identity=link_identity,anchors=anchors)
    if sealed_producer is not None:
        result['sealed_battle_producer']=dict(package_id=source_owner['package_id'],manifest_sha256=producer['producer_manifest_sha256'],input_sha256=certificate['input_sha256'],output_sha256=certificate['output_sha256'])
    if reuse is not None:result['exact_ptx_reuse']=reuse
    if historical_environment is not None:
        validate_historical_environment(historical_environment)
        result['historical_link_environment']=historical_environment
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


def valid_receipt(receipt,*,portable=False):
    try:
        identity=receipt['identity']
        if 'historical_link_environment' in identity:validate_historical_environment(identity['historical_link_environment'],portable=portable)
        return bool(identity['schema']==1 and identity['provider']==PROVIDER and identity['artifact']=='cubin' and receipt['key']==key(identity) and receipt.get('enabled') is True and receipt.get('reused') is True and type(receipt['artifact_bytes']) is int and receipt['artifact_bytes']>0 and len(receipt['artifact_sha256'])==64 and all(c in '0123456789abcdef' for c in receipt['artifact_sha256']))
    except (KeyError,TypeError,ValueError):return False


def valid_marker(row,*,portable=False):return row.get('stage')==STAGE and row.get('state')=='verified' and valid_receipt(row.get('receipt',{}),portable=portable)


def verify_phases(rows,receipt):
    """Shared saved-image phase checks for CLI audits and product responses."""
    if any(r['stage'].startswith('nvrtc') or r['stage'] in ('cuda_compile_cache','cuda_live_compile_forbidden') for r in rows):raise ValueError('Unexpected live NVRTC in saved CUBIN execution')
    if [r.get('receipt') for r in rows if r['stage']=='cuda_linked_origin' and r['state']=='verified']!=[receipt]:raise ValueError('Saved CUBIN source admission phase mismatch')
    if [r['state'] for r in rows if r['stage']=='cuda_linked_artifact']!=['entered','returned']:raise ValueError('Incomplete saved CUBIN read phase')
    origin_index=next(i for i,r in enumerate(rows) if r['stage']=='cuda_linked_origin')
    read_indices=[i for i,r in enumerate(rows) if r['stage']=='cuda_linked_artifact']
    receipt_indices=[i for i,r in enumerate(rows) if r['stage']==STAGE and r['state']=='verified']
    if len(receipt_indices)!=1 or rows[receipt_indices[0]].get('receipt')!=receipt or not origin_index<read_indices[0]<read_indices[1]<receipt_indices[0]:raise ValueError('Saved CUBIN admission phase order mismatch')
    if rows[receipt_indices[0]].get('source_loads',1)!=1:raise ValueError('Saved CUBIN source load count mismatch')
    return True
