"""Author input and arithmetic expectations once for both GPU backends."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def case(owner,reference,scenario,pct=100):
    shooter=(owner+1)%5 if scenario=='other-actor' else owner
    charge=scenario.startswith('charge-')
    timing={'pellet-callback':'pellet_hit','attack-callback':'on_attack',
            'charge-attack-callback':'on_attack'}.get(scenario,'battle_start')
    effects=[dict(name='charge-speed',source='스킬1',type='buff',stat='burst_charge_speed_pct',
        fixed_value=pct,target='all_allies',duration=-1,trigger=dict(timing=[timing],condition=[]))]
    owners=[owner]
    if scenario=='normal-mode':
        effects.append(dict(name='changed-weapon',source='스킬1',type='weapon_change',
            weapon_type='AR',damage_coeff={'10':100},max_ammo=-1,fire_rate=1,
            charge=False,pellets=1,muzzles=1,post_fire_delay=0,burst_energy=5,
            core_dmg_mult=200,target='self',duration=.5,
            trigger=dict(timing=['battle_start'],condition=[])))
        owners.append(shooter)
    count=10 if scenario in ('pellets','pellet-callback') else 2 if scenario=='dual-muzzle' else 1
    w=dict(enabled=True,base_weapon_type='SR' if charge else 'SG' if count==10 else 'AR',
        mode='charge' if charge else 'auto',coefficient=100,capacity=100,interval=1,
        charge=.5,gauge=.5,full_charge_mult=300,
        gauge_mult=300 if scenario=='charge-camera' else 100,
        pellets=10 if count==10 else 1,muzzles=2 if count==2 else 1)
    weapons=[dict(enabled=False) for _ in range(5)];weapons[shooter]=w
    refs=[dict(burst_energy=7,burst_energy_raw=3) for _ in range(5)];refs[owner]=reference
    flat_reference=reference.get('burst_energy_raw',reference['burst_energy']/2) if scenario=='other-actor' else reference['burst_energy']
    flat=flat_reference*pct/100
    if scenario=='attack-callback':flat=0
    gain=(5 if scenario=='normal-mode' else .5)*count*(3 if scenario=='charge-camera' else 1)+count*flat
    t=.5166666666666667 if charge else 0
    return dict(name=f'burst-speed-{owner}-{scenario}-{pct}-'+str(reference),
        burst_charge_reference=True,burst_charge_context=dict(shooter=shooter,camera=scenario=='charge-camera'),
        effects=effects,owners=owners,environment=dict(burst_references=refs),
        combat=dict(weapons=weapons,targets=[dict(hp=1000000,defense=0)]),
        script=[[t,24,0,0,0,-1,0,0],[t,2,0,0,-1,0,0,0]],
        expected_queries=[dict(combat=dict(gauge=min(100,max(0,gain))))])


def main():
    references=[dict(burst_energy=2,burst_energy_raw=.25),dict(burst_energy=4,burst_energy_raw=1.5),dict(burst_energy=2)]
    scenarios=['auto','other-actor','pellets','dual-muzzle','charge-camera','charge-no-camera',
               'normal-mode','pellet-callback','attack-callback','charge-attack-callback']
    rows=[case(o,r,s) for o in range(5) for r in references for s in scenarios]
    rows += [case(o,references[0],s,pct) for o in range(5) for s in ('auto','other-actor') for pct in (-200,-50,0,1000)]
    for owner in range(5):
        for duration in (-1,2):
            row=case(owner,references[0],'auto')
            row['name']=f'burst-speed-condition-{owner}-{duration}'
            row['effects'][0].update(duration=duration)
            row['effects'][0]['trigger']['condition']=['self_state:charge-marker']
            row['effects'].insert(0,dict(name='charge-marker',source='스킬1',type='buff',stat=None,
                target='self',duration=.5,trigger=dict(timing=['battle_start'],condition=[])))
            row['owners'].insert(0,owner)
            row['script']=[[0,24,0,0,0,-1,0,0],[0,2,0,0,-1,0,0,0],[1,24,0,0,0,-1,0,0],[1,2,0,0,-1,1,0,0]]
            row['expected_queries']=[dict(combat=dict(gauge=2.5)),dict(combat=dict(gauge=3 if duration==-1 else 5))]
            rows.append(row)
        for scenario in ('expiry','stack'):
            row=case(owner,references[0],'auto')
            row['name']=f'burst-speed-{scenario}-{owner}'
            if scenario=='expiry':row['effects'][0]['duration']=1
            else:row['effects'][0].update(max_stack=3,trigger=dict(timing=['on_attack'],condition=[]))
            row['script']=sum(([[t,24,0,0,0,-1,0,0],[t,2,0,0,-1,t,0,0]] for t in (0,1,2)),[])
            row['expected_queries']=[dict(combat=dict(gauge=g)) for g in ([2.5,3,3.5] if scenario=='expiry' else [.5,3,7.5])]
            rows.append(row)
    rows += [case(o,r,s,pct) for o in range(5)
             for r in (dict(burst_energy=2,burst_energy_raw=0),dict(burst_energy=0,burst_energy_raw=.25))
             for s in ('auto','other-actor','pellets') for pct in (-33.3,33.3)]
    (ROOT/'tests/fixtures/portable-burst-charge-speed.json').write_text(json.dumps(dict(cases=rows),ensure_ascii=False,indent=2)+'\n')
    print(len(rows),'shared burst charge cases authored')


if __name__=='__main__':main()
