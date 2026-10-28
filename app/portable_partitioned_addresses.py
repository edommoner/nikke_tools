"""Read-only typed-address view, never numeric output normalization.

The frozen DFS wire stores an absolute word address and a receipt ID at
scratch+530/+531. Separate GPU buffers have separate address spaces. Validate
both ends of every reference, then form a logical global-address view in RAM.
Raw GPU files, old failed receipts and all non-address words remain untouched.
"""
import hashlib,json,struct
from pathlib import Path

PROFILE='resident-frames-dfs-receipt-address-v1'
WORDS=2064786
TYPED_BASE=1769856
DFS_BASE=TYPED_BASE+153568
RECEIPT_BASE=TYPED_BASE+3568
SOURCES={
 'gpu/destructible_battle_runtime.slang':'91be4819b2f6f28d7fdedfbed014bea3c1aaa67f396968e506b39f11f2c75c8a',
 'gpu/destructible_shield_frame_hooks.slang':'8ab3384c7b37fd774ef20a2b60c15fd37f4dd0bbd965832e79b608aadd747d92',
 'gpu/world_coordinate_typed_entry.slang':'2dc5fb456a7f7edbceb4b5122fe99f6750f418a170ddb47694cb9678e3828f71',
 'gpu/world_coordinate_resident_frames_entry.slang':'c8a609773a753df312a3714958fe61e6b73a48c66a1afb120f957801b5851dc8'}


def logical_row_inplace(row,local_case,first_case):
    if type(row) is not bytearray or len(row)!=WORDS*4 or any(type(i) is not int or i<0 for i in (local_case,first_case)):raise ValueError('Exact frozen DFS wire row and explicit indices required')
    logical_case=local_case+first_case
    if (logical_case+1)*WORDS>0xffffffff:raise ValueError('Logical word addresses exceed the original uint32 wire')
    changes=[];active=0
    for depth in range(32):
        field=DFS_BASE+depth*544+530;pointer,receipt=struct.unpack_from('<II',row,field*4)
        if receipt==0:
            if pointer!=0:raise ValueError('Unowned DFS scratch address')
            continue
        if not 1<=receipt<=128:raise ValueError('DFS receipt address is outside the frozen bank')
        relative=RECEIPT_BASE+(receipt-1)*1040
        if pointer!=local_case*WORDS+relative or struct.unpack_from('<I',row,relative*4)[0]!=receipt:raise ValueError('DFS address does not target its own receipt')
        active+=1;logical=logical_case*WORDS+relative
        if pointer!=logical:changes.append(dict(global_case=logical_case,local_case=local_case,depth=depth,word=field,receipt_id=receipt,raw_address=pointer,logical_address=logical))
    # Validate every reference before modifying the temporary view. The source
    # files are never opened for writing, and no float/damage/status is changed.
    for item in changes:struct.pack_into('<I',row,item['word']*4,item['logical_address'])
    return active,changes


def check_source(root,source,words):
    if source!='gpu/world_coordinate_resident_frames_entry.slang' or words!=WORDS:raise ValueError('Unknown address-space wire profile')
    for name,digest in SOURCES.items():
        if hashlib.sha256((Path(root)/name).read_bytes()).hexdigest()!=digest:raise ValueError('Unknown DFS address ABI source: '+name)


def view_file(raw,layout,expected_cases=None):
    raw=Path(raw)
    if raw.is_symlink() or layout['output_words']!=WORDS or raw.stat().st_size!=layout['output_bytes']:raise ValueError('Incomplete address-profile raw wire')
    joined=hashlib.sha256();logical=hashlib.sha256();changes=[];active=0;verified=0;chunks=[]
    buffer=bytearray(WORDS*4)
    with raw.open('rb') as stream:
        for batch in layout['batches']:
            if batch['first_case']!=verified or type(batch['cases']) is not int or not 1<=batch['cases']<=layout['batch_size']:raise ValueError('Noncontiguous address-profile batch plan')
            chunk=hashlib.sha256()
            for local in range(batch['cases']):
                if stream.readinto(buffer)!=len(buffer):raise ValueError('Short raw row')
                joined.update(buffer);chunk.update(buffer)
                count,relocated=logical_row_inplace(buffer,local,batch['first_case']);active+=count;changes.extend(relocated)
                if expected_cases is not None and hashlib.sha256(buffer).hexdigest()!=expected_cases[verified]['output_sha256']:raise ValueError('Non-address words or logical references differ: '+expected_cases[verified]['name'])
                logical.update(buffer);verified+=1
            chunks.append(chunk.hexdigest())
        if stream.read(1) or verified!=layout['input_count']:raise ValueError('Incomplete logical address view')
    return dict(profile=PROFILE,raw_joined_output_sha256=joined.hexdigest(),logical_view_sha256=logical.hexdigest(),
        active_references_checked=active,logical_address_changes=changes,input_count=verified,batch_raw_sha256=chunks,
        raw_gpu_bytes_modified=0,numeric_words_modified=0,materialized_output_created=False)


