"""Real queued receipts retain shot snapshots; damage routing is unchanged."""
import array,copy,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
spec=importlib.util.spec_from_file_location('lock_packet_parent',ROOT/'research/verify-physical-lock-cover.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
from portable_lock_packet_layout import SOURCE,INPUT,OUTPUT,check
from portable_specs import LIMITS as L,FIELDS as F
from world_lock_packet_native import observe
suite=SimpleNamespace(SOURCE=SOURCE,INPUT=INPUT,OUTPUT=OUTPUT);cross=parent.cross

def fixtures():
    rows=[]
    for label,base in [('charge',parent.parent.fixtures()[0]),('short-grid',parent.parent.fixtures()[2]),('queued-death-rebirth',parent.parent.fixtures()[5]),('cover',parent.fixtures()[0])]:
        c=copy.deepcopy(base);c.update(name='lock-packet/'+label,observe_dynamic_skill_hits=True)
        if label=='queued-death-rebirth':c['effects'][-1]['trigger']['timing']=['full_charge_fire']
        for i in (4,8,9):c['effects'].append(copy.deepcopy(parent.parent.source_definitions()[i]));c['owners'].append(0)
        c['packet_skill']=parent.parent.source_definitions()[8]['name'];rows.append(c)
    return rows

def compile_case(case):
    check(ROOT)
    return parent.compile_case(case) if case.get('physical_cover_composition') else parent.parent.compile_case(case)

def native_reference(domain):return observe(domain[0])

def compare(block,domain):
    candidates=[];n=observe(domain[0],candidate_observer=lambda values:candidates.append(tuple(values)))
    return parent.parent.compare_observed(block,domain,n,candidates,manual=bool(domain[0].get('physical_cover_composition')),packet_bindings=True)

def prepare():
    entries=[]
    for c in fixtures():
        words,meta,bindings=compile_case(c);entries.append((c['name'],words,(c,meta,bindings)))
    seed=entries[0][1];case,meta,_=entries[0][2]
    row=next(i for i,name in enumerate(meta['effects']) if name==case['packet_skill'])
    for label,at,value in [('owner',L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['OWNER'],1),('timing',L['EVENT_BASE']+row*L['EVENT_WORDS'],7),('marker',L['MODE_BASE']+row*L['MODE_WORDS']+25,meta['states']['오토 파이어 레디']+1),('landing',L['LANDING_META_BASE'],0)]:
        words=list(seed);words[at]=value;entries.append(('reject/lock-packet/'+label,words,None))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()
