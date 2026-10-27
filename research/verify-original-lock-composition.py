"""Original full Heavyarms roster through shared locks, packets and typed effects."""
import array,copy,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from portable_heavyarms_original_composition import prepare_case,compile_case,native_reference as native
from portable_heavyarms_original_composition import composition
from portable_original_lock_layout import check,banks_and_project
from portable_specs import LIMITS as L,FIELDS as F
SOURCE='gpu/world_original_lock_composition_entry.slang'
suite=SimpleNamespace(SOURCE=SOURCE,INPUT=109536,OUTPUT=1310720);cross=composition.cross

def fixtures():return [prepare_case(duration,adds)[0] for duration in (3,30) for adds in (0,3)]

def native_reference(domain,*,candidate_observer=None):
    n=composition.native_reference(domain,enemy_carrier=True,candidate_observer=candidate_observer)
    # Keep static original-input proof alongside every calculated battle field.
    n['original_input_identity']=n['battle'].pop('original_input_identity')
    return n

def compare(block,domain):
    candidates=[];n=native_reference(domain,candidate_observer=lambda values:candidates.append(tuple(values)))
    c,m,b=domain
    identity=n['original_input_identity']
    if identity!=dict(definitions=len(c['effects']),chars_config_seed_weapon_verified=True,authored_metadata_overrides=False,authored_delays_overrides=False):raise AssertionError('Original native input identity changed')
    if set(m['binding_source_indices'])!=set(range(len(c['effects']))):raise AssertionError('Original source definition discarded')
    projected,pulses,packets,quotas=banks_and_project(block,n)
    composition.live.parent.parent.parent.compare_observed(projected,domain,n,candidates,manual=False,packet_bindings=True,pulse_rows=pulses,packet_rows=packets,quota_rows=quotas)
    if composition.typed.decode(block,domain)!=n['typed']:raise AssertionError('Complete original typed state/receipts differ')
    return n

def prepare():
    check(ROOT);entries=[]
    for c in fixtures():
        words,meta,bindings=compile_case(c);entries.append((c['name'],words,(c,meta,bindings)))
    seed=entries[0][1];meta=entries[0][2][1];row=meta['physical_lock_pulse_row']
    for name,at,value in [('typed-magic',109523,0),('trace-required',5,0),('not-enemy',L['HEALTH_DEFINITION_BASE']+row*L['HEALTH_DEFINITION_WORDS']+3,0),('wrong-charge-condition',L['CONDITION_BASE']+row*L['CONDITION_WORDS'],0)]:
        words=list(seed);words[at]=value;entries.append(('reject/original-lock/'+name,words,None))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()
