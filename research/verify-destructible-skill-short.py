"""Original definition -> shared damage query -> typed projectile producer."""
import array,copy,importlib.util,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
import engine_worker
from destructible_skill_cases import fixtures
from destructible_skill_specs import compiler_effect,MAGIC
from destructible_skill_runtime import execute
from destructible_world_runtime import DestructibleWorld
from test_target_counter_runtime import manager,NAMES
from portable_specs import LIMITS as L
s=importlib.util.spec_from_file_location('ds_attack',ROOT/'research/verify-destructible-attack-short.py');attack=importlib.util.module_from_spec(s);s.loader.exec_module(attack)
suite=types.SimpleNamespace(INPUT=102600);cross=attack.cross
def character(c):return dict(name=NAMES[0],skill_levels={str(i):c['level'] for i in (1,2,3)})
def compile_case(c):
    lowered=copy.deepcopy(c);row=c['skill_row'];lowered['effects'][row]=compiler_effect(c['effects'][row],character(c))
    # Existing world-skill counters require a boss sentinel carrier route.
    # Its explicit typed Actor policy remains untouched and owns the hit test.
    for e in lowered['effects']:
        if 'target_counter' in e:e['target']='boss'
    w=attack.compile_case(lowered);w[102584:]=[row,c['attack_id'],int(c['full_burst']),MAGIC]+[0]*12
    # This scalar context is authored input, not a CPU-computed damage result.
    w[L['TARGET_BASE']+6:L['TARGET_BASE']+8]=attack.dc.world.words(c['defense'])
    # Use the existing world-skill admission, not literal counter-only mode.
    w[0]=L['WORLD_SKILL_ABI'];w[L['TARGET_COUNTER_INPUT_BASE']+6]=7
    clock=w[L['WORLD_FRAME_INPUT_BASE']+6:L['WORLD_FRAME_INPUT_BASE']+8]
    w[L['COMMAND_BASE']:L['COMMAND_BASE']+8]=[24,*clock]+[0]*5
    at=L['TARGET_COUNTER_INPUT_BASE']+4104;w[at:at+1024]=[0]*1024
    return w
def prepare():
    rows=[(c['name'],compile_case(c),c) for c in fixtures()];seed=rows[0][1]
    for name,offset,value in [('row',0,256),('attack-id',1,1<<24),('full-burst',2,2),('magic',3,0),('reserved',4,1),('counter-as-skill',0,0)]:
        w=list(seed);w[102584+offset]=value;rows.append(('reject/destructible-skill/'+name,w,None))
    w=list(seed);w[L['COMMAND_BASE']+1:L['COMMAND_BASE']+3]=[0,0];rows.append(('reject/destructible-skill/unreached-native-clock',w,None))
    w=list(seed);w[L['DAMAGE_DEFINITION_BASE']]=0;rows.append(('reject/destructible-skill/literal-sentinel-route',w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(c):
    sampled={}
    def producer(world,bm):
        result,receipts=execute(world,bm,c['effects'][c['skill_row']],character(c),base_attack=1000.,weapon=engine_worker.META[NAMES[0]],defense=c['defense'],attack_id=c['attack_id'],full_burst=c['full_burst'])
        sampled.update(result);return receipts
    expected=attack.native_reference(c,producer=producer)
    expected['sampled']={k:attack.bits(sampled[k]) for k in ('coefficient','damage')};return expected
def decode(block,c):
    actual=attack.decode(block,c);actual['sampled']=dict(coefficient=struct.pack('<II',*block[705004:705006]).hex(),damage=struct.pack('<II',*block[705006:705008]).hex());return actual
def compare(block,c):
    expected=native_reference(c);actual=decode(block,c);assert actual==expected,(c['name'],actual,expected);return expected
def validate_rejection(block,name):assert name.startswith('reject/destructible-skill/') and block[0]==64,(name,block[:4])
