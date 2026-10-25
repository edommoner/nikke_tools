"""Shared sampled skill criticals, frozen factors and actual queue landings."""
import array,copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('sampled_skill_parent',ROOT/'research/verify-coordinate-sampled-parent-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_sampled_skill_cases import fixtures
from world_coordinate_sampled_skill_native import observe
from world_coordinate_aim_native import capture
SOURCE='gpu/world_coordinate_sampling_skill_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross;compile_case=parent.compile_case
MIGRATED='coordinate-sampled-skill/former-random-skill-rejection'
def migrated_case():
    c=copy.deepcopy(parent.parent.fixtures()[5]);c.update(name=MIGRATED,sampled_skill=True)
    c['effects']=[dict(name='unsupported-random-skill',source='declared',type='damage',stat='bonus_damage',fixed_value=100,target='boss',trigger=dict(timing=['battle_start'],condition=[]))];c['owners']=[0];return c
def prepare():
    rows,_=parent.prepare();index=next(i for i,r in enumerate(rows) if r[0]=='reject/sampled-battle/random-skill');c=migrated_case();w,m,b,d=compile_case(c);assert w==rows[index][1];rows[index]=(MIGRATED,w,(c,m,b,d))
    for c in fixtures():
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    # Delayed burst numeric/queue semantics remain an explicit next dependency.
    c=copy.deepcopy(fixtures()[0]);c['effects'][-1]['trigger']['timing']=['burst_cast'];c['owners'][-1]=2
    w,_,_,_=compile_case(c)
    from portable_specs import LIMITS as L
    # Existing fixture weapon metadata may be B1. Set the definition's pending
    # discriminator directly to test the dedicated profile's explicit guard.
    at=L['DAMAGE_DEFINITION_BASE']+(len(c['effects'])-1)*L['DAMAGE_DEFINITION_WORDS']+6;w[at]=1
    rows.append(('reject/sampled-skill/pending-burst',w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def native_reference(domain):
    if not domain[0].get('sampled_skill'):return parent.native_reference(domain)
    with capture(domain[0]) as aim:n,t=observe(domain[0])
    n['coordinate_aim']=aim;return n
def compare(block,domain):
    if not domain[0].get('sampled_skill'):return parent.compare(block,domain)
    from world_coordinate_sampled_skill_native import creation_indices,trace_view
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    expected_trace=trace_view(n['skill_trace'],indices)
    has_parent=any(e.get('stat')=='dealt_fixed_damage' for e in domain[0]['effects'])
    return parent.compare_observed(block,domain,n,check_parent=has_parent,trace_view=expected_trace)
def validate_rejection(block,name):
    if name.startswith('reject/sampled-skill/'):assert block[0]==64
    else:parent.validate_rejection(block,name)
