"""CPU-only regression/performance check with saved Metal bytes as fixtures.

This does not produce a GPU capture, audit, seal, execution claim, or file cache
of native results. Every oracle/creation receipt is freshly computed here.
"""
import argparse,ast,contextlib,hashlib,importlib.util,json,os,sys,tempfile,time,shutil
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('coordinate_parent_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
from portable_parent_oracles import ParentOracles,provider
from portable_phase_audit import Journal

def baseline_projection(golden):
    return dict(input_sha256=golden['input_sha256'],source_sha256=golden['source_sha256'],
                entries=[{k:r[k] for k in ('name','input_sha256','native_sha256')} for r in golden['entries']])

def method_shapes(path,names=('prepare','compile_case','native_reference','compare','validate_rejection')):
    tree=ast.parse(Path(path).read_text())
    return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names}

def admission(current,original,source_package,capture):
    if current['suite']!='coordinate-burst-control' or original['suite']!=current['suite']:raise ValueError('Coordinate burst-control fixture package required')
    if baseline_projection(current['golden'])!=baseline_projection(original['golden']):raise ValueError('Fixture input/native/source baseline changed')
    old={r['path']:r['sha256'] for r in original['files']};new={r['path']:r['sha256'] for r in current['files']}
    critical={n for n in old if n.startswith(('gpu/','app/','data/','research/upstream/'))}
    # These files own live reuse and static reporting, not numeric execution.
    # The original preparation/reference/full-comparison methods are checked
    # separately below; no math, native observer or normalization is exempted.
    critical-={'app/portable_parent_oracles.py','app/portable_coordinate_frontier.py'}
    critical|={n for n in old if n.startswith('research/world_') or n in ('research/portable_phase_audit.py','research/summarize-portable-cross-gpu.py','scripts/run-metal-probe.swift')}
    for name in critical:
        if name not in new or old[name]!=new[name]:raise ValueError('Fixture numeric/runtime/observer source changed: '+name)
    script='research/verify-coordinate-burst-control-short.py'
    if method_shapes(source_package/script)!=method_shapes(ROOT/script):raise ValueError('Original coordinate preparation/reference/comparator changed')
    names=('native_value','compare_readback','forbid_gpu','audit_capture','audited_comparison')
    if method_shapes(source_package/'scripts/nikke_gpu.py',names)!=method_shapes(ROOT/'scripts/nikke_gpu.py',names):raise ValueError('Original full comparison/audit boundary changed')
    run=cli.load(capture/'run.json');claim=cli.load(source_package/'gpu-claimed-metal.json');evidence=cli.load(capture/'evidence.json');result=cli.load(capture/'result.json');comparison=cli.load(capture/'comparison.json')
    if run.get('mode')!='gpu' or run.get('backend')!='metal' or run['package_id']!=original['package_id'] or claim['package_id']!=original['package_id'] or Path(claim['capture']).resolve()!=capture.resolve():raise ValueError('Original Metal execution claim mismatch')
    if result.get('calculation_verified') is not True or comparison.get('calculation_verified') is not True or comparison.get('mismatches')!=[] or evidence.get('gpu_execution_verified') is not True or evidence.get('backend')!='metal':raise ValueError('Successful original Metal fixture required')
    if evidence['source_sha256']!=current['golden']['source_sha256'] or evidence['input_sha256']!=current['golden']['input_sha256'] or evidence['output_sha256']!=current['golden']['output_sha256']:raise ValueError('Fixture Metal fingerprint mismatch')
    cli.check_records(capture,cli.load(capture/'artifacts.json')['files'])

def key(domain):
    from world_coordinate_comparison_context import ROUTES
    return (domain[0]['name'],*(bool(domain[0].get(flag)) for flag,_ in ROUTES))

