"""Authored reduction and raw-timing boundaries for both GPU transports."""
import copy
from portable_stun_cases import fixtures as status_fixtures
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(status_fixtures()[0]);base.update(duration=.9,effects=[],owners=[],state_queries=[])
    base['combat']['weapons'][0].update(capacity=100,interval=.1,pellets=3,muzzles=2)
    def proc(timing='on_attack_count:4',name='proc'):
        return dict(name=name,source='스킬1',type='damage',stat='bonus_damage',fixed_value=100,
                    target='same_target',trigger=dict(timing=[timing],condition=[]))
    def reduce(value=1,name='reducer',target_effect='proc',**kwargs):
        return field('trigger_count_reduce',value,'self',name,target_effect=target_effect,**kwargs)
    rows=[]
    def add(name,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='trigger-reduction-'+name,effects=effects,owners=owners or [0]*len(effects));rows.append(c);return c
    add('baseline',[proc()])
    for value in (0,1,100,-1,.75,-.75):add('value-'+str(value),[reduce(value),proc()])
    add('sum-before-positive-truncate',[reduce(.75),reduce(.75,'second'),field('debuff_immune',0,'self','immunity'),proc()])
    add('sum-before-negative-truncate',[reduce(-.75),reduce(-.75,'second'),proc()])
    add('threshold-above-counter-horizon',[*[reduce(-1e8,'reducer'+str(i)) for i in range(24)],proc()])
    add('empty-target-name',[reduce(target_effect=''),proc()])
    add('absent-target-name',[reduce(target_effect='absent'),proc()])
    add('other-caster',[reduce(),proc()],[1,0])
    c=add('other-recipient-still-caster-bound',[reduce(),proc()]);c['effects'][0]['target']=roster_names(base)[1]
    add('stack-is-not-a-multiplier',[reduce(timing='on_attack',max_stack=3),proc()])
    add('runtime-predicate-is-not-a-filter',[reduce(condition=['self_hp_below:1']),proc()])
    add('runtime-predicate-changes-after-activation',[reduce(condition=['self_hp_above:75']),instant('current_hp_reduce',50,'self','drain'),proc()])
    add('finite-false-condition-does-not-activate',[reduce(condition=['self_hp_below:1'],duration=.5),proc()])
    add('finite-expiry',[reduce(duration=.2),proc()])
    add('refresh-before-expiry',[reduce(duration=.2,timing='on_attack'),proc()])
    add('shared-timing-group',[reduce(target_effect='representative'),field('',0,'self','representative',timing='on_attack_count:4'),proc()])
    c=add('raw-placeholder-timing-is-not-intersection',[reduce(target_effect='representative'),field('',0,'self','representative',timing='on_attack_count:{0}'),proc()])
    c['effects'][1]['trigger_values']={'10':4}
    add('same-name-refresh-latest-definition',[reduce(),reduce(2),proc()])
    remove=instant('remove_named_buff',1,'self','remove','on_attack_count:3');remove['target_effect']='reducer'
    add('named-removal',[reduce(),proc(),remove])
    for timing in ('on_attack','hit_count','pellet_hit','squad_ammo_consume:4','received_hit_count:2','full_burst_start_count:2','burst_enter_count:1:2'):
        c=add('not-reducible-'+timing,[reduce(100 if 'burst' in timing else -2),proc(timing)])
        if 'burst' in timing:
            c['effects'].insert(0,instant('burst_charge_pct',100,'all_allies','initial-gauge'));c['owners'].insert(0,0)
        if timing=='received_hit_count:2':c['patterns']=[dict(id='incoming',kind='attack',delay=.1,spec=dict(atk=100,coeff=100,target='all',hits=4,interval=.1))]
    for timing in ('hit_count:4','pellet_hit_count:4','crit_hit_count:4','core_hit_count:4','full_charge_fire_count:4','full_charge_hit_count:4'):
        c=add('counter-'+timing,[reduce(),proc(timing)])
        if 'core_hit' in timing:c['enemy']['core_px']=100
        if 'full_charge' in timing:
            c['duration']=1.5;c['combat']['weapons'][0].update(mode='charge',charge=.1,interval=.2,min_cycle=.2,full_charge_mult=100,gauge_mult=100)
            # DOWN_Charge AR metadata normalizes to no post-fire delay and
            # minimum cycle1/fire_rate. Keep the literal GPU clocks identical.
            c['post_fire_delays'][0]=0
    add('named-hit-counter',[reduce(),proc('on_attack','source'),proc('hit_count:source:4')])
    c=add('missing-fixed-value-ignores-level-values',[reduce(),proc()]);c['effects'][0].pop('fixed_value');c['effects'][0]['values']={'10':99}
    c=add('bullet-expiry',[reduce(duration_bullets=2),proc()])
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    seed=compile_case(fixtures()[2])[0];d=L['DEFINITION_BASE'];m=L['MODE_BASE'];q=L['DEFINITION_EXTRA_BASE']+3
    rows=[]
    for name,at,value in [('no-combat',3,0),('missing-flag',q,0),('wrong-kind',d+F['KIND'],0),
                          ('wrong-magic',m+L['TRIGGER_REDUCTION_OFFSET'],1),
                          ('nan-literal',m+L['TRIGGER_REDUCTION_OFFSET']+2,0x7ff80000),
                          ('mask-outside-definitions',m+L['TRIGGER_REDUCTION_MASK']+7,0x80000000)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/trigger-reduction-'+name,raw,None))
    raw=list(seed);raw[m+L['TRIGGER_REDUCTION_OFFSET']]=0;rows.append(('reject/trigger-reduction-missing-magic',raw,None))
    other=copy.deepcopy(fixtures()[2]);other['owners'][1]=1
    raw=compile_case(other)[0];raw[m+L['TRIGGER_REDUCTION_MASK']]|=2
    rows.append(('reject/trigger-reduction-mask-other-caster',raw,None))
    return rows
