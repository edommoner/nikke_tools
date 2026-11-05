"""Literal witnesses for engine 67835ca3; no CPU result enters packed inputs."""
import copy
from portable_persona_cases import fixtures as persona_cases
from portable_revive_cases import fixtures as revive_cases
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant


def fixtures():
    base=copy.deepcopy(persona_cases()[0]);base.update(duration=1.2,effects=[],owners=[])
    rows=[]
    def add(name,effects,owners=None,parent=base):
        effects=effects or [field('atk_pct',0,'self','zero-control')]
        case=copy.deepcopy(parent);case.update(name='newchars-'+name,effects=effects,owners=owners or [0]*len(effects));rows.append(case);return case
    add('engaged',[field('engaged_state',0,'self','engaged'),field('atk_pct',50,'self_and_engaged_allies','witness',timing='every:0.2s')],[1,0])
    add('engaged-control',[field('atk_pct',50,'self_and_engaged_allies','witness',timing='every:0.2s')])
    add('width',[field('normal_atk_width_pct',100,'self','width')])
    add('width-control',[])
    down=copy.deepcopy(revive_cases()[0]);down.update(duration=.9,effects=[],owners=[])
    for side,limit in [('above',1),('below',0)]:
        add('down-'+side,[field('atk_pct',50,'self','down-witness',timing='every:0.2s',condition=[f'ally_down_count_{side}:{limit}'])],[1],down)
        add('down-'+side+'-control',[],parent=down)
    revive=instant('revive',50,'allies_down_all','revived','every:0.6s')
    add('revive',[field('atk_pct',50,'allies_down_all','dead-buff',timing='every:0.6s'),revive,field('atk_pct',50,'self','named-child',timing='event:revived')],[1,1,1],down)
    add('revive-control',[field('atk_pct',50,'allies_down_all','dead-buff',timing='every:0.6s'),field('atk_pct',50,'self','named-child',timing='event:revived')],[1,1],down)
    add('revive-alive',[revive,field('atk_pct',50,'self','named-child',timing='event:revived')],[1,1])
    add('revive-alive-control',[])
    charge=copy.deepcopy(base);charge['combat']['weapons'][0].update(mode='charge',base_weapon_type='RL',charge=.2,interval=.3,min_cycle=.3,full_charge_mult=250)
    add('full-charge',[field('atk_pct',50,'self','full-witness',timing='full_charge',condition=['during_full_charge'])],parent=charge)
    add('full-charge-control',[],parent=charge)
    return rows
