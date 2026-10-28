"""Fresh native comparison of saved, source-pinned partitioned Metal results.

The old failed capture is never promoted or modified. This is a separate CPU
audit: the packet's original semantic comparator receives an explicitly typed
logical row view; all raw bytes and all original golden fingerprints remain.
"""
import array,hashlib,json,os,subprocess,sys,time
from pathlib import Path


def compare(cli,manifest,capture,generated_root,case_indices=None,progress=None):
    from portable_partitioned_addresses import WORDS,logical_row_inplace
    from portable_partitioned_transport import plan
    from portable_comparison_groups import selection
    from portable_phase_audit import Journal
    journal=Journal(Path(progress)) if progress is not None else None
    with cli.forbid_gpu():
        if journal:journal.emit('fresh_native_prepare','entered')
        adapter=cli.open_suite(manifest)
        entries,packed=cli.prepare_entries(adapter,manifest)
        if journal:journal.emit('fresh_native_prepare','returned',input_count=len(entries))
        golden=manifest['golden'];capture=Path(capture)
        if packed!=(capture/'input.bin').read_bytes() or cli.sha(packed)!=golden['input_sha256']:
            raise ValueError('Fresh native input differs from frozen saved input')
        recipe=cli.load(capture/'run.json');layout=cli.load(capture/'readback.bin.batches/plan.json')
        if layout!=plan(packed,adapter.suite.INPUT,WORDS,recipe['batch_size'],runtime_stride=143048):
            raise ValueError('Fresh native partition plan differs')
        if len(entries)!=layout['input_count'] or len(entries)!=len(golden['entries']):
            raise ValueError('Every frozen native/rejection case is required')
        selected=selection(len(entries),case_indices);selected_set=set(selected)
        rows=[];mismatches=[];raw_hash=hashlib.sha256();logical_hash=hashlib.sha256();index=0;active=0;changes=[]
        with (capture/'readback.bin.partial').open('rb') as stream:
            for batch in layout['batches']:
                for local in range(batch['cases']):
                    part=bytearray(stream.read(WORDS*4))
                    if len(part)!=WORDS*4:raise ValueError('Truncated saved raw during native comparison')
                    raw_hash.update(part)
                    count,relocated=logical_row_inplace(part,local,batch['first_case'])
                    active+=count;changes.extend(relocated);logical_hash.update(part)
                    if index not in selected_set:
                        index+=1;continue
                    name,words,domain=entries[index]
                    block=array.array('I');block.frombytes(part)
                    if sys.byteorder!='little':block.byteswap()
                    try:
                        if journal:journal.emit('fresh_native_compare','entered',case_index=index,name=name)
                        if domain is None:
                            if block[0]!=64:raise ValueError('Expected rejection status64')
                            if hasattr(adapter,'validate_rejection'):adapter.validate_rejection(block,name)
                            if cli.SUITES[manifest['suite']].get('require_rejection_stage'):adapter.validate_rejection_stage(block,name)
                            native=dict(status=64)
                        else:
                            if block[0]!=0:raise ValueError('Expected GPU success status0; got status'+str(block[0]))
                            native=adapter.compare(block,domain)
                        row=dict(name=name,output_sha256=cli.sha(part),native_sha256=adapter.cross.digest(native))
                        # Input fingerprints are over the original little-endian
                        # wire, regardless of the host's array byte order.
                        start=4+index*adapter.suite.INPUT*4
                        row['input_sha256']=cli.sha(packed[start:start+adapter.suite.INPUT*4])
                        if row!=golden['entries'][index]:raise ValueError('Full original case fingerprint mismatch')
                        rows.append(row)
                        if journal:journal.emit('fresh_native_compare','returned',case_index=index,name=name)
                    except (AssertionError,ValueError,KeyError,IndexError) as error:
                        mismatches.append(dict(index=index,name=name,reason=cli.comparison_exception_details(error)))
                        if journal:journal.emit('fresh_native_compare','raised',case_index=index,name=name,error=str(error))
                    index+=1
            if stream.read(1):raise ValueError('Trailing raw bytes during native comparison')
        if index!=len(entries) or logical_hash.hexdigest()!=golden['output_sha256']:
            raise ValueError('Incomplete or changed logical native readback')
        source=Path(cli.SUITES[manifest['suite']]['source']).stem
        generation=cli.load(capture/'generation-preflight.json')['generation']['artifacts'];generated={}
        for backend,suffix in (('cuda','cu'),('metal','metal')):
            raw=(Path(generated_root)/'research/portable-build'/(source+'.'+suffix)).read_bytes()
            if cli.sha(raw)!=generation[backend]['sha256'] or len(raw)!=generation[backend]['bytes']:
                raise ValueError('Saved generated artifact differs from actual dispatch generation receipt')
            generated[backend]=adapter.cross.normalized(raw)
        if generated!=golden['generated_normalized']:raise ValueError('Strict paired generated-code fingerprint mismatch')
        return dict(calculation_verified=not mismatches and case_indices is None,comparison_subset_verified=not mismatches,
                    case_indices=selected,total_input_count=index,input_count=len(selected),native_oracles=sum(entries[i][2] is not None for i in selected),
                    entries=rows,mismatches=mismatches,input_sha256=cli.sha(packed),raw_output_sha256=raw_hash.hexdigest(),
                    logical_output_sha256=logical_hash.hexdigest(),generated_normalized=generated,
                    active_references_checked=active,logical_address_changes=changes,gpu_calls=0,
                    child_pid=os.getpid(),live_parent_receipt_present=False,raw_gpu_bytes_modified=0,numeric_words_modified=0)


