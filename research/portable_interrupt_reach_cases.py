"""Authored interrupt snapshot, destruction, periodic and healing contracts."""
import copy
from portable_parts_skill_extra_cases import fixtures as originals
from world_enemy_attack_cases import field

def fixtures():
    seed=next(c for c in originals() if c['name']=='parts-skill-extra-interrupt-lifesteal-unsaturated');rows=[]
    def add(name):
        c=copy.deepcopy(seed);c['name']='interrupt-reach-'+name;rows.append(c);return c
    c=add('heal-child-snapshot')
    c['effects'].insert(-1,field('intercept_dmg_pct',100,'self','intercept-after-heal',timing='event:heal_received'));c['owners'].insert(-1,0)
    c=add('named-child-snapshot')
    c['effects'].insert(-1,field('intercept_dmg_pct',100,'self','intercept-after-named',timing='hit_count:parts-source:1'));c['owners'].insert(-1,0)
    c['effects'][-1]['trigger']['timing']=['battle_start','every:0.2s']
    c['contract'].update(packet_damage=[2000,3000,3000,2000,2000,3000,3000,4000],packet_parts=['','near','far','']*2,damage=[16000,0,0,0,0],interrupt_damage=[6000,0,0,0,0],named_hit_notices=2,event_kinds=(['named-hit']+['packet']*4)*2,hp=[7200,5000,5000,5000,5000])
    c=add('destroy-group')
    c['patterns'][-1]['targets']=[dict(name='stop-a',hp=1,score=7,reach=1),dict(name='stop-b',hp=1,score=9,reach=1)]
    c['contract'].update(packet_damage=[2000,3000,3000,2000,2000],packet_parts=['','near','far','',''],interrupt_damage=[4000,0,0,0,0],event_kinds=['named-hit']+['packet']*5,hp=[6200,5000,5000,5000,5000])
    c=add('unbreakable');c['patterns'][-1]['targets'][0]['hp']=0
    c=add('periodic-three-ticks')
    c['effects'][-1].update(duration=.21,tick_interval=.1,tick_start='immediate')
    c['contract'].update(packet_damage=[2000,3000,3000,2000]*3,packet_parts=['','near','far','']*3,damage=[24000,0,0,0,0],interrupt_damage=[6000,0,0,0,0],named_hit_notices=3,event_kinds=(['named-hit']+['packet']*4)*3,hp=[8000,5000,5000,5000,5000])
    c=add('shared-lifesteal')
    c['effects'].insert(-1,field('heal_split',1,'all_allies','interrupt-share'));c['owners'].insert(-1,0)
    c['contract']['hp']=[5200]*5
    return rows
