"""Literal coordinate worlds and independent skill accounting expectations."""
import copy
from portable_parts_skill_cases import fixtures as original_cases
from world_enemy_attack_cases import field

def fixtures():
    base=copy.deepcopy(next(c for c in original_cases() if c['name']=='parts-skill-true'))
    base['enemy']['coord']=dict(auto_aim=[0,0],pierce_px=10,explosion_scale=.1)
    base['weapon_metadata']['spot_explosion_range']=100
    base['observe_parts_accounting']=True
    base['patterns']=[dict(id='parts',kind='parts',targets=[dict(name='near',hp=1e8,x=0,y=0,r=2,z=2),dict(name='far',hp=1e8,x=30,y=0,w=10,h=10,rotation=45,z=1)]),dict(id='interrupt',kind='interrupt',targets=[dict(name='stop',hp=1e8,x=0,y=0,r=1,z=3)])]
    rows=[]
    def add(label,marker,stat='bonus_damage',wide=False,reverse=False):
        c=copy.deepcopy(base);c['name']='coordinate-skill/'+label
        e=c['effects'][-1];e['stat']=stat
        if marker is None:e.pop('hits_parts',None)
        else:e['hits_parts']=marker
        if wide:c['effects'].insert(-1,field('pierce_range' if stat=='pierce_damage' else 'explosion_range',200,'self','range'));c['owners'].insert(-1,0)
        order=['near','far']
        if reverse:c['patterns'][0]['targets'][1]['z']=4;order.reverse()
        selected=order if marker else ([n for n in (['far','stop','near'] if reverse else ['stop','near','far']) if n!='far' or wide] if stat!='bonus_damage' else [])
        packets=[('',2000)]+[(n,2000 if n=='stop' else 3000) for n in selected]
        c['contract']=dict(event_kinds=['named-hit']+['packet']*len(packets),packets=packets,selected=[selected],damage=[2000+3000*sum(n!='stop' for n in selected),0,0,0,0],interrupt=[2000*int('stop' in selected),0,0,0,0],notices=1,geometry=[(['far','stop','near'] if reverse else ['stop','near','far'])],marker=marker)
        rows.append(c);return c
    for reverse in (False,True):
        for marker in (None,False,True):add(f'plain/{reverse}/{marker}',marker,reverse=reverse)
        for stat in ('pierce_damage','projectile_explosion_damage'):
            for marker in (False,True):
                for wide in (False,True):add(f'{stat}/{reverse}/{marker}/{wide}',marker,stat,wide,reverse)
    c=add('destroy-before-second',True);c['effects'][-1]['trigger']['timing']=['battle_start','every:0.2s']
    for target in c['patterns'][0]['targets']:target['hp']=1
    c['contract'].update(packets=[('',2000),('near',3000),('far',3000),('',2000)],selected=[['near','far'],[]],event_kinds=['named-hit']+['packet']*3+['named-hit','packet'],damage=[10000,0,0,0,0],notices=2,geometry=[['stop','near','far'],['stop']])
    c=add('unbreakable-second',True);c['effects'][-1]['trigger']['timing']=['battle_start','every:0.2s']
    for target in c['patterns'][0]['targets']:target['hp']=0
    c['contract'].update(packets=[('',2000),('near',3000),('far',3000)]*2,selected=[['near','far']]*2,event_kinds=(['named-hit']+['packet']*3)*2,damage=[16000,0,0,0,0],notices=2,geometry=[['stop','near','far']]*2)
    c=add('same-cast-retired-packets',True);c['effects'][-1]['stat']='bonus_damage:2'
    for target in c['patterns'][0]['targets']:target['hp']=1
    c['contract'].update(packets=[('',2000),('near',3000),('far',3000)]*2,selected=[['near','far']]*2,event_kinds=['named-hit']*2+['packet']*6,damage=[16000,0,0,0,0],notices=2,geometry=[['stop','near','far']]*2,retired_same_cast=True)
    assert len(rows)==25
    return rows
