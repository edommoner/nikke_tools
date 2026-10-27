"""Original enemy marker and named debuff run through shared actor carriers.

Candidate order is the existing explicitly declared body/spawn-order provider.
This is not a new claim about the game's unresolved crosshair metric.
"""
import array,copy,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
parent=module('enemy_lock_parent','research/verify-physical-locks.py')
from portable_heavyarms_lock_cases import source_definitions
from world_physical_locks_native import capture,baseline
from portable_specs import LIMITS as L,FIELDS as F
SOURCE='gpu/world_lock_enemy_carrier_entry.slang'
suite=SimpleNamespace(SOURCE=SOURCE,INPUT=parent.INPUT,OUTPUT=parent.OUTPUT);cross=parent.cross

def fixtures():
    rows=[]
    for index in (0,1,2,5):
        c=copy.deepcopy(parent.fixtures()[index]);c['name']='enemy-carrier/'+c['name'].split('/')[-1]
        marker=next(i for i,e in enumerate(c['effects']) if e.get('name')=='록 온')
        c['effects'][marker]=copy.deepcopy(source_definitions()[0])
        for i in (1,2,6):c['effects'].append(copy.deepcopy(source_definitions()[i]));c['owners'].append(0)
        c['observe_named_state']=True;c['source_effect_identity']=True
        c['state_queries']=[[0,5,1,1,'록 온'],[0,0,0,1,'록 온']]
        rows.append(c)
    return rows

def compile_case(case):
    c=copy.deepcopy(case);source=source_definitions()[0]
    matches=[i for i,e in enumerate(c['effects']) if e.get('stat')=='lock_on']
    if len(matches)!=1 or c['effects'][matches[0]]!=source:raise ValueError('Unchanged original Lock On definition required')
    c['effects'][matches[0]]=dict(source,stat='')
    words,meta,bindings=parent.compile_case(c)
    meta['original_lock_marker']=copy.deepcopy(source)
    return words,meta,bindings

def native_reference(domain,*,candidate_observer=None):
    c=domain[0];before=copy.deepcopy(c)
    def run(observer=None):
        with capture(c,enemy_carrier=True,candidate_observer=observer) as observed:battle,trace=baseline(c)
        return dict(battle=battle,skill_trace=trace,**observed)
    result=run(candidate_observer);plain=run()
    if result!=plain or c!=before:raise AssertionError('Lock carrier observation changed input/model')
    return result

def compare(block,domain):
    candidates=[];observed=native_reference(domain,candidate_observer=lambda values:candidates.append(tuple(values)))
    return parent.compare_observed(block,domain,observed,candidates)

def prepare():
    rows=[]
    for c in fixtures():
        words,meta,bindings=compile_case(c);rows.append((c['name'],words,(c,meta,bindings)))
    seed=rows[0][1];row=rows[0][2][1]['physical_lock_pulse_row'];at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
    for name,pos,value in [('not-enemy',L['HEALTH_DEFINITION_BASE']+row*L['HEALTH_DEFINITION_WORDS']+3,0),('wrong-route',L['DAMAGE_DEFINITION_BASE']+row*L['DAMAGE_DEFINITION_WORDS'],2),('wrong-count',L['DAMAGE_DEFINITION_BASE']+row*L['DAMAGE_DEFINITION_WORDS']+1,2)]:
        w=list(seed);w[pos]=value;rows.append(('reject/enemy-carrier/'+name,w,None))
    data=array.array('I',[len(rows)])
    for _,w,_ in rows:data.extend(w)
    if sys.byteorder!='little':data.byteswap()
    return rows,data.tobytes()
