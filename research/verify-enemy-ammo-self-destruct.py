"""One shared ADD/retirement/ammunition/incoming executor and exact decoder."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
spec=importlib.util.spec_from_file_location('final_queue_parent',ROOT/'research/verify-add-self-destruct.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
from portable_enemy_ammo_self_destruct_cases import fixtures
from world_enemy_ammo_self_destruct_battle_native import prepare_case,observe
from portable_enemy_ammo_self_destruct_wire import LAYOUT
from portable_enemy_ammo_wire import LAYOUT as E
from portable_add_attack_battle_wire import LAYOUT as A
from portable_enemy_ammo_readback import compare_ammo
from portable_enemy_ammo_self_destruct_contracts import verify
from portable_skill_history import require_capacity
SOURCE='gpu/world_enemy_ammo_self_destruct_entry.slang';STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=E['INPUT_WORDS'],OUTPUT=E['OUTPUT_WORDS']);cross=parent.cross;NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT


def prepare():
    rows=[(c['name'],*prepare_case(c)) for c in fixtures()];seed=rows[0][1]
    for name,at,value in [('magic',E['BASE'],0),('duplicate-order',E['BASE']+E['ORDER_BASE']+1,2),
        ('capacity',E['BASE']+E['ROW_BASE']+8+1,0),('rule-reserved',E['BASE']+E['ROW_BASE']+8+6,1),
        ('self-flag',A['BASE']+A['ROW_BASE']+4,2),('delay-nan',A['BASE']+A['ROW_BASE']+6,0x7ff80000),
        ('unbounded-self',A['BASE']+A['ROW_BASE']+1,0),('unused-self',A['BASE']+A['ROW_BASE']+24+4,1)]:
        words=list(seed);words[at]=value;rows.append(('reject/enemy-ammo-self-destruct/'+name,words,None))
    raw=array.array('I',[len(rows)])
    for _,words,_ in rows:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()


def native_reference(domain):
    n=observe(domain);identity=n['original_input_identity'];ammo=n['enemy_ammo']
    verify(dict(contract=domain[0]['enemy_ammo_contract']),dict(original_input_identity=dict(definitions=identity['definitions'],effects_owners_weapons_chars_config_seed_verified=identity['chars_config_seed_weapon_verified'],added_effects=0),enemy_ammo=ammo,battle=dict(squad_hits=ammo['public_squad_hits'])))
    assert len(n['self_destruct'])==len(ammo['retirements'])
    for r,a in zip(n['self_destruct'],ammo['retirements'],strict=True):
        assert (r['time'],r['generation'],r['fired'])==(a['time'],a['actor'][2],a['fired'])
        assert domain[2][r['slot']].label==a['label']
    require_capacity(n);return n


def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    clean=parent.compare_retirements(block,n,layout=LAYOUT)
    clean=compare_ammo(clean,domain,n,allow_retired_queue=True)
    return parent.base.compare_observed(clean,domain,n,indices)


def validate_rejection(block,name):assert name.startswith('reject/enemy-ammo-self-destruct/') and block[0]==64
