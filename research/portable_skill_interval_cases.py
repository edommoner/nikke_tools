"""Persistent interval percentages use native clocks, independent of GPU math."""
import copy
from portable_skill_cooldown_cases import fixtures as remaining_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(remaining_fixtures()[0])
    base.update(duration=1.3,observe_skill_clocks=True,effects=[],owners=[])
    def clock(name='clock',timing='every:0.4s'):
        return dict(name=name,source='스킬1',type='damage',stat='bonus_damage',fixed_value=10,
                    target='same_target',trigger=dict(timing=[timing],condition=[]))
    def modifier(value=-50,**options):
        return field('skill_cooldown_pct',value,'self','interval-percent',**options)
    rows=[]
    def add(name,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='skill-interval-'+name,effects=effects,
                                      owners=owners if owners is not None else [0]*len(effects))
        rows.append(c);return c
    for value in (0,-50,-95,-100,-200,50):add('percent-'+str(value),[clock(),modifier(value)])
    add('activate-mid-period',[clock(),modifier(timing='on_attack_count:2',max_trigger=1)])
    add('expire-mid-period',[clock(),modifier(duration=.3)])
    add('activate-and-expire',[clock(),modifier(timing='on_attack_count:2',max_trigger=1,duration=.3)])
    add('stacks',[clock(),modifier(-25,timing='on_attack',max_stack=3)])
    add('two-sources-ordered',[clock(),modifier(-25),field('skill_cooldown_pct',-25,'self','second-percent')])
    add('same-name-merge',[clock(),modifier(-25,max_stack=3),modifier(-25,max_stack=3)])
    names=roster_names(base)
    add('allied-clock',[clock(),clock('second-clock'),field('skill_cooldown_pct',-50,'all_allies','squad-percent')],[0,1,0])
    add('named-ally',[clock(),field('skill_cooldown_pct',-50,names[0],'named-percent')],[0,1])
    add('excluded-clock',[clock(),field('skill_cooldown_pct',-50,names[1],'other-percent')])
    add('ranked-lazy',[clock(),clock('second-clock'),field('skill_cooldown_pct',-50,'allies_top_atk:1','ranked-percent')],[0,1,0])
    add('overlapping-target-set',[clock(),field('skill_cooldown_pct',-50,['all_allies','self'],'overlap')])
    add('passive-runtime-false-is-not-rechecked',[clock(),modifier(timing='passive',condition=['self_hp_below:10'])])
    add('finite-activation-condition-false',[clock(),modifier(duration=.3,condition=['self_hp_below:10'])])
    c=add('runtime-crossing-does-not-gate-percent',[clock(),modifier(timing='passive',condition=['self_hp_below:60']),
              instant('current_hp_reduce',50,'self','health-change','on_attack_count:2')])
    add('target-effect-is-not-percent-filter',[clock(),dict(modifier(),target_effect='unrelated')])
    add('interacts-with-one-shot-remainder',[clock(),modifier(),instant('skill_cooldown_reduce_pct',50,'self','remaining','on_attack_count:2')])
    add('fractional-base',[clock(timing='every:0.37s'),modifier(-33.33333333333333,duration=.47)])
    c=add('level-values',[clock(),modifier()]);del c['effects'][1]['fixed_value'];c['effects'][1]['values']={'10':-50}
    c=add('two-period-descriptors',[clock(),modifier()]);c['effects'][0]['trigger']['timing'].append('every:0.6s')
    c=add('down-clock-keeps-advancing',[clock(),modifier()]);c['patterns']=[dict(id='lethal',kind='attack',delay=.3,spec=dict(atk=1e8,coeff=100,target='all'))]
    add('compensated-cancellation',[clock(),modifier(1e20),field('skill_cooldown_pct',-50,'self','small'),field('skill_cooldown_pct',-1e20,'self','cancel')])
    add('positive-sum-overflow',[clock(),modifier(1e308),field('skill_cooldown_pct',1e308,'self','overflow')])
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    seed=compile_case(fixtures()[1])[0];d=L['DEFINITION_BASE']+L['DEFINITION_WORDS']
    rows=[]
    for label,at,value in [('no-combat',3,0),('kind',d+F['KIND'],4),
                          ('nan',d+F['VALUE']+1,0x7ff80000),
                          ('bad-recipient',L['RECIPIENT_BASE']+8,99)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/skill-interval-'+label,raw,None))
    return rows
