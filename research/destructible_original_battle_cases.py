"""Unmodified original projectile definition on the real burst scheduler.

The surrounding world/weapons are declared; this is not the whole character.
"""
import copy,json
from pathlib import Path
from destructible_battle_cases import fixtures as battle_cases
from world_frame_native import roster_names
from world_enemy_attack_cases import field

CHARACTER='스노우 화이트 : 헤비암즈'
def original():
    return json.loads((Path(__file__).resolve().parents[1]/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text())[CHARACTER][24]

def fixtures():
    rows=[]
    for label,level in [('level1',1),('level5',5),('level10',10),('defense0',10),('live-buff',10),('named-child',10),('empty-targets',10),('last-owner',1)]:
        c=copy.deepcopy(battle_cases()[0]);names=roster_names(c);owner=4 if label=='last-owner' else 0
        names[owner]=CHARACTER;c.update(name='destructible-original-battle/'+label,names=names,duration=1.,skill_levels=[{'1':10,'2':10,'3':10} for _ in range(5)])
        c['skill_levels'][owner]={'1':2,'2':7,'3':level}
        c['patterns'][0]['until']['time']=2.
        for i,w in enumerate(c['combat']['weapons']):w.update(stage=3 if i==owner else 1 if i==(owner+1)%5 else 2 if i==(owner+2)%5 else 0,gauge=0,cooldown=40)
        c['effects']=[dict(name='start-gauge',source='스킬1',type='instant',stat='burst_charge_pct',fixed_value=100,target='all_allies',trigger=dict(timing=['battle_start'],condition=[])),copy.deepcopy(original())];c['owners']=[owner,owner]
        if label=='defense0':c['enemy']['def']=0
        if label=='live-buff':c['effects'].insert(1,field('atk_pct',50,'self','attack-before-cast'));c['owners'].insert(1,owner)
        if label=='named-child':
            c['effects'].append(dict(name='body-completion-child',source='스킬2',type='damage',stat='damage',fixed_value=50.,target='boss',trigger=dict(timing=['weapon_hit:'+original()['name']],condition=[])));c['owners'].append(owner)
        if label=='empty-targets':c['patterns'][0]['delay']=2.
        rows.append(c)
    return rows
