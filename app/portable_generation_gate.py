"""Read-only admission for generation inside the existing bounded packet child.

Metadata is necessary but insufficient: inspect the current Windows Job and
priority before package hashing or Slang. This never creates or owns a Job.
"""
import ctypes as C
import json
import os
from pathlib import Path
from portable_job_limits import read_job_limits


def current_containment():
    dll=C.WinDLL('kernel32',use_last_error=True)
    for name,args,result in (
        ('GetCurrentProcess',[],C.c_void_p),
        ('IsProcessInJob',[C.c_void_p,C.c_void_p,C.POINTER(C.c_int)],C.c_int),
        ('GetPriorityClass',[C.c_void_p],C.c_uint32)):
        fn=getattr(dll,name);fn.argtypes=args;fn.restype=result
    process=dll.GetCurrentProcess();member=C.c_int()
    if not dll.IsProcessInJob(process,None,C.byref(member)):raise C.WinError(C.get_last_error())
    if not member.value:raise ValueError('Generation requires an actual inherited Job')
    priority=dll.GetPriorityClass(process)
    if not priority:raise C.WinError(C.get_last_error())
    return dict(in_job=True,priority_class=priority,**read_job_limits(dll,None,include_flags=True))


def verify_packet_generation(root,folder,output):
    if folder is None:raise ValueError('Standalone generation is Mac CPU-only; Windows requires bounded packet-stage generation')
    root=Path(root).resolve();folder=Path(folder).resolve();output=Path(output).resolve()
    load=lambda name:json.loads((folder/name).read_text(encoding='utf-8'))
    plan=load('recipe.json');child=load('child.json');command=load('command.json')
    manifest=json.loads((root/'gpu-package.json').read_text(encoding='utf-8'))
    gate=load('start.json')
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location('generation_packet_admission',root/'scripts/run-gpu-packet.py')
    packet=module_from_spec(spec);spec.loader.exec_module(packet)
    expected=packet.recipe(manifest['package_id'],'generation',plan['backend'],folder,plan['original_workspace'],plan['timeout_seconds'])
    if plan!=expected or gate!={}:raise ValueError('Generation packet recipe/gate mismatch')
    if child['pid']!=os.getpid() or child['ppid']!=os.getppid() or child['package_id']!=manifest['package_id']:raise ValueError('Generation packet child identity mismatch')
    if (output!=Path(plan['proof_capture']).resolve() or command['cwd']!=str(root)
        or command['shell'] is not False or command['timeout_seconds']!=plan['timeout_seconds']
        or command['argv']!=[command['base_python'],str(root/'scripts/run-gpu-packet.py'),'--_child','--capture',str(folder)]):raise ValueError('Generation packet command/output mismatch')
    facts=current_containment()
    if (facts.get('in_job') is not True or facts.get('priority_class')!=0x4000
        or facts.get('job_memory_limit_bytes')!=2147483648
        or facts.get('job_limit_flags',0)&0x2200!=0x2200):raise ValueError('Generation packet native containment mismatch')
    return dict(packet_stage_verified=True,package_id=manifest['package_id'],**facts)
