"""Whole Makima profile and one literal incoming lethal hit stimulus."""
import importlib.util
from pathlib import Path


def fixtures():
    spec=importlib.util.spec_from_file_location('undying_roster_factory',Path(__file__).resolve().parent/'verify-world-projectile-rosters.py');real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
    rows=[]
    for label,duration,lethal,results,shots in [('3s',3,False,[],155),('30s',30,False,[False,False],1398),('30s-lethal',30,True,[True,False],1398)]:
        body=dict(real.body_for(real.policy.roster_for('마키마'),duration),burst_gauge_mode='accumulate')
        if lethal:
            slot=body['squad'].index('마키마')+1
            body['enemy']['patterns']=[dict(id='lethal-input',kind='attack',delay=1,spec=dict(atk=1e12,coeff=100,target='slot:'+str(slot),ignore_taunt=True))]
        rows.append(dict(name='undying-predicate-real-'+label,character='마키마',effect_name='조용히 해주겠니? 3',body=body,contract=dict(results=results,shots=shots)))
    return rows
