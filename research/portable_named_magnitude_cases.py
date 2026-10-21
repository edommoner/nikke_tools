"""Native named coefficient and received-damage amplification workloads."""
import copy
from portable_persona_cases import fixtures as persona_fixtures
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(persona_fixtures()[0]);base.update(effects=[],owners=[],duration=.8)
    names=roster_names(base);rows=[]
    def hit(timing='every:0.2s',**kw):
        return dict(name='named-hit',source='스킬1',type='damage',stat='damage',fixed_value=100,target='target',trigger=dict(timing=[timing],condition=[]),**kw)
    def amp(stat='dmg_scale_mag_pct',value=50,target='self',ref='named-hit',name='magnitude',**kw):
        return field(stat,value,target,name,target_effect=ref,**kw)
    def weakness(value=10,name='weakness',**kw):return field('received_dmg_pct',value,'all_enemies',name,**kw)
    def received(value=50,ref='weakness',**kw):return amp('received_dmg_buff_mag_pct',value,'all_enemies',ref,**kw)
    def add(name,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='named-mag-'+name,effects=effects,owners=owners if owners is not None else [0]*len(effects));rows.append(c);return c
    add('damage-baseline',[hit()])
    add('damage-zero-original-coefficient',[amp(),dict(hit(),fixed_value=0)])
    for value in (0,50,-50,-100,-150):add('damage-value-'+str(value),[amp(value=value),hit()])
    add('damage-wrong-name',[amp(ref='other'),hit()])
    add('damage-other-caster',[amp(),hit()],[1,0])
    add('damage-other-recipient-still-applies',[amp(target=names[1]),hit()])
    add('damage-enemy-carrier-still-applies',[amp(target='all_enemies'),hit()])
    add('damage-runtime-false-direct-carrier',[amp(timing='passive',condition=['self_hp_below:10']),hit()])
    add('damage-finite-condition-no-carrier',[amp(duration=.5,condition=['self_hp_below:10']),hit()])
    add('damage-expiry',[amp(duration=.4),hit()])
    add('damage-stacked',[amp(timing='on_attack',max_stack=3),hit()])
    add('damage-two-multipliers',[amp(value=25,name='one'),amp(value=50,name='two'),hit()])
    add('damage-named-child',[amp(),hit('event:magnitude')])
    add('damage-expiry-child',[amp(duration=.3),hit('event:state_end:magnitude')])
    add('damage-gear',[dict(amp(),_source_tag='equipment'),hit()])
    add('damage-scaling-ref',[field('atk_pct',0,'self','reference',timing='on_attack',max_stack=3),amp(scaling='stack_count',scaling_ref='reference'),hit()])
    c=add('damage-dot',[amp(),dict(hit('battle_start'),stat='dot_damage',duration=.7,tick_interval=.2)]);c['observe_periodic_skills']=True
    add('received-baseline',[weakness()])
    add('received-amplified',[weakness(),received()])
    add('received-wrong-name',[weakness(),amp('received_dmg_buff_mag_pct',50,'all_enemies','other')])
    add('received-other-owner-allowed',[weakness(),received()],[0,1])
    add('received-multiple-base',[weakness(),weakness(20),field('received_dmg_pct',3,'all_enemies','unrelated'),received()],[0,1,0,2])
    add('received-two-additive-increments',[weakness(),received(50,name='one'),received(25,name='two')])
    add('received-runtime-false',[weakness(),received(timing='passive',condition=['self_hp_below:10'])])
    add('received-base-runtime-false',[weakness(timing='passive',condition=['self_hp_below:10']),received()])
    add('received-expiry',[weakness(),received(duration=.4)])
    add('received-base-expiry',[weakness(duration=.4),received()])
    add('received-stacks',[weakness(timing='on_attack',max_stack=3),received(timing='on_attack',max_stack=2)])
    add('received-ally-amplifier-does-not-match',[weakness(),amp('received_dmg_buff_mag_pct',50,'all_allies','weakness')])
    c=add('received-ally-incoming-unmagnified',[field('received_dmg_pct',10,'all_allies','weakness'),amp('received_dmg_buff_mag_pct',50,'all_allies','weakness')]);c['patterns']=[dict(id='incoming',kind='attack',delay=.3,spec=dict(atk=300,coeff=100,target='all',hits=1))]
    c=add('received-enemy-generation',[weakness(),received()]);c['patterns']=[dict(id='wave',kind='summon',delay=.1,until=dict(time=.25),repeat=1,spec=dict(count=1,hp=1000000))]
    c=add('received-late-add',[weakness(),received(timing='every:0.2s',duration=.1)]);c['patterns'].append(dict(id='wave',kind='summon',delay=.3,spec=dict(count=1,hp=1000000)))
    for label,delay in [('early',0),('late',.1)]:
        c=add('received-boss-base-'+label,[received(ref='world·received_dmg_pct')]);c['patterns']=[dict(id='world',kind='buff',delay=delay,enemy=dict(received_dmg_pct=10))]
    c=add('received-boss-and-authored-base-order',[weakness(1e16,name='world·received_dmg_pct',timing='every:0.2s'),received(ref='world·received_dmg_pct')]);c['patterns']=[dict(id='world',kind='buff',delay=.1,enemy=dict(received_dmg_pct=-1e16))]
    from world_pending_cases import fixtures as pending_fixtures
    for label,timing,duration in [('early','battle_start',-1),('late','burst_cast',-1),('expired','battle_start',.1),('zero','battle_start',-1)]:
        c=copy.deepcopy(pending_fixtures()[0]);c['name']='named-mag-pending-'+label
        for key,value in base.items():
            if key not in c:c[key]=copy.deepcopy(value)
        damage=next((e,o) for e,o in zip(c['effects'],c['owners']) if e.get('type')=='damage')
        e=amp(value=-100 if label=='zero' else 50,ref=damage[0]['name'],timing=timing,duration=duration)
        c['effects'].append(e);c['owners'].append(damage[1]);c.update(observe_named_state=True,observe_enemy_fields=True,observe_counter_field_memberships=True);rows.append(c)
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    rows=[];seed=compile_case(next(c for c in fixtures() if c['name']=='named-mag-damage-value-50'))[0];d=L['DEFINITION_BASE']
    for label,at,value in [('kind',d+F['KIND'],4),('unported-atk-magnitude',d+F['STAT'],79),('reference-overflow',d+F['TARGET_NAME'],L['DEFINITIONS']),('reference-negative',d+F['TARGET_NAME'],0xffffffff),('no-combat',3,0),('nan',d+F['VALUE']+1,0x7ff80000),('persona-flag',L['DEFINITION_EXTRA_BASE']+3,1),('allied-health',L['HEALTH_DEFINITION_BASE']+1,1)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/named-mag-'+label,raw,None))
    boss=next(c for c in fixtures() if c['name']=='named-mag-received-boss-base-early');seed=compile_case(boss)[0];node=L['WORLD_OVERLAY_NODE_BASE']
    for label,at,value in [('overlay-name-overflow',node+11,L['DEFINITIONS']+1),('overlay-extra',node+12,1),('overlay-wrong-kind',node,6)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/named-mag-'+label,raw,None))
    return rows
