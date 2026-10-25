"""File-only audit of data-only packages sharing exact paired generation artifacts.

This proves source reuse, never an NVRTC/driver cache hit or battle equivalence.
"""
import hashlib,json
from pathlib import Path
from portable_generation_cache import audit_receipt

CONSUMERS=('app/portable_compile_cache.py','app/portable_backend.py','scripts/run-metal-probe.swift')

def compatible(reference,candidate):
    if reference['source_sha256']!=candidate['source_sha256']:raise ValueError('GPU source changed; data-only reuse is unavailable')
    if reference['identity']!=candidate['identity']:raise ValueError('Generation/compiler identity changed')
    if reference['artifacts']!=candidate['artifacts']:raise ValueError('Paired generated artifacts changed')
    if reference['consumers']!=candidate['consumers'] or set(reference['consumers'])!=set(CONSUMERS):raise ValueError('Transport/cache consumer changed or is missing')
    return dict(source_reuse_verified=True,paired_cuda_metal_artifacts_equal=True,
        candidate_generation_cache_hit=candidate['cache_hit'],candidate_generation_compiler_invocations=candidate['compiler_invocations'],
        cuda_compiler_cache_hit_verified=False,metal_pipeline_cache_hit_verified=False,calculation_verified=False,gpu_calls=0,
        scope='Exact source, code-generation identity, generated pair and transport consumers; backend cache execution must be verified separately')

def inspect(api,package,generation):
    package=Path(package).resolve();generation=Path(generation).resolve();m=api.verify_saved_package(package)
    api.check_records(generation,api.load(generation/'artifacts.json')['files'])
    report=api.load(generation/'generation.json');receipt=api.load(generation/'generation-cache.json')
    if report['package_id']!=m['package_id'] or report['source_sha256']!=m['golden']['source_sha256']:raise ValueError('Generation package/source anchor mismatch')
    sources=m['golden']['source_sha256'];paths={t:generation/('generated.'+s) for t,s in (('cuda','cu'),('metal','metal'))}
    checked=audit_receipt(receipt,sources,paths)
    if any(report[k]!=checked[k] for k in ('cache_hit','compiler_invocations','verified')):raise ValueError('Generation report disagrees with audited receipt')
    files={r['path']:r['sha256'] for r in m['files']}
    for name,digest in receipt['identity']['consumers'].items():
        if files.get(name)!=digest:raise ValueError('Generation consumer differs from immutable package')
    consumers={name:files[name] for name in CONSUMERS}
    return dict(package_id=m['package_id'],input_sha256=m['golden'].get('input_sha256'),input_count=len(m['golden']['entries']),source_sha256=sources,identity=receipt['identity'],artifacts=receipt['artifacts'],consumers=consumers,cache_hit=checked['cache_hit'],compiler_invocations=checked['compiler_invocations'])

def run(api,reference_package,candidate_package,reference_generation,candidate_generation,*,require_hit=False):
    a=inspect(api,reference_package,reference_generation);b=inspect(api,candidate_package,candidate_generation);result=compatible(a,b)
    if require_hit and (not b['cache_hit'] or b['compiler_invocations']!=0):raise ValueError('Candidate generation must use the existing cache without compilation')
    result.update(schema=1,reference_package_id=a['package_id'],candidate_package_id=b['package_id'],
        reference_input_count=a['input_count'],candidate_input_count=b['input_count'],input_datasets_differ=a['input_sha256']!=b['input_sha256'],
        auditor_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        reference_generation_report_sha256=hashlib.sha256((Path(reference_generation)/'generation.json').read_bytes()).hexdigest(),candidate_generation_report_sha256=hashlib.sha256((Path(candidate_generation)/'generation.json').read_bytes()).hexdigest())
    return result
