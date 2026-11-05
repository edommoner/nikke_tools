"""Aimed body/part counter children mutate later packets and following shots."""
import copy
from portable_aimed_area_cases import fixtures as area_fixtures
from target_counter_cases import marker
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant


def fixtures():
    rows=[]
    for actor in ('body','part'):
        for source,label in ((0,'pierce'),(1,'scatter'),(3,'explosion'),(6,'part-pierce'),(7,'part-explosion')):
            for stat,value in (('lifesteal_pct',40),('atk_pct',100)):
                case=copy.deepcopy(area_fixtures()[source])
                case['name']=f'aimed-callback-{actor}-{label}-{stat}'
                case.update(observe_target_counters=True,observe_named_state=True)
                counter=marker(threshold=1,attackers='owner',actor=dict(kind=actor,identity=0,generation=1))
                counter['target']='boss';counter['trigger']['timing']=['battle_start']
                case['effects'] += [instant('current_hp_reduce',50,'all_allies','wound'),
                    field('lifesteal_pct',1,'all_allies','leech'),counter,
                    field(stat,value,'self','callback-surge',timing='event:target_counter_complete:marker')]
                case['owners'] += [0,0,0,0]
                if actor=='part' and source in (0,1,3):
                    case['patterns'].append(dict(id='nearby',kind='parts',targets=[dict(name='other-part',hp=1e8,reach=1)]))
                rows.append(case)
    return rows
