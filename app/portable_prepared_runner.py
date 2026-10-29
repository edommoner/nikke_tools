"""Parent of one prepared CUDA launch, followed by separate bounded CPU audits.

No alternate calculation, compiler fallback or native result cache. The old
run protocols keep their admission path; this consumes only authenticated
in-process authority for the originally reserved attempt.
"""
import os
from pathlib import Path
from unittest.mock import patch
from portable_admission_authority import authenticate,claim,is_windows,PROTOCOL
from portable_admission_handoff import Handoff
from portable_admission_snapshot import binding,digest
from portable_staged_preflight import exclusive
from portable_prepared_execution import RUN_SCHEMA
from portable_prepared_audit import envelope
from portable_capture_storage import space_status


def separated(output,roots):
    if any(output==p or p in output.parents or output in p.parents for p in roots):
        raise ValueError('Prepared output/capture must be separate from source and evidence')


def run(cli,preparation_package,preparation_stage,expected_binding,snapshot_sha256,certificate_sha256,out,*,
        original_workspace,slang_root,generation_cache,timeout=60,header_materials=None):
    if not is_windows():raise ValueError('Prepared execution parent requires Windows')
    if type(timeout) is not int or not 1<=timeout<=60:raise ValueError('Prepared GPU timeout must be an integer from 1 to 60')
    b=binding(expected_binding);out=Path(out).resolve();capture=Path(b['future_capture']).resolve()
    prep=Path(preparation_package).resolve();stage=Path(preparation_stage).resolve()
    workspace=Path(original_workspace).resolve();slang=Path(slang_root);cache=Path(generation_cache)
    if any(not p.is_absolute() or not p.is_dir() for p in (slang,cache)) or not workspace.is_dir():
        raise ValueError('Explicit existing workspace, SDK and paired generation cache required')
    request=cli.load(stage/'recipe.json')['object_request']
    roots=[cli.ROOT.resolve(),prep,stage,Path(request['owner_package']).resolve(),Path(request['transaction']).resolve(),workspace,slang.resolve(),cache.resolve()]
    if header_materials is not None:roots.append(Path(header_materials['snapshot']).resolve())
    separated(out,[capture,*roots]);separated(capture,roots)
    if os.path.lexists(out) or os.path.lexists(capture):raise FileExistsError('Fresh parent output and original future capture required')
    m=cli.verify_package(cli.ROOT)
    if cli.is_development(m) or cli.compiler_only(m) or m.get('baseline_migration'):
        raise ValueError('Prepared execution requires a sealed, executable battle')
    config=cli.SUITES[m['suite']];wire=cli.registered_entry_wire_preflight(config)
    out.mkdir(parents=True,exist_ok=False)
    claim_entered=False;capture_created=False;launch_entered=False
    try:
        env=dict(NIKKE_SLANG_ROOT=str(slang.resolve()),NIKKE_SLANG_GENERATION_CACHE=str(cache.resolve()),
            NIKKE_SLANG_GENERATION_REQUIRED='1',NIKKE_CUDA_ARTIFACT='cubin',NIKKE_VALIDATION_JOB_MEMORY_MB='2048')
        with patch.dict(os.environ,env):
            if wire is not None:exclusive(out/'entry-wire-preflight.json',wire)
            # This helper installs its own stronger file-only guard and saves
            # the original cached reader before doing so. An outer forbid_gpu
            # would replace that reader before it can be saved.
            outputs,generation=cli.required_generation_snapshot(m)
            exclusive(out/'generation-preflight.json',generation)
            with cli.forbid_gpu():
                authority=authenticate(cli,prep,stage,expected_binding=b,snapshot_sha256=snapshot_sha256,
                    certificate_sha256=certificate_sha256,out=out/'authority',header_materials=header_materials)
                a=authority.receipt
                with Handoff(cli,a['snapshot'],a['snapshot_sha256'],certificate_sha256=a['certificate_sha256'],
                        expected_binding=b,expected_suite=m['suite'],expected_golden=m['golden'],consumer_package_id=m['package_id'],header_materials=header_materials) as handoff:
                    packed,_=handoff.read_input()
                    image,_=handoff.image_for_source(outputs['cuda'].read_bytes())
                    output_bytes=len(m['golden']['entries'])*config.get('output_words',786432)*4
                    needed=len(packed)+output_bytes+len(image)+sum(p.stat().st_size for p in outputs.values())
                    storage=space_status(capture,needed)
                    exclusive(out/'storage.json',dict(storage,input_bytes=len(packed),output_bytes=output_bytes,gpu_calls=0,calculation_verified=False))
                    if storage['passed'] is not True:raise ValueError('Prepared input/readback storage budget unavailable')
                # Recheck all consumer sources immediately before append-only
                # ownership publication; authenticate/claim recheck the rest.
                if cli.verify_package(cli.ROOT)!=m:raise ValueError('Prepared consumer changed before claim')
                claim_entered=True;owner=claim(cli,authority)
            claim_sha=digest((cli.ROOT/'gpu-claimed-cuda.json').read_bytes())
            capture.mkdir(parents=True,exist_ok=False)
            capture_created=True
            exclusive(capture/'run.json',dict(schema=RUN_SCHEMA,input_protocol=PROTOCOL,mode='snapshot-gpu',backend='cuda',
                package_id=m['package_id'],capture=str(capture),claim_sha256=claim_sha,
                authority_sha256=owner['authority_sha256'],binding=b))
            launch_entered=True
            facts=cli.run_job(capture,'cuda',timeout,workspace,prepared_claim_sha256=claim_sha)
            # No native battle runs in this parent. CPU envelope checks leave
            # calculation false until the existing fresh group audits finish.
            with cli.forbid_gpu():
                _,audit=envelope(cli,m,capture,claim_sha)
                evidence=cli.load(capture/'evidence.json')
                matches=evidence['output_sha256']==m['golden']['output_sha256']
                output=cli.file_records(capture,['readback.bin'])[0]
                if output['bytes']!=output_bytes or output['sha256']!=evidence['output_sha256']:
                    raise ValueError('Prepared parent raw readback/evidence mismatch')
            result=dict(mode='snapshot-gpu-pending-native-audit',protocol=PROTOCOL,package_id=m['package_id'],
                capture=str(capture),gpu_execution_completed=True,readback_fingerprint_matches=matches,
                containment_verified=audit['containment_verified'],process_preservation_verified=audit['process_preservation_verified'],
                preservation_verified=audit['preservation_verified'],calculation_verified=False,passed=False,
                independent_post_audit_required=True,execution_claim_retained=True,gpu_retries=0,full_goal_complete=False)
            exclusive(capture/'result.json',result);exclusive(out/'result.json',result)
            if not matches:raise ValueError('Prepared readback differs from sealed golden; fresh native diagnosis required')
            return result
    except BaseException as error:
        exclusive(out/'failure.json',dict(error=type(error).__name__+': '+str(error),execution_claim_may_exist=claim_entered,
            launch_entered=launch_entered,gpu_calls=None if launch_entered else 0,calculation_verified=False,gpu_retries=0))
        raise
    finally:
        if capture_created:cli.collect(capture,capture/'artifacts.json')
        cli.collect(out,out/'artifacts.json')