def aggregate(manifest,wire,groups,planned,timeout,parent_pid):
    from portable_comparison_groups import validate_facts
    if not groups or len(groups)!=len(planned):raise ValueError('Every native group required')
    entries=[];facts=[]
    for r,indices in zip(groups,planned,strict=True):
        if (r.get('calculation_verified') is not False or r.get('comparison_subset_verified') is not True
            or r.get('case_indices')!=indices or r.get('total_input_count')!=wire['input_count']
            or r.get('input_count')!=len(indices) or r.get('entries')!=[manifest['golden']['entries'][i] for i in indices]
            or r.get('mismatches')!=[] or r.get('input_sha256')!=wire['input_sha256']
            or r.get('raw_output_sha256')!=wire['raw_joined_output_sha256']
            or r.get('logical_output_sha256')!=wire['logical_view_sha256']
            or r.get('logical_address_changes')!=wire['logical_address_changes']
            or r.get('active_references_checked')!=wire['active_references_checked']
            or r.get('generated_normalized')!=manifest['golden']['generated_normalized']
            or r.get('child_pid')==parent_pid or r.get('live_parent_receipt_present') is not False
            or r.get('gpu_calls')!=0):raise ValueError('Fresh full independent native group failed')
        entries.extend(r['entries'])
        facts.append(dict(child_pid=r['child_pid'],case_indices=indices,input_count=len(indices),native_cases=r['native_oracles'],elapsed_seconds=r['elapsed_seconds']))
    total=dict(schema='independent-metal-audit-groups-v1',input_count=wire['input_count'],
               native_cases=sum(r['native_oracles'] for r in groups),groups=facts,child_pids=[r['child_pid'] for r in groups],
               live_parent_receipt_present=False,per_group_timeout_seconds=timeout)
    validate_facts(total,wire['input_count'],timeout)
    if entries!=manifest['golden']['entries']:raise ValueError('Native aggregation omitted or reordered frozen cases')
    return dict(calculation_verified=True,entries=entries,independent_comparison=total,
                input_count=wire['input_count'],native_oracles=total['native_cases'],gpu_calls=0,
                input_sha256=wire['input_sha256'],raw_output_sha256=wire['raw_joined_output_sha256'],
                logical_output_sha256=wire['logical_view_sha256'])


