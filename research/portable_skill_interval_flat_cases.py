"""Named flat periods: literal inputs for the common native clock comparator."""
import copy
from portable_skill_interval_cases import fixtures as percentage_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(percentage_fixtures()[0]);base.update(effects=[],owners=[])
    def clock(name='clock',timing='every:0.4s'):
        return dict(name=name,source='스킬1',type='damage',stat='bonus_damage',fixed_value=10,
                    target='same_target',trigger=dict(timing=[timing],condition=[]))
    def flat(value=-.2,stat='effect_interval',name='flat',target='self',reference='clock',**kw):
        return dict(field(stat,value,target,name,**kw),target_effect=reference)
    rows=[]
    def add(name,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='skill-flat-'+name,effects=effects,
                                      owners=owners if owners is not None else [0]*len(effects))
        rows.append(c);return c
    for stat in ('effect_interval','skill_cooldown'):
        for value in (0,-.2,-.4,-2,.2):add(stat+'-'+str(value),[clock(),flat(value,stat=stat)])
    add('activate-mid-period',[clock(),flat(timing='on_attack_count:2',max_trigger=1)])
    add('expire-mid-period',[clock(),flat(duration=.3)])
    add('activate-and-expire',[clock(),flat(timing='on_attack_count:2',max_trigger=1,duration=.3)])
    add('flat-before-percent',[clock(),flat(),field('skill_cooldown_pct',-50,'self','percent')])
    add('flat-positive-percent-floor',[clock(),flat(-.5),field('skill_cooldown_pct',100,'self','percent')])
    add('stacked',[clock(),flat(-.1,timing='on_attack',max_stack=3)])
    add('merged-name',[clock(),flat(-.1,max_stack=3),flat(-.1,max_stack=3)])
    add('separate-stats-with-same-name',[clock(),flat(-.1),flat(-.1,stat='skill_cooldown')])
    add('other-effect-is-not-selected',[clock(),clock('other'),flat()])
    for name,reference in [('missing-reference','missing'),('empty-reference','')]:
        add(name,[clock(),flat(reference=reference)])
    c=add('omitted-reference',[clock(),flat()]);del c['effects'][1]['target_effect']
    add('unnamed-clock-is-not-selected',[clock(''),flat(reference='')])
    names=roster_names(base)
    add('named-ally',[clock(),flat(target=names[0])],[0,1])
    add('allied-clocks',[clock(),clock('clock'),flat(target='all_allies')],[0,1,0])
    add('other-ally',[clock(),flat(target=names[1])])
    add('ranked-lazy',[clock(),clock('other'),flat(target='allies_top_atk:1')],[0,1,0])
    add('runtime-false',[clock(),flat(timing='passive',condition=['self_hp_below:10'])])
    add('runtime-crosses',[clock(),flat(timing='passive',condition=['self_hp_below:60']),
        instant('current_hp_reduce',50,'self','health-change','on_attack_count:2')])
    add('finite-keeps-activation-gate',[clock(),flat(duration=.8,condition=['self_hp_above:90']),
        instant('current_hp_reduce',50,'self','health-change','on_attack_count:2')])
    add('runtime-ally-hp-context',[clock(),flat(timing='passive',condition=['ally_hp_below:60']),
        instant('current_hp_reduce',50,names[1],'health-change','on_attack_count:2')])
    add('two-stats-sum-order',[clock(),flat(.1,stat='skill_cooldown',name='skill-first'),
        flat(1e16,name='large'),flat(-1e16,name='cancel')])
    add('compensated-small-amount',[clock(),flat(1e16,name='large'),flat(-.2,name='small'),flat(-1e16,name='cancel')])
    add('with-trigger-reducer',[clock(),flat(),field('trigger_count_reduce',1,'self','reduce',target_effect='clock')])
    add('with-stack-operation',[clock(),flat(-.1,max_stack=3),
        instant('buff_stack_add',1,'self','add-stack','on_attack_count:2')])
    rows[-1]['effects'][-1]['target_effect']='flat'
    c=add('value-table',[clock(),flat()]);del c['effects'][1]['fixed_value'];c['effects'][1]['values']={'10':-.2}
    add('both-operators-different-lifetimes',[clock(),flat(-.1,duration=.3),flat(-.1,stat='skill_cooldown',name='skill',duration=.7)])
    add('same-reference-unicode-colons',[clock('時計:α'),flat(reference='時計:α')])
    add('two-stats-overflow-order',[clock(),flat(1e308,stat='skill_cooldown',name='skill-first'),
        flat(1e308,name='large'),flat(-1e308,name='cancel')])
    add('runtime-ally-hp-matches-query-caster',[clock(),flat(timing='passive',condition=['ally_hp_below:60']),
        instant('current_hp_reduce',50,names[0],'health-change','on_attack_count:2')])
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    from portable_skill_interval_specs import OFFSET,FLAG
    seed=compile_case(fixtures()[1])[0];d=L['DEFINITION_BASE']+L['DEFINITION_WORDS']
    meta=L['MODE_BASE']+L['MODE_WORDS']+OFFSET
    rows=[]
    for label,at,value in [('no-combat',3,0),('kind',d+F['KIND'],0),('stat',d+F['STAT'],58),
            ('nan',d+F['VALUE']+1,0x7ff80000),('magic',meta,0),('operator',meta+1,3),
            ('name-overflow',meta+2,L['DEFINITIONS']),('bad-presence',meta+3,2),
            ('unused-mode-word',meta+4,1),('unused-mode-tail',meta+17,1),
            ('untagged-payload',L['DEFINITION_EXTRA_BASE']+L['DEFINITION_EXTRA_WORDS']+3,0),
            ('overlapping-union',L['DEFINITION_EXTRA_BASE']+L['DEFINITION_EXTRA_WORDS']+3,FLAG|256),
            ('bad-recipient',L['RECIPIENT_BASE']+8,99)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/skill-flat-'+label,raw,None))
    c=next(c for c in fixtures() if c['name']=='skill-flat-runtime-ally-hp-context')
    raw=compile_case(c)[0];condition=L['CONDITION_BASE']+L['CONDITION_WORDS']
    for label,offset,value in [('ally-hp-name',1,1),('ally-hp-nan',3,0x7ff80000)]:
        bad=list(raw);bad[condition+offset]=value;rows.append(('reject/skill-flat-'+label,bad,None))
    from portable_runtime import double_words
    for label,value in [('ally-hp-low',-1),('ally-hp-high',101)]:
        bad=list(raw);bad[condition+2:condition+4]=double_words(value);rows.append(('reject/skill-flat-'+label,bad,None))
    return rows
