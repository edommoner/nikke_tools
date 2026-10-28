"""Bound per-dispatch buffers while retaining an entire frozen wire result.

CUDA and Metal use their existing sequence adapters and one pipeline/context.
A full baseline fingerprint is mandatory: row independence is verified by the
complete ordered output, never inferred merely from the ability to split input.
"""
import hashlib,importlib.util,json,os,struct
from pathlib import Path

SCHEMA='partitioned-file-transport-v1'


def fingerprint(value):
    if type(value) is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('Exact lowercase SHA256 required')
    return value


def plan(packed,input_words,output_words,batch_size=16,*,runtime_stride=0):
    if (type(packed) is not bytes or len(packed)<4 or any(type(n) is not int for n in (input_words,output_words,batch_size,runtime_stride))
        or not 1<=input_words<=0xffffffff or not 1<=output_words<=0xffffffff
        or not 1<=batch_size<=65536 or runtime_stride<0):raise ValueError('Invalid partitioned wire dimensions')
    count,=struct.unpack_from('<I',packed)
    if not 1<=count<=65536 or len(packed)!=4+count*input_words*4 or 1+count*input_words>0xffffffff or count*output_words>0xffffffff:raise ValueError('Invalid complete partitioned input')
    rows=[];width=input_words*4
    for first in range(0,count,batch_size):
        size=min(batch_size,count-first);chunk=struct.pack('<I',size)+packed[4+first*width:4+(first+size)*width]
        rows.append(dict(first_case=first,cases=size,input_bytes=len(chunk),input_sha256=hashlib.sha256(chunk).hexdigest(),output_bytes=size*output_words*4))
    full_output=count*output_words*4;maximum=max(r['cases'] for r in rows)
    return dict(schema=SCHEMA,input_count=count,input_words=input_words,output_words=output_words,batch_size=batch_size,batches=rows,
        input_sha256=hashlib.sha256(packed).hexdigest(),input_bytes=len(packed),output_bytes=full_output,
        maximum_input_buffer_bytes=4+maximum*width,maximum_output_buffer_bytes=maximum*output_words*4,
        maximum_runtime_buffer_bytes=maximum*runtime_stride,runtime_stride_bytes=runtime_stride,
        staging_bytes=2*full_output+sum(r['input_bytes'] for r in rows),
        staging_scope='Batch inputs plus retained batch outputs plus joined output; original input and reserve are additional',
        allocation_scope='Explicit buffer sizes only; not total Job commit, VRAM availability or driver stack usage')


def split(packed,layout):
    """Reframe each contiguous row range, without re-encoding any row word."""
    rebuilt=plan(packed,layout['input_words'],layout['output_words'],layout['batch_size'],runtime_stride=layout['runtime_stride_bytes'])
    if rebuilt!=layout:raise ValueError('Partitioned plan changed')
    width=layout['input_words']*4
    return [struct.pack('<I',r['cases'])+packed[4+r['first_case']*width:4+(r['first_case']+r['cases'])*width] for r in layout['batches']]