def run(cli,source_package,capture,out,timeout=240,group_size=16):
    from portable_partitioned_addresses import audit
    from portable_continuation_package import owner_snapshot,functions
    from portable_staged_preflight import outside,exclusive
    if type(timeout) is not int or not 1<=timeout<=240:raise ValueError('Bounded CPU-only native audit required')
    if type(group_size) is not int or not 1<=group_size<=16:raise ValueError('Bounded native group size required')
    source_package=Path(source_package).resolve();capture=Path(capture).resolve()
    out=outside(out,[cli.ROOT,source_package,capture]);out.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter();manifest=cli.verify_package(cli.ROOT);original=owner_snapshot(cli,source_package)['manifest']
    if not manifest.get('partitioned_diagnostic') or manifest['golden']!=original['golden']:
        raise ValueError('Independent immutable packet must preserve the entire original golden')
    old={r['path']:r for r in original['files']};new={r['path']:r for r in manifest['files']}
    helpers=set(manifest['partitioned_diagnostic']['added'])|set(original['partitioned_diagnostic']['added'])
    if any(new.get(n)!=r for n,r in old.items() if n not in helpers|{'scripts/nikke_gpu.py'}):
        raise ValueError('Independent native/GPU/data/test source differs from executed packet')
    a=functions((source_package/'scripts/nikke_gpu.py').read_text());b=functions((cli.ROOT/'scripts/nikke_gpu.py').read_text())
    if any(b.get(n)!=value for n,value in a.items()):raise ValueError('Independent packet changed original comparison functions')
    anchors=cli.file_records(capture,['artifacts.json',*[r['path'] for r in cli.load(capture/'artifacts.json')['files']]])
    with cli.forbid_gpu():wire=audit(cli,source_package,capture,out/'wire-audit.json')
    from portable_comparison_groups import partition
    planned=partition(wire['input_count'],group_size)
    exclusive(out/'plan.json',dict(case_groups=planned,per_group_timeout_seconds=timeout,gpu_calls=0,calculation_verified=False))
    # No Python/native state crosses this boundary, only immutable path names.
    script='''import importlib.util,json,sys,pathlib
from types import SimpleNamespace
root=pathlib.Path(sys.argv[1])
s=importlib.util.spec_from_file_location('partitioned_native_owner',root/'scripts/nikke_gpu.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
from portable_partitioned_native import compare
m=c.verify_package(root)
with c.forbid_gpu():r=compare(SimpleNamespace(**vars(c)),m,pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3]),json.loads(sys.argv[4]),sys.argv[5])
if c.verify_package(root)!=m:raise ValueError('Independent packet changed during native comparison')
print(json.dumps(r))
'''
    try:
        groups=[]
        for group_index,indices in enumerate(planned):
            before=time.perf_counter();prefix=out/str(group_index)
            result=subprocess.run([sys.executable,'-B','-c',script,str(cli.ROOT),str(capture),str(source_package),json.dumps(indices),str(prefix.with_suffix('.phases.jsonl'))],cwd=cli.ROOT,
                                  capture_output=True,text=True,timeout=timeout,check=True)
            prefix.with_suffix('.stdout.log').write_text(result.stdout);prefix.with_suffix('.stderr.log').write_text(result.stderr)
            group=json.loads(result.stdout);group['elapsed_seconds']=time.perf_counter()-before
            cli.check_records(capture,anchors)
            exclusive(prefix.with_suffix('.json'),group);groups.append(group)
        comparison=aggregate(manifest,wire,groups,planned,timeout,os.getpid())
        if comparison['native_oracles']!=cli.SUITES[manifest['suite']]['native']:raise ValueError('Incomplete native coverage')
        cli.check_records(capture,anchors)
        if cli.verify_package(cli.ROOT)!=manifest or owner_snapshot(cli,source_package)['manifest']!=original:
            raise ValueError('Independent or original packet changed')
        report=dict(schema='partitioned-saved-native-audit-v1',package_id=manifest['package_id'],
                    original_package_id=original['package_id'],source_capture=str(capture),comparison=comparison,
                    wire_audit_sha256=cli.sha((out/'wire-audit.json').read_bytes()),capture_anchors=anchors,
                    calculation_verified=True,original_stage_passed=False,original_capture_modified=False,
                    full_goal_complete=False,public_gpu_admitted=False,gpu_calls=0,
                    elapsed_seconds=time.perf_counter()-started,
                    scope='Independent native equivalence for the entire frozen corpus using an explicit typed address view; the original failed raw-wire stage remains failed.')
        exclusive(out/'result.json',report);return report
    except BaseException as error:
        for name in ('stdout','stderr'):
            value=getattr(error,name,None)
            if value is not None:(out/(name+'.log')).write_text(value.decode(errors='replace') if isinstance(value,bytes) else value)
        exclusive(out/'failure.json',dict(error=type(error).__name__+': '+str(error),calculation_verified=False,gpu_calls=0))
        raise
