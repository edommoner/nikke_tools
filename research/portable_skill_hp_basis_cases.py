"""Literal per-skill HP basis witnesses; no portable packing or expected GPU data."""
import copy
from portable_parts_skill_cases import fixtures as part_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names

def fixtures():
    base=copy.deepcopy(part_fixtures()[0]);base.update(duration=.25,effects=[],owners=[],patterns=[dict(id='idle',kind='idle')],base_atk=[1000]*5,contract={})
    base['enemy']['def']=100
    for target in base['combat']['targets']:target['defense']=100
    for ally in base['environment']['allies']:ally['base_hp']=10000
    rows=[];names=roster_names(base)
    def add(label,mode,expected,maximum=10000,*,pct=None,before=(),before_owners=None,owner=0,stat='damage',timing='battle_start',packets=None):
        c=copy.deepcopy(base);hit=dict(name='parts-source',source='skill-HP',type='damage',stat=stat,fixed_value=100,target='target',trigger=dict(timing=[timing],condition=[]))
        if mode is not None:hit.update(scaling=mode,scaling_hp_pct=pct if pct is not None else 10 if mode=='max_hp_additive' else 5)
        prefix=[field('atk_pct',50,'self','attack-percent'),field('atk_caster_based_pct',10,'self','attack-flat'),field('crit_rate',-100,'self','no-crit')]
        c.update(name='skill-hp-basis-'+label,effects=[*prefix,*copy.deepcopy(before),instant('current_hp_reduce',50,'all_allies','not-current-hp'),hit],owners=[owner]*3+list(before_owners if before_owners is not None else [owner]*len(before))+[0,owner])
        c['contract']=dict(owner=owner,damage=[expected if i==owner else 0 for i in range(5)],packets=list(packets if packets is not None else [expected]),basis_maxima=[] if mode is None else [maximum])
        rows.append(c);return c
    add('ordinary',None,1500)
    for mode in ('max_hp_additive','max_hp_replacement'):
        tag='add' if mode=='max_hp_additive' else 'replace'
        add(tag,mode,2500 if tag=='add' else 400)
        add(tag+'-double-max',mode,3500 if tag=='add' else 900,20000,before=[field('max_hp_only_pct',100,'self','maximum-only')])
        add(tag+'-half-max',mode,2000 if tag=='add' else 150,5000,before=[field('max_hp_only_pct',-50,'self','half-maximum')])
        add(tag+'-zero-percent',mode,1500 if tag=='add' else 1,pct=0)
        c=add(tag+'-caster-hp-flat',mode,2700 if tag=='add' else 500,12000,before=[field('hp_only_caster_based_pct',10,names[0],'caster-hp')],before_owners=[4],timing='every:0.1s');c['effects'][-1]['max_trigger']=1;c['environment']['allies'][4]['base_hp']=20000
        c=add(tag+'-snapshot-hp',mode,3500 if tag=='add' else 900,20000,before=[field('max_hp_from_max_hp_pct',50,names[0],'snapshot-hp')],before_owners=[4],timing='every:0.1s');c['effects'][-1]['max_trigger']=1;c['environment']['allies'][4]['base_hp']=20000
        copy_hp=field('hp_copy',50,'self','copied-hp');copy_hp['copy_from']='allies_top_hp:1'
        c=add(tag+'-copied-hp',mode,3500 if tag=='add' else 900,20000,before=[copy_hp]);c['environment']['allies'][4]['base_hp']=20000
        c=add(tag+'-expiry',mode,6000 if tag=='add' else 1300,20000,before=[field('max_hp_only_pct',100,'self','expires',duration=.15)],timing='every:0.1s',packets=[3500,2500] if tag=='add' else [900,400]);c['contract']['basis_maxima']=[20000,10000]
        c=add(tag+'-two-hits',mode,5000 if tag=='add' else 800,stat='sequential_damage:2',packets=[2500,2500] if tag=='add' else [400,400])
        c=add(tag+'-lifesteal',mode,2500 if tag=='add' else 400,before=[field('lifesteal_pct',100,'self','life')]);c['contract']['hp']=[7500 if tag=='add' else 5400]+[5000]*4
        c=add(tag+'-parts',mode,10000 if tag=='add' else 1600,packets=[2500,3750,3750] if tag=='add' else [400,600,600]);c['effects'][-1]['hits_parts']=True
        c['effects'].insert(-1,field('part_dmg_pct',50,'self','part-factor'));c['owners'].insert(-1,0)
        c['patterns']=copy.deepcopy(part_fixtures()[0]['patterns'])
        c=add(tag+'-deferred',mode,5250 if tag=='add' else 1350,20000,owner=2,stat='bonus_damage',timing='burst_cast',before=[field('max_hp_only_pct',100,'self','full-burst-hp','full_burst_start')])
        c['duration']=.6;c['contract'].update(damage=[0,0,2250,0,0],packets=[2250],basis_maxima=[],reference_model_gap=True)
        for i,w in enumerate(c['combat']['weapons']):w['stage']=[1,2,3,3,3][i]
        c['effects'].insert(0,instant('burst_charge_pct',100,'all_allies','initial-gauge'));c['owners'].insert(0,0)
    c=add('add-flat-grouping','max_hp_additive',4,pct=.03,before=[field('atk_caster_based_pct',-100,names[0],'cancelling-flat')],before_owners=[4],timing='every:0.1s');c['effects'][-1]['max_trigger']=1;c['base_atk']=[1e16,1000,1000,1000,1e16]
    c['effects'][0]['fixed_value']=0;c['effects'][1]['fixed_value']=0;c['enemy']['def']=0
    for target in c['combat']['targets']:target['defense']=0
    c=add('replace-multiply-before-divide','max_hp_replacement',2,pct=.03);c['effects'][-1]['fixed_value']=50;c['enemy']['def']=0
    for target in c['combat']['targets']:target['defense']=0
    c=add('add-callback-snapshot','max_hp_additive',6800,stat='sequential_damage:2',packets=[2500,2500])
    hp_child=field('max_hp_only_pct',100,'self','hp-child','hit_count:parts-source:1')
    child=dict(name='nested-hit',source='nested',type='damage',stat='damage',fixed_value=100,target='target',scaling='max_hp_replacement',scaling_hp_pct=5,trigger=dict(timing=['hit_count:parts-source:1'],condition=[]))
    c['effects'][3:3]=[hp_child,child];c['owners'][3:3]=[0,0]
    return rows
