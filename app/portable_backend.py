"""Shared Slang build + buffer transport. No effect or numeric game logic here.
Both backends execute the same entry, input words and output comparison.
"""
import ctypes as C
import contextlib
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import struct
import subprocess
import tempfile
import selectors
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
from portable_wire_layout import MAX_INPUT_WORDS,MAX_OUTPUT_WORDS,LARGE_OUTPUT_WORDS
READBACK_CHUNK_BYTES=8*1024*1024


def source_hashes(source):
    from portable_slang_generation import source_hashes as generate_hashes
    return generate_hashes(ROOT,source)


def build(source,entry):
    from portable_slang_generation import build as generate
    return generate(ROOT,source,entry)


def _build_resident(compiler,source,entry,hashes,directory):
    from portable_slang_generation import _build_resident as generate
    return generate(ROOT,compiler,source,entry,hashes,directory)


def metal_compile_command(command,cache=None):
    command=list(command)
    if cache is None or Path(command[0]).name!='swift':return command
    cache=Path(cache)
    if not cache.is_absolute():raise ValueError('Absolute private Swift module cache required')
    cache.mkdir(parents=True,exist_ok=True)
    return [command[0],'-module-cache-path',str(cache),*command[1:]]


def run_metal_command(command, *, compile_timeout=300, gpu_timeout=120):
    """Bound cold compilation separately from GPU execution; consume both pipes.

    The Swift adapter emits the dispatch marker just before command.commit().
    A compile/lock wait can never consume the subsequent GPU deadline.
    """
    command=metal_compile_command(command,os.environ.get('NIKKE_METAL_MODULE_CACHE'))
    stage='compile';deadline=time.monotonic()+compile_timeout
    chunks={'stdout':bytearray(),'stderr':bytearray()}
    with subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE) as process:
        with selectors.DefaultSelector() as selector:
            for name in chunks:
                stream=getattr(process,name);os.set_blocking(stream.fileno(),False)
                selector.register(stream,selectors.EVENT_READ,name)
            try:
                while selector.get_map():
                    remaining=deadline-time.monotonic()
                    if remaining<=0:
                        raise RuntimeError('Metal timeout ('+stage+' phase): '+chunks['stderr'].decode('utf-8','replace').strip())
                    for key,_ in selector.select(min(remaining,.25)):
                        data=os.read(key.fd,65536)
                        if not data:selector.unregister(key.fileobj);continue
                        chunks[key.data].extend(data)
                        if stage=='compile' and b'portable_stage=gpu_dispatch\n' in chunks['stderr']:
                            stage='gpu';deadline=time.monotonic()+gpu_timeout
                code=process.wait(timeout=max(.001,deadline-time.monotonic()))
            except subprocess.TimeoutExpired as error:
                process.kill();process.wait()
                raise RuntimeError('Metal timeout ('+stage+' phase): '+chunks['stderr'].decode('utf-8','replace').strip()) from error
            except BaseException:
                process.kill();process.wait();raise
    return subprocess.CompletedProcess(command,code,chunks['stdout'].decode('utf-8','replace'),chunks['stderr'].decode('utf-8','replace'))


def resident_plan(source,entry,outputs):
    if not any(re.search(rb'^\s*#define\s+PORTABLE_RESIDENT_RUNTIME(?:\s|$)',(ROOT/name).read_bytes(),re.M) for name in source_hashes(source)):return None
    from portable_resident_layout import reflection_plan
    return reflection_plan(outputs,entry)


