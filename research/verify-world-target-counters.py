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
import portable_target_counter_specs as wire
from target_counter_cases import clone_cases
from world_target_counter_native import observe_case,NAMES
import detail_gpu,engine_worker
s=importlib.util.spec_from_file_location('counter_stack','research/verify-world-actor-stacks.py');stack=importlib.util.module_from_spec(s);s.loader.exec_module(stack)
SOURCE='gpu/target_counter_entry.slang'


def fixtures(): return clone_cases()


def compile_case(case):
    c=copy.deepcopy(stack.fixtures()[0]); c.update(name=case['name'],duration=max(.01,case['actions'][-1][0]),state_queries=[],field_queries=[])
    c['effects']=copy.deepcopy(case['effects']);c['owners']=[0]*len(c['effects'])
    for e in c['effects']:
        e.pop('target_counter');e.update(stat='def_pct',fixed_value=0)
        e['trigger']['timing']=[t.replace('event:target_counter_complete:','event:',1) if t.startswith('event:target_counter_complete:') else t for t in e['trigger']['timing']]
    words,meta,bindings=stack.compile_case(c)
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    original=detail_gpu.compile_effects(chars,[(e,NAMES[0]) for e in case['effects']])
    assert original['states']==meta['states'],(original['states'],meta['states'])
    for i,(e,row) in enumerate(zip(case['effects'],original['effects'])):
        at=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS'];words[at+F['KIND']]=4;words[at+F['STAT']]=0
        for slot in range(int(row[144])):
            base=145+slot*7
            if row[base]==58:
                event=L['EVENT_BASE']+i*L['EVENT_WORDS']+slot*8;words[event]=58
                assert words[event+4]==int(row[base+3])
                if slot==0: words[at+F['EVENT']]=58
    pack_event_candidates(words,L)
    words[0]=L['TARGET_COUNTER_ABI'];words[2]=len(case['actions'])
    words[L['COMMAND_BASE']:L['COMMAND_BASE']+L['COMMANDS']*8]=[0]*(L['COMMANDS']*8)
    for step,(time,_) in enumerate(case['actions']):
        at=L['COMMAND_BASE']+step*8;words[at:at+8]=[43,*struct.unpack('<II',struct.pack('<d',time)),step,0,0,0,0]
    words.extend(wire.pack([(e,0) for e in case['effects']],case['actions'],NAMES,meta['states']))
    assert len(words)==L['TARGET_COUNTER_INPUT_WORDS'];return words,meta


def decoded(block,case):
    def number(at): return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    result=[]
    for step,_ in enumerate(case['actions']):
        at=L['TARGET_COUNTER_QUERY_BASE']+step*16
        result.append([block[at],number(at+1),block[at+3],block[at+4]])
    trace=[]
    for i in range(block[L['TARGET_COUNTER_HEAD']+6]):
        at=L['TARGET_COUNTER_TRACE_BASE']+i*24;row=block[at+3];actor=dict(kind=block[at+5],identity=block[at+6],generation=block[at+7]);impact=None
        if block[at+18]: impact=dict(attacker=NAMES[block[at+10]],target=actor,family=block[at+11],outcome=block[at+12],damage=number(at+14),credit=number(at+16),attack_id=block[at+13])
        trace.append(dict(uid_ordinal=block[at+1],epoch=block[at+2],owner=NAMES[0],name=case['effects'][row]['name'],actor=actor,credit=number(at+8),reason={1:'threshold',2:'death'}[block[at+4]],impact=impact,time=number(at+20)))
    return dict(steps=result,completions=trace)


