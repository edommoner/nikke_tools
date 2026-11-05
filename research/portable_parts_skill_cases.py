"""Literal hits_parts stimuli; no portable packing or GPU-derived state."""
import copy
from portable_heal_share_cases import fixtures as healing_fixtures
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant


def fixtures():
    base=copy.deepcopy(healing_fixtures()[0]);base.update(duration=.25,effects=[],owners=[],contract={})
    base['enemy']['def']=0
    for weapon in base['combat']['weapons']:weapon.update(mode='charge',charge=10,interval=10,min_cycle=10,full_charge_mult=100)
    parts=dict(id='parts',kind='parts',targets=[dict(name='near',hp=1e8,reach=1),dict(name='far',hp=1e8,reach=5)])
    interrupt=dict(id='interrupt',kind='interrupt',targets=[dict(name='stop',hp=1e8,reach=1)])
    rows=[]
    def add(label,*,marker=True,patterns=None,damage=8000,packets=(2000,3000,3000),part_names=('', 'near','far'),notices=1,stat='bonus_damage'):
        c=copy.deepcopy(base);c['name']='parts-skill-'+label
        c['patterns']=copy.deepcopy([parts] if patterns is None else patterns)
        if not c['patterns']:c['patterns']=[dict(id='idle',kind='idle')]
        hit=dict(name='parts-source',source='스킬2',type='damage',stat=stat,fixed_value=100,target='all_enemies',trigger=dict(timing=['battle_start'],condition=[]))
        if marker is not None:hit['hits_parts']=marker
        c['effects']=[field('crit_rate',-100,'self','no-crit'),field('part_dmg_pct',50,'self','part-factor'),hit]
        c['owners']=[0]*len(c['effects']);c['contract']=dict(damage=[damage,0,0,0,0],packet_damage=list(packets),packet_parts=list(part_names),named_hit_notices=notices,event_kinds=['named-hit']*notices+['packet']*len(packets),gauge=0)
        rows.append(c);return c
    add('absent',marker=None,damage=2000,packets=[2000],part_names=[''])
    add('false',marker=False,damage=2000,packets=[2000],part_names=[''])
    add('true')
    c=add('static-only',patterns=[],damage=3000,packets=[3000],part_names=['']);c['enemy']['has_parts']=True
    c=add('static-false',marker=False,patterns=[],damage=2000,packets=[2000],part_names=['']);c['enemy']['has_parts']=True
    add('no-parts',patterns=[],damage=2000,packets=[2000],part_names=[''])
    c=add('unbreakable-part');c['patterns'][0]['targets'][0]['hp']=0
    c=add('interrupt-only',patterns=[interrupt],damage=2000,packets=[2000],part_names=['']);c['observe_parts_accounting']=True
    c['contract'].update(interrupt_damage=[0]*5,packet_times=[0],packet_reach=[(0,0,0,0)])
    c=add('parts-and-interrupt',patterns=[parts,interrupt]);c['observe_parts_accounting']=True
    c['contract'].update(interrupt_damage=[0]*5,packet_times=[0]*3,packet_reach=[(5,3000,0,0),(0,0,0,0),(0,0,0,0)])
    add('two-hits',stat='bonus_damage:2',damage=16000,packets=[2000,3000,3000]*2,part_names=['','near','far']*2,notices=2)
    add('burst',stat='burst_damage')
    add('armor-burst',stat='armor_break_burst_damage')
    c=add('lifesteal');c['effects'].insert(0,instant('current_hp_reduce',50,'all_allies','drain'));c['owners'].insert(0,0)
    c['effects'].insert(-1,field('lifesteal_pct',100,'self','lifesteal'));c['owners'].insert(-1,0);c['contract']['hp']=[10000,5000,5000,5000,5000]
    c=add('destroy-before-second',damage=10000,packets=[2000,3000,3000,2000],part_names=['','near','far',''],notices=2)
    for part in c['patterns'][0]['targets']:part['hp']=1
    c['effects'][-1]['trigger']['timing']=['battle_start','every:0.2s']
    c['contract']['event_kinds']=['named-hit']+['packet']*3+['named-hit','packet']
    c=add('static-basis-after-destroy',damage=11000,packets=[2000,3000,3000,3000],part_names=['','near','far',''],notices=2)
    c['enemy']['has_parts']=True
    for part in c['patterns'][0]['targets']:part['hp']=1
    c['effects'][-1]['trigger']['timing']=['battle_start','every:0.2s']
    c['contract']['event_kinds']=['named-hit']+['packet']*3+['named-hit','packet']
    return rows
