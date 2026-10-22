"""Conditional shield/decoy repairs witnessed by actual subsequent absorption."""
import copy
from portable_skill_hp_basis_cases import fixtures as hp_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field

def fixtures():
    rows=[]
    for kind in ('shield','decoy'):
        for maximum in (False,True):
            c=copy.deepcopy(hp_fixtures()[1]);c['name']='skill-hp-basis-'+kind+'-repair-'+('max-hp' if maximum else 'capacity')
            obj=field('shield_from_max_hp_pct' if kind=='shield' else 'decoy',10,'self','object')
            heal=instant(kind+'_heal_pct',10,'self','repair','every:0.1s');heal['max_trigger']=1;heal['trigger']['condition']=['self_state:object']
            if maximum:heal['scaling']='max_hp'
            c['effects'][:0]=[obj,heal];c['owners'][:0]=[0,0]
            c['patterns']=[dict(id='hit',kind='attack',delay=.05,spec=dict(atk=900,coeff=100,target='slot:1',hits=2,interval=.15))]
            c['contract']['protection_absorption']=dict(kind=kind,amounts=[900,900 if maximum else 200])
            rows.append(c)
    return rows
