"""Full original modifier carriers on an explicitly declared typed attack route."""
import array,copy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from original_modifier_probe_cases import fixtures
from portable_original_modifier_probe_input import compile_probe,SOURCE,INPUT_WORDS,OUTPUT_WORDS
from world_destructible_weapon_roster_native import observe
from portable_destructible_roster_skill_comparison import compare as shared_compare,prior
roster=prior.roster;cross=prior.cross;suite=prior.suite;STRICT_WIRE_DIMENSIONS=True

def prepare():
    rows=[]
    for case in fixtures():
        p=roster.engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True));case['probe_source']=len(p['effects']);case['original_effects']=copy.deepcopy(p['effects'])
        for e in case['declared_effects']:p['effects'].append(dict(effect=copy.deepcopy(e),owner=case.get('probe_owner',case['body']['squad'][0])))
        w,m=compile_probe(p,case['typed_bindings'],case['probe_source'],max_attacks=case['max_attacks'],probe_kind=case.get('probe_kind',2));rows.append((case['name'],w,(case,m,p,w)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def verify_witness(case,n):
    rows=n['typed']['attacks'];samples=n['modifier_samples'];assert rows and len(rows)==len(samples)==len(n['packet_samples'])
    assert all(r['completed'] and r['receipts'] and all(t['handle'][0]==case.get('probe_kind',2) and t['delivered'] for t in r['receipts']) for r in rows)
    assert all(r['source']==case['probe_source'] and r['coefficient']==100. for r in n['packet_samples'])
    assert all(r['modifier']>=0 for r in samples)
    if case.get('zero_projectile_modifier') or case.get('zero_probe_modifier'):assert all(r['modifier']==0 for r in samples)
    elif case['character']!='클레이' or case['body']['duration']>3:assert any(r['modifier']>0 for r in samples),'Original modifier must really contribute'
    else:assert all(r['modifier']==0 for r in samples)
    if case.get('projectile_negative'):assert any(r['projectile_modifier']>0 for r in samples)
    if case.get('shield_negative'):assert any(r['shield_modifier']>0 for r in samples)
    return True

def native_reference(domain):
    n,_=observe(domain[0]);verify_witness(domain[0],n);return n

def compare(block,domain):
    n=native_reference(domain);return shared_compare(block,domain,n,sample_key='modifier_samples')

def validate_rejection(block,name):raise AssertionError('Original modifiers must not be discarded')
