"""Original allied projectile modifiers; one declared attack, no CPU schedule."""
import importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('original_modifier_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
    rows=[]
    for character in ['사쿠라','앵커','일레그','클레이']:
        for duration in (3,12):
            body=dict(f.body_for(f.policy.roster_for(character),duration),burst_gauge_mode='accumulate',seed=4201)
            body['enemy']['patterns']=[dict(id='declared-projectiles',kind='idle',until=dict(time=duration))]
            probe=dict(type='damage',name='declared-projectile-modifier-probe',trigger=dict(timing=['every:2s'],condition=[]),target='all_projectiles',stat='damage',fixed_value=100.)
            rows.append(dict(name='original-modifier-probe/'+character+'/'+str(duration)+'s',body=body,declared_effects=[probe],typed_bindings=[dict(node='declared-projectiles',kind=2,identity=10,capacity=1e12)],max_attacks=128,character=character,declared_projectile_probe=True))
    import copy
    other=copy.deepcopy(next(r for r in rows if r['character']=='앵커' and r['body']['duration']==3));other['name']+='/other-caster';other['probe_owner']=other['body']['squad'][1];other['zero_projectile_modifier']=True;rows.append(other)
    shield=copy.deepcopy(rows[0]);shield['name']='original-modifier-probe/Rei/shield-not-projectile';shield['body']=dict(f.body_for(f.policy.roster_for('레이'),3),burst_gauge_mode='accumulate',seed=4201);shield['body']['enemy']['patterns']=copy.deepcopy(rows[0]['body']['enemy']['patterns']);shield['character']='레이';shield['zero_projectile_modifier']=True;shield['shield_negative']=True;rows.append(shield)
    for character in ['아스카','레이','마리','미사토','사쿠라']:
        for duration in ((3,) if character=='사쿠라' else (3,30) if character=='미사토' else (3,12)):
            body=dict(f.body_for(f.policy.roster_for(character),duration),burst_gauge_mode='accumulate',seed=4201)
            body['enemy']['patterns']=[dict(id='declared-shield',kind='idle',until=dict(time=duration))]
            if character=='미사토':body['enemy']['patterns'].append(dict(id='incoming-damage',kind='attack',delay=.1,spec=dict(atk=300000,coeff=100,target='all',pierce=True)))
            probe=dict(type='damage',name='declared-hp-modifier-probe',trigger=dict(timing=['every:2s'],condition=[]),target='boss',stat='damage',fixed_value=100.)
            case=dict(name='original-modifier-probe/HP/'+character+'/'+str(duration)+'s',body=body,declared_effects=[probe],typed_bindings=[dict(node='declared-shield',kind=3,identity=10,capacity=1e12,owner=[0,0,1])],max_attacks=128,character=character,declared_projectile_probe=True,probe_kind=3)
            if character=='사쿠라':case.update(zero_probe_modifier=True,projectile_negative=True)
            if character=='미사토' and duration==3:case['zero_probe_modifier']=True
            rows.append(case)
    return rows
