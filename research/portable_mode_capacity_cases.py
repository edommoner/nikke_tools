"""Literal mode magazine reference stimuli; never pack or simulate on import."""
import copy
from portable_entry_reload_cases import fixtures as entry_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field

REF='mode-magazine-reference'
def gauge(value,*,owner=0,timing='battle_start',name='reference-charge',**kw):
    e=instant('gauge_charge',value,'self',name,timing);e.update(gauge_id=REF,gauge_max=100,**kw);return e

def fixtures():
    base=copy.deepcopy(entry_fixtures()[0]);base.update(duration=.75,effects=[],owners=[],controls=[{} for _ in range(5)])
    for w in base['combat']['weapons']:w.update(capacity=5,interval=.2,reload=.3)
    mode=copy.deepcopy(entry_fixtures()[0]['effects'][-1]);mode.update(name='reference-mode',entry_reload=False,max_ammo=2,duration_bullets=2,reload_time=.3,max_ammo_scaling_ref=REF)
    rows=[]
    def add(label,capacity,shots,*,before=(),before_owners=None,owner=0,changes=None,refs=2,exit_time=None):
        c=copy.deepcopy(base);m=copy.deepcopy(mode);m.update(changes or {})
        c.update(name='mode-capacity-'+label,effects=[*copy.deepcopy(before),m],owners=list(before_owners if before_owners is not None else [owner]*len(before))+[owner])
        c['contract']=dict(owner=owner,capacities=capacity,mode_shots=shots,mode_packets=shots*m.get('pellets',1)*m.get('muzzles',1),ref_calls=refs,exit_time=0 if exit_time==0 else None,exit_count=0 if exit_time is None else 2 if label=='reentry-refresh' else 1);rows.append(c);return c
    add('missing',[2],2,exit_time=.1)
    add('gauge-zero',[0],0,before=[gauge(0)],exit_time=0)
    add('gauge-one',[2],2,before=[gauge(1)],exit_time=.1)
    add('gauge-three',[6],6,before=[gauge(3)],exit_time=.5)
    add('fraction-truncates',[4],4,before=[gauge(2.9)],exit_time=.3)
    for enabled in (False,True):
        add('ignores-buffs-'+str(enabled),[6],6,before=[gauge(3),field('max_ammo_pct',100,'self','ammo-percent'),field('max_ammo_flat',3,'self','ammo-flat')],changes=dict(max_ammo_buff_applies=enabled),exit_time=.5)
    consume=instant('gauge_consume',1,'self','reference-consume','on_attack');consume['gauge_id']=REF
    add('latched-after-consume',[6],6,before=[gauge(3),consume],exit_time=.5)
    grow=gauge(1,timing='every:0.15s',name='reference-grow',max_trigger=1)
    c=add('reload-resamples',[2,4],6,before=[gauge(1),grow],refs=3);c['duration']=.9;c['effects'][-1].pop('duration_bullets')
    add('entry-delay-resamples',[2,4],4,before=[gauge(1),gauge(1,timing='every:0.1s',name='grow-before-entry',max_trigger=1)],changes=dict(entry_reload=True),exit_time=.6)
    stack=field('atk_pct',0,'self',REF,max_stack=3);stack['trigger']['timing']*=3
    add('named-stack',[6],6,before=[stack],exit_time=.5)
    add('gauge-zero-shadows-stack',[0],0,before=[stack,gauge(0)],exit_time=0)
    add('owner-local',[2],2,before=[gauge(3)],before_owners=[0],owner=4,exit_time=.1)
    c=add('reentry-refresh',[2,4],6,before=[gauge(1),gauge(1,timing='every:0.3s',max_trigger=1,name='grow-before-reentry')],changes=dict(trigger=dict(timing=['battle_start','every:0.4s'],condition=[]),max_trigger=2),refs=3,exit_time=.7)
    add('zero-infinite-ammo',[0],1,before=[gauge(0),field('infinite_ammo',0,'self','infinite')],exit_time=0)
    add('zero-charge',[0],0,before=[gauge(0)],changes=dict(charge=True,weapon_type='SR'),exit_time=0)
    add('bullet-limit-prevents-reload',[2],2,before=[gauge(1),grow],changes=dict(duration_bullets=99))
    source=instant('periodic_source_refresh',0,'self','source-refresh');source.pop('fixed_value');source['periodic_source']=dict(name=REF,slots=[10,10,10],base_interval=1,population_reduction_pct=0)
    add('source-count',[6],6,before=[source],exit_time=.5)
    add('source-shadows-stack',[6],6,before=[stack,source],exit_time=.5)
    add('gauge-zero-shadows-source',[0],0,before=[source,gauge(0)],exit_time=0)
    short=copy.deepcopy(source);short['periodic_source']['slots']=[.1,.1,.1]
    add('source-expires-after-snapshot',[6],6,before=[short],exit_time=.5)
    add('expired-source-not-missing',[6,0],0,before=[stack,short],changes=dict(entry_reload=True),exit_time=.3)
    c=add('persistent-zero-reloads',[0,6],6,before=[gauge(0),gauge(3,timing='every:0.1s',max_trigger=1,name='zero-grow')],refs=3);c['duration']=.9;c['effects'][-1].pop('duration_bullets')
    add('sentinel-ignores-reference',[5],2,changes=dict(max_ammo=-1),refs=0,exit_time=.1)
    c=add('positive-charge',[6],6,before=[gauge(3)],changes=dict(charge=True,weapon_type='SR'),exit_time=1.5);c['duration']=1.6
    add('scatter-two-muzzles',[6],6,before=[gauge(3)],changes=dict(weapon_type='SG',pellets=3,muzzles=2),exit_time=.5)
    refill=instant('ammo_charge_pct',100,'self','instant-refill','on_attack')
    add('instant-refill-latched',[6],6,before=[gauge(3),consume,refill],exit_time=.5)
    remove=instant('ammo_charge_pct',-100,'self','instant-remove','on_attack');remove['max_trigger']=1
    add('instant-remove-latched',[6],1,before=[gauge(3),consume,remove])
    child_refill=instant('ammo_charge_pct',50,'self','preentry-refill','event:reference-mode')
    child_consume=instant('gauge_consume',1,'self','preentry-consume','event:reference-mode');child_consume['gauge_id']=REF
    add('instant-before-entry-reset',[2,0],0,before=[gauge(1),child_refill,child_consume],exit_time=0)
    return rows
