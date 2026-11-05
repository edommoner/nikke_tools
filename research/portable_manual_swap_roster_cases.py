"""Complete published profile with the native authored mode-swap flag."""
import importlib.util
from pathlib import Path


def fixtures():
    path=Path(__file__).resolve().parent/'verify-world-projectile-rosters.py'
    spec=importlib.util.spec_from_file_location('manual_swap_roster_inputs',path);real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
    character='신데렐라 : 크리스탈 웨이브';rows=[]
    for duration,ready,dispatches,shots in ((3,0,0,112),(30,1,8,1425)):
        body=dict(real.body_for(real.policy.roster_for(character),duration),burst_gauge_mode='accumulate',weapon_mode_swap=True)
        body['profile']['chars'][character]['favorite_stage']=0
        rows.append(dict(name='manual-swap-real-'+str(duration)+'s',character=character,body=body,contract=dict(ready=ready,dispatches=dispatches,shots=shots)))
    return rows
