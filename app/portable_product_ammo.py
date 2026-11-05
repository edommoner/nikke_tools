"""Original enemy ammo operator into the existing product/ADD executor."""
import copy,struct
from types import SimpleNamespace
from portable_enemy_ammo_wire import LAYOUT as E,MAGIC,enemy_percentage,compiler_policy,pack,check_schema
from portable_add_attack_battle_wire import LAYOUT as A
from portable_runtime import UnsupportedPortable

LONG_PLAIN_OUTPUT_WORDS=2064786

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
    if set(declarations)-{'enemy_ammo','enemy_healing'}:raise UnsupportedPortable('Enemy magazine composition requires its combined product wire')
    if spec is None and has_incoming_attacks(prepared):raise UnsupportedPortable('Enemy attacks require explicit reference_models.enemy_ammo magazines')
    names=[c['name'] for c in prepared['chars']]
    validate_enemy_effects([(r['effect'],r['owner']) for r in prepared['effects']],names)
    raw=prepared['enemy'].get('patterns') or [dict(id='portable-empty-world',kind='idle')]
    patterns=validate(copy.deepcopy(raw));lowered,_=lower_add(prepared)
    registry_raw=lowered['enemy'].get('patterns') or raw
    _,bindings=compile_registry(validate(copy.deepcopy(registry_raw)),pools=True)
    self_destruct=any(p.summon and p.summon.self_destruct for p in patterns)
    from portable_enemy_ammo_self_destruct_wire import check_schema as check_retirement
    check_retirement()
    from portable_product_healing import required as healing_required
    from portable_enemy_healing_wire import compiler_policy as healing_policy
    healing=healing_required(prepared)
    check_schema();inner=dict(prepared,_product_ammo_compiled=True,_product_healing_compiled=True);inner.pop('reference_models',None)
    with compiler_policy(),healing_policy():source,iw,ow,words,meta=producer(inner)
    weighted=source in ('gpu/product_weighted_battle_entry.slang','gpu/product_weighted_fixed_battle_entry.slang')
    if weighted:
        from portable_weighted_battle_wire import INPUT as WI,OUTPUT as WO,LAYOUT as W
        if (iw,ow)!=(WI,WO) or not meta['product_weighted_incoming']['unspecified_quantities'] or healing or self_destruct or prepared.get('_product_cover_compiled'):
            raise UnsupportedPortable('Ammo/weighted composition requires the checked unspecified weighted prefix')
        if any(words[104400:W['BASE']]):raise ValueError('Unowned weighted/ammo prefix is nonzero')
        weighted_bank=list(words[W['BASE']:]);words=list(words[:104400])
        source=source.replace('product_weighted_','product_',1);iw,ow=104400,786432
    grouped=source in ('gpu/product_group_battle_entry.slang','gpu/product_fixed_group_battle_entry.slang','gpu/product_add_group_battle_entry.slang','gpu/product_add_fixed_group_battle_entry.slang','gpu/product_group_target_battle_entry.slang','gpu/product_fixed_group_target_battle_entry.slang','gpu/product_add_group_target_battle_entry.slang','gpu/product_add_fixed_group_target_battle_entry.slang')
    plain_prefixes={'gpu/product_battle_entry.slang':(104400,786432),'gpu/product_fixed_battle_entry.slang':(104400,786432),
        'gpu/product_group_battle_entry.slang':(104408,1048576),'gpu/product_fixed_group_battle_entry.slang':(104408,1048576),
        'gpu/product_target_battle_entry.slang':(110112,1048576),'gpu/product_fixed_target_battle_entry.slang':(110112,1048576),
        'gpu/product_group_target_battle_entry.slang':(104672,1048576),'gpu/product_fixed_group_target_battle_entry.slang':(104672,1048576)}
    if source in plain_prefixes and (iw,ow)==plain_prefixes[source]:
        words=list(words)+[0]*(A['BASE']-len(words))+pack_add(patterns,bindings,raw)
    elif source not in ('gpu/product_add_battle_entry.slang','gpu/product_add_fixed_battle_entry.slang','gpu/product_add_group_battle_entry.slang','gpu/product_add_fixed_group_battle_entry.slang','gpu/product_add_group_target_battle_entry.slang','gpu/product_add_fixed_group_target_battle_entry.slang','gpu/product_add_target_battle_entry.slang','gpu/product_add_fixed_target_battle_entry.slang') or (iw,ow)!=(A['INPUT_WORDS'],A['OUTPUT_WORDS']):
        raise UnsupportedPortable('Enemy magazines require a checked plain, modifier or actual-shot group BODY/ADD product prefix')
    if len(words)!=E['BASE']:raise ValueError('Enemy magazine product prefix changed')
    if spec is not None:bank=pack(spec,patterns,bindings,allow_self_destruct=True)
    else:
        # Stationary world with no configured enemy magazines. Keep every
        # percentage operation and its completion, with an empty recipient set.
        # Real attacking actors always require literal magazines above/on GPU.
        bank=[0]*E['WORDS'];bank[:4]=[MAGIC,1,0,len(bindings)]
    if healing:
        from portable_enemy_healing_wire import AMMO_LAYOUT as H,AMMO_OUTPUT as HO,MAGIC as HM,VERSION as HV,pack as pack_healing,validate as validate_healing,check_ammo_schema
        from portable_specs import LIMITS as L
        from portable_world_schedule_specs import INPUT_WORDS as SCHEDULE_WORDS
        check_ammo_schema()
        if any(words[H['BASE']:H['BASE']+H['WORDS']]):raise ValueError('Healing/magazine input owner overlap')
        healing_spec=declarations.get('enemy_healing')
        if healing_spec:
            healing_bank=pack_healing(healing_spec,patterns,bindings)
            graph=L['WORLD_FRAME_INPUT_BASE']
            validate_healing(healing_bank,words[:115680],validate(copy.deepcopy(registry_raw)),bindings,words[graph:graph+SCHEDULE_WORDS])
        else:
            healing_bank=[0]*H['WORDS'];healing_bank[:5]=[HM,HV,0,len(patterns),len(bindings)]
        words[H['BASE']:H['BASE']+H['WORDS']]=healing_bank
        meta['product_enemy_healing']=dict(declarations={k:v for k,v in declarations.items() if k=='enemy_healing'},nodes=[p.id for p in patterns],
            bindings=[dict(kind=int(b.kind),identity=b.identity,label=b.label,run=b.run) for b in bindings],cpu_health_generations_or_schedule_supplied=False)
        meta['product_ammo_healing']=True
    meta['product_enemy_ammo']=dict(declarations={k:v for k,v in declarations.items() if k=='enemy_ammo'},self_destruct=self_destruct,healing=healing,
        case=dict(names=names,effects=[copy.deepcopy(r['effect']) for r in prepared['effects']],patterns=copy.deepcopy(raw)),
        bindings=[dict(kind=int(b.kind),identity=b.identity,label=b.label,run=b.run) for b in bindings],
        cpu_state_or_schedule_supplied=False)
    fixed='fixed_' in source
    targeted=source in ('gpu/product_target_battle_entry.slang','gpu/product_fixed_target_battle_entry.slang','gpu/product_add_target_battle_entry.slang','gpu/product_add_fixed_target_battle_entry.slang')
    stem=('fixed_' if fixed else '')+('group_' if grouped else 'target_' if targeted else '')
    # Versions 2/3 own a resource-only tail, including target/group prefixes.
    # Healing, retirement and cover retain their existing v1 output owners.
    long_plain=not weighted and prepared['policies']['config']['duration']>30. and not healing and not self_destruct and not prepared.get('_product_cover_compiled')
    if long_plain:bank[1]=2
    output_words=LONG_PLAIN_OUTPUT_WORDS if long_plain else E['OUTPUT_WORDS']
    if long_plain:
        from portable_product_resource_budget import output_words as budget,SUPPLY_OUTPUT_WORDS
        output_words,bound=budget(prepared,output_words)
        if output_words==SUPPLY_OUTPUT_WORDS:bank[1]=3
        meta['product_enemy_ammo']['notification_supply_bound']=bound
    meta['product_enemy_ammo']['output_words']=output_words
    if weighted:
        from portable_weighted_battle_wire import AMMO_INPUT,AMMO_BASE
        if len(words)+len(bank)!=AMMO_BASE or len(weighted_bank)!=16:raise ValueError('Ammo/weighted banks overlap')
        from portable_product_resource_budget import SUPPLY_OUTPUT_WORDS
        meta['product_ammo_weighted']=True
        meta['product_enemy_ammo']['output_words']=SUPPLY_OUTPUT_WORDS
        bank[1]=3
        return ('gpu/product_ammo_weighted_'+('fixed_' if fixed else '')+'battle_entry.slang',AMMO_INPUT,SUPPLY_OUTPUT_WORDS,words+bank+weighted_bank,meta)
    return ('gpu/product_ammo_'+stem+'battle_entry.slang',E['INPUT_WORDS'],output_words,words+bank,meta)

