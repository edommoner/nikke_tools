"""Literal original attacks exercising death inside a frozen allocation packet."""
import copy
from portable_weighted_battle_cases import fixtures as original_cases


def fixtures():
    rows=[]
    for label in ('caster-during-packet','other-before-activation'):
        case=copy.deepcopy(original_cases()[0])
        case['name']='weighted-incoming/Bay/owner-down/'+label+'/15s'
        case['body']['duration']=15
        case['patterns']=[p for p in case['patterns'] if p['kind']=='idle' or p['delay']<15]
        case['patterns'][0]['until']['time']=15
        if label=='caster-during-packet':
            next(p for p in case['patterns'] if p['id']=='incoming-10.0')['spec']['atk']=200000000.
        else:
            attack=next(p for p in case['patterns'] if p['id']=='incoming-0.1')
            attack['spec'].update(atk=100000000.,target='slot:3')
        case['body']['enemy']['patterns']=copy.deepcopy(case['patterns'])
        case['contract']['scenario']=label
        rows.append(case)
    return rows
