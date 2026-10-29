"""Fresh native audit of an explicitly Metal-origin, byte-identical wire witness.

This never authenticates an unseen CUDA capture. A subsequent source-host
envelope audit is required before the conditional result can certify CUDA.
"""
import json,os,subprocess,sys,time
from pathlib import Path

CUDA_SUMMARY_SHA='7bfa35fef584ae4efdecd22a869f3660f3bf9d424549755c29a6b98a964117ce'


def bind_summary(cli,raw,manifest,wire):
    if cli.sha(raw)!=CUDA_SUMMARY_SHA:raise ValueError('Pinned CUDA peer summary required')
    peer=json.loads(raw);g=manifest['golden']
    if (peer.get('schema')!='resident-current-cuda-public-summary-v1'
        or peer.get('package_id')!=manifest['package_id'] or peer.get('input_sha256')!=g['input_sha256']
        or peer.get('input_count')!=len(g['entries']) or peer.get('native_reference_cases')!=cli.SUITES[manifest['suite']]['native']
        or peer.get('logical_output_sha256')!=g['output_sha256']
        or peer.get('logical_output_sha256')!=wire['logical_view_sha256']
        or peer.get('output_sha256')!=wire['raw_joined_output_sha256']
        or peer.get('output_bytes')!=wire['output_bytes'] or wire['input_count']!=peer['input_count']
        or any(peer.get(k) is not True for k in ('gpu_protocol_verified','shared_metal_wire_equivalence_verified','current_source_metal_seal_verified'))):
        raise ValueError('Peer CUDA bytes, current corpus or wire witness differ')
    return peer


def bind_current_source(cli,current,executed_root,executed):
    from portable_continuation_package import functions
    from portable_partitioned_cli import CURRENT
    if (current.get('partitioned_cuda_execution',{}).get('schema')!=CURRENT
        or executed.get('partitioned_cuda_execution',{}).get('schema')!=CURRENT
        or current['suite']!='coordinate-resident-frames' or current['golden']!=executed['golden']):
        raise ValueError('Immutable current-source owner and complete original golden required')
    permitted={'scripts/nikke_gpu.py','app/portable_partitioned_native.py','app/portable_partitioned_cli.py',
               'app/portable_cpu_tests.py','app/portable_resident_validation.py','tests/test_portable_partitioned_native.py'}
    before={r['path']:r for r in executed['files']};after={r['path']:r for r in current['files']}
    if any(after.get(n)!=r for n,r in before.items() if n not in permitted):
        raise ValueError('Witness owner changed executed native/GPU/data/test bytes')
    a=functions((Path(executed_root)/'scripts/nikke_gpu.py').read_text());b=functions((cli.ROOT/'scripts/nikke_gpu.py').read_text())
    if any(b.get(n)!=v for n,v in a.items() if n not in ('main','_pre_partitioned_main')):
        raise ValueError('Witness owner changed original CLI calculation/comparison functions')
    return True


def bind_sources(cli,current,executed_root,executed,generation,witness):
    bind_current_source(cli,current,executed_root,executed)
    if witness['suite']!=current['suite'] or any(witness['golden'].get(k)!=current['golden'][k]
        for k in ('entries','input_sha256','output_sha256')):
        raise ValueError('Entire witness input/output/native corpus must match current source')
    if generation['suite']!=current['suite']:raise ValueError('Generation suite differs')
    if generation.get('purpose')=='development':
        # The actual M5 dispatch preceded seal. Validate its exact development
        # expectation projection; never manufacture sealed output fields.
        expected=dict(input_sha256=current['golden']['input_sha256'],source_sha256=current['golden']['source_sha256'],
            entries=[{k:v for k,v in row.items() if k!='output_sha256'} for row in current['golden']['entries']])
        if generation['golden']!=expected:raise ValueError('Exact development input/native/source expectations required')
    elif generation['golden']!=current['golden']:
        raise ValueError('Current paired generation source must match executed source')
    return True


def compare_group(cli,context,indices,progress):
    from portable_partitioned_native import compare_readback
    from portable_partitioned_addresses import check_source,WORDS
    manifest=cli.verify_package(cli.ROOT)
    if manifest['package_id']!=context['package_id']:raise ValueError('Witness audit owner changed')
    for item in context['anchors']:cli.check_records(Path(item['root']),item['records'])
    check_source(cli.ROOT,cli.SUITES[manifest['suite']]['source'],WORDS)
    generation=cli.load(Path(context['generation_capture'])/'generation-preflight.json')['generation']['artifacts']
    layout=cli.load(Path(context['witness_capture'])/'readback.bin.batches/plan.json')
    with cli.forbid_gpu():
        result=compare_readback(cli,manifest,input_path=Path(context['witness_capture'])/'input.bin',
            raw_path=Path(context['witness_capture'])/'readback.bin.partial',layout=layout,batch_size=16,
            generation=generation,generated_paths={k:Path(context['generation_capture'])/('generated.'+s) for k,s in (('cuda','cu'),('metal','metal'))},
            case_indices=indices,progress=progress)
    for item in context['anchors']:cli.check_records(Path(item['root']),item['records'])
    if cli.verify_package(cli.ROOT)!=manifest:raise ValueError('Witness audit packet changed during native comparison')
    return result


