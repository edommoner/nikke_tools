"""Frozen selection keys and native target-name resolution at later landing."""
import copy
from portable_coordinate_full_burst_cases import fixtures as pending
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant
from target_counter_cases import marker


def fixtures():
    originals=pending();rows=[]
    def add(label,kind='parts',reopen=True,until=.59):
        case=copy.deepcopy(next(c for c in originals if c['name'].endswith(kind+'-receipt-tail')))
        case['name']='coordinate-generation/'+label
        for pattern in case['patterns']:
            if pattern['kind']==kind:
                pattern['until']=dict(time=until)
                if reopen:pattern.update(after=['start',pattern['id']],repeat=2)
        case['generation_witness']=dict(kind=kind,reopened=reopen)
        rows.append(case);return case
    add('expired-parts',reopen=False)
    add('reopened-parts')
    add('expired-interrupt',kind='interrupt',reopen=False)
    add('reopened-interrupt',kind='interrupt')
    case=add('reopened-both',kind='interrupt');case['patterns'][0].update(until=dict(time=.59),after=['start','parts'],repeat=2)
    case=add('reopened-lifesteal')
    case['effects'].insert(0,instant('current_hp_reduce',50,'self','drain'));case['owners'].insert(0,0)
    case['effects'].append(field('lifesteal_pct',10,'self','leech'));case['owners'].append(0)
    case['contract']['hp']=[5570,10000,10000,10000,10000]
    case=add('reopened-interrupt-lifesteal',kind='interrupt')
    case['effects'].insert(0,instant('current_hp_reduce',50,'self','drain'));case['owners'].insert(0,0)
    case['effects'].append(field('lifesteal_pct',10,'self','leech'));case['owners'].append(0)
    case['contract']['hp']=[5540,10000,10000,10000,10000]
    case=add('reopened-counter')
    counter=marker('generation-two-counter',1,actor=dict(kind='part',identity=0,generation=2),families=['skill']);counter['target']='boss';counter['trigger']['timing']=['battle_start']
    case['effects'].append(counter);case['owners'].append(0)
    case=add('reopened-destroyed')
    for target in case['patterns'][0]['targets']:target['hp']=500
    add('reopen-after-landing',until=.61)
    case=add('mixed-pattern-generations');far=case['patterns'][0]['targets'].pop()
    case['patterns'].append(dict(id='far-parts',kind='parts',targets=[far]))
    case=add('expired-counter-order',reopen=False)
    for name,threshold in [('stale-hit-counter',2),('stale-death-counter',3)]:
        counter=marker(name,threshold,actor=dict(kind='part',identity=0,generation=1),families=['skill']);counter['target']='boss';counter['trigger']['timing']=['full_burst_start']
        case['effects'].append(counter);case['owners'].append(0)
    return rows