def read_result(block,meta):
    from portable_enemy_ammo_readback import read_ammo,read_retirements
    info=meta['product_enemy_ammo'];bindings=[SimpleNamespace(**r) for r in info['bindings']]
    if len(block)!=info.get('output_words',E['OUTPUT_WORDS']):raise UnsupportedPortable('Complete enemy magazine product readback required')
    try:
        data=read_ammo(block,(info['case'],meta,bindings,None),allow_retired_queue=info['self_destruct'])
        if info['self_destruct']:
            retired=read_retirements(block,info['case'],bindings,data['attempts'])
            if retired:data['retirements']=retired
    except (AssertionError,IndexError,KeyError,struct.error) as error:raise UnsupportedPortable('Invalid enemy magazine product history') from error
    # Resource continuation is already fully decoded by the common decoder;
    # unused words must still be empty, rather than discarded from the audit.
    from portable_specs import LIMITS as L
    count=block[L['RESOURCE_HEADER_BASE']]
    end=info.get('output_words',E['OUTPUT_WORDS'])
    if info['self_destruct'] or info.get('healing'):
        from portable_enemy_ammo_self_destruct_wire import LAYOUT as S
        if count>E['RESOURCE_CAPACITY']:raise UnsupportedPortable('Enemy magazine final-queue resource capacity exceeded')
        end=S['OUTPUT_BASE']
        after=end+S['HEADER']+S['ROWS']*S['ROW_WORDS']
        if not info['self_destruct'] and any(block[end:after]):raise UnsupportedPortable('Undeclared retirement receipt in a healing/magazine world')
        if info.get('healing'):
            from portable_enemy_healing_wire import AMMO_OUTPUT as H
            after=H['OUTPUT_BASE']+H['RECEIPT_BASE']+H['RECEIPTS']*H['RECEIPT_WORDS']
        if any(block[after:]):raise UnsupportedPortable('Unowned enemy magazine combined output is nonzero')
    start=E['OUTPUT_BASE']+E['RESOURCE_BASE']+max(0,count-128)*8
    if meta.get('product_ammo_weighted'):
        from portable_weighted_battle_wire import LAYOUT as W
        if start>=W['OUTPUT_BASE']:start+=W['OUTPUT']-W['OUTPUT_BASE']
        nonzero=any(block[start:min(end,W['OUTPUT_BASE'])]) or any(block[max(start,W['OUTPUT']):end])
    else:nonzero=any(block[start:end])
    if nonzero:raise UnsupportedPortable('Unused enemy magazine resource history is nonzero')
    if not info['declarations']:
        if any(data[k] for k in ('generations','final','attempts','reloads')) or any(r['targets'] for r in data['charges']):
            raise UnsupportedPortable('Undeclared magazine state appeared in a stationary product world')
        return None
    return dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(info['declarations']),enemy_ammo=data)