def run(cli,source_package,witness_package,witness_capture,generation_package,generation_capture,cuda_summary,out,timeout=180,group_size=8):
    from portable_continuation_package import owner_snapshot
    from portable_partitioned_addresses import audit,check_source,WORDS
    from portable_partitioned_native import aggregate
    from portable_comparison_groups import partition
    from portable_staged_preflight import outside,exclusive
    if type(timeout) is not int or not 1<=timeout<=180 or type(group_size) is not int or not 1<=group_size<=16:
        raise ValueError('Bounded fresh witness groups required')
    paths=[Path(p).resolve() for p in (source_package,witness_package,witness_capture,generation_package,generation_capture,cuda_summary)]
    source_package,witness_package,witness_capture,generation_package,generation_capture,cuda_summary=paths
    out=outside(out,[cli.ROOT,*paths]);out.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter()
    try:
        with cli.forbid_gpu():
            manifest=cli.verify_package(cli.ROOT)
            source=owner_snapshot(cli,source_package);gen=owner_snapshot(cli,generation_package);old=owner_snapshot(cli,witness_package)
            bind_sources(cli,manifest,source_package,source['manifest'],gen['manifest'],old['manifest'])
            for root in (cli.ROOT,source_package,generation_package,witness_package):
                check_source(root,source['config']['source'],WORDS)
            wire=audit(cli,witness_package,witness_capture,out/'metal-witness-wire.json')
            peer=bind_summary(cli,cuda_summary.read_bytes(),source['manifest'],wire)
            generation=cli.load(generation_capture/'generation-preflight.json')
            if (generation.get('package_id')!=gen['manifest']['package_id'] or generation.get('passed') is not True
                or generation.get('generated_normalized')!=manifest['golden']['generated_normalized']):
                raise ValueError('Current generation capture belongs to another source')
            anchors=[]
            for root,names in ((source_package,['gpu-package.json']), (witness_package,['gpu-package.json']),
                (generation_package,['gpu-package.json']), (witness_capture,['artifacts.json','run.json','input.bin','readback.bin.batches/plan.json']),
                (generation_capture,['artifacts.json','generation-preflight.json','generated.cu','generated.metal']),
                (cuda_summary.parent,[cuda_summary.name])):
                anchors.append(dict(root=str(root),records=cli.file_records(root,names)))
            context=dict(package_id=manifest['package_id'],source_package_id=source['manifest']['package_id'],
                witness_capture=str(witness_capture),generation_capture=str(generation_capture),anchors=anchors,
                raw_output_sha256=peer['output_sha256'],witness_origin='retained Metal capture',original_cuda_capture_observed=False)
            exclusive(out/'context.json',context)
            planned=partition(wire['input_count'],group_size)
            exclusive(out/'plan.json',dict(case_groups=planned,per_group_timeout_seconds=timeout,gpu_calls=0))
            script='''import importlib.util,json,pathlib,sys
from types import SimpleNamespace
root=pathlib.Path(sys.argv[1]);spec=importlib.util.spec_from_file_location('witness_cli',root/'scripts/nikke_gpu.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
from portable_partitioned_witness import compare_group
with c.forbid_gpu(): r=compare_group(SimpleNamespace(**vars(c)),c.load(pathlib.Path(sys.argv[2])),json.loads(sys.argv[3]),sys.argv[4])
print(json.dumps(r))
'''
            groups=[]
            for i,indices in enumerate(planned):
                prefix=out/str(i);before=time.perf_counter()
                result=subprocess.run([sys.executable,'-B','-c',script,str(cli.ROOT),str(out/'context.json'),json.dumps(indices),str(prefix.with_suffix('.phases.jsonl'))],
                    cwd=cli.ROOT,capture_output=True,text=True,timeout=timeout,check=True)
                prefix.with_suffix('.stdout.log').write_text(result.stdout);prefix.with_suffix('.stderr.log').write_text(result.stderr)
                row=json.loads(result.stdout);row['elapsed_seconds']=time.perf_counter()-before
                exclusive(prefix.with_suffix('.json'),row);groups.append(row)
            comparison=aggregate(manifest,wire,groups,planned,timeout,os.getpid())
            if comparison['native_oracles']!=source['config']['native']:raise ValueError('Every native case required')
            for item in anchors:cli.check_records(Path(item['root']),item['records'])
            if (cli.verify_package(cli.ROOT)!=manifest or owner_snapshot(cli,source_package)!=source
                or owner_snapshot(cli,generation_package)!=gen or owner_snapshot(cli,witness_package)!=old):
                raise ValueError('Original source packages changed during witness audit')
            report=dict(schema='partitioned-identical-wire-native-witness-v1',package_id=manifest['package_id'],
                source_package_id=source['manifest']['package_id'],comparison=comparison,wire=wire,
                witness_origin='retained Metal capture',original_cuda_capture_observed=False,
                witness_calculation_verified=True,conditional_cuda_native_equivalence_verified=True,
                pending_original_cuda_envelope_audit=True,calculation_verified=False,
                environment_preservation_verified=False,overall_stage_passed=False,
                public_gpu_admitted=False,full_goal_complete=False,gpu_calls=0,
                elapsed_seconds=time.perf_counter()-started,anchors=anchors)
            exclusive(out/'result.json',report);return report
    except BaseException as error:
        for name in ('stdout','stderr'):
            value=getattr(error,name,None)
            if value is not None:(out/(name+'.log')).write_text(value.decode(errors='replace') if isinstance(value,bytes) else value)
        exclusive(out/'failure.json',dict(error=type(error).__name__+': '+str(error),calculation_verified=False,gpu_calls=0))
        raise
