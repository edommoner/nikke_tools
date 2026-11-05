"""Independent CPU/GPU live boss lifecycle, scalar frames and full squads."""
import argparse,copy,hashlib,importlib.util,json,random,sys,ast,inspect,textwrap
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
import detail_gpu as g
from detail_boss import WEAPONS
from calculator.boss_pattern import BossScript
def load(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
t=load('boss_clock_team','scripts/verify-team-hits-detail.py')
E=t.E
NAMES=['리타','크라운','모더니아','앨리스','N102']
def pattern(id,kind,at=0,duration=None,**kw):
    return dict(id=id,kind=kind,delay=at,**({'until':{'time':duration}} if duration is not None else {}),**kw)
def worlds():
    yield 'startup-core',[pattern('core','core',0,2,core_px=6)],{}
    yield 'delayed-repeating-core',[pattern('core','core',.7,1.1,core_px=6,after=['start','core'],repeat=0)],{}
    yield 'overlapping-distance',[pattern('near','move',1,4,distance=5),pattern('far','move',2,1,distance=80)],{}
    yield 'start-order-not-declaration',[pattern('late','move',3,4,distance=60),pattern('early','move',1,6,distance=5)],{}
    yield 'same-start-last-move-wins',[pattern('a','move',1,4,distance=5),pattern('b','move',1,2,distance=80)],{}
    yield 'core-max-and-restore',[pattern('low','core',0,3,core_px=3),pattern('high','core',1,1,core_px=9)],{'core_px':1}
    yield 'filtered-parent',[pattern('wait','idle',.2,.7),pattern('core','core',.1,.5,core_px=6,after=[{'node':'wait','outcome':'expired'}])],{}
    yield 'followed-beats-expired',[pattern('a','idle',0,1),dict(id='b',kind='core',core_px=6,until={'time':1,'after':[{'node':'a'}]}),pattern('far','move',0,2,distance=80,after=[{'node':'b','outcome':'followed'}])],{}
    yield 'until-after-consumes-old-ends',[pattern('a','idle',.1,.4,after=['start','a'],repeat=0),dict(id='b',kind='core',core_px=6,after=['a'],repeat=0,until={'after':[{'node':'a','delay':.2}]})],{}
    yield 'or-links-consume-all',[pattern('a','idle',0,1),pattern('b','groggy',0,1),pattern('core','core',0,.25,core_px=6,after=['a','b'],repeat=0)],{}
    yield 'repeat-limit',[pattern('core','core',.05,.3,core_px=6,after=['start','core'],repeat=2)],{}
    events=['event:part_destroy','event:target_spawn','event:projectile_destroy','enemy_death']
    yield 'all-emissions',[pattern('core','core',0,.7,core_px=6,after=['start','core'],repeat=3,emit=events,emit_end=list(reversed(events)))],{}
    yield 'epsilon-lifecycle',[pattern('tiny','core',0,1e-12,core_px=6,after=['start','tiny'],repeat=2)],{}
    yield 'weapon-lists-and-mode',[pattern('mg','move',.2,1,weapons=['MG']),pattern('smg','move',2,8,weapons=['SMG'])],{'distance':None,'optimal_range_weapons':['SR']}
    yield 'distance-during-mode',[pattern('mode-range','move',2,7,distance=5),pattern('far','move',4,2,distance=80)],{}
    yield 'parts-carry-and-phase-events',[pattern('core','core',0,.2,core_px=6,emit=['event:target_spawn'],emit_end=['event:part_destroy'])],{'parts':[dict(name='armor',hp=0,reach=1),dict(name='cannon',hp=100000,reach=1)]}
    yield 'never-opens',[pattern('future','core',100,2,core_px=6)],{}
    yield 'indefinite-end',[pattern('core','core',.4,None,core_px=6)],{}
def fixtures(quick=False,long=False):
    selected=list(worlds())
    if quick:selected=[selected[i] for i in (0,1,3,7,8,11,13,15)]
    if long:selected=[selected[i] for i in (1,8,13,15)]
    for name,patterns,enemy in selected:
        body=body_for(NAMES,180 if long else 12,True)
        body.update(seed=12345,burst_policy='auto',shooting_policy='character',burst_gauge_mode='accumulate',_debug_random_state=True,_debug_boss_frames=True)
        body['enemy'].update({'core_px':0,'distance':30,'patterns':patterns,**enemy})
        probes=[E('startup core witness','buff','atk_pct',11,event='battle_start',condition=['core_hit'],duration=2),E('live range witness','buff','atk_pct',7,event='on_attack',condition=['optimal_range'],duration=.2)]
        for event in ('event:part_destroy','event:target_spawn','event:projectile_destroy','enemy_death'):
            probes.append(E('pulse '+event,'buff','crit_dmg',1,event=event,max_stack=100))
        yield name,body,{NAMES[0]:probes}
    for gauge in ('fixed','accumulate'):
        if long and gauge=='fixed':continue
        names=['D : 킬러 와이프','루마니','크라운','베스티','앨리스']
        body=body_for(names,180 if long else 20,True)
        body.update(seed=12345,burst_policy='rules',shooting_policy='character',burst_gauge_mode=gauge,_debug_random_state=True,_debug_boss_frames=True)
        body['enemy'].update(core_px=0,distance=30,patterns=[pattern('core','core',.7,1.1,core_px=6,after=['start','core'],repeat=0),pattern('near','move',2,3,distance=5)],parts=[dict(name='armor',hp=200000,reach=1),dict(name='cannon',hp=100000,reach=1)])
        yield 'real-team-hits-'+gauge,body,{}