def validate_composed_stride(source,input_words,output_words):
    if source in ('gpu/product_add_battle_entry.slang','gpu/product_add_group_battle_entry.slang',
                  'gpu/product_add_fixed_battle_entry.slang','gpu/product_add_fixed_group_battle_entry.slang',
                  'gpu/product_add_target_battle_entry.slang','gpu/product_add_fixed_target_battle_entry.slang',
                  'gpu/product_add_group_target_battle_entry.slang','gpu/product_add_fixed_group_target_battle_entry.slang'):
        from portable_add_attack_battle_wire import check_schema,LAYOUT
        from portable_add_self_destruct_wire import check_schema as check_retirement
        check_schema(ROOT);check_retirement(ROOT)
        if (input_words,output_words)!=(LAYOUT['INPUT_WORDS'],LAYOUT['OUTPUT_WORDS']):
            raise ValueError('Product ADD attacks require the complete shared source/retirement wire')
        return
    if source in ('gpu/product_fixed_battle_entry.slang','gpu/product_fixed_group_battle_entry.slang',
                  'gpu/product_fixed_target_battle_entry.slang','gpu/product_fixed_group_target_battle_entry.slang'):
        # Identical wire; only the guarded fixed-readiness consumer differs.
        return validate_composed_stride(source.replace('gpu/product_fixed_','gpu/product_',1),input_words,output_words)
    if source=='gpu/product_group_target_battle_entry.slang':
        from portable_destructible_roster_input import check_group_wire,GROUP_INPUT_WORDS,OUTPUT_WORDS
        check_group_wire(ROOT)
        if (input_words,output_words)!=(GROUP_INPUT_WORDS,OUTPUT_WORDS):raise ValueError('Product group target requires its complete carrier and group wire')
        return
    if source in ('gpu/world_weighted_incoming_entry.slang','gpu/world_weighted_incoming_diagnostic_entry.slang','gpu/product_weighted_battle_entry.slang','gpu/product_weighted_fixed_battle_entry.slang'):
        from portable_weighted_battle_wire import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Weighted incoming requires complete literal weights and owned receipt banks')
        return
    if source in ('gpu/world_cover_defense_entry.slang','gpu/product_cover_battle_entry.slang','gpu/product_cover_fixed_battle_entry.slang') or output_words==2048912:
        from portable_cover_defense_wire import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if source not in ('gpu/world_cover_defense_entry.slang','gpu/product_cover_battle_entry.slang','gpu/product_cover_fixed_battle_entry.slang') or (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Cover DEF requires complete independent bases and receipt bank')
        return
    if source=='gpu/world_coordinate_typed_ordered_history_entry.slang':
        from portable_recipient_order_observation import check_layout,INPUT_WORDS,OUTPUT_WORDS
        check_layout(ROOT)
        if (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):raise ValueError('Recipient-order observation requires the complete history wire')
        return
    if source=='gpu/world_moving_many_entry.slang':
        from portable_moving_many_wire import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Maximum-slot motion requires complete untruncated frame/segment banks')
        return
    if source in ('gpu/world_moving_typed_entry.slang','gpu/world_moving_frames_entry.slang'):
        from portable_moving_typed_wire import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Moving typed execution requires all physical, logical, movement and frozen aim banks')
        return
    if source in ('gpu/world_enemy_movement_entry.slang','gpu/product_movement_battle_entry.slang'):
        from portable_enemy_movement_wire import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Movement requires complete collider, marker and motion banks')
        return
    if source=='gpu/world_enemy_ammo_self_destruct_entry.slang':
        from portable_enemy_ammo_self_destruct_wire import check_schema,LAYOUT
        check_schema(ROOT)
        if (input_words,output_words)!=(LAYOUT['INPUT_WORDS'],LAYOUT['OUTPUT_WORDS']):raise ValueError('Final-queue magazines require both complete banks and disjoint receipts')
        return
    if source in ('gpu/world_enemy_ammo_entry.slang','gpu/product_ammo_battle_entry.slang','gpu/product_ammo_fixed_battle_entry.slang'):
        from portable_enemy_ammo_wire import check_schema,LAYOUT
        check_schema(ROOT)
        if (input_words,output_words)!=(LAYOUT['INPUT_WORDS'],LAYOUT['OUTPUT_WORDS']):raise ValueError('Enemy ammo requires complete actor and resource banks')
        return
    if source=='gpu/world_add_self_destruct_entry.slang':
        from portable_add_self_destruct_wire import check_schema,LAYOUT
        check_schema(ROOT)
        if (input_words,output_words)!=(LAYOUT['INPUT_WORDS'],LAYOUT['OUTPUT_WORDS']):raise ValueError('Self-destruct requires complete ADD input and receipt arena')
        return
    if source=='gpu/world_add_attack_battle_entry.slang':
        from portable_add_attack_battle_wire import check_schema,LAYOUT
        check_schema(ROOT)
        if (input_words,output_words)!=(LAYOUT['INPUT_WORDS'],LAYOUT['OUTPUT_WORDS']):raise ValueError('ADD attack battle requires its complete logical and firing wire')
        return
    if source in ('gpu/world_lock_projectile_entry.slang','gpu/world_original_lock_composition_entry.slang','gpu/world_original_lock_health_parts_entry.slang'):
        from portable_lock_typed_layout import check,INPUT,OUTPUT
        check(ROOT)
        if source in ('gpu/world_original_lock_composition_entry.slang','gpu/world_original_lock_health_parts_entry.slang'):
            from portable_original_lock_layout import check as check_original
            check_original(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Lock/projectile composition requires its complete disjoint arenas')
        return
    if source in ('gpu/world_lock_packet_entry.slang','gpu/world_lock_delivery_entry.slang'):
        from portable_lock_packet_layout import check,INPUT,OUTPUT
        check(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Lock packets require the full lock/manual/queue wire')
        return
    if source=='gpu/world_physical_lock_cover_entry.slang':
        from portable_physical_lock_cover_layout import check,INPUT,OUTPUT
        check(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Physical cover requires the complete lock/manual arena wire')
        return
    if source in ('gpu/world_lock_enemy_carrier_entry.slang','gpu/world_lock_enemy_carrier_diagnostic_entry.slang'):
        from portable_physical_lock_layout import check,INPUT,OUTPUT
        check(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Enemy lock carriers require the complete physical arena wire')
        return
    if source=='gpu/world_physical_locks_entry.slang' or output_words==806912:
        from portable_physical_lock_layout import check,INPUT,OUTPUT
        check(ROOT)
        if source!='gpu/world_physical_locks_entry.slang' or (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Physical locks require their separate arena wire')
        return
    if source=='gpu/world_named_range_battle_entry.slang':
        from portable_named_range_battle_wire import check_schema,INPUT,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT,OUTPUT):raise ValueError('Named radial battle requires its complete declared wire')
        return
    if source in ('gpu/world_enemy_healing_entry.slang','gpu/product_healing_battle_entry.slang','gpu/product_healing_fixed_battle_entry.slang'):
        from portable_enemy_healing_wire import check_schema,INPUT_WORDS,OUTPUT
        check_schema(ROOT)
        if (input_words,output_words)!=(INPUT_WORDS,OUTPUT['OUTPUT_WORDS']):raise ValueError('Enemy healing requires its complete declared source wire')
        return
    if source=='gpu/world_coordinate_logical_actor_entry.slang':
        from portable_logical_geometry_wire import check_schema,LAYOUT,SCRATCH
        check_schema(ROOT)
        if (input_words,output_words)!=(LAYOUT['BASE']+LAYOUT['WORDS'],SCRATCH['OUTPUT_WORDS']):raise ValueError('Logical ADD geometry requires its complete registered wire')
        return
    if source=='gpu/world_coordinate_resident_frames_entry.slang':
        from portable_coordinate_resident_arc_specs import check_layout,INPUT_WORDS,OUTPUT_WORDS
        check_layout(ROOT)
        if (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):raise ValueError('Resident frames require the complete106 wire')
        return
    if source=='gpu/world_coordinate_resident_arc_entry.slang' or output_words==2064786:
        from portable_coordinate_resident_arc_specs import check_layout,SOURCE,INPUT_WORDS,OUTPUT_WORDS
        check_layout(ROOT)
        if source!=SOURCE or (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):raise ValueError('Resident arc requires the complete registered tail wire')
        return
    if source in ('gpu/world_coordinate_typed_entry.slang','gpu/world_coordinate_typed_weapon_entry.slang','gpu/world_coordinate_typed_aim_entry.slang','gpu/world_coordinate_typed_actor_entry.slang','gpu/world_coordinate_typed_owner_entry.slang','gpu/world_coordinate_typed_logical_owner_entry.slang','gpu/world_coordinate_typed_history_entry.slang') or output_words==2032000:
        from portable_coordinate_typed_specs import check_layout,SOURCE,INPUT_WORDS,OUTPUT_WORDS
        check_layout(ROOT)
        if source=='gpu/world_coordinate_typed_history_entry.slang':
            from portable_skill_history import check_layout as check_history
            check_history(ROOT)
        if source not in (SOURCE,'gpu/world_coordinate_typed_weapon_entry.slang','gpu/world_coordinate_typed_aim_entry.slang','gpu/world_coordinate_typed_actor_entry.slang','gpu/world_coordinate_typed_owner_entry.slang','gpu/world_coordinate_typed_logical_owner_entry.slang','gpu/world_coordinate_typed_history_entry.slang') or (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):raise ValueError('Coordinate typed targets require the complete registered wire')
        return
    if source in ('gpu/world_coordinate_policy_entry.slang','gpu/world_coordinate_squad_entry.slang','gpu/world_coordinate_squad_mode_entry.slang','gpu/world_coordinate_burst_control_entry.slang','gpu/world_coordinate_mode_actions_entry.slang','gpu/world_coordinate_auto_reload_entry.slang','gpu/world_coordinate_healing_entry.slang','gpu/world_coordinate_original_entry.slang','gpu/world_coordinate_original_clock_entry.slang','gpu/world_coordinate_original_resource_entry.slang','gpu/world_coordinate_original_ammo_entry.slang','gpu/world_coordinate_original_stack_entry.slang','gpu/world_coordinate_original_cleanse_entry.slang','gpu/world_coordinate_original_slot_entry.slang','gpu/world_coordinate_original_reload_entry.slang','gpu/world_coordinate_original_shield_entry.slang','gpu/world_coordinate_original_cover_entry.slang','gpu/world_coordinate_original_shared_entry.slang') or output_words==1769856:
        expected={'gpu/world_coordinate_policy_entry.slang':109656,'gpu/world_coordinate_squad_entry.slang':109792,'gpu/world_coordinate_squad_mode_entry.slang':109792,'gpu/world_coordinate_burst_control_entry.slang':109968,'gpu/world_coordinate_mode_actions_entry.slang':109968,'gpu/world_coordinate_auto_reload_entry.slang':109968,'gpu/world_coordinate_healing_entry.slang':109968,'gpu/world_coordinate_original_entry.slang':109968,'gpu/world_coordinate_original_clock_entry.slang':109968,'gpu/world_coordinate_original_resource_entry.slang':109968,'gpu/world_coordinate_original_ammo_entry.slang':109968,'gpu/world_coordinate_original_stack_entry.slang':109968,'gpu/world_coordinate_original_cleanse_entry.slang':109968,'gpu/world_coordinate_original_slot_entry.slang':109968,'gpu/world_coordinate_original_reload_entry.slang':109968,'gpu/world_coordinate_original_shield_entry.slang':109968,'gpu/world_coordinate_original_cover_entry.slang':109968,'gpu/world_coordinate_original_shared_entry.slang':109968}
        if source not in expected or (input_words,output_words)!=(expected[source],1769856):raise ValueError('Cover policy requires its complete registered wire')
        return
    if source in ('gpu/world_coordinate_sampling_burst_entry.slang','gpu/world_coordinate_sampling_vital_entry.slang','gpu/world_coordinate_manual_entry.slang') or output_words==1769472:
        from portable_coordinate_sampled_burst_wire import SOURCE,INPUT_WORDS,OUTPUT_WORDS,check_schema
        check_schema(ROOT)
        if source not in (SOURCE,'gpu/world_coordinate_sampling_vital_entry.slang','gpu/world_coordinate_manual_entry.slang') or (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):
            raise ValueError('Sampled burst requires its complete registered wire')
        return
    if source in ('gpu/world_coordinate_group_entry.slang','gpu/world_coordinate_mixed_entry.slang','gpu/world_coordinate_sampling_entry.slang','gpu/world_coordinate_sampling_parent_entry.slang','gpu/world_coordinate_sampling_skill_entry.slang') or output_words==1507328:
        from portable_coordinate_group_wire import INPUT_WORDS,OUTPUT_WORDS,check_schema
        check_schema(ROOT)
        if source not in ('gpu/world_coordinate_group_entry.slang','gpu/world_coordinate_mixed_entry.slang','gpu/world_coordinate_sampling_entry.slang','gpu/world_coordinate_sampling_parent_entry.slang','gpu/world_coordinate_sampling_skill_entry.slang') or (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):
            raise ValueError('Coordinate group requires the complete registered wire')
        return
    if output_words==1310720 or source=='gpu/world_coordinate_composed_entry.slang':
        from portable_arena_specs import audit_profile
        plan=audit_profile('combined-v1')
        if source in ('gpu/world_coordinate_aim_entry.slang','gpu/world_coordinate_control_entry.slang'):
            from portable_coordinate_aim_wire import INPUT_WORDS,OUTPUT_WORDS,check_schema
            check_schema(ROOT)
            if (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):
                raise ValueError('Coordinate aim requires the complete authored wire')
        elif source in ('gpu/world_coordinate_core_entry.slang','gpu/world_coordinate_cache_entry.slang'):
            from portable_coordinate_core_specs import INPUT_WORDS,OUTPUT_WORDS,check_schema
            check_schema(ROOT)
            if source=='gpu/world_coordinate_cache_entry.slang':
                from portable_coordinate_cache_specs import check_schema as check_cache_schema
                check_cache_schema(ROOT)
            if (input_words,output_words)!=(INPUT_WORDS,OUTPUT_WORDS):
                raise ValueError('Coordinate live core stride requires the complete wire')
        elif source=='gpu/world_coordinate_physical_entry.slang':
            from portable_coordinate_physical_specs import audit_arena
            physical=audit_arena(ROOT)
            if (input_words,output_words)!=(physical['input_words'],physical['output_words']):
                raise ValueError('Coordinate physical stride requires the complete wire')
        elif source!='gpu/world_coordinate_composed_entry.slang' or (input_words,output_words)!=(plan['input_words'],plan['output_words']):
            raise ValueError('Composed stride requires the registered shared entry and complete wire')


def execute(source, entry, packed, input_words, output_words, backend='metal', *, readback_path=None):
    if backend not in ('metal', 'cuda'):
        raise ValueError('Explicit metal or cuda backend required; no CPU fallback')
    if type(input_words) is not int or type(output_words) is not int or not 1<=input_words<=MAX_INPUT_WORDS or not 1<=output_words<=MAX_OUTPUT_WORDS or output_words>524288 and output_words not in LARGE_OUTPUT_WORDS:
        raise ValueError('Invalid portable word strides')
    validate_composed_stride(source,input_words,output_words)
    count, = struct.unpack_from('<I', packed)
    if not 1 <= count <= 65536 or 1+count*input_words>0xffffffff or count*output_words>0xffffffff or len(packed) != (1+count*input_words)*4:
        raise ValueError('Invalid portable wire dimensions')
    if readback_path is not None and Path(readback_path).is_symlink():raise ValueError('Fresh readback destination required')
    destination=Path(readback_path).resolve() if readback_path is not None else None
    partial=destination.with_name(destination.name+'.partial') if destination is not None else None
    if destination is not None and (destination.exists() or partial.exists() or partial.is_symlink() or not destination.parent.is_dir()):
        raise ValueError('Fresh readback destination and partial required')
    outputs, hashes = build(source, entry)
    resident=resident_plan(source,entry,outputs)
    directory = ROOT/'research/portable-build'
    with tempfile.TemporaryDirectory(prefix='dispatch-', dir=directory) as tmp:
        input_path, output_path = Path(tmp)/'input.bin', partial if destination is not None else Path(tmp)/'output.bin'
        input_path.write_bytes(packed)
        if backend == 'metal':
            if platform.system() != 'Darwin':
                raise RuntimeError('Metal requires macOS')
            process = run_metal_command(['swift', str(ROOT/'scripts/run-metal-probe.swift'),
                                         str(outputs['metal']), str(input_path), str(output_path),
                                         entry, str(input_words), str(output_words),*([str(resident["stride"])] if resident else [])])
            if process.returncode:
                raise RuntimeError(process.stderr or process.stdout)
            raw, transport = None if destination is not None else output_path.read_bytes(), json.loads(process.stdout)
            transport.update(compile_timeout_seconds=300,gpu_timeout_seconds=120)
        else:
            raw, transport = execute_cuda(outputs['cuda'], entry, packed, count*output_words*4, count,**({'resident':resident} if resident else {}),**({'output_path':partial} if destination is not None else {}))
    if destination is not None:
        from portable_capture_storage import file_digest
        if raw is not None or not partial.is_file() or partial.is_symlink() or partial.stat().st_size!=count*output_words*4 or transport['cases']!=count or transport['command_status']!='completed' or transport.get('input_bytes')!=len(packed) or transport.get('output_bytes')!=count*output_words*4:
            raise RuntimeError('Incomplete file readback')
        output_digest=file_digest(partial)
        if backend=='cuda':
            receipt=transport['readback_stream']
            if receipt['output_sha256']!=output_digest or receipt['output_bytes']!=count*output_words*4 or receipt['chunk_bytes']!=READBACK_CHUNK_BYTES or receipt['chunks']!=(count*output_words*4+READBACK_CHUNK_BYTES-1)//READBACK_CHUNK_BYTES:raise RuntimeError('CUDA streamed readback digest mismatch')
        elif transport.get('file_readback_chunk_bytes')!=READBACK_CHUNK_BYTES:raise RuntimeError('Metal did not use the bounded file writer')
    else:output_digest=hashlib.sha256(raw).hexdigest()
    if (destination is None and len(raw)!=count*output_words*4) or hashes!=source_hashes(source):
        raise RuntimeError('Invalid GPU output or source changed during execution')
    if destination is not None:
        with partial.open('r+b') as stream:os.fsync(stream.fileno())
        # Publish without replacing an existing result, keeping the partial on failure.
        os.link(partial,destination);partial.unlink()
        if os.name!='nt':
            fd=os.open(destination.parent,os.O_RDONLY)
            try:os.fsync(fd)
            finally:os.close(fd)
    return raw, dict(**(dict(resident_runtime=resident) if resident else {}),transport=transport, source_sha256=hashes,
                    generated_sha256={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in outputs.items()},
                    input_sha256=hashlib.sha256(packed).hexdigest(), output_sha256=output_digest,
                    gpu_execution_verified=True, backend=backend)


def execute_batches(source, entry, batches, input_words, output_words, backend='metal'):
    """Sequential independent dispatches in one compiled GPU session.

    Wire inputs and readbacks remain separate; a failure never returns a partial
    success. Both adapters reuse their pipeline/context and two bounded buffers.
    """
    if backend not in ('metal','cuda'):raise ValueError('Explicit metal or cuda backend required; no CPU fallback')
    if type(input_words) is not int or type(output_words) is not int or not 1<=input_words<=MAX_INPUT_WORDS or not 1<=output_words<=MAX_OUTPUT_WORDS or output_words>524288 and output_words not in LARGE_OUTPUT_WORDS:raise ValueError('Invalid portable word strides')
    batches=list(batches)
    if not batches:raise ValueError('Empty portable dispatch sequence')
    counts=[]
    validate_composed_stride(source,input_words,output_words)
    for packed in batches:
        if len(packed)<4:raise ValueError('Missing portable batch header')
        count,=struct.unpack_from('<I',packed)
        if not 1<=count<=65536 or 1+count*input_words>0xffffffff or count*output_words>0xffffffff or len(packed)!=(1+count*input_words)*4:raise ValueError('Invalid portable wire dimensions')
        counts.append(count)
    outputs,hashes=build(source,entry)
    resident=resident_plan(source,entry,outputs)
    if backend=='cuda':
        raw,transports=execute_cuda_batches(outputs['cuda'],entry,batches,[n*output_words*4 for n in counts],counts,**({'resident':resident} if resident else {}))
    else:
        if platform.system()!='Darwin':raise RuntimeError('Metal requires macOS')
        with tempfile.TemporaryDirectory(prefix='sequence-',dir=ROOT/'research/portable-build') as tmp:
            paths=[]
            for i,packed in enumerate(batches):
                inp,out=Path(tmp)/f'{i}.in',Path(tmp)/f'{i}.out';inp.write_bytes(packed)
                paths.append(dict(input=str(inp),output=str(out)))
            manifest=Path(tmp)/'batches.json';manifest.write_text(json.dumps(paths))
            process=run_metal_command(['swift',str(ROOT/'scripts/run-metal-probe.swift'),str(outputs['metal']),str(manifest),'--batches',entry,str(input_words),str(output_words),*([str(resident['stride'])] if resident else [])])
            if process.returncode:raise RuntimeError(process.stderr or process.stdout)
            status=json.loads(process.stdout);transports=status['batches'];raw=[Path(p['output']).read_bytes() for p in paths]
            for t in transports:t.update(compile_timeout_seconds=300,gpu_timeout_seconds=120)
    if len(raw)!=len(batches) or len(transports)!=len(batches) or hashes!=source_hashes(source):raise RuntimeError('Incomplete GPU dispatch sequence or source changed')
    generated={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in outputs.items()}
    results=[]
    for i,(packed,output,transport,count) in enumerate(zip(batches,raw,transports,counts)):
        if len(output)!=count*output_words*4 or transport['cases']!=count or transport['command_status']!='completed':raise RuntimeError('Invalid GPU output stride or transport')
        transport.update(session_dispatches=len(batches),session_dispatch_index=i,pipeline_instances=1,buffer_allocations=3 if resident else 2)
        results.append((output,dict(**(dict(resident_runtime=resident) if resident else {}),transport=transport,source_sha256=hashes,generated_sha256=generated,input_sha256=hashlib.sha256(packed).hexdigest(),output_sha256=hashlib.sha256(output).hexdigest(),gpu_execution_verified=True,backend=backend)))
    return results



@contextlib.contextmanager
def _cuda_module(artifact_bytes,entry,artifact_kind,resident,*,jit_opt_level=None,stream_readback=False):
    """Shared driver/context/module lifecycle, with no battle allocations."""
    if jit_opt_level is not None and (type(jit_opt_level) is not int or jit_opt_level not in range(5) or artifact_kind!='ptx'):
        raise ValueError('Driver JIT optimization requires PTX and integer0..4')
    artifact_buffer=C.create_string_buffer(artifact_bytes)
    driver=C.WinDLL('nvcuda.dll')
    signatures=dict(cuInit=[C.c_uint],cuDeviceGet=[C.POINTER(C.c_int),C.c_int],cuDeviceGetName=[C.c_char_p,C.c_int,C.c_int],
        cuDeviceComputeCapability=[C.POINTER(C.c_int),C.POINTER(C.c_int),C.c_int],
        cuCtxCreate_v2=[C.POINTER(C.c_void_p),C.c_uint,C.c_int],cuCtxDestroy_v2=[C.c_void_p],
        cuModuleLoadData=[C.POINTER(C.c_void_p),C.c_void_p],cuModuleGetFunction=[C.POINTER(C.c_void_p),C.c_void_p,C.c_char_p],
        cuModuleGetGlobal_v2=[C.POINTER(C.c_uint64),C.POINTER(C.c_size_t),C.c_void_p,C.c_char_p],
        cuMemAlloc_v2=[C.POINTER(C.c_uint64),C.c_size_t],cuMemcpyHtoD_v2=[C.c_uint64,C.c_void_p,C.c_size_t],
        cuMemcpyDtoH_v2=[C.c_void_p,C.c_uint64,C.c_size_t],cuCtxSynchronize=[],
        cuLaunchKernel=[C.c_void_p,*([C.c_uint]*7),C.c_void_p,C.c_void_p,C.c_void_p])
    if stream_readback:signatures['cuMemsetD8_v2']=[C.c_uint64,C.c_ubyte,C.c_size_t]
    for name, signature in signatures.items():
        getattr(driver,name).argtypes=signature;getattr(driver,name).restype=C.c_int
    if jit_opt_level is not None:
        driver.cuModuleLoadDataEx.argtypes=[C.POINTER(C.c_void_p),C.c_void_p,C.c_uint,C.POINTER(C.c_int),C.POINTER(C.c_void_p)]
        driver.cuModuleLoadDataEx.restype=C.c_int
    def call(name,*args):
        code=getattr(driver,name)(*args)
        if code:raise RuntimeError(f'{name}: CUDA error {code}')
    context=C.c_void_p()
    call('cuInit',0);device=C.c_int();call('cuDeviceGet',C.byref(device),0)
    if artifact_kind=='cubin':
        major=C.c_int();minor=C.c_int();call('cuDeviceComputeCapability',C.byref(major),C.byref(minor),device)
        if (major.value,minor.value)!=(8,6):raise RuntimeError('The native CUDA artifact requires SM86')
    name=C.create_string_buffer(256);call('cuDeviceGetName',name,256,device)
    try:
        call('cuCtxCreate_v2',C.byref(context),0,device)
        module=C.c_void_p();function=C.c_void_p()
        if jit_opt_level is None:
            call('cuModuleLoadData',C.byref(module),C.cast(artifact_buffer,C.c_void_p))
        else:
            # CU_JIT_OPTIMIZATION_LEVEL=7; scalar option values are cast to void*, not pointers to scalars.
            options=(C.c_int*1)(7);values=(C.c_void_p*1)(jit_opt_level)
            call('cuModuleLoadDataEx',C.byref(module),C.cast(artifact_buffer,C.c_void_p),1,options,values)
        call('cuModuleGetFunction',C.byref(function),module,entry.encode())
        global_ptr=C.c_uint64();global_size=C.c_size_t()
        call('cuModuleGetGlobal_v2',C.byref(global_ptr),C.byref(global_size),module,b'SLANG_globalParams')
        if global_size.value!=(48 if resident else 32):raise RuntimeError('Unexpected Slang CUDA constant buffer ABI')
        yield call,function,global_ptr,dict(backend="cuda",device=name.value.decode(),constant_buffer_bytes=global_size.value)
    finally:
        if context:
            primary = sys.exc_info()[1]
            try:call('cuCtxDestroy_v2',context)
            except Exception as cleanup_error:
                if primary is None:raise
                primary.add_note('CUDA context cleanup also failed: '+str(cleanup_error))


def execute_cuda(source, entry, packed, output_size, count,*,resident=None,output_path=None):
    raw,transports=execute_cuda_batches(source,entry,[packed],[output_size],[count],**({'resident':resident} if resident else {}),**({'output_paths':[output_path]} if output_path is not None else {}))
    return raw[0],transports[0]


def cuda_compiler_files(cuda_root=None):
    cuda_bin=Path(cuda_root if cuda_root is not None else os.environ.get('CUDA_PATH',r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.3'))/'bin'
    compiler_files=sorted(cuda_bin.glob('nvrtc*.dll'))
    libraries=[p for p in compiler_files if p.name.lower().startswith('nvrtc64_')]
    builtins=[p for p in compiler_files if p.name.lower().startswith('nvrtc-builtins64_')]
    if len(libraries)!=1 or len(builtins)!=1:
        raise RuntimeError('CUDA compiler root requires exactly one NVRTC and one builtins DLL')
    return cuda_bin,compiler_files,libraries,builtins


def probe_cuda_source_cache(source, directory, *, cuda_root=None,artifact_kind='cubin',ptxas_level=None):
    """File-only inspection, also usable on archived toolchains off Windows."""
    from portable_compile_cache import probe,quoted_headers
    _,files,_,_=cuda_compiler_files(cuda_root)
    raw=Path(source).read_bytes()
    artifact,receipt=probe(raw,cuda_compile_options(artifact_kind,ptxas_level),files,directory,
        header_files=quoted_headers(raw),artifact_kind=artifact_kind)
    if artifact is not None and artifact_kind=='cubin' and not artifact.startswith(b'\x7fELF'):
        raise RuntimeError('Cached CUBIN artifact is not a native ELF binary')
    return receipt


def compile_cuda_source(source, *, artifact_kind=None):
    """CPU-only compiler/cache path; never loads nvcuda or creates a context."""
    if os.name != 'nt':raise RuntimeError('CUDA compiler requires Windows')
    artifact_kind=cuda_artifact_kind() if artifact_kind is None else artifact_kind
    cuda_bin,compiler_files,libraries,builtins=cuda_compiler_files()
    with os.add_dll_directory(str(cuda_bin)):
        def load_compiler():
            lib = C.WinDLL(str(libraries[0]))
            # NVRTC's internal bare-name LoadLibrary need not use Python's
            # AddDllDirectory search context. Load the fingerprinted companion
            # explicitly, and retain it for the entire compilation lifetime.
            # This factory is never invoked for cache hits or required misses.
            lib._nikke_builtins = C.WinDLL(str(builtins[0]))
            signatures = dict(nvrtcCreateProgram=[C.POINTER(C.c_void_p),C.c_char_p,C.c_char_p,C.c_int,C.c_void_p,C.c_void_p],
                          nvrtcCompileProgram=[C.c_void_p,C.c_int,C.POINTER(C.c_char_p)],
                          nvrtcGetProgramLogSize=[C.c_void_p,C.POINTER(C.c_size_t)], nvrtcGetPTXSize=[C.c_void_p,C.POINTER(C.c_size_t)],
                          nvrtcGetProgramLog=[C.c_void_p,C.c_void_p], nvrtcGetPTX=[C.c_void_p,C.c_void_p],
                          nvrtcDestroyProgram=[C.POINTER(C.c_void_p)])
            if artifact_kind=='cubin':
                signatures.update(nvrtcGetCUBINSize=[C.c_void_p,C.POINTER(C.c_size_t)],nvrtcGetCUBIN=[C.c_void_p,C.c_void_p])
            if cuda_split_compile_threads()==2:
                signatures['nvrtcVersion']=[C.POINTER(C.c_int),C.POINTER(C.c_int)]
            for name, signature in signatures.items():
                getattr(lib,name).argtypes=signature; getattr(lib,name).restype=C.c_int
            return lib
        # Exact-byte cache validation precedes DLL loading. Hits and required
        # misses need file reads only, without activating NVRTC at all.
        artifact_bytes,compile_receipt=compile_cuda_artifact(None,source.read_bytes(),compiler_files,artifact_kind=artifact_kind,library_factory=load_compiler)
        # Capture exact compiled bytes for independent local audits, including hits.
        source.with_suffix('.'+artifact_kind).write_bytes(artifact_bytes)
    return artifact_bytes,compile_receipt


def execute_cuda_batches(source, entry, batches, output_sizes, counts,*,resident=None,output_paths=None):
    """Opt-in sequential dispatches sharing one NVRTC build and CUDA context.
    The pinned Slang StructuredBuffer ABI is pointer + size_t; validate the
    actual constant-symbol size before copying. No numeric/game logic here.
    """
    if not batches or len(batches)!=len(output_sizes) or len(batches)!=len(counts):raise ValueError('Invalid CUDA dispatch sequence')
    for packed,size,count in zip(batches,output_sizes,counts):
        if type(count) is not int or not 1<=count<=65536 or type(size) is not int or size<=0 or len(packed)<4 or struct.unpack_from('<I',packed)[0]!=count:raise ValueError('Invalid CUDA dispatch dimensions')
    if output_paths is not None:
        if len(output_paths)!=len(batches):raise ValueError('One fresh file destination per dispatch required')
        if any(Path(p).is_symlink() for p in output_paths):raise ValueError('Fresh distinct readback destinations required')
        output_paths=[Path(p).resolve() for p in output_paths]
        if len(set(output_paths))!=len(output_paths) or any(p.exists() or not p.parent.is_dir() for p in output_paths):raise ValueError('Fresh distinct readback destinations required')
    if os.name != 'nt':
        raise RuntimeError('This CUDA NVRTC adapter currently requires Windows')
    if resident:
        from portable_resident_layout import verify_cuda_layout_assertions
        verify_cuda_layout_assertions(source,resident)
    artifact_kind=cuda_artifact_kind()
    artifact_bytes,compile_receipt=compile_cuda_source(source,artifact_kind=artifact_kind)
    with _cuda_module(artifact_bytes,entry,artifact_kind,resident,**({'stream_readback':True} if output_paths is not None else {})) as loaded:
        call,function,global_ptr,module_metadata=loaded
        inp=C.c_uint64();out=C.c_uint64()
        call('cuMemAlloc_v2',C.byref(inp),max(map(len,batches)));call('cuMemAlloc_v2',C.byref(out),max(output_sizes))
        scratch=C.c_uint64();scratch_bytes=resident['stride']*max(counts) if resident else 0
        if resident:call('cuMemAlloc_v2',C.byref(scratch),scratch_bytes)
        results=[];transports=[]
        for i,(packed,output_size,count) in enumerate(zip(batches,output_sizes,counts)):
            call('cuMemcpyHtoD_v2',inp,C.cast(C.c_char_p(packed),C.c_void_p),len(packed))
            if output_paths is None:
                zero=C.create_string_buffer(output_size);call('cuMemcpyHtoD_v2',out,C.cast(zero,C.c_void_p),output_size)
            else:call('cuMemsetD8_v2',out,0,output_size)
            params=struct.pack('<'+'Q'*(6 if resident else 4),inp.value,len(packed)//4,out.value,output_size//4,*([scratch.value,max(counts)] if resident else []))
            call('cuMemcpyHtoD_v2',global_ptr,C.cast(C.c_char_p(params),C.c_void_p),len(params))
            started=time.perf_counter();call('cuLaunchKernel',function,count,1,1,1,1,1,0,None,None,None);call('cuCtxSynchronize')
            elapsed=time.perf_counter()-started
            if output_paths is None:
                output=C.create_string_buffer(output_size);call('cuMemcpyDtoH_v2',output,out,output_size)
                results.append(output.raw)
            else:
                stream=cuda_readback_file(call,out.value,output_size,output_paths[i]);results.append(None)
            transports.append(dict(backend='cuda',device=module_metadata['device'],cases=count,command_status='completed',host_dispatch_seconds=elapsed,compile_artifact=compile_receipt))
            if output_paths is not None:transports[-1].update(readback_stream=stream,input_bytes=len(packed),output_bytes=output_size)
        if resident:
            for transport in transports:transport.update(runtime_stride_bytes=resident['stride'],runtime_buffer_bytes=scratch_bytes,runtime_element_capacity=max(counts))
        return results,transports


def cuda_readback_file(call,device_address,output_size,path):
    """Transfer every device byte once with one bounded reusable host buffer."""
    output=C.create_string_buffer(min(READBACK_CHUNK_BYTES,output_size));h=hashlib.sha256();chunks=0
    with Path(path).open('xb') as stream:
        for offset in range(0,output_size,READBACK_CHUNK_BYTES):
            size=min(READBACK_CHUNK_BYTES,output_size-offset)
            call('cuMemcpyDtoH_v2',output,device_address+offset,size)
            view=memoryview(output).cast('B')[:size]
            if stream.write(view)!=size:raise OSError('Short streamed readback write')
            h.update(view);chunks+=1
        stream.flush();os.fsync(stream.fileno())
    return dict(output_bytes=output_size,output_sha256=h.hexdigest(),chunk_bytes=READBACK_CHUNK_BYTES,chunks=chunks)


def inspect_cuda_module(source,entry,*,resident=None,jit_opt_level=None):
    """Load/JIT an exact cached PTX; never allocate, copy, sync or launch."""
    if os.name!='nt':raise RuntimeError('CUDA module check requires Windows')
    if os.environ.get('NIKKE_CUDA_CACHE_REQUIRED')!='1' or cuda_artifact_kind()!='ptx':
        raise ValueError('CUDA module check requires cache-only PTX')
    if resident:
        from portable_resident_layout import verify_cuda_layout_assertions
        verify_cuda_layout_assertions(source,resident)
    artifact,receipt=compile_cuda_source(source,artifact_kind='ptx')
    if receipt.get('enabled') is not True or receipt.get('hit') is not True or receipt.get('identity',{}).get('artifact')!='ptx':
        raise ValueError('CUDA module check did not obtain a verified PTX cache hit')
    with _cuda_module(artifact,entry,'ptx',resident,jit_opt_level=jit_opt_level) as loaded:
        metadata=dict(loaded[3],module_verified=True,artifact_kind='ptx',compile_artifact=receipt,
                      kernel_calls=0,buffer_allocations=0,calculation_verified=False,jit_optimization_level=jit_opt_level)
    return metadata

def cuda_artifact_kind():
    kind=os.environ.get('NIKKE_CUDA_ARTIFACT','cubin')
    if kind not in ('ptx','cubin'):raise ValueError('NIKKE_CUDA_ARTIFACT must be cubin or ptx')
    return kind


def cuda_split_compile_threads():
    value=os.environ.get('NIKKE_CUDA_SPLIT_COMPILE','1')
    if value not in ('1','2'):
        raise ValueError('NIKKE_CUDA_SPLIT_COMPILE must be1 or2; automatic/all-core compilation is forbidden')
    return int(value)


def cuda_compile_options(kind, ptxas_level=None, *, split_compile=None):
    if kind not in ('ptx','cubin'):raise ValueError('Invalid CUDA artifact kind')
    if ptxas_level is not None and (kind!='cubin' or type(ptxas_level) is not int or ptxas_level not in range(4)):
        raise ValueError('ptxas optimization level requires CUBIN and integer0..3')
    options=['--std=c++17','--gpu-architecture='+('sm_86' if kind=='cubin' else 'compute_86'),'--fmad=false']
    threads=cuda_split_compile_threads() if split_compile is None else split_compile
    if type(threads) is not int or threads not in (1,2):raise ValueError('NVRTC compiler threads must be1 or2')
    # Opt-in only: default argv/cache identities stay byte-identical. The
    # parallel optimizer count participates in the ordinary exact cache key.
    if threads==2:options.append('--split-compile=2')
    # NVRTC11.3 accepts the forwarding option and payload as separate argv
    # strings. Its parser rejects the joined '= -O' form before compilation.
    if ptxas_level is not None:options.extend(['--ptxas-options','-O'+str(ptxas_level)])
    return options


def compile_cuda_artifact(lib, source, compiler_files, *, artifact_kind=None, library_factory=None):
    from portable_compile_cache import get_or_compile,quoted_headers
    artifact_kind=cuda_artifact_kind() if artifact_kind is None else artifact_kind
    level=os.environ.get('NIKKE_CUDA_PTXAS_OPT_LEVEL')
    if level not in (None,'','0','1','2','3'):raise ValueError('Invalid NIKKE_CUDA_PTXAS_OPT_LEVEL')
    threads=cuda_split_compile_threads()
    options = cuda_compile_options(artifact_kind,None if level in (None,'') else int(level),split_compile=threads)
    required=os.environ.get('NIKKE_CUDA_CACHE_REQUIRED','0')
    if required not in ('0','1'):raise ValueError('NIKKE_CUDA_CACHE_REQUIRED must be0 or1')
    directory=os.environ.get('NIKKE_CUDA_COMPILE_CACHE') or None
    if required=='1' and directory is None:raise ValueError('Required CUDA cache directory is missing')
    def compile_now():
        nonlocal lib
        if required=='1':raise RuntimeError('Cold CUDA compilation forbidden; required cache miss')
        if lib is None:lib=library_factory()
        def check(code):
            if code: raise RuntimeError(f'NVRTC error {code}')
        if threads==2:
            major,minor=C.c_int(),C.c_int()
            check(lib.nvrtcVersion(C.byref(major),C.byref(minor)))
            if major.value!=12 or minor.value<4:
                raise ValueError('Two-thread NVRTC compilation requires verified NVRTC12.4..12.x')
        program=C.c_void_p()
        try:
            check(lib.nvrtcCreateProgram(C.byref(program),source,b'portable.cu',0,None,None))
            encoded=[option.encode() for option in options]
            code=lib.nvrtcCompileProgram(program,len(encoded),(C.c_char_p*len(encoded))(*encoded))
            size=C.c_size_t();check(lib.nvrtcGetProgramLogSize(program,C.byref(size)))
            log=C.create_string_buffer(size.value);check(lib.nvrtcGetProgramLog(program,log))
            if code: raise RuntimeError(log.value.decode('utf-8','replace'))
            get_size=getattr(lib,'nvrtcGetCUBINSize' if artifact_kind=='cubin' else 'nvrtcGetPTXSize')
            get_data=getattr(lib,'nvrtcGetCUBIN' if artifact_kind=='cubin' else 'nvrtcGetPTX')
            check(get_size(program,C.byref(size)))
            if size.value==0:raise RuntimeError('NVRTC returned an empty '+artifact_kind+' artifact')
            artifact=C.create_string_buffer(size.value);check(get_data(program,artifact))
            if artifact_kind=='cubin' and not artifact.raw.startswith(b'\x7fELF'):
                raise RuntimeError('NVRTC CUBIN artifact is not a native ELF binary')
            return artifact.raw
        finally:
            if program: lib.nvrtcDestroyProgram(C.byref(program))
    artifact,receipt=get_or_compile(source,options,compiler_files,compile_now,directory,header_files=quoted_headers(source),artifact_kind=artifact_kind)
    if artifact_kind=='cubin' and not artifact.startswith(b'\x7fELF'):
        raise RuntimeError('NVRTC CUBIN artifact is not a native ELF binary')
    return artifact,receipt
