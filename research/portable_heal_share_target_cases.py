"""Literal composite self/RL-rank contracts; no GPU-derived expectations."""
import copy
from portable_heal_share_cases import fixtures as original
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=next(c for c in original() if c['name']=='heal-share-presence-1')
    rows=[]
    def add(label,weapons,hp,weights):
        c=copy.deepcopy(base);c['name']='heal-share-target-'+label
        for weapon,kind in zip(c['combat']['weapons'],weapons):weapon['base_weapon_type']=kind
        c['effects'][1]['target']=['self','allies_weapon_top_atk:RL:2']
        c['effects'][-1]['fixed_value']=60
        c['contract'].update(hp=hp,weights=weights)
        rows.append(c);return c
    add('self-plus-two-rl',['AR','RL','RL','RL','AR'],[7000,7000,7000,5000,5000],[(0,1),(1,1),(2,1)])
    add('self-already-ranked',['RL','RL','RL','AR','AR'],[8000,8000,5000,5000,5000],[(0,1),(1,1)])
    add('no-rl-self-remains',['AR']*5,[10000,5000,5000,5000,5000],[(0,1)])
    c=add('overlap-distinct-carriers',['AR','RL','RL','RL','AR'],[6000,6000,6000,5500,5500],[(0,2),(1,2),(2,2),(3,1),(4,1)])
    c['effects'].insert(-1,field('heal_split',1,'all_allies','second-share'));c['owners'].insert(-1,0);c['effects'][-1]['fixed_value']=40
    # Native sync_hp divides by maxHP before multiplying by100. 5500/100
    # would erase the required final binary64 bit at this boundary.
    c['contract']['hp_pct']=[60,60,60,55.00000000000001,55.00000000000001]
    c=add('stable-ranked-tie',['AR','RL','RL','RL','AR'],[7000,7000,7000,5000,5000],[(0,1),(1,1),(2,1)])
    c['base_atk'][1:4]=[1800]*3
    c=add('self-is-carrier-owner',['AR','RL','RL','RL','AR'],[5000,8000,8000,5000,5000],[(1,1),(2,1)])
    c['owners'][1]=1;c['effects'][-1]['target']=roster_names(c)[1]
    # All battle_start effects for owner0 run before owner1's link exists.
    # The heal must be later than registration to test owner-relative self.
    c['effects'][-1]['trigger']['timing']=['every:0.2s']
    return rows
