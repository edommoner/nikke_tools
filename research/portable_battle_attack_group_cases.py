"""Literal whole-scene logical-enemy policies, never authored hit/group lists."""
import importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('group_battle_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
    rows=[]
    for profile,threshold in [('니힐리스타',2),('벨로타',4)]:
        for duration in (3,30):
            for count in (0,1,3,5):
                names=[profile,'미란다','도라','N102','메어리'];body=dict(r.body_for(names,duration),burst_gauge_mode='accumulate')
                body['enemy']['has_parts']=False;body['enemy']['patterns']=[dict(id='wave',kind='summon',spec=dict(count=count,hp=1e12))] if count else [dict(id='idle',kind='idle')]
                rows.append(dict(name=f'attack-group-battle/{profile}/{duration}s/{count}adds',body=body,routing='all-logical-enemies',contract=dict(profile=profile,threshold=threshold,duration=duration,adds=count,capacity=1e12)))
        body=dict(r.body_for([profile,'미란다','도라','N102','메어리'],3),burst_gauge_mode='accumulate');body['enemy']['has_parts']=False
        first=1. if threshold==2 else 1.5166666666666666
        body['enemy']['patterns']=[dict(id='wave',kind='summon',delay=first,spec=dict(count=threshold-1,hp=1.))]
        rows.append(dict(name=f'attack-group-battle/{profile}/break',body=body,routing='all-logical-enemies',contract=dict(profile=profile,threshold=threshold,duration=3,adds=threshold-1,capacity=1.)))
        import copy
        body=copy.deepcopy(body);end=1+1/60 if threshold==2 else 1.5166666666666666+1/60
        body['enemy']['patterns']=[dict(id='wave',kind='summon',after=['start','wave'],until=dict(time=end),repeat=2,spec=dict(count=threshold-1,hp=1e12))]
        rows.append(dict(name=f'attack-group-battle/{profile}/reopened-before-child',body=body,routing='all-logical-enemies',contract=dict(profile=profile,threshold=threshold,duration=3,adds=threshold-1,capacity=1e12,reopened=True)))
    # Declared listeners exercise original scatter/muzzle returns, without
    # changing their weapon metadata or claiming original multi_hit support.
    for profile in ('누아르','츠바이'):
        body=dict(r.body_for([profile,'미란다','도라','N102','메어리'],3),burst_gauge_mode='accumulate')
        body['enemy']['has_parts']=False
        body['enemy']['patterns']=[dict(id='wave',kind='summon',spec=dict(count=1,hp=1e12))]
        effect=dict(name='declared-group-child',source='declared',type='damage',stat='bonus_damage',target='target',fixed_value=10.,trigger=dict(timing=['multi_hit:2'],condition=[]))
        rows.append(dict(name=f'attack-group-battle/declared/{profile}',body=body,routing='all-logical-enemies',declared_effects=[effect],contract=dict(profile=profile,threshold=2,duration=3,adds=1,capacity=1e12,declared_listener=True,min_packets=2)))
    return rows
