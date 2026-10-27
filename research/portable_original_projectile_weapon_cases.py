"""Original modifiers and physical weapons in the existing declared typed world."""
import copy
import importlib.util
from pathlib import Path

def fixtures():
    from portable_coordinate_typed_aim_gpu_cases import fixtures as aims
    spec=importlib.util.spec_from_file_location('original_projectile_weapon_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'))
    factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
    rows=[];base=aims()[0]
    for character,label,durations in [('사쿠라','Sakura',(3,30)),('앵커','Anchor',(3,30)),('클레이','Clay',(3,12,30))]:
        for duration in durations:
            c=copy.deepcopy(base)
            c.update(name=f'original-projectile-weapons/{label}/{duration}s',character=character,
                     body=dict(factory.body_for(factory.policy.roster_for(character),duration),burst_gauge_mode='accumulate',seed=4301),
                     typed_actor_policy=dict(mode='body-owned-current-fields-v1'))
            c['patterns'][0]['until']['time']=duration
            c['body']['enemy']['patterns']=copy.deepcopy(c['patterns'])
            for shape in c['typed_geometry']['shapes']:shape['r']=10000.
            for binding in c['typed_bindings']:binding['owner']=[0,0,1]
            c.pop('typed_aim_witness',None)
            rows.append(c)
    c=copy.deepcopy(rows[0]);c['name']='original-projectile-weapons/Sakura/no-projectiles'
    c['patterns'][0]['delay']=c['body']['duration']+1
    c['body']['enemy']['patterns']=copy.deepcopy(c['patterns']);rows.append(c)
    return rows

def prepare(row):
    from portable_coordinate_typed_owner_cases import prepare as owners
    c,p=owners(row)
    c['coordinate_packet_history']='ordered-sha256-v1';c['python_observers_only']=True
    return c,p
