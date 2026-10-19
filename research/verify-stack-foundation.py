"""Shared integer-stack/notice foundation proof for either real GPU backend.

Expected arithmetic uses Python arbitrary-precision integers. Expected event
order comes from the adapted native manager, after actual GPU execution.
"""
import argparse,hashlib,importlib.util,json,math,random,struct,sys
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts','tests')]
from portable_backend import execute
from portable_runtime import pack_programs
from portable_specs import LIMITS as L

def oracle(current,value,cap,floor,policy):
    if not math.isfinite(current) or not math.isfinite(value) or int(current)!=current or floor not in (0,1) or cap==0 or cap!=0xffffffff and not 1<=cap<=0x7fffffff or not 0<=policy<=3:return 0,64
    delta=int(1 if policy&1 and value==0 else value)
    if policy&2:delta=-delta
    result=int(current)+delta
    if cap!=0xffffffff:result=min(result,cap)
    result=max(floor,result)
    return (0,2) if result>0x7fffffff else (result,0)

def numeric_cases():
    currents=[0.,-0.,1.,-1.,3.,2147483646.,2147483647.,float(2**53),-float(2**53),1e308,-1e308]
    values=[0.,-0.,5e-324,-5e-324,.5,-.5,.999,-.999,1.,-1.,1.9,-1.9,2147483647.,-2147483647.,float(2**53),-float(2**53),1e308,-1e308]
    rows=[(c,v,cap,floor,policy,0) for c in currents for v in values for cap in (1,3,0x7fffffff,0xffffffff) for floor in (0,1) for policy in range(4)]
    rng=random.Random(20261020)
    for _ in range(12000):
        c=struct.unpack('<d',rng.getrandbits(64).to_bytes(8,'little'))[0]
        v=struct.unpack('<d',rng.getrandbits(64).to_bytes(8,'little'))[0]
        if not math.isfinite(c) or not math.isfinite(v):continue
        rows.append((float(int(c)),v,rng.choice((1,31,0x7fffffff,0xffffffff)),rng.randrange(2),rng.randrange(4),0))
    rows += [(1.,float('inf'),1,0,0,0),(1.,float('nan'),1,0,0,0),(float('inf'),1.,1,0,0,0),
             (1.5,1.,3,0,0,0),(1.,1.,0,0,0,0),(1.,1.,0x80000000,0,0,0),(1.,1.,3,2,0,0),(1.,1.,3,0,4,0)]
    for current in [0,1,0x7ffffffe,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]+[rng.getrandbits(32) for _ in range(257)]:
        for cap in (0,1,31,0x7fffffff,0x80000000,0xffffffff):rows.append((float(current),1.,cap,0,0,1))
    return rows

def numeric(backend):
    cases=numeric_cases();packed=struct.pack('<I',len(cases))+b''.join(struct.pack('<dd4I',*c) for c in cases)
    raw,evidence=execute('gpu/stack_numeric_probe.slang','stackNumericProbe',packed,8,2,backend)
    statuses=Counter()
    for i,c in enumerate(cases):
        expected=oracle(*c[:5]);actual=struct.unpack_from('<2I',raw,i*8)
        assert actual==expected,(i,c,actual,expected)
        statuses[actual[1]]+=1
    result=dict(passed=True,cases=len(cases),statuses=dict(statuses),cpu_trace_used_as_gpu_input=False,
                scope='Integer update/default/sign/clamp before checked signed31-bit result; not effect-family admission',**evidence)
    (R/f'research/portable-stack-numeric-{backend}.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Stack numeric cases passed',len(cases),backend,flush=True)

def definitions():
    def buff(name,value,event):return dict(name=name,source='스킬1',type='buff',stat='atk_pct',fixed_value=value,target='self',duration=-1,max_stack=100,trigger=dict(timing=[event],condition=[]))
    return [buff('topic',1,'stack_reach:topic:2'),
            dict(name='remove first',source='스킬1',type='instant',stat='remove_named_buff',target='self',target_effect='topic',trigger=dict(timing=['stack_reach:topic:2'],condition=[])),
            buff('nested',100,'event:state_end:topic'),buff('tail',10,'stack_reach:topic:3'),buff('ended',1000,'event:state_end:topic')]

