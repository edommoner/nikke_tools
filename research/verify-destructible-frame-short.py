"""Ordinary notify -> activation/budget -> common damage Frame -> typed landings."""
import array,copy,importlib.util,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from destructible_frame_cases import fixtures
from destructible_frame_runtime import projectile_handler
s=importlib.util.spec_from_file_location('df_skill',ROOT/'research/verify-destructible-skill-short.py');skill=importlib.util.module_from_spec(s);s.loader.exec_module(skill)
suite=types.SimpleNamespace(INPUT=102600);cross=skill.cross
def compile_case(c):
    w=skill.compile_case(c);w[102587]=0x44465231;w[102588]=c['roots'];w[102589]=dict(burst_cast=3,on_attack=7)[c['event']]
    # The existing ordinary end-of-skill path owns gauge; this contract's
    # declared scalar context has no weapon gauge gain.
    for who in range(5):
        p=skill.L['WEAPON_BASE']+who*skill.L['WEAPON_WORDS']+12;w[p:p+2]=[0,0]
    return w
def prepare():
    rows=[(c['name'],compile_case(c),c) for c in fixtures()];seed=rows[0][1]
    for name,offset,value in [('row',0,256),('attack-id',1,1<<24),('full-burst',2,2),('manual-skill-magic',3,0x44534b31),('roots-zero',4,0),('roots-overflow',4,3),('event',5,49),('reserved',6,1),('counter-as-skill',0,0)]:
        w=list(seed);w[102584+offset]=value;rows.append(('reject/destructible-frame/'+name,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(c):
    sampled=dict(coefficient=0.,damage=0.);calls=[]
    def producer(world,bm):
        receipts=[];bm.state['full_burst']=c['full_burst']
        def observe(effect,amount,answers):
            sampled.update(amount);calls.append(effect['name']);receipts[:]=answers
        with projectile_handler(bm,world,skill.character(c),base_attack=1000.,weapon=skill.engine_worker.META[skill.NAMES[0]],defense=c['defense'],attack_id=c['attack_id'],observe=observe):
            for _ in range(c['roots']):bm.notify(c['event'],world.last,skill.NAMES[0])
        return receipts
    result=skill.attack.native_reference(c,producer=producer)
    result['sampled']={k:skill.attack.bits(sampled[k]) for k in ('coefficient','damage')};result['activations']=len(calls);return result
def decode(block,c):
    result=skill.decode(block,c);result['activations']=block[705008]
    at=skill.L['COUNTER_CONTEXT_BASE'];assert not any(block[at:at+1096]),'Counter context leaked after ordinary root dispatch'
    return result
def compare(block,c):
    expected=native_reference(c);actual=decode(block,c);assert actual==expected,(c['name'],actual,expected);return expected
def validate_rejection(block,name):assert name.startswith('reject/destructible-frame/') and block[0]==64,(name,block[:4])
