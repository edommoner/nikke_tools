"""Unmodified catalogue instant under an explicit charged-weapon stimulus."""
import copy,json
from pathlib import Path
from portable_ammo_equivalent_cases import fixtures as base_fixtures

def fixtures():
    source=Path(__file__).resolve().parent/'upstream/nikke-calc-master/data/parsed_skills.json'
    effects=json.loads(source.read_text())['신데렐라 : 크리스탈 웨이브']
    authored=next(e for e in effects if e.get('stat')=='squad_ammo_consume_as')
    case=copy.deepcopy(next(c for c in base_fixtures() if c['name']=='ammo-equivalent-charge'))
    case['name']='ammo-equivalent-catalogue-charge40';case['effects'][1]=copy.deepcopy(authored)
    case['contract'].update(notices=80,stack=20,packet_damage=[6000,12000],call_names=[authored['name']]*2,call_values=[40.0]*2,notice_origin=authored['name'],notice_groups=[40,40])
    return [case]