def notices(backend):
    spec=importlib.util.spec_from_file_location('notice_compile',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    import copy
    effects=definitions();cases=[dict(name='notice-'+str(mode),effects=copy.deepcopy(effects),owners=[0]*5,script=[[0,0,7,0,mode,-1,0,0]]) for mode in range(9)]
    cases[8]['owners']=[4]*5;cases[8]['effects'][0]['trigger']['timing']=['stack_reach:topic:2147483647']
    programs=[v.compile_case(c) for c in cases]
    assert all(words[L['COMMAND_BASE']+5]==mode for mode,(words,_) in enumerate(programs))
    raw,evidence=execute('gpu/stack_notice_probe.slang','stackNoticeProbe',pack_programs(programs),L['INPUT_WORDS'],L['OUTPUT_WORDS'],backend)
    rows=[]
    for mode in range(9):
        base=mode*L['OUTPUT_WORDS']*4
        if mode==8:
            assert struct.unpack_from('<5I',raw,base)==(0,0,1,1,16)
            assert struct.unpack_from('<d',raw,base+24)[0]==1
            from test_target_counter_runtime import manager,NAMES
            bm=manager(cases[8]['effects'],[4]*5);bm.notify('stack_reach:topic:2147483647',0,NAMES[4])
            assert bm.get_buffs(NAMES[4],'__enemy__',0)['atk_pct']==1
            rows.append(dict(mode=mode,passed=True,owner=4,stack=2147483647,native_attack_pct=1));continue
        if mode==6:
            assert struct.unpack_from('<6I',raw,base)==(0,0,0,2,1,2)
            assert struct.unpack_from('<d',raw,base+24)[0]==2210
            from test_target_counter_runtime import manager,NAMES
            bm=manager(effects);seen=[];original=bm._activate
            def activate(effect,caster,t,*args,**kwargs):
                seen.append(effect['name']);return original(effect,caster,t,*args,**kwargs)
            bm._activate=activate
            bm.notify('stack_reach:topic:2',0,NAMES[0]);bm.notify('stack_reach:topic:3',0,NAMES[0]);bm.notify('event:state_end:topic',0,NAMES[0])
            assert seen==['topic','remove first','nested','ended','tail','nested','ended'],seen
            assert bm.get_buffs(NAMES[0],'__enemy__',0)['atk_pct']==2210
            rows.append(dict(mode=mode,passed=True,native_activation_order=seen,native_attack_pct=2210));continue
        if mode<=1:payloads=[32768+(i%256)*8+i%5 for i in range(4096)];values=[i*524287 for i in range(4096)]
        elif mode==5:payloads=[(32768 if i&1 else 0)+(i%256)*8+i%5 for i in range(4096)];values=[0x7fffffff-i if i&1 else 0 for i in range(4096)]
        elif mode==7:payloads=[0];values=[0]
        else:payloads=[];values=[]
        status=64 if mode in (1,2,3) else 0
        assert struct.unpack_from('<4I',raw,base)==(status,len(payloads),sum(payloads)&0xffffffff,sum(values)&0xffffffff),(mode,struct.unpack_from('<4I',raw,base))
        actual_meta=struct.unpack_from('<'+str(len(payloads))+'H',raw,base+L['REMOVAL_QUEUE_BASE']*4)
        actual_values=struct.unpack_from('<'+str(len(values))+'I',raw,base+L['STACK_NOTICE_VALUE_BASE']*4)
        assert list(actual_meta)==payloads and list(actual_values)==values,mode
        rows.append(dict(mode=mode,passed=True,status=status,notices=len(payloads)))
    result=dict(passed=True,cases=rows,cpu_trace_used_as_gpu_input=False,scope='4096 shared reservations; atomic rejection; 31-bit snapshots; mixed end/stack drain and nested child reuse; not new effect admission',**evidence)
    (R/f'research/portable-stack-notices-{backend}.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Stack notice cases passed',len(rows),backend,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--backend',choices=('metal','cuda'),default='metal');a=p.parse_args()
    numeric(a.backend);notices(a.backend)
