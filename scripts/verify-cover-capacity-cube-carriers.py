"""Full raw Moran/A2 skills with Cover cube; no support skill injection."""
import argparse,copy,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('capacity_cube_oracle',ROOT/'scripts/verify-cover-capacity.py');cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap)
hp=cap.load('capacity_cube_HP_fixture','scripts/verify-hp-edge-real.py')
def fixtures():
    _,b,extra=next(x for x in cap.v.real_fixtures() if x[0]=='raw-목단-no-shots');assert not any(extra.values())
    b['profile']['chars']['목단'].update(cube={'name':'렐릭 커버 큐브','level':4},core_enhancement=2,collection_stage='SR15',affinity=20)
    b['stat_deltas']={'목단':{'atk':12000,'hp':100000,'def':250}}
    b['enemy']['patterns']=[dict(id='Moran cover-cube hits',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=40000,target='slot:1',hits=10,interval=1,pierce=True))]
    yield 'raw-Moran-capacity-cover-cube',b,extra
    _,b,extra=next(x for x in hp.fixtures() if x[0]=='raw-A2-mixed-growth');assert not any(extra.values())
    b['profile']['chars']['A2']['cube']={'name':'렐릭 커버 큐브','level':4}
    b['enemy']['patterns'].append(dict(id='A2 cover-cube hits',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=100000,target='all',hits=6,interval=4)))
    yield 'raw-A2-capacity-cover-cube',b,extra
