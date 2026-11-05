"""Literal named-hit contexts, snapshots and accumulator identities."""
import copy
from portable_stun_cases import fixtures as status_fixtures
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant


def fixtures():
    base=copy.deepcopy(status_fixtures()[0]);base.update(duration=.9,effects=[],owners=[],state_queries=[],observe_skill_critical=True)
    base['combat']['weapons'][0].update(capacity=100,interval=.1)
    def damage(name='source',timing='on_attack',stat='bonus_damage',condition=()):
        return dict(name=name,source='스킬1',type='damage',stat=stat,fixed_value=100,target='same_target',trigger=dict(timing=[timing],condition=list(condition)))
    def watch(name='witness',source='source',timing=None):
        return damage(name,timing or 'hit_count:'+source+':1',condition=['trigger_hit_crit'])
    rows=[]
    def add(name,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='skill-critical-'+name,effects=effects,owners=owners or [0]*len(effects));rows.append(c);return c
    for value in (-100,0,35,85,200):add('rate-'+str(value),[field('crit_rate',value,'self','rate'),damage(),watch()])
    add('multi-hit-snapshot-before-critical-child',[field('crit_rate',35,'self','rate'),damage(stat='bonus_damage:3'),
        field('crit_rate',100,'self','child-rate',timing='hit_count:source:1',condition=['trigger_hit_crit']),watch()])
    add('two-sources-have-distinct-keys',[damage(),damage('other'),watch(),watch('other-witness','other')])
    add('two-casters-have-distinct-keys',[damage(),watch(),damage(),watch()],[0,0,1,1])
    add('siblings-restore-parent-context',[field('crit_rate',35,'self','rate'),damage(),watch(),watch('second-witness'),watch('nested','witness')])
    for timing in ('battle_start','on_attack','hit_count','crit_hit','every:0.1s'):
        add('no-context-'+timing,[field('crit_rate',200,'self','rate'),damage(),watch(timing=timing)])
    c=add('unit-and-zero-keep-fractional-residue',[damage(),watch(),field('crit_rate',100,'self','unit',timing='on_attack_count:3',duration=.2),field('crit_rate',-200,'self','zero',timing='on_attack_count:6',duration=.2)])
    add('normal-only-rate-does-not-boost-skill',[field('normal_atk_crit_rate',200,'self','normal-rate'),damage(),watch()])
    c=add('normal-formula-uses-normal-rate',[field('normal_atk_crit_rate',50,'self','normal-rate'),damage(),watch()]);c['effects'][1]['damage_formula']='normal_attack'
    c=add('periodic-named-hits',[field('crit_rate',35,'self','rate'),damage(timing='battle_start',stat='dot_damage'),watch()]);c['effects'][1].update(duration=.65,tick_interval=.1)
    c=add('zero-coefficient-emits-no-context',[damage(),watch()]);c['effects'][0]['fixed_value']=0
    c=add('unnamed-packet-emits-no-context',[damage(name=''),watch()])
    add('empty-notify-does-not-inherit-critical-parent',[field('crit_rate',200,'self','rate'),damage(),
        field('atk_pct',1,'self','mark',timing='hit_count:source:1',condition=['trigger_hit_crit']),
        watch('leak',timing='event:mark'),damage('positive-notice',timing='event:mark')])
    c=add('deferred-burst-emits-no-named-hit',[instant('burst_charge_pct',100,'all_allies','gauge'),damage(timing='burst_cast'),watch()],[0,2,2])
    for i,w in enumerate(c['combat']['weapons']):w['stage']=[1,2,3,3,3][i]
    rate=field('crit_rate',85,'self','rate',timing='every:20s')
    rate['source']='스킬1';source=damage();source['source']='스킬2';witness=watch();witness['source']='스킬2'
    force=instant('force_skill_use',0,'self','force');force.update(source='스킬3',target_skill='스킬1')
    c=add('forced-slot-starts-inactive-rate',[rate,source,witness,force]);c['observe_authored_effect_lookup']=True
    forced=damage('forced',timing='every:20s',condition=['trigger_hit_crit']);forced['source']='스킬3'
    force=instant('force_skill_use',0,'self','force');force.update(source='스킬2',target_skill='스킬3')
    c=add('forced-slot-checks-condition',[forced,force]);c['observe_authored_effect_lookup']=True
    force=copy.deepcopy(force);force['trigger']['timing']=['hit_count:source:1']
    c=add('forced-slot-preserves-hit-context',[field('crit_rate',85,'self','rate'),source,forced,force]);c['observe_authored_effect_lookup']=True
    clock=damage(timing='every:0.4s');clock['source']='스킬3'
    force=instant('force_skill_use',0,'self','force','every:0.3s');force.update(source='스킬2',target_skill='스킬3')
    c=add('forced-slot-preserves-period-grid',[clock,watch(),force]);c.update(duration=1.1,observe_authored_effect_lookup=True)
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    seed=compile_case(fixtures()[2])[0];condition=L['CONDITION_BASE']+2*L['CONDITION_WORDS'];d=L['DEFINITION_BASE']+L['DEFINITION_WORDS']
    rows=[]
    for label,at,value in [('no-combat',3,0),('missing-policy',L['WORLD_META_BASE']+3,0),('invalid-policy',L['WORLD_META_BASE']+3,2),
                           ('condition-name',condition+1,1),('condition-value',condition+3,0x3ff00000),
                           ('name-overflow',d+F['NAME'],L['DEFINITIONS']),('no-native-landing',L['LANDING_META_BASE'],0)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/skill-critical-'+label,raw,None))
    case=next(c for c in fixtures() if c['name']=='skill-critical-forced-slot-starts-inactive-rate')
    seed=compile_case(case)[0];force=L['FORCE_BASE']+3*L['MASK_WORDS']
    for label,at,value in [('force-self',force,8),('force-overflow',force+7,0x80000000)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/skill-critical-'+label,raw,None))
    case=copy.deepcopy(case);case['owners'][0]=1
    raw=compile_case(case)[0];raw[force]|=1;rows.append(('reject/skill-critical-force-other-caster',raw,None))
    return rows
