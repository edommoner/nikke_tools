"""Literal coordinate DoT lifetime, modifier and family contracts."""
import copy
from portable_coordinate_skill_cases import fixtures as originals
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

def fixtures():
    base=copy.deepcopy(originals()[2]);rows=[]
    def add(label,ticks,*,part_ticks=None,body=2000,part=3000):
        c=copy.deepcopy(base);c['name']='coordinate-dot/'+label;c['coordinate_packet_trace']=True;c['observe_periodic_skills']=True;c['coordinate_sources']=['parts-source']
        c['effects'][-1].update(stat='dot_damage',duration=.21,tick_interval=.1,tick_start='immediate')
        selected=part_ticks if part_ticks is not None else [['near','far'] for _ in range(ticks)]
        packets=[item for names in selected for item in [('',body)]+[(name,part) for name in names]]
        c['contract'].update(packets=packets,selected=selected,damage=[sum(v for _,v in packets),0,0,0,0],notices=ticks,event_kinds=[kind for names in selected for kind in ['named-hit']+['packet']*(1+len(names))],geometry=[['stop','near','far']]*ticks)
        rows.append(c);return c
    add('immediate-three-ticks',3)
    c=add('delayed-start',2);c['effects'][-1].pop('tick_start')
    c=add('parts-expire-before-second',3,part_ticks=[['near','far'],[],[]]);c['patterns'][0]['until']=dict(time=.1);c['contract']['geometry']=[['stop','near','far'],['stop'],['stop']]
    c=add('destroyed-before-second',3,part_ticks=[['near','far'],[],[]]);c['contract']['geometry']=[['stop','near','far'],['stop'],['stop']]
    for t in c['patterns'][0]['targets']:t['hp']=1
    c=add('reopened-generation-two',3,part_ticks=[['near','far'],['near','far'],[]]);c['patterns'][0].update(until=dict(targets_cleared=True),after=['start','parts'],repeat=2);c['contract']['geometry']=[['stop','near','far'],['stop','near','far'],['stop']]
    for t in c['patterns'][0]['targets']:t['hp']=1
    c=add('unbreakable-reverse-depth',3,part_ticks=[['far','near']]*3);c['patterns'][0]['targets'][1]['z']=4;c['contract']['geometry']=[['far','stop','near']]*3
    for t in c['patterns'][0]['targets']:t['hp']=0
    c=add('dot-family-counter-and-lifesteal',3)
    c['effects'].insert(0,instant('current_hp_reduce',50,'self','drain'));c['owners'].insert(0,0)
    c['effects'].insert(-1,field('lifesteal_pct',10,'self','lifesteal'));c['owners'].insert(-1,0)
    from target_counter_cases import marker
    e=marker('coordinate-dot-counter',2,actor=dict(kind='part',identity=0,generation=1),families=['dot']);e['target']='boss';e['trigger']['timing']=['battle_start'];c['effects'].insert(-1,e);c['owners'].insert(-1,0)
    c['contract'].update(hp=[7400,10000,10000,10000,10000],dot_counter=True)
    c=add('birth-after-created-final-tick',3,part_ticks=[[],[],['near','far']]);c['patterns'][0]['delay']=.21;c['contract']['geometry']=[['stop'],['stop'],['stop','near','far']]
    c=add('dot-layer-ordered-part-product',3,body=6000,part=7000);c['effects'].insert(-1,field('dot_dmg_pct',200,'self','dot-factor'));c['owners'].insert(-1,0)
    return rows
