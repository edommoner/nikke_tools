"""Live projectile selection plus existing typed landing/counter execution."""
import array,copy,dataclasses,importlib.util,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
import engine_worker
from destructible_attack_cases import fixtures
from destructible_attack_runtime import projectiles
from destructible_world_runtime import DestructibleWorld
from effect_runtime import state,pool
from impact_specs import ActorHandle
from test_target_counter_runtime import manager,NAMES
from portable_specs import LIMITS as L
s=importlib.util.spec_from_file_location('da_counter',ROOT/'research/verify-destructible-counter-short.py');dc=importlib.util.module_from_spec(s);s.loader.exec_module(dc)
suite=types.SimpleNamespace(INPUT=102600);cross=dc.cross;bits=dc.bits
def compile_case(c):
    d=copy.deepcopy(c);d['who']=[0,0]
    w=dc.compile_case(d)
    extra=[c['who'],c['family'],c['outcome'],c['attack_id'],*dc.world.words(c['damage']),*dc.world.words(c['credit']),*([0]*8)]
    return w+extra
def prepare():
    rows=[(c['name'],compile_case(c),c) for c in fixtures()];seed=rows[0][1]
    for name,offset,value in [('attacker',0,5),('family',1,4),('outcome',2,3),('attack-id',3,1<<24),('reserved',8,1)]:
        w=list(seed);w[102584+offset]=value;rows.append(('reject/destructible-attack/'+name,w,None))
    w=list(seed);w[102584+2]=0;rows.append(('reject/destructible-attack/miss-with-damage',w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(c):
    w=DestructibleWorld(c['nodes'],c['bindings']);bm=manager(c['effects']);bm.notify('battle_start',0,NAMES[0])
    for op in c['ops']:w.advance(op[5]);bm.tick(op[5])
    receipts=projectiles(w,bm,NAMES[c['who']],c['family'],c['outcome'],c['damage'],c['credit'],c['attack_id'])
    actual=[]
    for slot,h,r in receipts:actual.append(dict(slot=slot,handle=[int(h.kind),h.identity,h.generation],delivered=r['delivered'],broken=r['broken'],took=bits(r['took'])))
    live=[r for r in pool(bm,'target_hit_counter').values() if any(ab is r.carrier for ab in bm._active)]
    trace=[dc.trace_normal(dict(dataclasses.asdict(r),time=t)) for t,r in state(bm).counter_trace]
    return dict(receipts=actual,state=dc.world.old.snapshot(w.targets),clock=dc.world.clock_states(w),trace=trace,counters=dict(live=len(live),credit=bits(sum(r.credit for r in live)),completed=state(bm).counter_completed,epoch=state(bm).counter_epoch,dead=len(state(bm).dead_actors)),atk=bits(bm.get_buffs(NAMES[0],'__enemy__',w.last).get('atk_pct',0)))
def decode(block,c):
    assert block[0]==0,(c['name'],block[:4])
    bit=lambda at:struct.pack('<II',*block[at:at+2]).hex()
    count=block[710000];assert count<=128
    receipts=[]
    for i in range(count):
        at=710001+i*8;receipts.append(dict(slot=block[at],handle=list(block[at+1:at+4]),delivered=bool(block[at+4]),broken=bool(block[at+5]),took=bit(at+6)))
    targets=[]
    for slot in range(128):
        p=616384+slot*14
        if block[p+2]==0:assert not any(block[p:p+14]);continue
        assert slot<len(c['bindings']) and block[p+13]==0
        targets.append(dict(slot=slot,handle=list(block[p:p+3]),owner=None if block[p+10]==0xffffffff else list(block[p+10:p+13]),alive=bool(block[p+3]),remaining=bit(p+4),capacity=bit(p+6),expires=bit(p+8)))
    q=L['TARGET_COUNTER_QUERY_BASE'];trace=[dc.trace_normal(r) for r in dc.literal.decoded(block,dict(c,actions=[None]))['completions']]
    return dict(receipts=receipts,state=targets,clock=[list(block[600032+n*24:600032+(n+1)*24]) for n in range(32)],trace=trace,counters=dict(live=block[q],credit=bit(q+1),completed=block[q+3],epoch=block[q+4],dead=block[q+5]),atk=bit(705000))
def compare(block,c):
    expected=native_reference(c);actual=decode(block,c);assert actual==expected,(c['name'],actual,expected);return expected
def validate_rejection(block,name):assert name.startswith('reject/destructible-attack/') and block[0]==64,(name,block[:4])
