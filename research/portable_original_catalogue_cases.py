"""Explicit original profile selection; unselected profiles are never prepared."""
import copy
from portable_original_identity_inventory import profile_bodies
MAX_SELECTED_CASES=4

def catalog():
    rows={}
    for character,stage,body in profile_bodies():
        for label,kind in [('projectile',2),('hp-shield',3)]:
            for duration in (3,30):
                name=f'original-catalogue/{label}/{character}/favorite-{stage}/{duration}s'
                if name in rows:raise ValueError('Duplicate original catalogue identity')
                rows[name]=dict(character=character,favorite_stage=stage,kind=kind,duration=duration,body=body)
    return rows

def selected_rows(names):
    if not isinstance(names,list) or not 1<=len(names)<=MAX_SELECTED_CASES or any(not isinstance(n,str) or not n for n in names) or len(set(names))!=len(names):raise ValueError('Select one to four distinct original catalogue cases')
    entries=catalog()
    if not set(names)<=entries.keys():raise ValueError('Unknown original catalogue case')
    rows=[]
    for name in names:
        descriptor=entries[name];body=copy.deepcopy(descriptor['body']);duration=descriptor['duration'];kind=descriptor['kind']
        body.update(duration=duration,seed=4301)
        patterns=[dict(id='world',kind='idle',until=dict(time=duration))];body['enemy']['patterns']=copy.deepcopy(patterns)
        rows.append(dict(name=name,character=descriptor['character'],body=body,patterns=patterns,
            coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),coordinate_weapon_targets=True,max_attacks=128,
            typed_bindings=[dict(node='world',kind=kind,identity=10,capacity=1e30,owner=[0,0,1],label='entry-inventory-typed')],
            typed_geometry=dict(point_source='caster_aim',shapes=[dict(x=0.,y=0.,r=10000.,z=1.)]),
            typed_aim_policy=dict(mode='typed-before-body-v1'),typed_actor_policy=dict(mode='body-owned-current-fields-v1'),
            catalogue_profile={k:descriptor[k] for k in ('character','favorite_stage','kind','duration')}))
    return rows

def prepare(row):
    from portable_original_projectile_weapon_cases import prepare as original
    c,p=original(row);c['catalogue_profile']=copy.deepcopy(row['catalogue_profile'])
    return c,p

def verify(case,native):
    from portable_coordinate_typed_weapon_contracts import verify as weapons
    weapons(case,native);identity=native['original_input_identity']
    assert identity==dict(definitions=len(case['effects']),chars_config_seed_weapon_verified=True,authored_metadata_overrides=False,authored_delays_overrides=False)
    profile=case['catalogue_profile'];original=case['original_run'];source=original['prepared']['effects']
    assert case['names'][0]==profile['character'] and original['body']['profile']['chars'][profile['character']]['favorite_stage']==profile['favorite_stage']
    assert len(case['effects'])==len(source)
    assert all(e==r['effect'] and case['names'][o]==r['owner'] for e,o,r in zip(case['effects'],case['owners'],source,strict=True))
    assert not case['declared_owner_counter'],'Catalogue must not add an effect to make a witness'
    # Initial cohort requirements are proof witnesses, never handler branches
    # or changes to the original effect/weapon implementation.
    attacks=native['coordinate_typed_weapon']['attacks'];name=case['name']
    if name=='original-catalogue/hp-shield/모더니아/favorite-0/30s':
        own=[a for a in attacks if a['owner']==0]
        assert any(a['weapon_mode_skill'] for a in own) and any(not a['weapon_mode_skill'] for a in own),'Original Modernia must enter its real skill-weapon mode'
    if name=='original-catalogue/projectile/앨리스/favorite-0/30s':
        assert any(a['owner']==0 for a in attacks) and any(a['owner']==0 for a in native['coordinate_typed_weapon']['full_charge_boundaries']),'Original Alice must actually fire full-charge shots'
    if name=='original-catalogue/hp-shield/프리바티 : 언카인드 메이드/favorite-0/30s':
        by_shot={}
        for a in attacks:
            if a['owner']==0:by_shot.setdefault(a['shot_identity'],[]).append(a)
        assert any(len(rows)>1 for rows in by_shot.values()),'Original shotgun must deliver several real pellets in one shot'
    return native
