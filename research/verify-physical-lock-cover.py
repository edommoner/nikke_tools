"""Real manual producer + generation locks; shared CUDA/Metal comparison."""
import array,copy,importlib.util,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
spec=importlib.util.spec_from_file_location('physical_cover_parent',ROOT/'research/verify-physical-locks.py')
parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
from portable_manual_control_specs import normalize,pack
from portable_physical_lock_cover_layout import SOURCE,INPUT,OUTPUT,check
from portable_physical_lock_cover_cases import fixtures as native_cases
from world_physical_lock_cover_native import observe
from portable_specs import LIMITS as L
suite=type('Suite',(),dict(SOURCE=SOURCE,INPUT=INPUT,OUTPUT=OUTPUT))
cross=parent.cross

def fixtures():
    rows=native_cases()
    for case in rows:
        case['physical_cover_composition']=True
        # Bind the existing named event tag to a real, visible native effect.
        case['effects'].append(dict(name='cover-witness',source='스킬1',type='buff',stat='atk_pct',fixed_value=1,target='self',duration=.1,trigger=dict(timing=['event:cover'],condition=[])))
        case['owners'].append(0)
    return rows

def compile_case(case):
    check(ROOT)
    adapter=parent.parent.reload.charge
    with patch.object(adapter,'normalize_static_controls',normalize),patch.object(adapter,'compile_policy',pack):
        return parent.compile_case(case)

def native_reference(domain):
    return observe(domain[0])[0] if domain[0].get('physical_cover_composition') else parent.native_reference(domain)

def compare(block,domain):
    if not domain[0].get('physical_cover_composition'):return parent.compare(block,domain)
    candidates=[];native,_=observe(domain[0],candidate_observer=lambda values:candidates.append(tuple(values)))
    from portable_physical_lock_cover_contracts import verify
    verify(domain[0],native)
    return parent.compare_observed(block,domain,native,candidates,manual=True)

def prepare():
    entries,_=parent.prepare()
    for case in fixtures():
        words,meta,bindings=compile_case(case);entries.append((case['name'],words,(case,meta,bindings)))
    seed=entries[-1][1];base=L['WORLD_CONTROL_INPUT_BASE']
    from portable_charge_control_specs import SEQUENCE_BASE
    for name,at,value in [('version',base+1,4),('magic',base+7,0),('reserved',base+8,1),('tag',base+6,256),('missing-tag',base+6,0xffffffff),('unassociated',base+6,255),('action',base+SEQUENCE_BASE+4,2),('capacity',base+17,9)]:
        words=list(seed);words[at]=value;entries.append(('reject/physical-cover/'+name,words,None))
    data=array.array('I',[len(entries)])
    for _,words,_ in entries:data.extend(words)
    if sys.byteorder!='little':data.byteswap()
    return entries,data.tobytes()
