"""Read-only audit of a sanitized scalar-core report, never a GPU proof rerun."""
import hashlib,json,re
from pathlib import Path,PurePosixPath

MAX_FILES=64
MAX_BYTES=16*1024*1024

def audit(report_root,golden,normalize,manifest_sha256):
    root=Path(report_root).resolve();manifest_path=root/'manifest.json'
    if not manifest_path.resolve().is_relative_to(root) or manifest_path.stat().st_size>MAX_BYTES:raise ValueError('Invalid bounded report manifest')
    raw=manifest_path.read_bytes()
    def need(condition,message):
        if not condition:raise ValueError(message)
    def digest(data):return hashlib.sha256(data).hexdigest()
    need(isinstance(manifest_sha256,str) and re.fullmatch('[0-9a-f]{64}',manifest_sha256) is not None,'Trusted manifest SHA256 required')
    need(digest(raw)==manifest_sha256,'Report manifest fingerprint mismatch');manifest=json.loads(raw)
    need(manifest.get('schema')==1,'Unknown report schema')
    need(manifest.get('raw_sdk_personal_process_lists_and_settings_included') is False and manifest.get('original_artifacts_modified') is False,'Report must declare sanitized copies and unchanged originals')
    rows=manifest.get('files');need(isinstance(rows,list) and 1<=len(rows)<=MAX_FILES,'Invalid small-report file count')
    files={};total=len(raw)
    for row in rows:
        name=row.get('path');need(isinstance(name,str) and name and '\\' not in name and '\x00' not in name,'Invalid report path')
        rel=PurePosixPath(name);need(not rel.is_absolute() and '..' not in rel.parts and str(rel)==name and name!='manifest.json' and name not in files,'Unsafe or duplicate report path')
        need(rel.suffix in ('.json','.cu','.metal'),'Unsupported report payload')
        path=root.joinpath(*rel.parts);need(path.resolve().is_relative_to(root) and path.is_file(),'Report path escapes root or is missing')
        expected=row.get('export',{});size=expected.get('bytes');need(type(size) is int and 0<=size<=MAX_BYTES,'Invalid report payload size')
        total+=size;need(total<=MAX_BYTES,'Small report exceeds byte budget')
        need(path.stat().st_size==size,'Report payload size mismatch: '+name);data=path.read_bytes()
        need(digest(data)==expected.get('sha256'),'Report payload fingerprint mismatch: '+name);files[name]=(data,row)
    required=('safe-summary.json','package-provenance.json','gpu/proof/comparison.json','gpu/proof/evidence.json','gpu/proof/cpu-tests.json','gpu/stage-result.json','cache-check.json','saved-observation-counts.json','generated/damage_accum_probe.cu','generated/damage_accum_probe.metal')
    need(all(name in files for name in required),'Incomplete scalar-core report')
    load=lambda name:json.loads(files[name][0])
    summary=load('safe-summary.json');provenance=load('package-provenance.json');comparison=load('gpu/proof/comparison.json');evidence=load('gpu/proof/evidence.json');cache=load('cache-check.json');stage=load('gpu/stage-result.json');counts=load('saved-observation-counts.json')
    package=manifest.get('package_id');need(isinstance(package,str) and re.fullmatch('[0-9a-f]{64}',package) is not None,'Invalid source package identity')
    need(summary.get('package_id')==provenance.get('package_id')==cache.get('package_id')==stage.get('package_id')==package,'Source package identities disagree')
    need(summary.get('calculation_verified') is True and comparison.get('calculation_verified') is True and comparison.get('mismatches')==[] and evidence.get('gpu_execution_verified') is True,'Saved CUDA report did not verify calculation')
    need(evidence.get('backend')=='cuda' and evidence.get('transport',{}).get('backend')=='cuda','Expected saved CUDA evidence')
    need(evidence.get('source_sha256')==golden['source_sha256'],'Saved report source differs from sealed core')
    for key in ('input_sha256','output_sha256'):
        need(comparison.get(key)==evidence.get(key)==golden[key],'Saved '+key+' differs from sealed Metal')
    need(comparison.get('entries')==golden['entries'],'Per-input native/output fingerprints differ from sealed Metal')
    count=len(golden['entries']);need(comparison.get('input_count')==evidence['transport'].get('cases')==count,'Reported input counts disagree')
    need(evidence['transport'].get('output_bytes')==count*786432*4 and evidence['transport'].get('readback_stream',{}).get('output_sha256')==golden['output_sha256'],'Reported readback shape or fingerprint differs from sealed core')
    need(comparison.get('generated_normalized')==golden['generated_normalized'],'Saved generated fingerprints differ from sealed Metal')
    for backend,suffix in (('cuda','cu'),('metal','metal')):
        name='generated/damage_accum_probe.'+suffix;data,row=files[name]
        need(normalize(data)==golden['generated_normalized'][backend],'Exported generated '+backend+' differs under strict normalizer')
        need(row.get('source',{}).get('sha256')==evidence.get('generated_sha256',{}).get(backend),'Original generated fingerprint disagrees with receipt')
    runtime=evidence.get('resident_runtime',{});transport=evidence['transport'];need(runtime.get('stride')==transport.get('runtime_stride_bytes')==8 and runtime.get('fields')==[dict(name='nextOrder',scalar='uint64',count=1,offset=0,size=8)],'Unexpected scalar-core resident layout')
    need(transport.get('runtime_element_capacity')==count and transport.get('runtime_buffer_bytes')==count*8,'Unexpected scalar-core runtime buffer shape')
    cold=transport.get('compile_artifact',{});warm=cache.get('cache',{})
    need(cold.get('hit') is False and cache.get('passed') is True and warm.get('hit') is True,'Expected cold execution plus file-only warm cache check')
    for key in ('key','identity','artifact_sha256','artifact_bytes'):need(cold.get(key)==warm.get(key),'Cold/warm cache identities disagree: '+key)
    need(cold.get('identity',{}).get('source_sha256')==evidence['generated_sha256']['cuda'],'Cache source fingerprint differs from original CUDA')
    need(cache.get('gpu_calls')==0 and cache.get('nvrtc_compile_calls')==0,'Warm cache receipt must be file-only')
    need(manifest.get('environment_preservation_verified')==stage.get('whole_stage_environment_preservation_verified')==summary.get('environment_preservation_verified'),'Environment-preservation reports disagree')
    reported_environment=manifest['environment_preservation_verified']
    need(type(reported_environment) is bool and counts.get('original_environment_preservation_verified')==reported_environment,'Saved environment summary disagrees with manifest')
    need(type(stage.get('stage_verified')) is bool and (reported_environment or stage['stage_verified'] is False),'Whole-stage success contradicts failed environment preservation')
    need(not reported_environment or counts.get('outer_missing')==counts.get('inner_missing')==0,'Preservation success contradicts missing processes')
    need(counts.get('cause')==manifest.get('cause') and isinstance(counts.get('cause'),str),'Saved cause claims disagree')
    tests=load('gpu/proof/cpu-tests.json');need(all(r.get('exit_code')==0 and r.get('errors')==0 and r.get('failures')==0 for r in tests),'Saved proof CPU tests failed')
    return dict(schema=1,passed=True,scope='Sanitized report integrity and cross-Metal fingerprints only',manifest_sha256=manifest_sha256,package_id=package,files=len(files)+1,bytes=total,source_files=len(golden['source_sha256']),inputs=len(golden['entries']),per_input_native_and_output_fingerprints_identical=True,strict_generated_fingerprints_identical=True,reported_CUDA_calculation_verified=True,calculation_verified=False,CUDA_raw_independently_audited=False,compiled_CUBIN_independently_audited=False,full_battle_CUDA_verified=False,reported_environment_preservation_verified=reported_environment,reported_whole_stage_verified=stage['stage_verified'],environment_preservation_verified=False,whole_stage_verified=False,cause='unknown',reported_cause=counts['cause'],cause_independently_verified=False,saved_observation_counts=counts,cache_receipts_consistent=True,cold_compile_seconds=summary.get('compile',{}).get('seconds'),warm_file_only_seconds=cache.get('elapsed_seconds'),proof_cpu_tests=sum(r['tests'] for r in tests),gpu_calls=0,nvrtc_compile_calls=0)
