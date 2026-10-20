"""Author flag/classification stimuli once for both GPU backends."""
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def buff(stat,value=None,*,name=None,duration=-1,target='self',timing='passive',conditions=None):
    row=dict(name=name or stat,source='스킬1',type='buff',stat=stat,duration=duration,target=target,
             trigger=dict(timing=[timing],condition=conditions or []))
    if value is not None:row['fixed_value']=value
    return row


def bonuses():
    return [buff('crit_rate',-15),buff('pierce_dmg_pct',50),buff('armor_break_dmg_pct',40)]


def weapon(typ='AR',mode='auto',**extra):
    return dict(enabled=True,base_weapon_type=typ,mode=mode,coefficient=100,capacity=100,interval=1,
                charge=.5,full_charge_mult=100,reload=1,gauge=0,**extra)


def query(t,index=0):return [t,2,0,0,0,index,0,0]


def physical(name,effects,owners,*,w=None,script=None,totals=None):
    script=script or [[1.5,24,0,0,0,-1,0,0],query(1.5)]
    expected=[{} for c in script if c[1]==2]
    if totals is not None:expected=[dict(damage=[value,0,0,0,0]) for value in totals]
    return dict(name='attack-flag-'+name,attack_flag_reference=True,effects=effects,owners=owners,
        combat=dict(weapons=[w or weapon()]+[dict(enabled=False) for _ in range(4)],targets=[dict(hp=1000000,defense=100)]),
        script=script,expected_queries=expected)


def main():
    rows=[]
    stats=[('pierce_enabled',1350),('armor_break_enabled',1400)]
    for owner in range(5):
        for stat,per_shot in stats:
            for index,value in enumerate((None,0,-100,100)):
                for target in ('self','all_allies'):
                    active=owner==0 or target=='all_allies'
                    rows.append(physical(f'presence-{owner}-{stat}-{index}-{target}',bonuses()+[buff(stat,value,target=target)],
                        [0,0,0,owner],totals=[2*(per_shot if active else 900)]))
            w=weapon();w['interval']=.5
            script=[[.999999,24,0,0,0,-1,0,0],query(.999999),[1,24,0,0,0,-1,0,0],query(1,1),[1.000001,24,0,0,0,-1,0,0],query(1.000001,2)]
            rows.append(physical(f'expiry-{owner}-{stat}',bonuses()+[buff(stat,0,target='all_allies',duration=1)],
                [0,0,0,owner],w=w,script=script,totals=[2*per_shot,2*per_shot+900,2*per_shot+900]))
            for duration in (-1,2):
                marker=buff(None,name='state',duration=.5,timing='battle_start')
                flag=buff(stat,0,target='all_allies',duration=duration,timing='battle_start',conditions=['self_state:state'])
                rows.append(physical(f'gate-{owner}-{stat}-{duration}',bonuses()+[marker,flag],[0,0,0,owner,owner],w=w,
                    script=[[1,24,0,0,0,-1,0,0],query(1)],totals=[per_shot+1800 if duration==-1 else 3*per_shot]))
    for stat,per_shot in stats:
        for index,values in enumerate(((0,0),(100,-100),(-100,-100))):
            for target in ('self','all_allies'):
                aliases=[buff(stat,value,name='alias',target=target) for value in values]
                for alias in aliases:alias['max_stack']=2
                rows.append(physical(f'alias-{stat}-{index}-{target}',bonuses()+aliases,[0]*5,totals=[2*per_shot]))
    for typ,mode in [('AR','auto'),('SMG','auto'),('SG','auto'),('SR','charge'),('RL','charge'),('MG','auto_warmup')]:
        w=weapon(typ,mode)
        if typ=='SG':w['pellets']=10
        flags=[buff('pierce_enabled',0),buff('armor_break_enabled',-100)]
        rows.append(physical('both-'+typ,bonuses()+flags,[0]*5,w=w,totals=[3800]))
    for stat,per_shot in stats:
        for duration in (-1,2):
            flag=buff(stat,0,duration=duration)
            flag.update(scaling='stack_count',scaling_ref='absent')
            rows.append(physical(f'ignored-scaling-{stat}-{duration}',bonuses()+[flag],[0]*4,totals=[2*per_shot]))
    for typ in ('AR','SG'):
        flags=[buff('pierce_enabled',0),buff('armor_break_enabled',-100)]
        rows.append(physical('muzzles-'+typ,bonuses()+flags,[0]*5,
            w=weapon(typ,pellets=10 if typ=='SG' else 1,muzzles=2),totals=[7600]))
    # Reuse authored mode/range stimuli, never native-derived state or clocks.
    geometry=json.loads((ROOT/'tests/fixtures/portable-geometry.json').read_text())['cases']
    for index,c in enumerate(c for c in geometry if c.get('geometry_physical_reference') and c['effects'][0]['type']=='weapon_change'):
        row=copy.deepcopy(c);row.update(name='attack-flag-mode-'+str(index),attack_flag_reference=True)
        row.pop('geometry_reference',None)
        added=bonuses()+[buff('pierce_enabled',0),buff('armor_break_enabled',-100)]
        row['effects']+=added;row['owners']+=[0]*len(added);row['expected_queries']=[{} for cmd in row['script'] if cmd[1]==2]
        rows.append(row)
    for family,per_hit in [('damage',900),('auto_damage',900),('pierce_damage',1350),('armor_break_damage',1400),('armor_break_burst_damage',1400)]:
        for mask in range(4):
            effects=bonuses()
            if mask&1:effects.append(buff('pierce_enabled',0))
            if mask&2:effects.append(buff('armor_break_enabled',-100))
            effects.append(dict(name='skill',source='스킬1',type='damage',stat=family,fixed_value=100,target='boss',trigger=dict(timing=['on_attack'],condition=[])))
            row=physical(f'skill-{family}-{mask}',effects,[0]*len(effects),
                script=[[0,4,0,0,0,-1,0,0],[.1,0,7,0,0,-1,0,0],query(.1)],totals=[per_hit])
            row['combat']['weapons']=[dict(enabled=False) for _ in range(5)];row['attack_flag_skill_reference']=True;rows.append(row)
    effects=bonuses()+[buff('pierce_enabled',0),buff('armor_break_enabled',-100)]
    row=physical('external-normal-packet',effects,[0]*len(effects),
        script=[[0,4,0,0,0,-1,0,0],[.1,18,0,0,0,-1,100,0],query(.1)],totals=[900])
    row['combat']['weapons']=[dict(enabled=False) for _ in range(5)];row['attack_flag_skill_reference']=True;rows.append(row)
    for mask,second in [(1,1350),(2,1400),(3,1900)]:
        effects=bonuses()
        if mask&1:effects.append(buff('pierce_enabled',0,timing='hit_count'))
        if mask&2:effects.append(buff('armor_break_enabled',0,timing='hit_count'))
        rows.append(physical('pellet-parent-'+str(mask),effects,[0]*len(effects),w=weapon('SG',pellets=10),
            script=[[1,24,0,0,0,-1,0,0],query(1)],totals=[900+second]))
    (ROOT/'tests/fixtures/portable-attack-flags.json').write_text(json.dumps(dict(cases=rows),ensure_ascii=False,indent=2)+'\n')
    print('Authored attack flag cases',len(rows))


if __name__=='__main__':main()
