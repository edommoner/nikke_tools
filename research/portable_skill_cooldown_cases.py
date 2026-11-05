"""Remaining periodic-skill clocks: shared CUDA/Metal fixtures and native oracle."""
import copy
from portable_stun_cases import fixtures as status_fixtures
from portable_burst_recipient_cases import instant
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(status_fixtures()[0])
    base.update(duration=1.3,effects=[],owners=[],state_queries=[])
    names=roster_names(base)
    def clock(name='clock',timing='every:0.4s'):
        return dict(name=name,source='스킬1',type='damage',stat='bonus_damage',fixed_value=10,
                    target='same_target',trigger=dict(timing=[timing],condition=[]))
    def reduction(value,target='self',timing='on_attack_count:2'):
        return instant('skill_cooldown_reduce_pct',value,target,'remaining-clock',timing)
    rows=[]
    def add(name,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='skill-cooldown-'+name,effects=effects,owners=owners or [0]*len(effects))
        rows.append(c);return c
    for value in (0,50,100,150,-50):add('value-'+str(value),[clock(),reduction(value)])
    add('before-first-clock-init',[clock(),reduction(50,timing='battle_start')])
    add('periodic-reduction-includes-own-clock',[clock(),reduction(50,timing='every:0.2s')])
    add('duplicate-targets-are-one-set',[clock(),reduction(50,target=['all_allies','self'])])
    add('allied-clocks',[clock(),clock('other','every:0.5s'),reduction(50,target='all_allies')],[0,1,0])
    add('literal-other-owner',[clock(),reduction(50,target=names[0])],[0,1])
    c=add('ranked-owner',[clock(),clock('other'),reduction(50,target='allies_top_atk:1')],[0,1,0])
    c['base_atk']=[1000,9000,3000,4000,5000]
    from calculator.timeline import _NIKKE
    absent=next(n for n in _NIKKE if n not in names)
    add('absent-owner',[clock(),reduction(50,target=absent)])
    c=add('condition-false-clock-still-advances',[clock(),reduction(50)])
    c['effects'][0]['trigger']['condition']=['self_hp_below:10']
    c=add('target-effect-is-not-a-filter',[clock(),reduction(50)])
    c['effects'][1]['target_effect']='unrelated-clock-name'
    c=add('one-shot-preserves-later-interval',[clock(),reduction(50)])
    c['effects'][1]['max_trigger']=1
    add('reduction-before-due-clock',[reduction(50,timing='every:0.4s'),clock()])
    add('reduction-after-due-clock',[clock(),reduction(50,timing='every:0.4s')])
    add('huge-positive-clamps-factor',[clock(),reduction(1e308)])
    add('huge-negative-defers-clock',[clock(),reduction(-1e308)])
    c=add('overflow-then-zero-factor-is-unordered',[clock(),reduction(-1e308),reduction(100,timing='on_attack_count:5')])
    c['effects'][1]['max_trigger']=2;c['effects'][2]['max_trigger']=1;c['effects'][2]['name']='zero-factor'
    c=copy.deepcopy(c);c['name']='skill-cooldown-unordered-clock-recovers';c['effects'].append(reduction(50,timing='on_attack_count:6'))
    c['effects'][-1]['name']='recover-unordered';c['effects'][-1]['max_trigger']=1;c['owners'].append(0);rows.append(c)
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    seed=compile_case(fixtures()[1])[0];row=L['DEFINITION_BASE']+L['DEFINITION_WORDS']
    rows=[]
    for name,at,value in [('no-combat',3,0),('nonzero-stat',row+F['STAT'],1),
                          ('nan-value',row+F['VALUE']+1,0x7ff80000),
                          ('bad-recipient',L['RECIPIENT_BASE']+8,99)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/skill-cooldown-'+name,raw,None))
    return rows
