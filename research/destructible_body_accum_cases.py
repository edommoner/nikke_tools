"""Complete Trony profiles and explicit pool/shield inputs, never hit lists."""
import importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('body_accum_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
    rows=[]
    for profile,label,names in [('트로니','Trony',['헬름','미란다','도라','트로니','메어리'])]:
        for duration in (3,30):
            for mode,kind,capacity in [('hp',3,1e12),('hit',4,128.),('break',3,100.)]:
                start,length=(.5,.2) if duration==3 else (13.,2.) if label=='Dorothy' else (6.,.3)
                body=dict(r.body_for(names,duration),burst_gauge_mode='accumulate')
                body['enemy']['patterns']=[dict(id='incoming',kind='attack',delay=.1,spec=dict(atk=300000,coeff=100,target='all',pierce=True)),dict(id='shield',kind='idle',delay=start,until=dict(time=length))]
                rows.append(dict(name=f'destructible-body-accum/{label}/{duration}s/{mode}',body=body,typed_bindings=[dict(node='shield',kind=kind,identity=10,capacity=capacity,owner=[0,0,1])],max_attacks=128,skill_shield_interception_v1=True,body_lifesteal_v1=True,body_accumulation_v1=True,contract=dict(profile=profile,label=label,duration=duration,mode=mode,shield_start=start,shield_length=length)))
    for duration in (3,30):
        for amount,value in [('positive',5000.),('zero-integer',0.0000001)]:
            for mode,kind,capacity in [('hp',3,1e12),('hit',4,128.)]:
                body=dict(r.body_for(['누아르','밀크','도라','레이','미사토'],duration),burst_gauge_mode='accumulate')
                body['enemy']['patterns']=[dict(id='incoming',kind='attack',delay=.1,spec=dict(atk=300000,coeff=100,target='all',pierce=True)),dict(id='shield',kind='idle',delay=.9,until=dict(time=.3))]
                effects=[dict(source='declared',type='buff',stat='dmg_accum_received_atk_pct',name='declared-pool',target='boss',fixed_value=value,duration=1.,trigger=dict(timing=['battle_start'],condition=[])),dict(source='declared',type='damage',stat='accum_split_damage',name='declared-release',target='all_enemies',target_effect='declared-pool',trigger=dict(timing=['event:state_end:declared-pool'],condition=[])),dict(source='declared',type='buff',stat='shield_dmg_pct',name='declared-shield-factor',target='self',fixed_value=100.,duration=-1,trigger=dict(timing=['battle_start'],condition=[]))]
                rows.append(dict(name=f'destructible-body-accum/declared-{amount}/{duration}s/{mode}',body=body,declared_effects=effects,typed_bindings=[dict(node='shield',kind=kind,identity=10,capacity=capacity,owner=[0,0,1])],max_attacks=128,skill_shield_interception_v1=True,body_lifesteal_v1=True,body_accumulation_v1=True,contract=dict(label='declared-'+amount,duration=duration,mode=mode,shield_start=.9,shield_length=.3)))
    return rows