def prepare():
    rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0];base=L['TARGET_COUNTER_INPUT_BASE'];p=base+8;a=base+wire.ACTION_BASE
    for name,at,value in [('unknown-counter-magic',base,wire.MAGIC+1),('counter-header-reserved',base+7,1),('counter-policy-reserved',p+15,1),('counter-zero-generation',p+3,0),('counter-kind-overflow',p+1,6),('counter-zero-family',p+6,0),('counter-miss-credit-policy',p+7,1),('counter-unknown-flags',p+8,16),('counter-threshold-nan',p+5,0x7ff80000),('counter-unused-policy',p+16+2,1),('counter-action-reserved',a+15,1),('counter-unused-action',a+len(rows[0]['actions'])*16,1)]:
        words=list(seed);words[at]=value;bad.append((name,words))
    hit=a+16
    for name,at,value in [('impact-family-overflow',hit+7,4),('impact-outcome-overflow',hit+8,3),('impact-attacker-overflow',hit+3,5),('impact-attack-id-overflow',hit+13,1<<24),('impact-credit-nan',hit+12,0x7ff80000),('impact-miss-positive-credit',hit+12,0x3ff00000),('impact-miss-positive-damage',hit+10,0x3ff00000),('impact-negative-credit',hit+12,0xbff00000),('counter-command-step-mismatch',L['COMMAND_BASE']+3,1),('counter-scalar-forgery',L['DEFINITION_BASE']+F['VALUE']+1,0x3ff00000)]:
        words=list(seed);words[at]=value;bad.append((name,words))
    return rows,programs,bad


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);args=ap.parse_args()
    rows,programs,bad=prepare();native=[observe_case(c) for c in rows]
    if args.cpu_only: print('Counter inputs',len(rows),'native48 steps, raw',len(bad),'GPU0');return
    old=json.loads((ROOT/'research/portable-world-actor-stack-metal.json').read_text());prior=Path(old['captured']);oldin=(prior/'input.bin').read_bytes();oldout=(prior/'readback.bin').read_bytes();n=int.from_bytes(oldin[:4],'little');assert n==590
    packed=array.array('I',[len(rows)+len(bad)+n]);iw=92336*4;ow=524288*4
    for words,_ in programs: packed.extend(words)
    for _,words in bad: packed.extend(words)
    for i in range(n):
        words=list(struct.unpack_from('<'+'I'*92336,oldin,4+i*iw));words[0]=L['TARGET_COUNTER_ABI'];words.extend([0]*wire.INPUT_WORDS);packed.extend(words)
    if sys.byteorder!='little': packed.byteswap()
    data=packed.tobytes()
    if args.replay:
        folder=args.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert evidence['source_sha256']==source_hashes(SOURCE)
    else:
        folder=ROOT/'research/portable-build'/('world-target-counter-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
        try: raw,evidence=execute(SOURCE,'portableEvents',data,L['TARGET_COUNTER_INPUT_WORDS'],524288,args.backend)
        except Exception as error: (folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
        (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    blocks=array.array('I');blocks.frombytes(raw)
    if sys.byteorder!='little': blocks.byteswap()
    checked=[]
    for i,(case,expected) in enumerate(zip(rows,native)):
        block=blocks[i*524288:(i+1)*524288]
        try:
            actual=decoded(block,case);wanted=dict(steps=[r['summary'] for r in expected['steps']],completions=expected['steps'][-1]['completions']);passed=block[0]==0 and actual==wanted
        except Exception as error: actual=dict(error=repr(error));wanted=expected;passed=False
        checked.append(dict(name=case['name'],passed=passed,status=block[0],actual=actual,native=wanted))
    rejected=[dict(name=name,status=blocks[(len(rows)+j)*524288],passed=blocks[(len(rows)+j)*524288]==64) for j,(name,_) in enumerate(bad)]
    offset=len(rows)+len(bad);preserved=[dict(index=i,passed=raw[(offset+i)*ow:(offset+i+1)*ow]==oldout[i*ow:(i+1)*ow]) for i in range(n)]
    report=dict(passed=all(c['passed'] for c in checked+rejected+preserved),cases=checked,rejected_cases=rejected,preserved590=preserved,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),cpu_state_used_as_input=False,physical_landing_bridge=False,typed_target_conditions=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
    (ROOT/f'research/portable-world-target-counter-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    assert report['passed'],[c.get('name',c.get('index')) for c in checked+rejected+preserved if not c['passed']]
    print('Counter native10/48 steps, raw',len(bad),'old590 all output words exact',args.backend)


if __name__=='__main__':main()
