"""Native duration-reference battles; shared normal and diagnostic adapters."""
import array,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
def module(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'research'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=module('duration_base','verify-world-not-core-short.py');suite,cross=base.suite,base.cross
from portable_duration_scaling_extended_cases import fixtures
from portable_duration_scaling_extended_contracts import verify
from world_duration_scaling_native import observe
from portable_specs import LIMITS as L,FIELDS as F

def prepare():
    rows=[]
    for c in fixtures():
        if 'body' in c:
            p=base.roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));w,m=base.roster.compile_projectile_battle(p)
        else:w,m,p=suite.compile_case(c)
        rows.append((c['name'],w,(c,m,p,w)))
    seed=rows[0][1];at=L['REFERENCE_DEFINITION_BASE']+2*4+3;d=L['DEFINITION_BASE']+2*L['DEFINITION_WORDS'];assert seed[at]&0x80000000
    for name,changes in [('key',[(at,0x800001ff)]),('name',[(at,seed[at]^(1<<9))]),('reserved',[(at,seed[at]|(1<<20))]),('kind',[(d+F['KIND'],3)]),('duration-nan',[(d+F['DURATION']+1,0x7ff80000)]),('no-world',[(L['WORLD_FRAME_INPUT_BASE'],0)]),('no-combat',[(3,0)])]:
        w=list(seed)
        for i,value in changes:w[i]=value
        rows.append(('reject/duration-scaling-'+name,w,None))
    data=array.array('I',[len(rows)])
    for _,w,_ in rows:data.extend(w)
    if sys.byteorder!='little':data.byteswap()
    return rows,data.tobytes()

def native_reference(domain):
    c=domain[0];n,t=observe(c);verify(c,n);state=n.pop('duration_scaling');return dict(battle=n,skill_trace=t,duration=state)
def compare(block,domain):
    c,m,p,words=domain;expected=native_reference(domain);assert block[0]==0,(c['name'],block[0])
    if 'body' in c:
        n=expected['battle'];_,_,_,diff=base.roster.compare(block,p,(words,m),n['battle'],n['projectile_shots']);assert not diff,(c['name'],diff[:8])
    else:
        actual=suite.decoded(block,m,c,p)
        if c.get('observe_healing_storage'):actual['healing_storage']=base.storage.decoded_storage(block,m,c)
        changed=[k for k in expected['battle'] if k!='scope' and actual[k]!=expected['battle'][k]];assert not changed,(c['name'],changed)
        assert suite.reload.charge.team.skill_trace(block,m)==expected['skill_trace'],(c['name'],'skill trace')
    return expected
def validate_rejection(block,name):assert name.startswith('reject/duration-scaling-') and block[0]==64

def compare_diagnostic(block,domain):
    expected=compare(block,domain);checks=expected['duration']['checks'];head=L['NATIVE_DIAG_BASE'];assert list(block[head:head+3])==[0x44555331,len(checks),0];assert not any(block[head+3:head+16])
    for i,row in enumerate(checks):
        at=head+16+i*16;duration=row['duration']
        if duration is None and row['duration_values'] is not None:duration=float(row['duration_values'].get('10',0))
        if duration is None:duration=-1
        read=bool(row['reads']);value=row['reads'][0]['value'] if read else None;present=value is not None
        assert list(block[at:at+4])==[row['definition'],row['owner'],int(read),int(present)],(domain[0]['name'],i,'identity/read')
        for offset,number in zip((4,6,8,10),(row['time'],duration,value if present else 0,row['expires_at'])):
            assert tuple(block[at+offset:at+offset+2])==struct.unpack('<II',struct.pack('<d',number)),(domain[0]['name'],i,offset,'binary64 duration reference/expiry')
        descriptor=domain[3][L['REFERENCE_DEFINITION_BASE']+row['definition']*4+3];assert block[at+12]==descriptor and not any(block[at+13:at+16])
    assert not any(block[head+16+len(checks)*16:head+L['NATIVE_DIAG_WORDS']])
    return expected
