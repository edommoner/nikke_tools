"""One literal resource/event fixture table for both CUDA and Metal.

Carrier descriptors use the existing packer, with an explicit private mapping
from target_counter to a nonnumeric sentinel marker. Policies and authored
impacts use CounterSpec/Impact. CPU resource state is never supplied to GPU.
"""
import argparse
import array
import copy
import datetime
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
from portable_trigger_specs import pack_event_candidates
from portable_target_counter_program import compiler_effects,patch_program
import portable_target_counter_specs as wire
from target_counter_cases import clone_cases
from world_target_counter_native import observe_case,NAMES
import detail_gpu,engine_worker
s=importlib.util.spec_from_file_location('counter_stack','research/verify-world-actor-stacks.py');stack=importlib.util.module_from_spec(s);s.loader.exec_module(stack)
SOURCE='gpu/target_counter_entry.slang'


def fixtures(): return clone_cases()


def compile_case(case):
    c=copy.deepcopy(stack.fixtures()[0]); c.update(name=case['name'],duration=max(.01,case['actions'][-1][0]),state_queries=[],field_queries=[])
    c['effects']=compiler_effects(case['effects']);c['owners']=[0]*len(c['effects'])
    words,meta,bindings=stack.compile_case(c)
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    patch_program(words,meta,chars,[(e,NAMES[0]) for e in case['effects']])
    words[0]=L['TARGET_COUNTER_ABI'];words[2]=len(case['actions'])
    words[L['COMMAND_BASE']:L['COMMAND_BASE']+L['COMMANDS']*8]=[0]*(L['COMMANDS']*8)
    for step,(time,_) in enumerate(case['actions']):
        at=L['COMMAND_BASE']+step*8;words[at:at+8]=[43,*struct.unpack('<II',struct.pack('<d',time)),step,0,0,0,0]
    words.extend(wire.pack([(e,0) for e in case['effects']],case['actions'],NAMES,meta['states']))
    assert len(words)==L['TARGET_COUNTER_INPUT_WORDS'];return words,meta


def decoded(block,case):
    def number(at): return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    result=[];resources=[]
    for step,_ in enumerate(case['actions']):
        at=L['TARGET_COUNTER_QUERY_BASE']+step*16
        result.append([block[at],number(at+1),block[at+3],block[at+4]])
        assert block[at]<=2  # This table has at most two simultaneous carriers.
        resources.append([dict(uid_ordinal=block[at+8+i*4],epoch=block[at+9+i*4],credit=number(at+10+i*4)) for i in range(block[at])])
    trace=[]
    for i in range(block[L['TARGET_COUNTER_HEAD']+6]):
        at=L['TARGET_COUNTER_TRACE_BASE']+i*24;row=block[at+3];actor=dict(kind=block[at+5],identity=block[at+6],generation=block[at+7]);impact=None
        if block[at+18]: impact=dict(attacker=NAMES[block[at+10]],target=actor,family=block[at+11],outcome=block[at+12],damage=number(at+14),credit=number(at+16),attack_id=block[at+13])
        trace.append(dict(uid_ordinal=block[at+1],epoch=block[at+2],owner=NAMES[0],name=case['effects'][row]['name'],actor=actor,credit=number(at+8),reason={1:'threshold',2:'death'}[block[at+4]],impact=impact,time=number(at+20)))
    return dict(steps=result,resource_steps=resources,completions=trace)


def expected_observation(native):
    return dict(steps=[r['summary'] for r in native['steps']],
        resource_steps=[[{k:r[k] for k in ('uid_ordinal','epoch','credit')} for r in step['resources']] for step in native['steps']],
        completions=native['steps'][-1]['completions'])


def prepare():
    rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0];base=L['TARGET_COUNTER_INPUT_BASE'];p=base+8;a=base+wire.ACTION_BASE
    for name,at,value in [('unknown-counter-magic',base,wire.MAGIC+1),('counter-header-reserved',base+7,1),('counter-policy-reserved',p+15,1),('counter-zero-generation',p+3,0),('counter-kind-overflow',p+1,6),('counter-zero-family',p+6,0),('counter-miss-credit-policy',p+7,1),('counter-unknown-flags',p+8,16),('counter-threshold-nan',p+5,0x7ff80000),('counter-unused-policy',p+16+2,1),('counter-action-reserved',a+15,1),('counter-unused-action',a+len(rows[0]['actions'])*16,1)]:
        words=list(seed);words[at]=value;bad.append((name,words))
    hit=a+16
    for name,at,value in [('impact-family-overflow',hit+7,4),('impact-outcome-overflow',hit+8,3),('impact-attacker-overflow',hit+3,5),('impact-attack-id-overflow',hit+13,1<<24),('impact-credit-nan',hit+12,0x7ff80000),('impact-miss-positive-credit',hit+12,0x3ff00000),('impact-miss-positive-damage',hit+10,0x3ff00000),('impact-negative-credit',hit+12,0xbff00000),('counter-command-step-mismatch',L['COMMAND_BASE']+3,1),('counter-scalar-forgery',L['DEFINITION_BASE']+F['VALUE']+1,0x3ff00000)]:
        words=list(seed);words[at]=value;bad.append((name,words))
    return rows,programs,bad
