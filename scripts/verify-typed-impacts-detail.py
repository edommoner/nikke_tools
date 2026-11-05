"""Typed transport witnesses plus independently simulated existing squad paths."""
import argparse,hashlib,importlib.util,json,math,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from calculator.buff_manager import BuffManager
from effect_runtime import state
from impact_specs import ActorHandle,Impact,ImpactTrace,impact_command
from resource_frame_capture import FrameCapture
import detail_gpu as g
spec=importlib.util.spec_from_file_location('impact_gauge_oracle',ROOT/'scripts/verify-gauge-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)




def scenarios():
    body=body_for(v.NAMES,8,True);body.update(seed=12345,burst_gauge_mode='fixed',_debug_impact_frames=True)
    body['enemy']['core_px']=10000
    yield 'existing-grown-squad-all-core',body,None
    names=['슈가']+v.NAMES[:4]
    body=body_for(names,8,True);body.update(seed=12345,burst_gauge_mode='fixed',_debug_impact_frames=True)
    body['enemy']['core_px']=10000
    body['enemy']['parts']=[dict(name='left',hp=0,reach=1),dict(name='right',hp=7000000,reach=1)]
    E=v.effect
    effects={names[0]:[
        E('piercing weapons','buff','pierce_enabled',1,'all_allies'),
        E('damage over time','damage','dot_damage',50,'target',tick_interval=.25,duration=7,hits_parts=True),
        E('sequential landing','damage','sequential_damage:3',150,'target',event='burst_cast',land_in_full_burst=True,hits_parts=True),
        E('named direct hit','damage','damage',75,'target',event='on_attack',hits_parts=True),
        E('drain','instant','current_hp_reduce',50),E('heal from landed hits','buff','lifesteal_pct',25)]}
    yield 'shotgun-skill-dot-body-parts-and-recovery',body,effects





if __name__=='__main__':main()
