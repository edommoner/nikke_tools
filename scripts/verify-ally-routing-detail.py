"""Additional recipient routes: special ATK, grouped charge and enemy stats."""
import hashlib, importlib.util, json, math
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ally_routing',ROOT/'scripts/verify-ally-conditions-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def cases():
    for stat,target in [('atk_caster_based_pct','all_allies'),('charge_speed_pct','all_allies'),('crit_rate','all_allies'),('received_dmg_pct','boss'),('def_pct','boss'),('charge_speed_caster_based_pct','all_allies')]:
        owner=v.NAMES[4] if stat=='charge_speed_caster_based_pct' else v.NAMES[0]
        effects=[(v.E('routing gate','buff',stat,23,target,event='passive',condition=['ally_hp_below:50']),owner),
                 (v.E('routing drain','instant','current_hp_reduce',50,v.NAMES[2],event='burst_cast'),v.NAMES[1])]
        commands=[(0,0,i) for i in range(5)]+[(.1,3,1)]+[(.2,'query',i) for i in [4,2,0,3,1]]
        yield stat+'-'+target,v.NAMES,effects,commands,None
