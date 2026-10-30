"""Static complete-roster input for the declared weapon-only shield policy.

Keep original effect identities; lower the two modifier axes to the shared
carrier representation after ordinary world compilation. No battle is run.
"""
import copy,re,struct
from portable_specs import LIMITS as L,FIELDS as F
from destructible_damage_policy import modifier_axis
from portable_target_modifier_input import lower_effect,pack_axes
from destructible_world_runtime import compile_bindings
from portable_projectile_roster_input import compile_projectile_battle

SOURCE='gpu/destructible_weapon_shield_entry.slang'
INPUT_WORDS=110112
OUTPUT_WORDS=1048576

GROUP_SOURCE='gpu/product_group_target_battle_entry.slang'
GROUP_INPUT_WORDS=104672

def check_group_wire(root):
    from portable_battle_attack_group_input import INPUT_WORDS as base
    source=(root/GROUP_SOURCE).read_text()
    stride=re.search(r'uint input=1\+id\.x\*(\d+),output=id\.x\*(\d+);',source)
    descriptor=re.search(r'uint descriptor=s.inputBase\+(\d+);',source)
    if not stride or tuple(map(int,stride.groups()))!=(GROUP_INPUT_WORDS,OUTPUT_WORDS) or not descriptor or int(descriptor[1])!=base or GROUP_INPUT_WORDS!=base+8+L['DEFINITIONS']:
        raise ValueError('Product group target wire disagrees with the shared shader')

def product_body_world(prepared):
    """Prove the original world has only BODY/PART, without discarding its script.

    Incoming attacks and scalar/core changes retain the existing world clock.
    Shields have separate intercept semantics even when absent from actor pools.
    """
    enemy=prepared['enemy']
    if enemy.get('coord') is not None or enemy.get('has_parts') or enemy.get('part_break_interval',0):
        raise ValueError('Product target modifiers require a plain body with no typed targets')
    from calculator.boss_pattern import validate
    from portable_actor_specs import compile_registry
    raw=enemy.get('patterns') or [dict(id='portable-empty-world',kind='idle')]
    patterns=validate(copy.deepcopy(raw))
    if any(p.kind not in ('idle','attack','buff','core','parts') for p in patterns):
        raise ValueError('Product target modifiers require a plain body with no typed targets')
    _,bindings=compile_registry(patterns,pools=True)
    if not bindings or int(bindings[0].kind)!=0 or any(int(b.kind)!=1 for b in bindings[1:]):
        raise ValueError('Product target modifiers require a plain body with no typed targets')
    return raw


def compile_body_modifier_group_roster(prepared):
    """Compose native groups and lossless target carriers in a BODY/PART world."""
    product_body_world(prepared)
    original=prepared['effects'];lowered=copy.deepcopy(prepared)
    for dest,row in zip(lowered['effects'],original,strict=True):
        if modifier_axis(row['effect']) and any(t.startswith('multi_hit:') for t in row['effect'].get('trigger',{}).get('timing',[])):
            raise ValueError('A target modifier that is itself a multi_hit listener is not connected')
        dest['effect']=lower_effect(row['effect'])
    from portable_battle_attack_group_input import compile_battle
    words,meta=compile_battle(lowered,routing='native')
    axes=pack_axes(words,meta,[r['effect'] for r in original])
    count=sum(axis!=0 for axis in axes)
    if not count:raise ValueError('At least one original target modifier required')
    words.extend([0x50474131,1,count,0,0,0,0,0,*axes])
    if len(words)!=GROUP_INPUT_WORDS:raise ValueError('Complete product group target axis wire required')
    meta['real_prepared_input']['target_modifier_carriers']=dict(axis_rows=axes,typed_targets=0,
        original_effects=copy.deepcopy(original),typed_target_game_model_verified=False,group_composition=True)
    return words,meta

def compile_body_modifier_roster(prepared):
    """Retain target-specific carriers in a proven BODY/PART product world.

    The same typed-axis table is consumed by the existing typed executor. This
    path supplies no typed targets: it does not infer projectile/shield models
    or substitute their bonuses for ordinary outgoing damage.
    """
    patterns=product_body_world(prepared)
    if any(t.startswith('multi_hit:') for row in prepared['effects'] for t in row['effect'].get('trigger',{}).get('timing',[])):
        raise ValueError('Product target modifier/group wire composition is not connected')
    original=prepared['effects'];lowered=copy.deepcopy(prepared)
    for dest,row in zip(lowered['effects'],original,strict=True):
        dest['effect']=lower_effect(row['effect'])
    words,meta=compile_projectile_battle(lowered)
    from portable_original_modifier_probe_input import pack_target_input
    extra,axes=pack_target_input(words,meta,original,patterns,[],None,2,128,weapon_only=True,empty_body=True)
    words.extend(extra)
    if len(words)!=INPUT_WORDS:raise ValueError('Complete product target modifier wire required')
    meta['real_prepared_input']['target_modifier_carriers']=dict(axis_rows=axes,typed_targets=0,
        original_effects=copy.deepcopy(original),typed_target_game_model_verified=False)
    return words,meta

