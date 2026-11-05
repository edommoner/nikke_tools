"""Full physical battle and consumption trace, one CUDA/Metal comparator."""
import array,copy,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from effect_target_count_policy import MODEL
from portable_effect_target_count_shot_cases import fixtures
from portable_effect_target_count_shot_specs import compile_case,decode,SOURCE,INPUT,OUTPUT
from portable_specs import LIMITS as L,FIELDS as F
from world_effect_target_count_shot_native import observe

def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
parent=module('count_shot_parent','research/verify-world-projectile.py')
cross=module('count_shot_digest','research/summarize-portable-cross-gpu.py')
suite=SimpleNamespace(SOURCE=SOURCE,INPUT=INPUT,OUTPUT=OUTPUT)

def prepare():
    entries=[]
    for c in fixtures():
        w,m,b=compile_case(parent,c,model=MODEL);entries.append((c['name'],w,(c,m,b)))
    _,seed,domain=entries[0];row=domain[1]['named_count_physical']['row'];base=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
    for name,at,value in [('zero-shot-lifetime',L['BULLET_DEFINITION_BASE']+row*2,0),('marker-kind',base+F['KIND'],4),('query-trace-overlap',L['COMMAND_BASE']+2*8+6,1)]:
        w=list(seed);w[at]=value;entries.append(('reject/'+name,w,None))
    c=copy.deepcopy(fixtures()[0]);c['duration']=3.;w,_,_=compile_case(parent,c,model=MODEL);entries.append(('reject/shot-trace-capacity',w,None))
    data=array.array('I',[len(entries)])
    for _,words,_ in entries:data.extend(words)
    if sys.byteorder!='little':data.byteswap()
    return entries,data.tobytes()

def native_reference(domain):return observe(domain[0])

def compare(block,domain):
    c,m,b=domain;native=native_reference(domain);actual=parent.decoded(block,m,c,b)
    changed=[k for k in native['battle'] if k!='scope' and actual[k]!=native['battle'][k]]
    if block[0]!=0 or changed:raise AssertionError((c['name'],block[0],changed))
    if parent.reload.charge.team.skill_trace(block,m)!=native['skill_trace']:raise AssertionError('Physical skill trace changed')
    if any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]):raise AssertionError('Physical counter context not restored')
    if decode(block,m)!=native['target_count_shots']:raise AssertionError((c['name'],'physical named count trace differs',decode(block,m),native['target_count_shots']))
    return native
