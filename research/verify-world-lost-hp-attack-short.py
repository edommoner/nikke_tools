"""Live lost-HP ATK through the existing full-battle decoder and native observer."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('lost_hp_battle_base',ROOT/'research/verify-world-heal-share-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_lost_hp_attack_cases import fixtures
from world_lost_hp_attack_native import observe
from portable_lost_hp_attack_contracts import verify
from portable_specs import LIMITS as L,FIELDS as F

def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,metadata,bindings)))
    seed=entries[0][1];d=L['DEFINITION_BASE'];h=L['HEALTH_DEFINITION_BASE'];flags=seed[d+F['FLAGS']]
    mutations=[('no-combat',3,0),('wrong-stat',d+F['STAT'],38),('wrong-kind',d+F['KIND'],4),('wrong-allied-policy',h+1,1),('enemy-policy',h+3,1),('reference-conflict',d+F['FLAGS'],flags|4),('non-self',L['RECIPIENT_BASE'],1),('damage-kind',d+F['KIND'],3)]
    for label,at,value in mutations:
        words=list(seed);words[at]=value;entries.append(('reject/lost-hp-attack-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()

def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native)
    native.pop('lost_hp_attack');native.pop('parts_skill_events')
    return dict(battle=native,skill_trace=trace)
def compare(block,domain):return base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):assert name.startswith('reject/lost-hp-attack-') and block[0]==64
