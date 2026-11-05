"""Additional range/accounting and delayed-packet CPU contracts."""
import copy
from portable_parts_skill_cases import fixtures as originals
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field


def fixtures():
    base=next(c for c in originals() if c['name']=='parts-skill-true');rows=[]
    def add(label,packets,parts,*,damage=8000,interrupt=0,notices=1):
        c=copy.deepcopy(base);c['name']='parts-skill-extra-'+label;c['observe_parts_accounting']=True
        c['contract'].update(packet_damage=packets,packet_parts=parts,damage=[damage,0,0,0,0],interrupt_damage=[interrupt,0,0,0,0],named_hit_notices=notices,event_kinds=['named-hit']*notices+['packet']*len(packets))
        rows.append(c);return c
    def interrupts(c,far=False):
        targets=[dict(name='stop-near',hp=1e8,reach=1)]
        if far:targets.append(dict(name='stop-far',hp=1e8,reach=4))
        c['patterns'].append(dict(id='interrupt',kind='interrupt',targets=targets))
    c=add('pierce-parts',[2000,3000,3000,2000],['','near','far',''],interrupt=2000);c['effects'][-1]['stat']='pierce_damage';interrupts(c)
    c=add('explosion-parts',[2000,3000,3000,2000],['','near','far',''],interrupt=2000);c['effects'][-1]['stat']='projectile_explosion_damage';interrupts(c,True)
    c=add('explosion-range100',[2000,3000,3000,2000,2000],['','near','far','',''],interrupt=4000);c['effects'][-1]['stat']='projectile_explosion_damage';interrupts(c,True)
    c['effects'].insert(-1,field('explosion_range',100,'self','wide'));c['owners'].insert(-1,0)
    c=add('explosion-without-marker',[2000,3000,2000],['','near',''],damage=5000,interrupt=2000);c['effects'][-1].update(stat='projectile_explosion_damage',hits_parts=False);interrupts(c,True)
    c=add('adds-outside-body-total',[2000,3000,3000,2000],['','near','far','']);c['patterns'].append(dict(id='adds',kind='summon',spec=dict(count=1,hp=1e8)))
    c=add('periodic-three-ticks',[2000,3000,3000]*3,['','near','far']*3,damage=24000,notices=3)
    c['effects'][-1].update(stat='dot_damage',duration=.21,tick_interval=.1,tick_start='immediate')
    c['contract']['event_kinds']=(['named-hit']+['packet']*3)*3
    # Legacy _fire_pending_burst_dmg constructs plain HitEvent values without
    # _reach_hit or named-hit notify. Record this as a model gap, never a proof
    # that pending part-inclusive effects have their intended semantics.
    c=add('deferred-burst3-reference-gap',[3000],[''],damage=3000,notices=0)
    c['contract'].update(reference_model_gap=True,packet_reach=[(0,0,0,0)],pending=dict(count=0,enqueued=1,fired=1))
    c['duration']=3;c['observe_pending_skills']=True;c['effects'][-1]['trigger']['timing']=['burst_cast']
    c['effects'].insert(0,instant('burst_charge_pct',100,'all_allies','initial-gauge'));c['owners'].insert(0,0)
    for i,weapon in enumerate(c['combat']['weapons']):weapon['stage']=[3,1,2,3,3][i]
    # Non-saturating HP makes missing or duplicated part/interrupt healing visible.
    c=add('lifesteal-unsaturated',[2000,3000,3000],['','near','far'])
    c['effects'].insert(0,instant('current_hp_reduce',50,'all_allies','drain'));c['owners'].insert(0,0)
    c['effects'].insert(-1,field('lifesteal_pct',10,'self','lifesteal'));c['owners'].insert(-1,0)
    c['contract']['hp']=[5800,5000,5000,5000,5000]
    c=add('interrupt-lifesteal-unsaturated',[2000,3000,3000,2000],['','near','far',''],interrupt=2000)
    c['effects'][-1]['stat']='pierce_damage';interrupts(c)
    c['effects'].insert(0,instant('current_hp_reduce',50,'all_allies','drain'));c['owners'].insert(0,0)
    c['effects'].insert(-1,field('lifesteal_pct',10,'self','lifesteal'));c['owners'].insert(-1,0)
    c['contract']['hp']=[6000,5000,5000,5000,5000]
    c=add('shared-lifesteal-unsaturated',[2000,3000,3000],['','near','far'])
    c['effects'].insert(0,instant('current_hp_reduce',50,'all_allies','drain'));c['owners'].insert(0,0)
    for effect in (field('lifesteal_pct',10,'self','lifesteal'),field('heal_split',1,'all_allies','share')):
        c['effects'].insert(-1,effect);c['owners'].insert(-1,0)
    c['contract']['hp']=[5160]*5
    return rows
