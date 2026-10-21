"""Literal down/revive contracts; no battle, packing or GPU work in construction."""
import copy
from portable_persona_cases import fixtures as persona_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(persona_fixtures()[0])
    base.update(duration=.9,effects=[],owners=[],base_atk=[2000,1800,1600,1400,1200])
    for a in base['environment']['allies']:a.update(base_hp=10000,base_defense=0)
    for w in base['combat']['weapons']:w.update(interval=.1,capacity=3,reload=.4,stage=0)
    base['patterns']=[dict(id='lethal',kind='attack',delay=.3,spec=dict(atk=1e8,coeff=100,target='slot:1',pierce=True,hits=1))]
    names=roster_names(base);rows=[]
    def add(label,revival=True):
        c=copy.deepcopy(base);c['name']='revive-'+label
        c['effects']=[field('atk_pct',10,'self','own-permanent'),field('atk_pct',10,'all_allies','shared-permanent',max_stack=3)]
        c['owners']=[0,0]
        if revival:
            c['effects'].append(dict(instant('revive',50,'allies_down_top_atk_excl:1','revive','event:ally_down'),max_trigger=1));c['owners'].append(1)
        rows.append(c);return c
    add('down-control',False)
    add('synchronous')
    c=add('preserved');c['effects'].append(field('atk_pct',7,'self','preserved',persist_on_revive=True));c['owners'].append(0)
    c=add('passive-not-periodic');c['effects'] += [field('max_hp_pct',25,'self','passive-hp',timing='passive'),field('atk_pct',5,'self','periodic-permanent',timing='every:0.1s')];c['owners'] += [0,0]
    add('shared-no-double-stack')
    c=add('once-only');c['patterns'][0]['spec'].update(hits=2,interval=.3)
    c=add('no-hp-threshold');c['effects'].append(field('atk_pct',77,'self','low-hp',timing='hp_below:60'));c['owners'].append(0)
    c=add('whole-squad');c['patterns'][0]['spec']['target']='all'
    c=add('delayed');c['effects'][-1]['trigger']['timing']=['every:0.6s']
    c=add('alive-noop');c['patterns']=[dict(id='idle',kind='idle')];c['effects'][-1].update(target='all_allies');c['effects'][-1]['trigger']['timing']=['every:0.2s']
    c=add('caster-down');c['effects'][-1]['trigger']['timing']=['every:0.6s'];c['effects'].append(field('max_hp_pct',25,names[0],'dead-caster-passive'));c['owners'].append(2)
    c['patterns'].insert(0,dict(id='caster-down',kind='attack',delay=.2,spec=dict(atk=1e8,coeff=100,target='slot:3',pierce=True,hits=1)))
    c=add('finite-passive');c['effects'].append(field('max_hp_pct',25,'self','finite-passive',timing='passive',duration=.8));c['owners'].append(0)
    c=add('bullet-passive');c['effects'].append(field('atk_pct',25,'self','bullet-passive',timing='passive',duration_bullets=100));c['owners'].append(0)
    c=add('charge-reset');c['combat']['weapons'][0].update(mode='charge',charge=.5,full_charge_mult=250,capacity=3)
    c=add('restored-max-ammo');c['effects'].append(field('max_ammo_flat',7,'self','extra-ammo',timing='passive'));c['owners'].append(0)
    from calculator import timeline
    role=timeline._NIKKE[names[0]]['class']
    c=add('class-random');c['effects'][-1]['target']='allies_down_class_random:'+role+':1'
    c=add('class-random-self');c['effects'][-1].update(target='allies_down_class_random:'+role+':1');c['effects'][-1]['trigger']['timing']=['event:self_down'];c['owners'][-1]=0
    c=add('class-random-empty');c['effects'][-1]['target']='allies_down_class_random:'+timeline._NIKKE[names[1]]['class']+':1'
    return rows