def digest_file(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def generated_baseline(adapter,outputs,expected):
    path=adapter.ROOT/'research/summarize-portable-cross-gpu.py'
    spec=importlib.util.spec_from_file_location('partitioned_generated_normalizer',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if {k:module.normalized(p.read_bytes()) for k,p in outputs.items()}!=expected:raise ValueError('Partitioned generated source differs from the complete sealed baseline')


def execute(source,entry,packed,input_words,output_words,backend,*,readback_path,expected_input_sha256,
            expected_output_sha256,expected_source_sha256,expected_generated_normalized,batch_size=16,adapter=None,address_profile=None):
    if adapter is None:import portable_backend as adapter
    from portable_wire_layout import MAX_INPUT_WORDS,MAX_OUTPUT_WORDS,LARGE_OUTPUT_WORDS
    if backend not in ('metal','cuda'):raise ValueError('Explicit partitioned backend required')
    if (type(input_words) is not int or type(output_words) is not int or not 1<=input_words<=MAX_INPUT_WORDS
        or not 1<=output_words<=MAX_OUTPUT_WORDS or output_words>524288 and output_words not in LARGE_OUTPUT_WORDS):raise ValueError('Invalid registered partitioned word strides')
    if os.environ.get('NIKKE_SLANG_GENERATION_REQUIRED')!='1':raise ValueError('Partitioned transport requires a mandatory paired generation cache')
    if backend=='cuda' and (os.environ.get('NIKKE_CUDA_CACHE_REQUIRED')!='1' or os.environ.get('NIKKE_CUDA_ARTIFACT')!='cubin'):raise ValueError('Partitioned CUDA requires CUBIN and a no-compile required-cache policy')
    for value in (expected_input_sha256,expected_output_sha256):fingerprint(value)
    if type(expected_source_sha256) is not dict or not expected_source_sha256:raise ValueError('Complete sealed source hashes required')
    expected_source_sha256=dict(expected_source_sha256)
    if type(expected_generated_normalized) is not dict or set(expected_generated_normalized)!={'cuda','metal'}:raise ValueError('Complete paired generated baseline required')
    expected_generated_normalized=dict(expected_generated_normalized)
    for value in (*expected_source_sha256.values(),*expected_generated_normalized.values()):fingerprint(value)
    layout=plan(packed,input_words,output_words,batch_size)
    if layout['input_sha256']!=expected_input_sha256:raise ValueError('Partitioned input differs from complete sealed input')
    # Preserve the existing registered entry/wire checks before compilation.
    adapter.validate_composed_stride(source,input_words,output_words)
    if not isinstance(expected_source_sha256,dict) or not expected_source_sha256 or adapter.source_hashes(source)!=expected_source_sha256:raise ValueError('Partitioned source differs from complete sealed source')
    if address_profile is not None:
        from portable_partitioned_addresses import PROFILE,check_source
        if address_profile!=PROFILE:raise ValueError('Unknown partitioned address profile')
        check_source(adapter.ROOT,source,output_words)
    destination=Path(readback_path)
    if not destination.is_absolute() or destination.is_symlink():raise ValueError('Fresh absolute partitioned output required')
    destination=destination.resolve();partial=destination.with_name(destination.name+'.partial');parts=destination.with_name(destination.name+'.batches')
    if not destination.parent.is_dir() or any(p.exists() or p.is_symlink() for p in (destination,partial,parts)):raise FileExistsError('Fresh partitioned output, partial and parts required')
    from portable_capture_storage import space_status
    # Two complete disk copies are deliberate evidence, not two resident RAM
    # buffers. Do not delete source/failed readbacks to fit a measurement.
    storage=space_status(destination.parent,layout['staging_bytes']+64*1024*1024)
    if not storage['passed']:raise RuntimeError('Insufficient space for retained partitioned readbacks')
    parts.mkdir(exist_ok=False)
    with (parts/'intent.json').open('x') as f:json.dump(dict(plan=layout,backend=backend,storage=storage,calculation_verified=False),f,indent=2)
    outputs,hashes=adapter.build(source,entry)
    if hashes!=expected_source_sha256:raise ValueError('Partitioned source changed during generation')
    generated_baseline(adapter,outputs,expected_generated_normalized)
    generated={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in outputs.items()}
    resident=adapter.resident_plan(source,entry,outputs)
    layout=plan(packed,input_words,output_words,batch_size,runtime_stride=resident['stride'] if resident else 0)
    batches=split(packed,layout);input_paths=[];output_paths=[]
    for i,raw in enumerate(batches):
        inp=parts/(str(i)+'.in');out=parts/(str(i)+'.out')
        with inp.open('xb') as f:f.write(raw)
        input_paths.append(inp);output_paths.append(out)
        if inp.stat().st_size!=len(raw) or digest_file(inp)!=layout['batches'][i]['input_sha256']:raise RuntimeError('Partitioned input file differs before dispatch')
    with (parts/'plan.json').open('x') as f:json.dump(layout,f,indent=2)
    if backend=='cuda':
        raw,transports=adapter.execute_cuda_batches(outputs['cuda'],entry,batches,[r['output_bytes'] for r in layout['batches']],
            [r['cases'] for r in layout['batches']],**({'resident':resident} if resident else {}),output_paths=output_paths)
        if raw!=[None]*len(batches):raise RuntimeError('Partitioned CUDA unexpectedly returned whole readbacks')
    else:
        if adapter.platform.system()!='Darwin':raise RuntimeError('Partitioned Metal requires macOS')
        manifest=parts/'batches.json'
        with manifest.open('x') as f:json.dump([dict(input=str(inp),output=str(out)) for inp,out in zip(input_paths,output_paths,strict=True)],f)
        process=adapter.run_metal_command(['swift',str(adapter.ROOT/'scripts/run-metal-probe.swift'),str(outputs['metal']),str(manifest),'--batches',entry,str(input_words),str(output_words),*([str(resident['stride'])] if resident else [])])
        with (parts/'metal-command.json').open('x') as f:json.dump(dict(exit_code=process.returncode,stdout=process.stdout,stderr=process.stderr),f)
        if process.returncode:raise RuntimeError(process.stderr or process.stdout)
        status=json.loads(process.stdout)
        if status.get('pipeline_instances')!=1 or status.get('buffer_allocations')!=(3 if resident else 2):raise RuntimeError('Partitioned Metal did not reuse its bounded buffers')
        transports=status['batches']
    if len(transports)!=len(batches):raise RuntimeError('Missing partitioned dispatch')
    if any(p.is_symlink() or p.stat().st_size!=r['input_bytes'] or digest_file(p)!=r['input_sha256'] for p,r in zip(input_paths,layout['batches'],strict=True)):raise RuntimeError('Partitioned input changed during dispatch')
    joined=hashlib.sha256();records=[];total=0
    with partial.open('xb') as target:
        for row,out,transport in zip(layout['batches'],output_paths,transports,strict=True):
            if (out.is_symlink() or not out.is_file() or out.stat().st_size!=row['output_bytes']
                or any(type(transport.get(k)) is not int for k in ('cases','input_bytes','output_bytes'))
                or transport.get('cases')!=row['cases'] or transport.get('command_status')!='completed'
                or transport.get('input_bytes')!=row['input_bytes'] or transport.get('output_bytes')!=row['output_bytes']):raise RuntimeError('Invalid partitioned file receipt')
            digest=hashlib.sha256()
            with out.open('rb') as stream:
                for block in iter(lambda:stream.read(adapter.READBACK_CHUNK_BYTES),b''):
                    if target.write(block)!=len(block):raise OSError('Short joined partition write')
                    total+=len(block);joined.update(block);digest.update(block)
            receipt=transport.get('readback_stream')
            if backend=='cuda':
                expected=dict(output_bytes=row['output_bytes'],output_sha256=digest.hexdigest(),chunk_bytes=adapter.READBACK_CHUNK_BYTES,
                    chunks=(row['output_bytes']+adapter.READBACK_CHUNK_BYTES-1)//adapter.READBACK_CHUNK_BYTES)
                if receipt!=expected:raise RuntimeError('Partitioned CUDA readback hash/stream mismatch')
            elif transport.get('file_readback_chunk_bytes')!=adapter.READBACK_CHUNK_BYTES:raise RuntimeError('Partitioned Metal did not use bounded file writes')
            records.append(dict(**row,output_sha256=digest.hexdigest(),transport=transport))
        target.flush();os.fsync(target.fileno())
    if total!=layout['output_bytes']:raise RuntimeError('Incomplete ordered partitioned output')
    address_view=None
    if address_profile is not None:
        from portable_partitioned_addresses import view_file
        address_view=view_file(partial,layout)
        if address_view['raw_joined_output_sha256']!=joined.hexdigest() or address_view['logical_view_sha256']!=expected_output_sha256:raise RuntimeError('Complete typed-address wire view differs from sealed baseline')
    elif joined.hexdigest()!=expected_output_sha256:raise RuntimeError('Complete ordered partitioned output differs from sealed baseline')
    if adapter.source_hashes(source)!=hashes or {k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in outputs.items()}!=generated:raise RuntimeError('Partitioned source changed during dispatch')
    evidence=dict(schema=SCHEMA,backend=backend,source_sha256=hashes,generated_sha256=generated,input_sha256=expected_input_sha256,
        output_sha256=joined.hexdigest(),plan=layout,dispatches=records,transport=dict(backend=backend,cases=layout['input_count'],
        command_status='completed',session_dispatches=len(batches),pipeline_instances=1,buffer_allocations=3 if resident else 2,
        input_bytes=len(packed),output_bytes=total),gpu_execution_verified=True,sealed_output_fingerprint_matches=joined.hexdigest()==expected_output_sha256,
        wire_address_profile=address_profile,address_view=address_view,logical_wire_equivalence_verified=address_view is not None,
        calculation_verified=False,scope='Raw output is unchanged. An explicit source-pinned address view, when present, has a separate logical digest. Native audit and feature admission remain separate.')
    with (parts/'validated.json').open('x') as f:json.dump(evidence,f,indent=2)
    os.link(partial,destination);partial.unlink()
    if os.name!='nt':
        fd=os.open(destination.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    return None,evidence
