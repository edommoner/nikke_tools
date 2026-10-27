"""One battle clock, independent typed and frozen-lock recipient consumers."""
import array,copy,importlib.util,sys
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
live=module('lock_typed_live','research/verify-live-lock-delivery.py')
typed=module('lock_typed_battle','research/verify-destructible-battle-short.py')
from portable_lock_typed_layout import SOURCE,INPUT,OUTPUT,check,lock_view
from world_lock_packet_native import capture
from world_physical_locks_native import baseline
from live_lock_delivery_policy import MODEL
from destructible_battle_runtime import typed_battle
from portable_heavyarms_lock_cases import NAME,source_definitions
from world_frame_native import roster_names
suite=SimpleNamespace(SOURCE=SOURCE,INPUT=INPUT,OUTPUT=OUTPUT);cross=live.cross

def fixtures():
    rows=[]
    for label,count,capacity,delay,cover in [('live',3,1e8,0,False),('broken',3,1,0,False),('late',3,1e8,.3,False),('capacity128',128,1e8,0,False),('cover',3,1e8,0,True)]:
        c=copy.deepcopy(live.fixtures()[2 if cover else 0]);c.update(name='lock-projectile/'+label,max_attacks=128)
        names=roster_names(c);names[0]=NAME;c['names']=names
        c['patterns'].append(dict(id='typed',kind='idle',delay=delay,until=dict(time=3)))
        c['typed_bindings']=[dict(node='typed',kind=2,identity=10+i,capacity=capacity) for i in range(count)]
        c['effects'].append(copy.deepcopy(source_definitions()[24]));c['owners'].append(0)
        rows.append(c)
    return rows

def compile_case(c):
    check(ROOT)
    with patch.object(typed.base,'compile_case',live.compile_case):words,domain=typed.compile_case(c)
    return words,domain[1],domain[2]

def native_reference(domain,*,candidate_observer=None):
    c,meta,bindings=domain;before=copy.deepcopy(c)
    def run(diagnostics,observer=None):
        with typed_battle(c['typed_bindings'],max_attacks=c['max_attacks']) as data:
            with capture(c,delivery_model=MODEL,diagnostics=diagnostics,candidate_observer=observer) as result:
                battle,trace=baseline(c)
        result.update(battle=battle,skill_trace=trace,typed=typed.typed_observation(c,data));return result
    n=run(True,candidate_observer);plain=run(False)
    if n['battle']!=plain['battle'] or n['skill_trace']!=plain['skill_trace'] or n['typed']!=plain['typed'] or c!=before:raise AssertionError('Composed diagnostics changed full native model/input')
    return n

def compare(block,domain):
    candidates=[];n=native_reference(domain,candidate_observer=lambda values:candidates.append(tuple(values)))
    live.parent.parent.parent.compare_observed(lock_view(block),domain,n,candidates,manual=bool(domain[0].get('physical_cover_composition')),packet_bindings=True)
    actual=typed.decode(block,domain)
    if actual!=n['typed']:raise AssertionError(('Composed typed state/attacks',actual,n['typed']))
    return n

def prepare():
    entries=[]
    for c in fixtures():
        w,m,b=compile_case(c);entries.append((c['name'],w,(c,m,b)))
    seed=entries[0][1]
    for name,at,value in [('typed-magic',109523,0),('typed-node',104400+2328,32),('typed-capacity',109521,0),('typed-reserved',104400+2336,1)]:
        w=list(seed);w[at]=value;entries.append(('reject/lock-projectile/'+name,w,None))
    raw=array.array('I',[len(entries)])
    for _,w,_ in entries:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()
