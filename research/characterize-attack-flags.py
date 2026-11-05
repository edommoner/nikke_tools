"""Observe unported physical attack flags without changing GPU admission."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','tests')]
from test_target_counter_runtime import manager,NAMES
from portable_weapon_oracle import observe as physical


def effect(stat,value=None,*,duration=-1,conditions=None,timing='on_attack',target='self',name=None):
    row=dict(name=name or stat,source='스킬1',type='buff',stat=stat,duration=duration,target=target,
             trigger=dict(timing=[timing],condition=conditions or []))
    if value is not None:row['fixed_value']=value
    return row
