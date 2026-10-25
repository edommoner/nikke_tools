"""Shared sampled storage/share/discharge, with existing native pool observers."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
parent=module('coordinate_healing_parent','research/verify-coordinate-auto-reload-short.py')
charge=module('coordinate_healing_charge','research/verify-world-heal-charge-short.py')
from portable_coordinate_healing_cases import fixtures
from portable_heal_charge_observation import compare_final
from world_frame_native import roster_names
from world_heal_charge_native import capture
SOURCE='gpu/world_coordinate_healing_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross;compile_case=parent.compile_case
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
def prepare():
    rows,_=parent.prepare()
    cases=fixtures()
    for c in cases:
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    from portable_specs import LIMITS as L,FIELDS as F
    seed=rows[-len(cases)][1]
    discharge=next(i for i in range(seed[1]) if seed[L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']+F['KIND']]==32)
    pool=next(i for i in range(seed[1]) if seed[L['PROTECTION_DEFINITION_BASE']+i]&255==10)
    for label,at,value in [('missing-discharge-name',L['DEFINITION_BASE']+discharge*L['DEFINITION_WORDS']+F['TARGET_NAME'],0xffffffff),('missing-pool-policy',L['PROTECTION_DEFINITION_BASE']+pool,0)]:
        w=list(seed);w[at]=value;rows.append(('reject/coordinate-healing/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def native_reference(domain):
    if not domain[0].get('coordinate_healing'):return parent.native_reference(domain)
    with capture(roster_names(domain[0]),record_final=True) as observed:n=parent.native_reference(domain)
    n['healing_charge']=observed;return n
def compare(block,domain):
    if not domain[0].get('coordinate_healing'):return parent.compare(block,domain)
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    return compare_observed(block,domain,n,indices)
def compare_observed(block,domain,n,indices):
    leaf=parent
    while Path(leaf.__file__).name!='verify-coordinate-manual-short.py':leaf=leaf.parent
    burst=leaf.parent.parent.parent
    burst.compare_observed(block,domain,n,indices,manual=bool(domain[0].get('manual_controls')))
    if domain[0].get('manual_controls'):leaf.compare_manual(block,n)
    charge.compare_trace(block,n['healing_charge']['events'])
    compare_final(block,domain[1],domain[0],n['healing_charge'])
    return n
def native_comparison_adapter(domain):
    if domain[0].get('coordinate_healing'):return SimpleNamespace(compare=compare,native_reference=native_reference)
    return parent.native_comparison_adapter(domain)
def validate_rejection(block,name):
    if name.startswith('reject/coordinate-healing/'):assert block[0]==64
    else:parent.validate_rejection(block,name)
