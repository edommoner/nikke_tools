"""Original Velvet enemy ammo effect in the one shared full battle executor."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
spec=importlib.util.spec_from_file_location('enemy_ammo_add_parent',ROOT/'research/verify-add-attack-battle.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_enemy_ammo_cases import fixtures
from world_enemy_ammo_full_native import prepare_case,observe
from portable_enemy_ammo_wire import LAYOUT as E
from portable_enemy_ammo_contracts import verify
from portable_enemy_ammo_readback import compare_ammo
from portable_skill_history import require_capacity
SOURCE='gpu/world_enemy_ammo_entry.slang';STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=E['INPUT_WORDS'],OUTPUT=E['OUTPUT_WORDS']);cross=base.cross;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT


def prepare():
    rows=[]
    for c in fixtures():
        words,domain=prepare_case(c);rows.append((c['name'],words,domain))
    seed=rows[0][1]
    for label,at,value in [('magic',0,0),('version',1,2),('count',2,0),('actors',3,128),('reserved',4,1),('order-zero',16,0),('duplicate-order',17,1),('capacity',145,0),('initial',146,17),('cancel',147,2),('reload-negative',149,0xbff00000),('reload-nan',149,0x7ff80000),('row-reserved',150,1),('undeclared-row',168,1)]:
        w=list(seed);w[E['BASE']+at]=value;rows.append(('reject/enemy-ammo/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()


def native_reference(domain):
    n=observe(domain);identity=n['original_input_identity'];data=n['enemy_ammo']
    verify(dict(contract=domain[0]['enemy_ammo_contract']),dict(original_input_identity=dict(definitions=identity['definitions'],effects_owners_weapons_chars_config_seed_verified=identity['chars_config_seed_weapon_verified'],added_effects=0),enemy_ammo=data,battle=dict(squad_hits=data['public_squad_hits'])))
    require_capacity(n);return n


def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    assert len(block)==suite.OUTPUT and block[0]==0
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    clean=compare_ammo(block,domain,n)
    return base.compare_observed(clean,domain,n,indices)


def validate_rejection(block,name):assert name.startswith('reject/enemy-ammo/') and block[0]==64
