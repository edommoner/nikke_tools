"""GPU decides reloads from its state; no CPU-selected times feed its inputs."""
import argparse,copy,hashlib,importlib.util,json,math,sys,time
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a,body_for
from test_weapon_mode_specs import effect,mode,NAMES
from calculator.buff_manager import BuffManager
from calculator.timeline import CharState
import detail_gpu as g
spec=importlib.util.spec_from_file_location('mode_input_legacy',ROOT/'scripts/verify-modes-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def cases():
    for flag,conditional,ready in ((True,True,True),(False,True,True),(True,True,False),(True,False,True)):
        body=body_for(NAMES,2,True);body.update(weapon_mode_swap=flag,seed=12345,burst_gauge_mode='fixed')
        es=[effect('reload duration','buff','reload_time_fixed',.5,'battle_start',duration=-1),
            mode(event='event:full_reload',duration=.6,charge_time=.2,full_charge_mult=100),
            effect('off core','buff','core_dmg_pct',10,'battle_start',duration=-1),
            effect('on core','buff','core_dmg_pct',10,'event:mode',duration=-1),
            effect('clear on core','instant','remove_named_buff',0,'event:state_end:mode',target_effect='on core'),
            effect('equivalent','instant','squad_ammo_consume_as',40,'full_charge_fire')]
        es[1]['trigger']['condition']=['self_state:ready'] if conditional else []
        if ready:es.insert(0,effect('ready','buff','',0,'battle_start',duration=-1))
        yield 'conditional-mode-'+''.join(str(int(i)) for i in (flag,conditional,ready)),body,{NAMES[0]:es},NAMES[0],bool(flag and conditional and ready),10
    name='신데렐라 : 크리스탈 웨이브'
    for flag,gauge,parts in ((True,'fixed',False),(True,'accumulate',False),(False,'fixed',False),(True,'fixed',True)):
        body=body_for([name,'리타','크라운','앨리스','모더니아'],45,True);body.update(weapon_mode_swap=flag,seed=12345,burst_gauge_mode=gauge)
        if parts:body['enemy']['parts']=[dict(name='left',hp=0,reach=1),dict(name='right',hp=0,reach=3)]
        yield 'raw-mode-'+str(int(flag))+'-'+gauge+('-parts' if parts else ''),body,{},name,flag,0



if __name__=='__main__':main()
