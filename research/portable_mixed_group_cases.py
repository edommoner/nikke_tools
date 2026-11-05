"""Real paired multi-hit listeners in two formations; no authored hit lists."""
import importlib.util
from pathlib import Path
OWNERS={'니힐리스타':2,'벨로타':4}
def fixtures():
    spec=importlib.util.spec_from_file_location('mixed_group_body_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
    rows=[]
    formations=[['니힐리스타','벨로타','미란다','도라','메어리'],['미란다','도라','메어리','벨로타','니힐리스타']]
    for order,names in enumerate(formations):
        for duration,adds in ((3,1),(3,3),(30,1),(30,3),(180,3)):
            for routing in ('native','all-logical-enemies'):
                body=dict(real.body_for(names,duration),burst_gauge_mode='accumulate');body['enemy']['has_parts']=False
                body['enemy']['patterns']=[dict(id='wave',kind='summon',spec=dict(count=adds,hp=1e12))]
                rows.append(dict(name=f'attack-group-mixed/{order}/{duration}s/{adds}adds/{routing}',body=body,routing=routing,group_history='compact',contract=dict(mixed_owners=dict(OWNERS),formation=order,duration=duration,adds=adds,baseline_unchanged=routing=='native')))
    return rows
