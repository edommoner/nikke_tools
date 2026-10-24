"""Static complete-roster input for the declared weapon-only shield policy.

Keep original effect identities; lower the two modifier axes to the shared
carrier representation after ordinary world compilation. No battle is run.
"""
import copy,struct
from portable_specs import LIMITS as L,FIELDS as F
from destructible_damage_policy import modifier_axis
from destructible_world_runtime import compile_bindings
from portable_projectile_roster_input import compile_projectile_battle

SOURCE='gpu/destructible_weapon_shield_entry.slang'
INPUT_WORDS=110112
OUTPUT_WORDS=1048576

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
        if modifier_axis(effect):dest['effect']['stat']='atk_dmg_pct'
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
    for row,index in enumerate(meta['binding_source_indices']):
        axis=modifier_axis(original[index]['effect'])
        if skill_shields and original[index]['effect'].get('type')=='damage' and original[index]['effect'].get('stat')!='accum_split_damage':extra[5424+row]=4 if hit_shields else 3
        if axis:
            at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];assert words[at+F['KIND']]==0
            words[at+F['KIND']]=4;words[at+F['STAT']]=0;extra[5168+row]=axis
    words.extend(extra);assert len(words)==INPUT_WORDS
    meta['real_prepared_input']['declared_weapon_shield_policy']=dict(hit_shields=hit_shields,max_attacks=max_attacks,weapon_only=not skill_shields,in_game_rules_verified=False)
    return words,meta