def compile_weapon_shield_roster(prepared,bindings,*,hit_shields=True,max_attacks=128,skill_shields=False,body_lifesteal=False,body_accumulation=False):
    if type(skill_shields) is not bool:raise ValueError('Explicit skill shield policy boolean required')
    if type(body_lifesteal) is not bool or body_lifesteal and not skill_shields:raise ValueError('Body lifesteal requires explicit skill shield policy')
    if type(body_accumulation) is not bool or body_accumulation and not body_lifesteal:raise ValueError('Body accumulation requires body lifesteal policy')
    if type(hit_shields) is not bool or type(max_attacks) is not int or not 1<=max_attacks<=128:raise ValueError('Explicit bounded weapon shield policy required')
    if prepared['enemy'].get('coord') is not None or prepared['enemy'].get('has_parts') or prepared['enemy'].get('part_break_interval',0):raise ValueError('Plain body geometry required for roster shield policy')
    if any(b.get('kind') not in (3,4) for b in bindings):raise ValueError('Weapon roster requires HP/hit shield bindings')
    original=prepared['effects'];lowered=copy.deepcopy(prepared)
    chars={c['name']:c for c in prepared['chars']}
    if skill_shields and any(p.get('kind') in ('parts','interrupt','summon') for p in prepared['enemy'].get('patterns',[])):raise ValueError('Skill shield requires a plain single boss')
    from damage_accum_runtime import STATS
    for item,dest in zip(original,lowered['effects'],strict=True):
        effect=item['effect']
        if effect.get('stat')=='pierce_enabled':raise ValueError('Weapon shield piercing policy is not declared')
        if (effect.get('stat')=='lifesteal_pct' and not body_lifesteal) or effect.get('stat') in STATS and not body_accumulation:raise ValueError('Weapon shield post-landing consumer is not declared')
        if effect.get('type')=='damage':
            if skill_shields:
                from destructible_skill_shield_policy import skill
                if body_accumulation and effect.get('stat')=='accum_split_damage':
                    from destructible_skill_shield_policy import accumulation_skill
                    accumulation_skill(effect)
                else:skill(effect,chars[item['owner']],allow_split=body_accumulation)
            elif effect.get('target') in ('boss','all_projectiles'):raise ValueError('Roster policy currently routes weapons only')
        if modifier_axis(effect):dest['effect']=lower_effect(effect)
    words,meta=compile_projectile_battle(lowered)
    patterns=prepared['enemy'].get('patterns') or [dict(id='portable-empty-world',kind='idle')]
    _,_,rows=compile_bindings([dict(id=p['id']) for p in patterns],bindings)
    extra=[0]*5712;extra[2320]=len(rows)
    for slot,row in enumerate(rows):
        at=2328+slot*12;owner=[0xffffffff,0,0] if row.owner is None else [int(row.owner.kind),row.owner.identity,row.owner.generation]
        extra[at:at+8]=[row.node,int(row.handle.kind),row.handle.identity,*struct.unpack('<II',struct.pack('<d',row.capacity)),*owner]
    extra[5120:5124]=[0xffffffff,max_attacks,1,0x44425431]
    extra[5136]=0x444d4231
    extra[5680:5686]=[0x48534936 if body_accumulation else 0x48534935 if body_lifesteal else 0x48534934 if skill_shields else 0x48534933,0,0,1,int(hit_shields),1]
    if body_lifesteal:extra[5686]=1
    if body_accumulation:extra[5687]=1
    axes=pack_axes(words,meta,[r['effect'] for r in original])
    for row,index in enumerate(meta['binding_source_indices']):
        axis=axes[row]
        if skill_shields and original[index]['effect'].get('type')=='damage' and original[index]['effect'].get('stat')!='accum_split_damage':extra[5424+row]=4 if hit_shields else 3
        if axis:
            extra[5168+row]=axis
    words.extend(extra);assert len(words)==INPUT_WORDS
    meta['real_prepared_input']['declared_weapon_shield_policy']=dict(hit_shields=hit_shields,max_attacks=max_attacks,weapon_only=not skill_shields,in_game_rules_verified=False)
    return words,meta
