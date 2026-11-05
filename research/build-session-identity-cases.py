"""Mechanical session boundaries with fixed damage/magazine expectations.

No native execution or GPU observations are used to construct these inputs.
"""
import copy
import json
from pathlib import Path

R=Path(__file__).resolve().parents[1]
base=json.loads((R/'tests/fixtures/portable-combat-extensions.json').read_text())['cases']
template=next(c for c in base if c['name']=='mode-replacement-first-shot-coefficient')
rows=[]

def replacement(name, timing, *, charge=False, pellets=1):
    c=copy.deepcopy(template);c['name']='session-identity-'+name;c['mode_session_reference']=True
    old,new=c['effects'][1:3]
    old.update(max_ammo=1,duration_bullets=1,pellets=pellets,damage_coeff={'10':300 if pellets==3 else 200})
    if charge:old.update(charge=True,charge_time=.25,post_fire_delay=.25,full_charge_mult=100)
    new.update(max_ammo=3,trigger=dict(timing=[timing],condition=[]),max_trigger=1)
    return c

def finish(c,times,damages,extra=None):
    c['script']=[]
    for i,t in enumerate(times):c['script'] += [[t,4,0,0,0,-1,0,0],[t,2,0,0,-1,i,0,0]]
    c['expected_queries']=[dict(damage=[d,0,0,0,0]) for d in damages]
    for i,values in (extra or {}).items():c['expected_queries'][i].update(values)
    c['owners']=[0]*len(c['effects']);rows.append(c)

finish(replacement('old-auto-limit-cannot-end-replacement','on_attack'),[0,.25,.5],[2000,6000,9000])
finish(replacement('old-charge-limit-cannot-end-replacement','on_attack',charge=True),[0,.25,.5,.75],[0,2000,6000,9000])
finish(replacement('full-charge-change-cancels-old-shot','full_charge',charge=True),[0,.25,.5,.75],[0,0,4000,7000])
finish(replacement('auto-last-fire-keeps-committed-packet','last_bullet_fire'),[0,.25,.5],[2000,6000,9000])
finish(replacement('charge-last-fire-cancels-old-charge','last_bullet_fire',charge=True),[0,.25,.5],[0,4000,7000])
finish(replacement('pellet-change-keeps-parent-packet','pellet_hit',pellets=3),[0,.25,.5],[3000,7000,10000])
c=replacement('warmup-shot-keeps-physical-clock','on_attack')
c['effects'][1].update(weapon_type='MG',fire_rate=4,fire_rate_max=8,warmup_bullets=4)
c['mode_timing_reference']=True
finish(c,[0,.25,.5],[2000,6000,9000])
c['expected_final']=dict(weapons=[dict(warm=1,last_fire=0,last_interval=.25)])

toggle=next(c for c in base if c['name']=='mode-toggle-end-child-reentry')
for cancel in [False,True]:
    c=copy.deepcopy(toggle);c['name']='session-identity-end-pct-'+('child-cancel' if cancel else 'child-reentry')
    c['mode_session_reference']=True
    removal=dict(name='remove half base magazine',source='스킬1',type='instant',stat='ammo_charge_pct',fixed_value=-50,
                 target='self',max_trigger=1,trigger=dict(timing=['event:state_end:mode'],condition=[]))
    c['effects'].insert(3,removal)
    if cancel:
        child=copy.deepcopy(c['effects'][-1]);child['name']='cancel child';c['effects'].append(child)
    finish(c,[0,.25,.5],[2000,3000,4000] if cancel else [2000,4000,6000],
           {0:dict(combat=dict(weapons=[dict(ammo=5,mode_index=-1 if cancel else 1,mode_shots=0)]))})

c=copy.deepcopy(next(c for c in base if c['name']=='mode-round-limit-restores-magazine'))
c['name']='session-identity-same-definition-refresh-keeps-round-progress';c['mode_session_reference']=True
c['effects'].append(dict(name='refresh once',source='스킬1',type='instant',stat='force_skill_use',fixed_value=0,
                         target='self',target_skill='스킬3',max_trigger=1,trigger=dict(timing=['on_attack'],condition=[])))
finish(c,[0,.25,.5],[2000,4000,5000],{0:dict(combat=dict(weapons=[dict(ammo=1,mode_shots=1)]))})

path=R/'tests/fixtures/portable-mode-sessions.json';data=json.loads(path.read_text())
data['cases']=[c for c in data['cases'] if not c['name'].startswith('session-identity-')]+rows
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('Wrote session-identity cases',len(rows))