def check(source_package,capture,output):
    output=Path(output);output.mkdir(exist_ok=False,parents=True)
    current=cli.verify_package(ROOT);original=cli.verify_saved_package(source_package)
    admission(current,original,source_package,capture)
    anchors={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source_package/'gpu-package.json',capture/'artifacts.json',capture/'run.json',capture/'comparison.json')}
    adapter=cli.open_suite(current);rows,_=adapter.prepare();targets={}
    journal=Journal(output/'phases.jsonl')
    for _,_,domain in rows:
        if domain is None:continue
        target=provider(adapter,domain)
        if target is None or target[4]!='reference' or target[3] is not domain:raise ValueError('Direct original native provider required')
        owner,name,fn,_,_=target;k=(id(owner),name)
        item=targets.setdefault(k,dict(owner=owner,name=name,fn=fn,keys=set()));item['keys'].add(key(domain))
    calls=[0]
    with tempfile.TemporaryDirectory(prefix='nikke-parent-reuse-fixture-') as tmp,contextlib.ExitStack() as stack:
        fixture=Path(tmp)
        # Hardlinks are used only as read-only fixtures, not a fabricated GPU run.
        for name in ('readback.bin','generated.cu','generated.metal','evidence.json'):os.link(capture/name,fixture/name)
        for item in targets.values():
            def witnessed(domain,entry=item):
                if key(domain) in entry['keys']:calls[0]+=1
                return entry['fn'](domain)
            stack.enter_context(patch.dict(item['owner'],{item['name']:witnessed}))
        stack.enter_context(patch.object(cli,'open_suite',return_value=adapter))
        parent=ParentOracles(current,fixture)
        try:
            started=time.perf_counter();pre=journal.invoke('fresh_native_preflight',cli.cpu_preflight,current,parent_oracles=parent,input_capture=fixture);pre_seconds=time.perf_counter()-started;pre_calls=calls[0]
            for name in ('preparation.jsonl','input-preflight.json'):shutil.copyfile(fixture/name,output/name)
            if not parent.usable:raise ValueError('Fixture unexpectedly requires fresh fallback')
            started=time.perf_counter();cached=journal.invoke('live_parent_comparison',cli.compare_readback,current,fixture,parent_oracles=parent);cached_seconds=time.perf_counter()-started;cached_calls=calls[0]-pre_calls
            if not cached['calculation_verified'] or cached_calls!=0:raise ValueError('Live parent reuse did not preserve all comparisons')
            parent.close()
            started=time.perf_counter();fresh=journal.invoke('fresh_native_comparison',cli.compare_readback,current,fixture,adapter);fresh_seconds=time.perf_counter()-started;fresh_calls=calls[0]-pre_calls-cached_calls
            if not fresh['calculation_verified'] or {k:v for k,v in cached.items() if k!='parent_oracles'}!=fresh:raise ValueError('Fresh and reused comparisons differ')
            if pre_calls!=pre['native_oracles'] or fresh_calls!=pre_calls or cached['parent_oracles']['reused_native_cases']!=pre_calls:raise ValueError('Unexpected native invocation counts')
        finally:parent.close()
    cli.verify_package(ROOT)
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=want for p,want in anchors.items()):raise ValueError('Original package/capture anchors changed')
    cli.check_records(capture,cli.load(capture/'artifacts.json')['files'])
    for name,value in [('fresh-comparison-test.json',fresh),('reused-comparison-test.json',cached),('cpu-preflight-test.json',pre)]:cli.write(output/name,value)
    report=dict(schema='coordinate-parent-reuse-cpu-test-v1',passed=True,mode='cpu-fixture-check',gpu_calls=0,
        calculation_verified=False,independent_audit=False,gpu_execution_verified=False,
        package_id=current['package_id'],source_gpu_package_id=original['package_id'],source_capture=str(capture.resolve()),
        inputs=cached['input_count'],native_cases=pre_calls,preflight_native_calls=pre_calls,additional_comparison_native_calls=cached_calls,fresh_comparison_native_calls=fresh_calls,
        reused_context_cases=cached['parent_oracles'].get('reused_context_cases',0),preflight_seconds=pre_seconds,reused_comparison_seconds=cached_seconds,fresh_comparison_seconds=fresh_seconds,
        identical_full_comparison_results=True,saved_native_values_loaded=False,original_capture_modified=False,
        scope='Fresh live-parent preflight and auxiliary receipt reuse test against original saved Metal bytes; no GPU dispatch/capture or independent-audit cache')
    cli.write(output/'result.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-package',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    with cli.forbid_gpu():print(json.dumps(check(a.source_package,a.capture,a.out),ensure_ascii=False,indent=2))
