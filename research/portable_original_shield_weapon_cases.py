"""All four original shield-modifier carriers, with real weapons and cover inputs."""
import copy,importlib.util
from pathlib import Path

def fixtures():
    from portable_original_projectile_weapon_cases import fixtures as projectiles
    template=projectiles()[0]
    spec=importlib.util.spec_from_file_location('original_shield_weapon_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'))
    factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
    rows=[]
    for character,label in [('레이','Rei'),('아스카','Asuka'),('마리','Mari'),('미사토','Misato')]:
        for duration in (3,30):
            c=copy.deepcopy(template)
            c.update(name=f'original-shield-weapons/{label}/{duration}s',character=character,
                     body=dict(factory.body_for(factory.policy.roster_for(character),duration),burst_gauge_mode='accumulate',seed=4301))
            c['patterns'][0]['until']['time']=duration;c['body']['enemy']['patterns']=copy.deepcopy(c['patterns'])
            for binding in c['typed_bindings']:binding['kind']=3
            rows.append(c)
    for label,duration,at,length in [('Mari',12,2.,6.),('Misato',22,7.,8.)]:
        c=copy.deepcopy(next(c for c in rows if f'/{label}/3s' in c['name']))
        c['name']=f'original-shield-weapons/{label}/cover-expiry';c['body']['duration']=duration
        c['patterns'][0]['until']['time']=duration;c['body']['enemy']['patterns']=copy.deepcopy(c['patterns'])
        c['declared_manual_sequences']={c['body']['squad'][0]:[dict(action='cover',t=at,duration=length)]}
        rows.append(c)
    return rows

def prepare(row):
    from portable_original_projectile_weapon_cases import prepare as original
    c,p=original(row)
    if row.get('declared_manual_sequences'):
        from portable_declared_manual_sequences import apply
        c['declared_manual_sequences']=copy.deepcopy(row['declared_manual_sequences'])
        p['chars']=apply(p['chars'],c['declared_manual_sequences'])
        c['controls']=[copy.deepcopy(char.get('control',{})) for char in p['chars']]
        p['policies']['controls']={char['name']:copy.deepcopy(char.get('control',{})) for char in p['chars']}
    return c,p
