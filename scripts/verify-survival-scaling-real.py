"""Actual Moran/Biscuit squads, including post-revival hits and owned gear."""
import argparse,copy,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('scaling_actual_oracle',ROOT/'scripts/verify-survival-scaling.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
def fixtures():
    base=list(v.real_fixtures())
    for name,b,extra in base:
        if name.endswith('-revival'):b['enemy']['patterns'].append(dict(id='after revival',kind='attack',delay=4,until={'time':10},spec=dict(coeff=100,atk=800000,target='slot:4',hits=10,interval=.5,pierce=True)))
        yield name,b,extra
    for character in ('목단','비스킷'):
        original=next(x for x in base if x[0]=='raw-'+character+'-incoming')
        for variant in ('owned-growth','reordered'):
            name,b,extra=copy.deepcopy(original);name+='-'+variant
            if variant=='reordered':
                b['squad']=list(reversed(b['squad']))
                for p in b['enemy']['patterns']:
                    if p['spec']['target']=='slot:1':p['spec']['target']='slot:5'
            else:
                c=b['profile']['chars'][character];c.update(breakthrough=3,core_enhancement=2,affinity=20,skill_levels={'1':7,'2':5,'3':9},collection_stage='SR15',cube={'name':'렐릭 베어 큐브','level':4})
                c['equip_skills'].update(atk_pct=[11.11,11.11,12.34],charge_speed_pct=[2.34,2.34,4.3])
                b['stat_deltas']={character:{'atk':12000,'hp':100000,'def':250}}
            yield name,b,extra
