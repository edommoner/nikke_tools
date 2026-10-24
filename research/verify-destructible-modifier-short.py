"""Same declared CPU table on resident carriers and shared scalar factors."""
import array,copy,importlib.util,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_runtime import compile_program
from portable_specs import LIMITS as L,FIELDS as F
from destructible_modifier_cases import fixtures
from world_destructible_modifier_native import observe
from portable_destructible_modifier_contracts import verify
from timer_registry_cases import NAMES
suite=types.SimpleNamespace(INPUT=86304,OUTPUT=159744)
s=importlib.util.spec_from_file_location('dm_cross',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
AXES={'projectile_dmg_pct':2,'shield_dmg_pct':3}

def compile_case(c):
    effects=copy.deepcopy(c['effects']);axes=[]
    for e in effects:
        axis=AXES.get(e.get('stat'),0);axes.append(axis)
        if axis:
            if e.get('type')!='buff' or e.get('target') not in ('self','all_allies') or e.get('scaling') is not None:raise ValueError('Declared plain allied modifier required')
            e['stat']='atk_dmg_pct'
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    script=[[0.,0,0,who,0,-1,0,0] for _ in range(c.get('activations',1)) for who in range(5)]
    w,m=compile_program(chars,[(e,NAMES[o]) for e,o in zip(effects,c['owners'])],script,[c['base_attack']]*5,defense=c['defense'])
    assert len(w)==86016
    extension=[0x444d5131,c['kind'],c['attacker'],0,*struct.unpack('<II',struct.pack('<d',c['when'])),*struct.unpack('<II',struct.pack('<d',c['coefficient']))]+[0]*280
    for row,index in enumerate(m['binding_source_indices']):
        extension[32+row]=axes[index]
        if axes[index]:
            # The existing numeric compiler owns value/stack/condition encoding.
            # Marker kind4/stat0 owns the payload; numeric stat0 means ATK and must not be used.
            at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];assert w[at+F['KIND']]==0
            w[at+F['KIND']]=4;w[at+F['STAT']]=0
    w.extend(extension);assert len(w)==suite.INPUT
    return w,c

def prepare():
    rows=[(c['name'],*compile_case(c)) for c in fixtures()];seed=rows[1][1]
    for name,offset,value in [('magic',86016,0),('hit-shield',86017,4),('attacker',86018,5),('reserved',86019,1),('nan-time',86021,0x7ff80000),('negative-coefficient',86023,0xbff00000),('axis',86049,4),('unused-axis',86048+255,2),('axis-on-numeric-stat',86048,2)]:
        w=list(seed);w[offset]=value;rows.append(('reject/destructible-modifier/'+name,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(c):
    n,_=observe(c);verify(c,n);return n

def compare(block,c):
    n=native_reference(c);assert block[0]==0 and block[159712]==0x444d5131 and block[159713]==c['kind']
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    for offset,key in [(159714,'damage'),(159716,'factor5'),(159718,'projectile_modifier'),(159720,'shield_modifier')]:
        assert struct.pack('<II',*block[offset:offset+2])==struct.pack('<d',float(n[key])),(c['name'],key,number(offset),n[key])
    assert not any(block[159722:]),'Unused modifier output tail'
    return n

def validate_rejection(block,name):assert name.startswith('reject/destructible-modifier/') and block[0]==64,(name,block[0])
