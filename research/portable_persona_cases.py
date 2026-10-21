"""Native persona presence, innate-B3 filtering and lifecycle workloads."""
import copy
from portable_stun_cases import fixtures as status_fixtures
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(status_fixtures()[0]);base.update(effects=[],owners=[],duration=.8,patterns=[dict(id='idle',kind='idle')])
    names=roster_names(base)
    for w,stage in zip(base['combat']['weapons'],(3,3,3,2,1)):w.update(stage=stage,interval=.2,capacity=1000)
    rows=[]
    def marker(value=0,name='persona',target='self',**kw):return field('persona_state',value,target,name,**kw)
    def witness(timing='every:0.2s',target='allies_burst3_persona_excl_self',**kw):return field('atk_pct',50,target,'witness',timing=timing,**kw)
    def add(name,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='persona-'+name,effects=effects,owners=owners if owners is not None else [0]*len(effects));rows.append(c);return c
    add('no-marker',[witness()])
    for value in (0,1,-5):add('value-'+str(value),[marker(value),witness()],[1,0])
    add('exclude-self',[marker(),witness()])
    add('innate-b3-only',[marker(target='all_allies'),witness()])
    add('different-names',[marker(name='Johanna'),marker(name='Konohana'),witness()],[1,2,0])
    add('marker-after-selection',[witness(timing='battle_start'),marker()],[0,1])
    add('instant-resolves-each-activation',[marker(duration=.3),instant('heal_hp_pct',10,'allies_burst3_persona_excl_self','heal','every:0.2s')],[1,0])
    add('finite-marker-expires',[marker(duration=.3),witness(timing='every:0.2s',duration=.1)],[1,0])
    add('runtime-false-still-presence',[marker(timing='passive',condition=['self_hp_below:10']),witness()],[1,0])
    add('finite-false-not-active',[marker(duration=.4,condition=['self_hp_below:10']),witness()],[1,0])
    add('marker-stacks',[marker(timing='on_attack',max_stack=3),witness(timing='every:0.2s')],[1,0])
    add('marker-removed',[marker(),dict(instant('remove_named_buff',0,names[1],'remove','on_attack_count:2'),target_effect='persona'),witness(timing='every:0.2s',duration=.1)],[1,0,0])
    add('ordered-composite',[marker(target='all_allies'),witness(target=['self','allies_burst3_persona_excl_self'])])
    add('marker-named-child',[marker(),witness(timing='event:persona')],[1,0])
    add('marker-end-child',[marker(duration=.3),witness(timing='event:state_end:persona')],[1,0])
    c=add('innate-stage-ignores-override',[marker(),field('burst_stage_override:1',0,'self','override'),witness()],[1,1,0])
    c=add('marked-non-b3-not-promoted',[marker(),field('burst_stage_override:3',0,'self','override'),witness()],[3,3,0])
    c=add('marked-actor-down',[marker(),witness(timing='every:0.2s',duration=.1)],[1,0]);c['patterns']=[dict(id='kill-marked',kind='attack',delay=.3,spec=dict(atk=10000000,coeff=100,target='slot:2',hits=1))]
    c=add('gear-source-presence',[dict(marker(),_source_tag='equipment'),witness()],[1,0])
    add('zero-stack-still-presence',[marker(),dict(instant('debuff_stack_remove',1,names[1],'zero','on_attack_count:2'),target_effect='persona'),witness()],[1,0,0])
    add('bullet-lifetime',[marker(duration_bullets=2),witness(timing='every:0.2s',duration=.1)],[1,0])
    for code in ('persona-code','different-code'):
        c=add('target-code-'+code,[marker(),witness(),field('atk_pct',30,'self','code-buff',duration=.5,condition=['target_code:persona-code'])],[1,0,0])
        c['enemy']=dict(c.get('enemy',{}),code=code)
        c['environment']['enemy_code']=code
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L,FIELDS as F
    seed=compile_case(fixtures()[1])[0];d=L['DEFINITION_BASE'];q=L['DEFINITION_EXTRA_BASE']+3;p=L['RECIPIENT_BASE']+8
    rows=[]
    for label,at,value in [('kind',d+F['KIND'],0),('stat',d+F['STAT'],1),('no-combat',3,0),('mixed-marker',q,3),('mixed-charge',q,9),
            ('nan',d+F['VALUE']+1,0x7ff80000),('enemy',L['HEALTH_DEFINITION_BASE']+3,1),
            ('selector-count',p+1,1),('selector-mask',p+2,32),('selector-extra',p+3,1),('selector-order',p+4,1),('selector-key',p+5,1)]:
        raw=list(seed);raw[at]=value;rows.append(('reject/persona-'+label,raw,None))
    code_seed=compile_case(fixtures()[-2])[0];condition=L['CONDITION_BASE']+2*L['CONDITION_WORDS']
    for label,word,value in [('zero-name',1,0),('name-overflow',1,L['DEFINITIONS']+1),('nonzero-value',2,1),('nan-value',3,0x7ff80000)]:
        raw=list(code_seed);raw[condition+word]=value;rows.append(('reject/persona-code-'+label,raw,None))
    return rows
