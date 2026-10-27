"""CPU source generation plus read-only cache check, before native work/claim."""
import hashlib,os,time
from pathlib import Path
from portable_metal_cache_probe import probe_identity

def identity(source,consumer,device,*,stride=0):
    if device.get('passed') is not True or device.get('device_visible') is not True:raise ValueError('Fresh visible Metal device required')
    for field in ('device','registry_id','os_build'):
        if not isinstance(device.get(field),str) or not device[field]:raise ValueError('Missing current Metal identity: '+field)
    if not device['registry_id'].isdecimal() or type(stride) is not int or not 0<=stride<2**32:raise ValueError('Invalid Metal registry/stride')
    digest=lambda b:hashlib.sha256(b).hexdigest()
    return dict(schema='1',source_sha256=digest(source),consumer_sha256=digest(consumer),entry='portableEvents',resident_stride=str(stride),threads_per_threadgroup='1',math_mode='safe',registry_id=device['registry_id'],device=device['device'],os_build=device['os_build'])

def preflight(api,manifest,capture,device):
    required=os.environ.get('NIKKE_METAL_PIPELINE_REQUIRED','0')
    if required not in ('0','1'):raise ValueError('Required Metal cache flag must be0 or1')
    if required!='1':return False
    started=time.perf_counter();root=Path(api.ROOT);capture=Path(capture)
    report=dict(schema='required-metal-cache-preflight-v1',passed=False,package_id=manifest['package_id'],gpu_calls=0,pipeline_compile_calls=0,calculation_verified=False,source_generation_api_calls=0,native_cache_revalidation_required=True)
    try:
        cache=Path(os.environ.get('NIKKE_METAL_PIPELINE_CACHE',''))
        if not cache.is_absolute() or not cache.is_dir() or cache.is_symlink():raise ValueError('Existing absolute private Metal cache required')
        import portable_backend
        source=api.SUITES[manifest['suite']]['source']
        outputs,hashes=portable_backend.build(source,'portableEvents');report['source_generation_api_calls']=1
        if hashes!=manifest['golden']['source_sha256']:raise ValueError('Metal source identity changed during preflight')
        plan=portable_backend.resident_plan(source,'portableEvents',outputs)
        request=identity(outputs['metal'].read_bytes(),(root/'scripts/run-metal-probe.swift').read_bytes(),device,stride=plan['stride'] if plan else 0)
        checked=probe_identity(cache,request);report.update(cache=checked,passed=checked['hit_snapshot'])
        if not report['passed']:raise ValueError('Required Metal pipeline cache miss or corruption: '+str(checked.get('reason')))
    except Exception as error:
        report['error']=type(error).__name__+': '+str(error)
        raise RuntimeError('Required Metal pipeline cache unavailable before CPU preparation; no execution claim consumed: '+str(error)) from error
    finally:
        report['elapsed_seconds']=time.perf_counter()-started
        api.write(capture/'metal-cache-preflight.json',report)
    return True