def audit(cli,package,capture,out):
    from portable_continuation_package import owner_snapshot
    from portable_partitioned_transport import plan,digest_file
    from portable_staged_preflight import outside,exclusive
    package=Path(package).resolve();capture=Path(capture).resolve();out=outside(out,[package,capture])
    if out.exists():raise FileExistsError(out)
    controller_sha=cli.sha(Path(__file__).read_bytes())
    info=owner_snapshot(cli,package);m=info['manifest'];g=m['golden']
    if m['suite']!='coordinate-resident-frames' or not m.get('partitioned_diagnostic') or m.get('purpose')!='sealed':raise ValueError('Frozen resident-frame partitioned diagnostic required')
    for name,digest in SOURCES.items():
        if g['source_sha256'].get(name)!=digest or cli.sha((package/name).read_bytes())!=digest:raise ValueError('Unknown DFS address ABI source: '+name)
    anchors=cli.load(capture/'artifacts.json')['files'];cli.check_records(capture,anchors)
    run=cli.load(capture/'run.json');result=cli.load(capture/'result.json');facts=cli.load(capture/'execution.json')
    if (run.get('package_id')!=m['package_id'] or run.get('mode')!='partitioned-file-diagnostic-v1' or run.get('backend')!='metal'
        or result.get('passed') is not False or result.get('calculation_verified') is not False or facts.get('timed_out') is not False
        or facts.get('child_exit_code')!=1 or any(facts.get(k) is not None for k in ('error','cleanup_error','observation_error'))
        or (capture/'readback.bin').exists()):raise ValueError('Only the preserved failed flat-wire diagnostic can be inspected')
    if 'Complete ordered partitioned output differs from sealed baseline' not in (capture/'stderr.log').read_text():raise ValueError('Unknown partitioned failure')
    cpu=cli.load(capture/'cpu.json');packed=(capture/'input.bin').read_bytes();layout=cli.load(capture/'readback.bin.batches/plan.json')
    if (cpu.get('passed') is not True or cpu.get('native_oracles')!=info['config']['native']
        or cpu.get('input_count')!=len(g['entries']) or cli.sha(packed)!=g['input_sha256']
        or layout!=plan(packed,run['input_words'],WORDS,run['batch_size'],runtime_stride=143048)):
        raise ValueError('Frozen complete input, native preflight or partition plan changed')
    command=cli.load(capture/'readback.bin.batches/metal-command.json');status=json.loads(command['stdout'])
    if command['exit_code']!=0 or len(status['batches'])!=len(layout['batches']) or status['pipeline_instances']!=1 or status['buffer_allocations']!=3:raise ValueError('Incomplete Metal sequence')
    raw=capture/'readback.bin.partial'
    if raw.stat().st_size!=layout['output_bytes']:raise ValueError('Incomplete raw joined output')
    view=view_file(raw,layout,g['entries'])
    from portable_metal_cache import verify as verify_metal_cache
    generated=package/'research/portable-build'/(Path(info['config']['source']).stem+'.metal')
    generation=cli.load(capture/'generation-preflight.json')
    if (generation.get('generated_normalized')!=g['generated_normalized']
        or cli.sha(generated.read_bytes())!=generation['generation']['artifacts']['metal']['sha256']):raise ValueError('Saved generation source changed')
    runtime=cli.load(capture/'runtime.json');cache_checks=[]
    for i,(batch,transport) in enumerate(zip(layout['batches'],status['batches'],strict=True)):
        if (transport['cases']!=batch['cases'] or transport['input_bytes']!=batch['input_bytes'] or transport['output_bytes']!=batch['output_bytes'] or transport['command_status']!='completed'):raise ValueError('Metal batch dimensions changed')
        if digest_file(capture/('readback.bin.batches/'+str(i)+'.out'))!=view['batch_raw_sha256'][i]:raise ValueError('Joined raw differs from preserved batch readback')
        cache_checks.append(verify_metal_cache(transport,runtime,generated.read_bytes(),(package/'scripts/run-metal-probe.swift').read_bytes()))
    if view['input_count']!=len(g['entries']) or view['logical_view_sha256']!=g['output_sha256']:raise ValueError('Incomplete logical wire identity')
    cli.check_records(capture,anchors)
    if cli.sha(Path(__file__).read_bytes())!=controller_sha:raise ValueError('Address auditor changed during inspection')
    report=dict(schema='partitioned-wire-address-audit-v1',profile=PROFILE,package_id=m['package_id'],
        input_sha256=g['input_sha256'],input_count=view['input_count'],output_bytes=raw.stat().st_size,
        raw_joined_output_sha256=view['raw_joined_output_sha256'],logical_view_sha256=view['logical_view_sha256'],expected_output_sha256=g['output_sha256'],
        source_abi=SOURCES,view_controller_sha256=controller_sha,metal_cache_checks=cache_checks,
        active_references_checked=view['active_references_checked'],logical_address_changes=view['logical_address_changes'],
        logical_wire_equivalence_verified=True,original_stage_passed=False,original_capture_modified=False,
        materialized_output_created=False,raw_gpu_bytes_modified=0,numeric_words_modified=0,expected_hash_changed=False,
        gpu_calls=0,compiler_calls=0,native_calls=0,calculation_verified=False,full_goal_complete=False,
        scope='Read-only explicit address-space view. Raw physical GPU readbacks differ; no byte-normalization of numeric/status data and no promotion of the failed stage.')
    out.parent.mkdir(parents=True,exist_ok=True);exclusive(out,report);return report
