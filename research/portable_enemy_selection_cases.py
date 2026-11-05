"""One seeded random/code enemy selection table for native, CUDA and Metal."""
import copy
from portable_persona_cases import fixtures as persona_fixtures
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant


def fixtures():
    base=copy.deepcopy(persona_fixtures()[0]);base.update(effects=[],owners=[],duration=.35)
    rows=[]
    def hit(target='enemies_random:1',stat='damage',timing='every:0.1s',**kw):
        return dict(name='random-hit',source='스킬1',type='damage',stat=stat,fixed_value=100,target=target,trigger=dict(timing=[timing],condition=[]),**kw)
    def add(label,population,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='enemy-selection-'+label,effects=effects,owners=owners if owners is not None else [0]*len(effects))
        c['patterns']=[dict(id='idle',kind='idle')]
        if population>1:c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=population-1,hp=1e15)))
        rows.append(c);return c
    for population,k in ((1,1),(2,1),(2,2),(5,1),(5,5),(21,1),(22,1),(85,6),(86,6),(128,1),(128,5),(128,6),(128,21),(128,22),(128,128),(128,256)):
        add(f'random-{population}-{k}',population,[hit('enemies_random:'+str(k))])
    add('random-default-one',5,[hit('enemies_random')])
    add('random-multihit-reselects',8,[hit(stat='sequential_damage:5')])
    add('random-split',8,[hit('enemies_random:3',stat='split_damage')])
    add('random-zero-coefficient-no-draws',8,[dict(hit(),fixed_value=0)])
    c=add('random-before-spawn-no-draws',4,[hit()]);c['patterns'][-1]['delay']=1
    c=add('random-retired-wave',4,[hit()]);c['patterns'][-1]['until']={'time':.2}
    c=add('random-reopened-wave-generation',4,[hit()]);c['patterns'][-1].update(until=dict(time=.1),repeat=1)
    c=add('random-lethal-multihit-retarget',6,[hit(stat='sequential_damage:5')]);c['patterns'][-1].update(delay=.05);c['patterns'][-1]['spec']['hp']=100
    c=add('random-multihit-child-selection',8,[hit(stat='sequential_damage:3'),field('received_dmg_pct',10,'enemies_random:2','child',timing='hit_count:random-hit:1',duration=.2)])
    c=add('random-reused-slots-birth-order',3,[hit()]);c['patterns'][-1].update(delay=.05,until=dict(time=.12),repeat=1);c['patterns'].append(dict(id='wave2',kind='summon',delay=.1,spec=dict(count=2,hp=1e15)))
    c=add('random-parts-not-in-pool',1,[hit()]);c['patterns'].append(dict(id='parts',kind='parts',targets=[dict(name='part',hp=1e10)]))
    c=add('random-shared-with-boss-victims',7,[hit()]);c['patterns'].append(dict(id='boss-random',kind='attack',delay=.1,spec=dict(atk=300,coeff=100,target='random:2',hits=3,interval=.05)))
    for k in (1,2,5,6,21,22,128):
        c=add('random-buff128-'+str(k),128,[field('received_dmg_pct',10,'enemies_random:'+str(k),'weakness',timing='every:0.1s',duration=.2)])
        if k==128:c['duration']=1.2 # Cross several MT twists without expanding per-hit traces.
    add('random-buff-named-child',6,[field('received_dmg_pct',10,'enemies_random:2','weakness',timing='every:0.1s',duration=.2),hit('target',timing='event:weakness')])
    for operation in ('remove_named_buff','debuff_stack_add','named_buff_duration_extend','debuff_cleanse'):
        initial=field('received_dmg_pct',10,'all_enemies','weakness',timing='every:0.1s',duration=.2,max_stack=3)
        e=instant(operation,1,'enemies_random:2','mutation','every:0.2s')
        if operation!='debuff_cleanse':e['target_effect']='weakness'
        if operation=='remove_named_buff':e['remove_scope']='target'
        add('random-'+operation,7,[initial,e])
    c=add('random-dot-snapshot',7,[dict(hit(timing='battle_start',stat='dot_damage'),duration=.3,tick_interval=.1)]);c['observe_periodic_skills']=True
    c=add('random-dot-late-activation',7,[dict(hit(timing='every:0.1s',stat='dot_damage'),duration=.2,tick_interval=.1)]);c['observe_periodic_skills']=True
    add('random-budget-damage',7,[dict(hit(),max_trigger=1)])
    add('random-budget-zero-damage',7,[dict(hit(),max_trigger=1,fixed_value=0)])
    add('random-budget-buff',7,[field('received_dmg_pct',10,'enemies_random:2','weakness',timing='every:0.1s',max_trigger=1)])
    c=add('random-budget-dot',7,[dict(hit(stat='dot_damage'),max_trigger=1,duration=.2,tick_interval=.1)]);c['observe_periodic_skills']=True
    c=add('random-dot-alias-refresh',7,[dict(hit(stat='dot_damage'),duration=.2,tick_interval=.1),dict(hit('enemies_random:2',stat='dot_damage',timing='every:0.2s'),duration=.2,tick_interval=.1)]);c['observe_periodic_skills']=True
    c=add('dot-named-removal-empty-reference',1,[
        dict(instant('gauge_charge',10,'self','charge'),gauge_id='g',gauge_max=10),
        dict(hit('target',stat='dot_damage',timing='battle_start'),name='captured-dot',duration=-1,tick_interval=.1,scaling='stack_count',scaling_ref='g',max_stack=20),
        dict(instant('gauge_consume',-1,'self','spend'),gauge_id='g'),
        dict(instant('remove_named_buff',1,'target','remove','every:0.2s'),target_effect='captured-dot')]);c['observe_periodic_skills']=True
    c=copy.deepcopy(c);c['name']='enemy-selection-dot-named-removal-restarts-phase';c['duration']=.55
    c['effects'][0]['trigger']['timing'].append('every:0.27s')
    c['effects'][1]['trigger']['timing'].append('every:0.27s');c['effects'][1]['tick_start']='immediate'
    rows.append(c)
    for population in (1,7):
        for selector in ('enemies_code:전격','enemies_code:풍압','enemies_lowest_hp_code:풍압:1'):
            add('code-damage-'+str(population)+'-'+selector,population,[hit(selector)])
            add('code-buff-'+str(population)+'-'+selector,population,[field('received_dmg_pct',10,selector,'weakness',timing='every:0.1s')])
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    seed=compile_case(fixtures()[1])[0];d=L['DEFINITION_BASE'];p=L['DAMAGE_DEFINITION_BASE'];rng=L['ENEMY_TARGET_META_BASE']
    rows=[]
    for name,at,value in [('unknown-route',p,11),('missing-rng',rng,0),('invalid-rng',rng,2),('rng-reserved',rng+3,1),('zero-count',p+1,0),('count-overflow',p+1,129),('no-combat',3,0),('nan',d+F['VALUE']+1,0x7ff80000),('no-actor-pool',L['WORLD_ACTOR_POOL_INPUT_BASE'],0)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/enemy-selection-'+name,raw,None))
    return rows
