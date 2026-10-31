"""Original enemy ammo operator into the existing product/ADD executor."""
import copy,struct
from types import SimpleNamespace
from portable_enemy_ammo_wire import LAYOUT as E,MAGIC,enemy_percentage,compiler_policy,pack,check_schema
from portable_add_attack_battle_wire import LAYOUT as A
from portable_runtime import UnsupportedPortable

def required(prepared):
    return 'enemy_ammo' in prepared.get('reference_models',{}) or any(enemy_percentage(r['effect']) for r in prepared['effects'])

def compile_product(prepared,producer):
    from calculator.boss_pattern import validate
    from portable_actor_specs import compile_registry
    from enemy_ammo_model import validate_enemy_effects
    from portable_product_world_contract import has_incoming_attacks
    from portable_add_attack_battle_wire import pack as pack_add
    from portable_product_add_attack import lower as lower_add
    declarations=copy.deepcopy(prepared.get('reference_models',{}));spec=declarations.get('enemy_ammo')
    if set(declarations)-{'enemy_ammo'}:raise UnsupportedPortable('Enemy magazine composition requires its combined product wire')
    if spec is None and has_incoming_attacks(prepared):raise UnsupportedPortable('Enemy attacks require explicit reference_models.enemy_ammo magazines')
    names=[c['name'] for c in prepared['chars']]
    validate_enemy_effects([(r['effect'],r['owner']) for r in prepared['effects']],names)
    raw=prepared['enemy'].get('patterns') or [dict(id='portable-empty-world',kind='idle')]
    patterns=validate(copy.deepcopy(raw));lowered,_=lower_add(prepared)
    registry_raw=lowered['enemy'].get('patterns') or raw
    _,bindings=compile_registry(validate(copy.deepcopy(registry_raw)),pools=True)
    if any(p.summon and p.summon.self_destruct for p in patterns):raise UnsupportedPortable('Product enemy magazines with retired self-destruct queues require the combined consumer')
    check_schema();inner=dict(prepared,_product_ammo_compiled=True);inner.pop('reference_models',None)
    with compiler_policy():source,iw,ow,words,meta=producer(inner)
    if source in ('gpu/product_battle_entry.slang','gpu/product_fixed_battle_entry.slang') and iw==104400:
        words=list(words)+[0]*(A['BASE']-len(words))+pack_add(patterns,bindings,raw)
    elif source not in ('gpu/product_add_battle_entry.slang','gpu/product_add_fixed_battle_entry.slang') or iw!=A['INPUT_WORDS']:
        raise UnsupportedPortable('Enemy magazines require the plain shared BODY/ADD product prefix')
    if len(words)!=E['BASE']:raise ValueError('Enemy magazine product prefix changed')
    if spec is not None:bank=pack(spec,patterns,bindings)
    else:
        # Stationary world with no configured enemy magazines. Keep every
        # percentage operation and its completion, with an empty recipient set.
        # Real attacking actors always require literal magazines above/on GPU.
        bank=[0]*E['WORDS'];bank[:4]=[MAGIC,1,0,len(bindings)]
    meta['product_enemy_ammo']=dict(declarations=declarations,
        case=dict(names=names,effects=[copy.deepcopy(r['effect']) for r in prepared['effects']],patterns=copy.deepcopy(raw)),
        bindings=[dict(kind=int(b.kind),identity=b.identity,label=b.label,run=b.run) for b in bindings],
        cpu_state_or_schedule_supplied=False)
    fixed='fixed_' in source
    return ('gpu/product_ammo_fixed_battle_entry.slang' if fixed else 'gpu/product_ammo_battle_entry.slang',E['INPUT_WORDS'],E['OUTPUT_WORDS'],words+bank,meta)

def read_result(block,meta):
    from portable_enemy_ammo_readback import read_ammo
    info=meta['product_enemy_ammo'];bindings=[SimpleNamespace(**r) for r in info['bindings']]
    if len(block)!=E['OUTPUT_WORDS']:raise UnsupportedPortable('Complete enemy magazine product readback required')
    try:data=read_ammo(block,(info['case'],meta,bindings,None))
    except (AssertionError,IndexError,KeyError,struct.error) as error:raise UnsupportedPortable('Invalid enemy magazine product history') from error
    # Resource continuation is already fully decoded by the common decoder;
    # unused words must still be empty, rather than discarded from the audit.
    from portable_specs import LIMITS as L
    count=block[L['RESOURCE_HEADER_BASE']]
    end=E['OUTPUT_WORDS']
    start=E['OUTPUT_BASE']+E['RESOURCE_BASE']+max(0,count-128)*8
    if any(block[start:end]):raise UnsupportedPortable('Unused enemy magazine resource history is nonzero')
    if not info['declarations']:
        if any(data[k] for k in ('generations','final','attempts','reloads')) or any(r['targets'] for r in data['charges']):
            raise UnsupportedPortable('Undeclared magazine state appeared in a stationary product world')
        return None
    return dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(info['declarations']),enemy_ammo=data)
