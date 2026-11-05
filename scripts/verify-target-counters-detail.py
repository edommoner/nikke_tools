"""Shared target-counter quantities and real autonomous landing integration."""
import argparse,copy,hashlib,importlib.util,json,math,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a,body_for
from calculator.buff_manager import BuffManager
from effect_runtime import state,pool
from impact_specs import ActorHandle,Impact,impact_command
from target_counter_cases import clone_cases,marker
from resource_frame_capture import FrameCapture
import detail_gpu as g

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
v=load('counter_gauge_oracle','scripts/verify-gauge-detail.py')
cpu=load('counter_cpu_table','tests/test_target_counter_runtime.py')


def scenarios():
    E=v.effect
    name='body progress';m=marker(name,30);m['trigger']['timing']=['battle_start','every:0.5s']
    effects={v.NAMES[0]:[m,E('completion ATK','buff','atk_pct',15,'all_allies',event='event:target_counter_complete:'+name,duration=.4),
        E('completion resource','instant','gauge_charge',1,event='event:target_counter_complete:'+name,gauge_id='captures',gauge_max=100),
        E('retirement crit','buff','crit_dmg',7,'all_allies',event='event:state_end:'+name,duration=.2),
        E('counted periodic damage','damage','dot_damage',25,'target',tick_interval=.2,duration=8)]}
    body=body_for(v.NAMES,8,True);body.update(seed=12345,burst_gauge_mode='fixed',_debug_impact_frames=True,_debug_target_counter_frames={'who':0})
    yield 'autonomous-body-hits-refresh-and-effect-order',body,effects
    names=['슈가']+v.NAMES[:4];name='part progress'
    m=marker(name,1000000000,actor=dict(kind='part',identity=0,generation=1));m['trigger']['timing']=['battle_start']
    effects={names[0]:[m,E('piercing weapons','buff','pierce_enabled',1,'all_allies'),
        E('drain','instant','current_hp_reduce',50,'all_allies'),E('landed recovery','buff','lifesteal_pct',25,'all_allies'),
        E('death ATK','buff','atk_pct',25,'all_allies',event='event:target_counter_complete:'+name,duration=5),
        E('death before landed healing','buff','heal_received_pct',50,'all_allies',event='event:target_counter_complete:'+name,duration=3)]}
    body=body_for(names,8,True);body.update(seed=12345,burst_gauge_mode='fixed',_debug_impact_frames=True,_debug_target_counter_frames={'who':0})
    body['enemy']['parts']=[dict(name='fragile',hp=100000,reach=1),dict(name='solid',hp=0,reach=1)]
    yield 'autonomous-part-death-before-lifesteal',body,effects

def raw_scenarios():
    owner='일레그 : 붐 앤 쇼크'
    body=body_for(['N102','크라운','앨리스','모더니아',owner],90,True)
    body['enemy']['code']='작열'
    body.update(seed=12345,burst_gauge_mode='fixed',_debug_target_counter_frames={'who':4})
    yield 'raw-capture-to-cap-and-overflow',body,{}
    body=body_for(['N102','크라운',owner,'앨리스','모더니아'],8,True)
    body['enemy']['code']='작열'
    body.update(seed=12345,burst_gauge_mode='fixed',_debug_target_counter_frames={'who':2})
    yield 'raw-in-burst-six-hit-consumption-floor',body,{}
    yield 'raw-in-burst-thirteen-hit-at-initial-cap',body,{owner:[v.effect('authored initial resource','instant','gauge_charge',13,gauge_id='유령',gauge_max=13)]}

def additive_effects(extra):
    from contextlib import contextmanager
    @contextmanager
    def apply():
        original=BuffManager.char_effects
        def effects(manager,name):return original(manager,name)+copy.deepcopy(extra.get(name,[]))
        with patch.object(BuffManager,'char_effects',effects):yield
    return apply()



if __name__=='__main__':main()
