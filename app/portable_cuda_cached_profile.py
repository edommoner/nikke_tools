"""Explicit cached-CUBIN execution policy, reusing the shared CUDA transport."""
import contextlib,os
from pathlib import Path
from unittest.mock import patch

PROFILE='compile-cache-only-v1'

def validate(config,backend,*,execute=True,linked=False,environment=None):
    name=config.get('cuda_cache_profile')
    if name is None:return False
    if name!=PROFILE:raise ValueError('Unknown cached CUDA profile')
    if not execute:return False
    env=os.environ if environment is None else environment
    if backend!='cuda' or linked:raise ValueError('Cached CUDA profile requires the shared CUDA compile-cache transport')
    directory=env.get('NIKKE_CUDA_COMPILE_CACHE','')
    if env.get('NIKKE_CUDA_CACHE_REQUIRED')!='1' or not directory or not Path(directory).is_absolute() or not Path(directory).is_dir():
        raise ValueError('Cached CUDA profile requires --require-cache and an existing absolute --compile-cache')
    if env.get('NIKKE_CUDA_ARTIFACT','cubin')!='cubin' or env.get('NIKKE_CUDA_PTXAS_OPT_LEVEL')!='1':
        raise ValueError('Cached CUDA profile requires CUBIN with --ptxas-level1')
    source=env.get('NIKKE_CUDA_PREFLIGHT_SOURCE','')
    if not source or not Path(source).is_absolute() or not Path(source).is_file():
        raise ValueError('Cached CUDA profile requires an existing absolute --cached-cuda-source')
    return True

@contextlib.contextmanager
def library_guard(config,backend,journal):
    if not validate(config,backend):yield;return
    import portable_backend
    journal.emit('cuda_cache_only_profile','required',profile=PROFILE)
    def gate(original,loader):
        def load(name,*args,**kwargs):
            base=str(name).replace('\\','/').rsplit('/',1)[-1].lower()
            if base.startswith('nvrtc'):
                journal.emit('cuda_cache_only_library','rejected',loader=loader,name=base)
                raise RuntimeError('NVRTC library forbidden by cached CUDA profile')
            journal.emit('cuda_cache_only_library','allowed',loader=loader,name=base)
            return original(name,*args,**kwargs)
        return load
    with contextlib.ExitStack() as stack:
        for loader in ('WinDLL','CDLL'):
            original=getattr(portable_backend.C,loader,None)
            if original is not None:stack.enter_context(patch.object(portable_backend.C,loader,gate(original,loader)))
        yield

def audit(config,runtime,rows):
    if config.get('cuda_cache_profile') is None:return None
    if config['cuda_cache_profile']!=PROFILE:raise ValueError('Unknown cached CUDA profile')
    from portable_phase_audit import valid_cache_hit
    markers=[r for r in rows if r.get('stage')=='cuda_cache_only_profile']
    hits=[r for r in rows if valid_cache_hit(r)]
    if (runtime.get('cache_required')!='1' or runtime.get('compile_cache_enabled') is not True
        or runtime.get('cuda_artifact_kind')!='cubin' or runtime.get('ptxas_optimization_level')!='1'
        or len(markers)!=1 or markers[0].get('state')!='required' or markers[0].get('profile')!=PROFILE
        or len(hits)!=1):raise ValueError('Cached CUDA profile requires an observed required CUBIN hit')
    if any(r.get('stage','').lower().startswith('nvrtc') or
           r.get('stage')=='cuda_cache_only_library' and (r.get('state')!='allowed' or r.get('name','').lower().startswith('nvrtc')) for r in rows):
        raise ValueError('Cached CUDA profile observed a forbidden compiler request')
    return dict(profile=PROFILE,required_cache_hit_verified=True,nvrtc_calls=0,
                compiler_library_requests=0,calculation_verified=False,
                scope='Compiler-free cached transport policy only; full calculation still requires the existing readback comparison and native trace audit')
