"""Data-only decoy cases use the fixed shared entry and existing protection audit."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('original_decoy_shield',ROOT/'research/verify-coordinate-original-shield-short.py');shield=importlib.util.module_from_spec(s);s.loader.exec_module(shield);parent=shield.parent
from portable_coordinate_original_cases import prepare_case
from portable_coordinate_original_decoy_cases import fixtures
from world_original_shield_native import capture
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_shared_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);c['decoy_witness']=row['decoy_witness'];c['python_observers_only']=True;w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    with capture(domain[0],kind='decoy') as observed:n=parent.native_reference(domain)
    n['original_decoy']=observed;scenario=domain[0]['decoy_witness'];deliveries=observed['deliveries'];hits=n['battle']['hits']
    assert observed['requests'] and all(domain[0]['effects'][r['row']]['stat']=='decoy_heal_pct' for r in observed['requests'])
    if scenario=='full':assert deliveries and all(d['healed']==0 and d['before']==d['after'] for d in deliveries)
    elif scenario=='chipped':
        assert len(hits)==2 and all(h['decoy']>0 for h in hits)
        assert any(d['healed']>0 and d['time']<hits[-1]['time'] for d in deliveries),'Actual restoration must precede a real later hit'
    else:
        assert len(hits)==1 and hits[0]['decoy']>0 and not observed['final'],'A consumed decoy must retire its carrier'
        after=[d for d in deliveries if d['time']>hits[0]['time']]
        assert after and all(d['healed']==0 and d['before']==d['after']==[] for d in after),'Latched finite ticks may attempt delivery, but cannot heal or recreate a missing decoy'
    for d in deliveries:
        assert d['amount']>=d['healed']>=0 and d['target']==0
        assert [(r['row'],r['capacity']) for r in d['before']]==[(r['row'],r['capacity']) for r in d['after']],'Healing cannot create a decoy or change capacity'
    return n

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices)
    return shield.compare_protections(block,domain,n,kind=2,stat='decoy_heal_pct',field='original_decoy')

def validate_rejection(block,name):raise AssertionError('Original decoy definitions cannot be discarded')
