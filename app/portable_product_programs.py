"""One product CLI family, with explicit kernel and immutable baseline selection.

Program identifiers are data, never import paths supplied by a packet. Legacy
packets without product_program retain their exact registered configuration.
"""
import copy
import json
from pathlib import Path

FAMILY = 'product-detail'
GOLDEN = 'research/portable-product-programs-v66-expected.json'
_registry=json.loads((Path(__file__).resolve().parents[1]/'data/portable-product-programs.json').read_text(encoding='utf-8'))
if type(_registry) is not dict or set(_registry)!={'schema','programs'} or type(_registry['schema']) is not int or _registry['schema']!=1 or type(_registry['programs']) is not dict:
    raise ValueError('Invalid product program registry')
PROGRAMS=_registry['programs']
for _name,_program in PROGRAMS.items():
    if type(_program) is not dict or set(_program)!={'source','input_words','output_words','mode','kind'}:
        raise ValueError('Invalid product program declaration')
    _mode,_kind=_program['mode'],_program['kind']
    _default=_name.startswith('default-');_selector=_name[8:] if _default else _name
    _typed_lock=_selector.startswith('typed-lock-')
    _typed=_selector.startswith('typed-') and not _typed_lock
    _named_carriers=_selector.startswith('named-carriers-')
    _coordinate_lock=_selector.startswith('coordinate-lock-')
    _coordinate_healing=_selector.startswith('coordinate-healing-')
    _coordinate_add=_selector.startswith('coordinate-add-')
    _coordinate_weighted=_selector.startswith('coordinate-weighted-')
    _coordinate_cover=_selector.startswith('coordinate-cover-')
    _coordinate=_selector.startswith('coordinate-') and not (_coordinate_cover or _coordinate_weighted or _coordinate_add or _coordinate_healing or _coordinate_lock)
    _lock_cover=_selector.startswith('lock-cover-')
    _range_cover=_selector.startswith('named-range-cover-')
    _movement_range_cover=_selector.startswith('movement-range-cover-')
    _movement_cover=_selector.startswith('movement-cover-');_ammo_cover=_selector.startswith('ammo-cover-');_healing_cover=_selector.startswith('healing-cover-');_add=_selector.startswith('add-');_healing=_selector.startswith('healing-');_weighted=_selector.startswith('weighted-');_cover=_selector.startswith('cover-');_ammo=_selector.startswith('ammo-');_movement=_selector.startswith('movement-');_range=_selector.startswith('named-range-');_lock=_selector.startswith('lock-')
    if _default and (not (_weighted or _cover) or _mode!='fixed' or _kind):raise ValueError('Invalid default-world product program')
    _prefix=('default-' if _default else '')+('typed-lock-' if _typed_lock else 'typed-' if _typed else 'named-carriers-' if _named_carriers else 'coordinate-lock-' if _coordinate_lock else 'coordinate-healing-' if _coordinate_healing else 'coordinate-add-' if _coordinate_add else 'coordinate-weighted-' if _coordinate_weighted else 'coordinate-cover-' if _coordinate_cover else 'coordinate-' if _coordinate else 'add-' if _add else 'ammo-cover-' if _ammo_cover else 'healing-cover-' if _healing_cover else 'healing-' if _healing else 'weighted-' if _weighted else 'cover-' if _cover else 'ammo-' if _ammo else 'movement-range-cover-' if _movement_range_cover else 'movement-cover-' if _movement_cover else 'movement-' if _movement else 'named-range-cover-' if _range_cover else 'named-range-' if _range else 'lock-cover-' if _lock_cover else 'lock-' if _lock else '')
    if _mode not in ('fixed','accumulate') or _kind not in ('','group','target','group-target') or (_typed_lock or _typed or _named_carriers or _coordinate_lock or _coordinate_healing or _coordinate_add or _coordinate_weighted or _coordinate_cover or _coordinate or _movement or _range or _lock) and _kind!='' or _weighted and _kind not in ('','group') or (_ammo or _ammo_cover) and _kind not in ('','group','target') or _healing and _kind not in ('','group') or _healing_cover and _kind not in ('','group') or _name!=_prefix+_mode+('-'+_kind if _kind else ''):
        raise ValueError('Invalid product program identity')
    _stem=('fixed_' if _mode=='fixed' else '')+(_kind.replace('-','_')+'_' if _kind else '')
    if _program['source']!='gpu/product_'+('typed_lock_' if _typed_lock else 'typed_' if _typed else 'named_carriers_' if _named_carriers else 'coordinate_lock_' if _coordinate_lock else 'coordinate_healing_' if _coordinate_healing else 'coordinate_add_' if _coordinate_add else 'coordinate_weighted_' if _coordinate_weighted else 'coordinate_cover_' if _coordinate_cover else 'coordinate_' if _coordinate else 'add_' if _add else 'ammo_cover_' if _ammo_cover else 'healing_cover_' if _healing_cover else 'healing_' if _healing else 'weighted_' if _weighted else 'cover_' if _cover else 'ammo_' if _ammo else 'movement_range_cover_' if _movement_range_cover else 'movement_cover_' if _movement_cover else 'movement_' if _movement else 'named_range_cover_' if _range_cover else 'named_range_' if _range else 'lock_cover_' if _lock_cover else 'lock_' if _lock else '')+_stem+'battle_entry.slang' or any(type(_program[k]) is not int or _program[k]<=0 for k in ('input_words','output_words')):
        raise ValueError('Invalid product source or wire declaration')


def configuration(suites, selection):
    if isinstance(selection, str):
        return suites[selection]
    base = suites[selection['suite']]
    if 'product_program' not in selection:
        return base
    name = selection['product_program']
    if selection['suite'] != FAMILY or not isinstance(name, str) or name not in PROGRAMS:
        raise ValueError('Invalid product program selection')
    program = PROGRAMS[name]
    return dict(base, product_program=name, source=program['source'], golden=GOLDEN,
                input_words=program['input_words'], output_words=program['output_words'],
                inputs=7 if name=='ammo-cover-fixed-group' else 6 if name.startswith('typed-') else 3 if name=='fixed' else 2 if name.startswith('coordinate-lock-') or name=='lock-fixed' else 1,native=7 if name=='ammo-cover-fixed-group' else 6 if name.startswith('typed-') else 3 if name=='fixed' else 2 if name.startswith('coordinate-lock-') or name=='lock-fixed' else 1)


def registered_golden(root, config, *, allow_unsealed=False):
    document = json.loads((Path(root) / config['golden']).read_text(encoding='utf-8'))
    if 'product_program' not in config:
        return document
    if (type(document) is not dict or set(document) != {'schema', 'programs'}
            or type(document['schema']) is not int or document['schema'] != 1
            or type(document['programs']) is not dict or not set(document['programs']) <= set(PROGRAMS)):
        raise ValueError('Invalid registered product program baselines')
    name = config['product_program']
    if name not in document['programs']:
        if allow_unsealed:return None
        raise ValueError('Product program has no independently sealed baseline: ' + name)
    golden = document['programs'][name]
    if type(golden) is not dict:
        raise ValueError('Invalid registered product program golden')
    return golden


def body_for_program(root, name=None):
    if name is not None and (not isinstance(name,str) or name not in PROGRAMS):
        raise ValueError('Invalid product program body')
    program = PROGRAMS.get(name, dict(mode='accumulate', kind=''))
    if name is not None and name.startswith('typed-lock-'):
        from coordinate_typed_actor_policy import FIELD_MODE
        from coordinate_typed_aim_runtime import POLICY
        body=body_for_program(root,'coordinate-lock-'+program['mode']);body['duration']=4.
        body['enemy']['patterns'][0]['until']['time']=5.
        models=body['reference_models'];locks=copy.deepcopy(models['lock_on'])
        for i,row in enumerate(locks['typed_bindings']):row.update(owner=[0,0,1],label='projectile-'+str(i))
        typed=dict(coord=models['coordinate']['coord'],bindings=copy.deepcopy(locks['typed_bindings']),
            geometry=dict(point_source='caster_aim',shapes=[dict(x=0.,y=0.,r=1000.,z=float(i)) for i in range(3)]),
            aim_policy={'mode':POLICY},actor_policy={'mode':FIELD_MODE})
        body['reference_models']=dict(typed_targets=typed,lock_on=locks)
    elif name is not None and name.startswith('typed-'):
        from portable_coordinate_typed_owner_cases import fixtures
        case=next(row for row in fixtures() if row['name'].endswith('/body'))
        body=copy.deepcopy(case['body']);body['duration']=3.
        body['reference_models']={'typed_targets':dict(coord=copy.deepcopy(case['coord']),bindings=copy.deepcopy(case['typed_bindings']),geometry=copy.deepcopy(case['typed_geometry']),aim_policy=copy.deepcopy(case['typed_aim_policy']),actor_policy=copy.deepcopy(case['typed_actor_policy']))}
    elif name is not None and name.startswith('named-carriers-'):
        from portable_original_identity_inventory import selected_profile_bodies
        body=selected_profile_bodies(['레이 (가칭)'],0)[0][2]
    elif name is not None and name.startswith('coordinate-lock-'):
        body=body_for_program(root,'lock-'+program['mode'])
        body['reference_models']['coordinate']=dict(coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),logical_geometry=[])
        body['enemy']['patterns']=[dict(id='coordinate-projectiles',kind='idle',until=dict(time=31.))]
        body['reference_models']['lock_on']['typed_bindings']=[dict(node='coordinate-projectiles',kind=2,identity=i,capacity=1e8) for i in (10,11,12)]
    elif name is not None and name.startswith('coordinate-healing-'):
        from portable_enemy_healing_cases import fixtures
        case=fixtures()[0];body=copy.deepcopy(case['body']);body['duration']=30
        body['reference_models']={'coordinate':dict(coord=copy.deepcopy(case['coord']),logical_geometry=copy.deepcopy(case['logical_geometry'])),'enemy_healing':copy.deepcopy(case['enemy_healing'])}
    elif name is not None and name.startswith('coordinate-add-'):
        from portable_add_self_destruct_cases import fixtures
        case=next(row for row in fixtures() if row['contract']['scenario']=='spaced')
        body=copy.deepcopy(case['body'])
        body['reference_models']={'coordinate':dict(coord=copy.deepcopy(case['coord']),logical_geometry=copy.deepcopy(case['logical_geometry']))}
    elif name is not None and name.startswith('coordinate-weighted-'):
        from portable_coordinate_original_cases import fixtures
        body=body_for_program(root,'weighted-'+program['mode']+'-group')
        case=fixtures()[0]
        body['reference_models']['coordinate']=dict(coord=copy.deepcopy(case['coord']),logical_geometry=[])
        # Original finite ADD actors with explicitly declared colliders, no PART proxies.
        body['enemy']['patterns'].append(dict(id='declared-wave',kind='summon',spec=dict(count=4,hp=1e12)))
        body['reference_models']['coordinate']['logical_geometry']=[dict(label='__enemy__:declared-wave#'+str(i+1),shape=dict(x=0.,y=0.,r=100.,z=i)) for i in range(4)]
    elif name is not None and name.startswith('coordinate-cover-'):
        body=body_for_program(root,'coordinate-'+program['mode'])
        names=body['squad'];body['reference_models']['cover_defense']=[dict(name=n,base_defense=100+10*i) for i,n in enumerate(names)]
        body['manual_cover_sequences']={names[0]:[dict(action='cover',t=.5,duration=2.)]}
        body['enemy']['patterns'].append(dict(id='coordinate-incoming',kind='attack',delay=.75,spec=dict(atk=1000,coeff=100,target='all',hits=2,interval=.5)))
    elif name is not None and name.startswith('coordinate-'):
        import engine_worker
        from portable_coordinate_original_cases import fixtures
        case=fixtures()[0];body=copy.deepcopy(case['body']);body['duration']=30
        body['enemy']['patterns']=copy.deepcopy(case['patterns'])
        body['reference_models']={'coordinate':dict(coord=copy.deepcopy(case['coord']),logical_geometry=[])}
    elif name is not None and name.startswith('movement-range-cover-'):
        from detail_coverage import body_for
        body=body_for_program(root,'named-range-'+program['mode'])
        motion=body_for_program(root,'movement-'+program['mode'])['reference_models']['enemy_movement']
        roster=body['squad'][:2]+['솔져 O.W.','유니','얀'];body['squad']=roster;body['duration']=30
        body['profile']=body_for(roster,30)['profile']
        spec=body['reference_models']['named_range']
        motion['coord']=copy.deepcopy(spec['coord']);motion['logical_geometry']=copy.deepcopy(spec['logical_geometry'])
        motion['motion']['actors']=[dict(label=r['label'],velocity=[.1,0.],force_center=[0.,0.]) for r in spec['logical_geometry']]
        body['reference_models'].update(enemy_movement=motion,cover_defense=[dict(name=n,base_defense=100+10*i) for i,n in enumerate(roster)])
        body['manual_cover_sequences']={roster[2]:[dict(action='cover',t=10,duration=2)]}
        body['enemy']['patterns'].append(dict(id='declared-incoming',kind='attack',delay=10.25,spec=dict(atk=1000,coeff=100,target='all',hits=5,interval=.5)))
    elif name is not None and name.startswith('lock-cover-'):
        from detail_coverage import body_for
        body=body_for_program(root,'lock-'+program['mode'])
        roster=body['squad'][:-1]+['솔져 O.W.'];literal=body_for(roster,body['duration'])
        body['squad']=roster;body['profile']=literal['profile']
        body['reference_models']['cover_defense']=[dict(name=n,base_defense=100+10*i) for i,n in enumerate(roster)]
        body['manual_cover_sequences']={roster[0]:[dict(action='cover',t=10,duration=2)]}
        body['enemy']['patterns']=[dict(id='lock-wave',kind='summon',spec=dict(count=2,hp=1e30)),dict(id='declared-incoming',kind='attack',delay=10.25,spec=dict(atk=1000,coeff=100,target='all',hits=5,interval=.5))]
    elif name is not None and name.startswith('lock-'):
        import engine_worker
        from portable_heavyarms_lock_cases import fixtures,NAME,source_definitions
        from product_lock_model import ORDER,MARKER,DELIVERY_MODEL
        body=copy.deepcopy(fixtures()[1]['body'])
        body['reference_models']={'lock_on':dict(owner=NAME,marker=MARKER,packet_skill=source_definitions()[8]['name'],candidate_order=ORDER,delivery=DELIVERY_MODEL,typed_bindings=[])}
    elif name is not None and name.startswith('named-range-cover-'):
        from detail_coverage import body_for
        body=body_for_program(root,'named-range-'+program['mode'])
        roster=body['squad'][:-1]+['솔져 O.W.'];literal=body_for(roster,body['duration'])
        body['squad']=roster;body['profile']=literal['profile']
        body['reference_models']['cover_defense']=[dict(name=n,base_defense=100+10*i) for i,n in enumerate(roster)]
        body['manual_cover_sequences']={roster[0]:[dict(action='cover',t=10,duration=2)]}
        body['enemy']['patterns'].append(dict(id='declared-incoming',kind='attack',delay=10.25,spec=dict(atk=1000,coeff=100,target='all',hits=5,interval=.5)))
    elif name is not None and name.startswith('named-range-'):
        from portable_named_range_battle_cases import fixtures
        case=fixtures()[0];body=copy.deepcopy(case['body'])
        body['reference_models']={'named_range':dict(coord=copy.deepcopy(case['coord']),logical_geometry=copy.deepcopy(case['logical_geometry']),rules=copy.deepcopy(case['named_range_rules']))}
    elif name is not None and name.startswith('movement-cover-'):
        body=body_for_program(root,'movement-'+program['mode'])
        body['manual_cover_sequences']={body['squad'][0]:[dict(action='cover',t=.5,duration=.25)]}
    elif name is not None and name.startswith('movement-'):
        import engine_worker
        from portable_enemy_movement_cases import fixtures
        case=fixtures()[0];body=copy.deepcopy(case['body'])
        body['reference_models']={'enemy_movement':dict(coord=copy.deepcopy(case['coord']),logical_geometry=copy.deepcopy(case['logical_geometry']),motion=copy.deepcopy(case['enemy_movement']))}
    elif name is not None and name.startswith('ammo-') and program['kind']=='target':
        from detail_coverage import body_for
        from portable_enemy_ammo_cases import fixtures
        cover=name.startswith('ammo-cover-')
        body=body_for(['벨벳','아스카','솔져 O.W.' if cover else '미란다','도라','드레이크'],30)
        case=fixtures()[0];body['enemy'].update(has_parts=False,patterns=copy.deepcopy(case['patterns']))
        body['reference_models']={'enemy_ammo':copy.deepcopy(case['enemy_ammo'])}
        if cover:
            body['reference_models']['cover_defense']=[dict(name=n,base_defense=1000.) for n in body['squad']]
            body['manual_cover_sequences']={body['squad'][2]:[dict(action='cover',t=.5,duration=.25)]}
    elif name is not None and (name.startswith('ammo-') or name.startswith('ammo-cover-')) and program['kind']=='group':
        from detail_coverage import body_for
        from portable_enemy_ammo_cases import fixtures
        body=body_for(['벨벳','벨로타','솔져 O.W.' if name.startswith('ammo-cover-') else '미란다','도라','드레이크'],30)
        case=fixtures()[0]
        body['enemy'].update(has_parts=False,patterns=copy.deepcopy(case['patterns']))
        body['reference_models']={'enemy_ammo':copy.deepcopy(case['enemy_ammo'])}
        if name.startswith('ammo-cover-'):
            body['reference_models']['cover_defense']=[dict(name=n,base_defense=1000.) for n in body['squad']]
            body['manual_cover_sequences']={body['squad'][2]:[dict(action='cover',t=.5,duration=.25)]}
    elif name is not None and name.startswith('ammo-cover-'):
        from detail_coverage import body_for
        body=body_for(['벨벳','솔져 O.W.','미란다','도라','드레이크'],30)
        body['manual_cover_sequences']={body['squad'][1]:[dict(action='cover',t=.5,duration=.25)]}
    elif name is not None and name.startswith('ammo-'):
        if program['mode']=='fixed':
            from portable_original_identity_inventory import selected_profile_bodies
            body=selected_profile_bodies(['벨벳'],0)[0][2]
        else:
            import engine_worker
            from portable_enemy_ammo_cases import fixtures
            case=fixtures()[0];body=copy.deepcopy(case['body'])
            body['reference_models']={'enemy_ammo':copy.deepcopy(case['enemy_ammo'])}
    elif name is not None and name.startswith('default-'):
        from portable_original_identity_inventory import selected_profile_bodies
        body=selected_profile_bodies(['베이' if name.startswith('default-weighted-') else '솔져 O.W.'],0)[0][2]
    elif name is not None and name.startswith('cover-') and program['kind']:
        body=body_for_program(root,program['mode']+'-'+program['kind'])
        body['manual_cover_sequences']={body['squad'][0]:[dict(action='cover',t=.5,duration=.25)]}
    elif name is not None and name.startswith('cover-'):
        from portable_cover_defense_battle_cases import fixtures
        case=fixtures()[0];body=copy.deepcopy(case['body'])
        body['reference_models']={'cover_defense':copy.deepcopy(case['cover_defense'])}
        body['manual_cover_sequences']=copy.deepcopy(case['declared_manual_sequences'])
    elif name is not None and name.startswith('weighted-'):
        from portable_weighted_battle_cases import fixtures
        case=fixtures()[0];body=copy.deepcopy(case['body'])
        body['reference_models']={'weighted_incoming':copy.deepcopy(case['allocation'])}
        if program['kind']=='group':
            from detail_coverage import body_for
            names=['베이','벨로타','미란다','도라','드레이크']
            literal=body_for(names,body['duration'])
            literal['profile']['chars']['베이']=copy.deepcopy(body['profile']['chars']['베이'])
            body.update(squad=names,profile=literal['profile'])
    elif name is not None and name.startswith('healing-cover-') and program['kind']=='group':
        from detail_coverage import body_for
        from portable_enemy_healing_cases import fixtures
        case=fixtures()[0];roster=['앤 : 미라클 페어리','벨로타','솔져 O.W.','도라','드레이크']
        body=body_for(roster,30);body['enemy']['patterns']=copy.deepcopy(case['patterns'])
        body['enemy']['patterns'].append(dict(id='declared-cover-hit',kind='attack',delay=7.5,spec=dict(atk=100000.,coeff=100,target='slot:3',ignore_taunt=True,pierce=False,hits=1,interval=.1)))
        body['reference_models']={'enemy_healing':copy.deepcopy(case['enemy_healing']),'cover_defense':[dict(name=n,base_defense=1000.) for n in roster]}
        body['manual_cover_sequences']={roster[2]:[dict(action='cover',t=7.4,duration=.25)]}
    elif name is not None and name.startswith('healing-cover-'):
        from detail_coverage import body_for
        body=body_for(['앤 : 미라클 페어리','솔져 O.W.','미란다','도라','드레이크'],30)
        body['manual_cover_sequences']={body['squad'][1]:[dict(action='cover',t=.5,duration=.25)]}
    elif name is not None and name.startswith('healing-') and program['kind']=='group':
        from detail_coverage import body_for
        from portable_enemy_healing_cases import fixtures
        case=fixtures()[0];roster=['앤 : 미라클 페어리','벨로타','미란다','도라','드레이크']
        body=body_for(roster,30);body['enemy']['patterns']=copy.deepcopy(case['patterns'])
        body['reference_models']={'enemy_healing':copy.deepcopy(case['enemy_healing'])}
    elif name is not None and name.startswith('healing-'):
        from portable_original_identity_inventory import selected_profile_bodies
        body=selected_profile_bodies(['앤 : 미라클 페어리'],0)[0][2]
    elif program['kind'] in ('group', 'target'):
        from portable_original_identity_inventory import selected_profile_bodies
        character = '벨로타' if program['kind'] == 'group' else '아스카'
        body = selected_profile_bodies([character], 0)[0][2]
    elif program['kind'] == 'group-target':
        from detail_coverage import body_for
        body = body_for(['사쿠라', '벨로타', '미란다', '도라', '드레이크'], 30)
    else:
        body = json.loads((Path(root) / 'tests/fixtures/portable-detail-product-v1.json').read_text(encoding='utf-8'))['body']
    body = copy.deepcopy(body)
    body['burst_gauge_mode'] = program['mode']
    if name is not None and name.startswith('add-'):
        body['enemy']['patterns']=[dict(id='product-escort',kind='summon',until=dict(targets_cleared=True),spec=dict(
            name='Escort',count=2,hp=1e12,attack_at=.25,self_destruct=True,
            attack=dict(atk=1000,coeff=100,hits=2,interval=.5,target='all',debuffs=[
                dict(stat='atk_pct',value=-10),dict(stat='dot',coeff=10,interval=.5,duration=1)])))]
    return body


def cases_for_program(root,name=None):
    """Extend the existing product corpus, keeping its original case first."""
    base=body_for_program(root,name);rows=[(None,base)]
    if name in ('fixed','lock-fixed'):
        from portable_original_identity_inventory import selected_profile_bodies
        owners=['\uc2a4\ub178\uc6b0 \ud654\uc774\ud2b8 : \ud5e4\ube44\uc554\uc988'] if name.startswith('lock-') else ['\uc720\ub2c8','\uc580']
        for i,owner in enumerate(owners):
            body=copy.deepcopy(selected_profile_bodies([owner],0)[0][2]);body.update(duration=30.,burst_gauge_mode=PROGRAMS[name]['mode'])
            rows.append(('default-body-'+str(i),body))
    if name is not None and name.startswith('coordinate-lock-'):
        body=copy.deepcopy(base);body['duration']=56.;body['enemy']['patterns'][0]['until']['time']=57.
        rows.append(('long56',body))
    if name is not None and name.startswith('typed-lock-'):
        body=copy.deepcopy(base)
        for model,key in ((body['reference_models']['lock_on'],'typed_bindings'),(body['reference_models']['typed_targets'],'bindings')):
            for row in model[key]:row['capacity']=1.
        rows.append(('broken',body))
        body=copy.deepcopy(base)
        body['enemy']['patterns'].append(dict(id='typed-lock-wave',kind='summon',delay=.5,until=dict(time=3.5),spec=dict(count=2,hp=1e8)))
        body['reference_models']['typed_targets']['logical_geometry']=[dict(label='__enemy__:typed-lock-wave#'+str(i+1),shape=dict(x=0.,y=0.,r=1000.,z=3.+i)) for i in range(2)]
        rows.append(('two-adds',body))
        body=copy.deepcopy(next(b for v,b in cases_for_program(root,'typed-'+PROGRAMS[name]['mode']) if v=='nearby-primary'))
        from portable_heavyarms_lock_cases import NAME
        body['squad']=[NAME if n=='\ub4dc\ub808\uc774\ud06c' else n for n in body['squad']]
        body['profile']['chars'][NAME]=copy.deepcopy(base['profile']['chars'][NAME])
        lock=copy.deepcopy(base['reference_models']['lock_on'])
        lock['typed_bindings']=copy.deepcopy(body['reference_models']['typed_targets']['bindings'])
        body['reference_models']['lock_on']=lock
        rows.append(('nearby-mixed',body))
    if name in ('typed-fixed','typed-accumulate'):
        body=copy.deepcopy(base)
        body['enemy']['patterns'].append(dict(id='typed-wave',kind='summon',delay=.5,until=dict(time=2.),spec=dict(count=2,hp=1e8)))
        body['reference_models']['typed_targets']['logical_geometry']=[dict(label='__enemy__:typed-wave#'+str(i+1),shape=dict(x=0.,y=0.,r=1000.,z=3.+i)) for i in range(2)]
        rows.append(('two-adds',body))
        body=copy.deepcopy(body)
        body['reference_models']['typed_targets']['bindings'][0]['kind']=2
        rows.append(('mixed-two-adds',body))
        from portable_original_identity_inventory import selected_profile_bodies
        nearby=copy.deepcopy(selected_profile_bodies(['\uc77c\ub808\uadf8'],0)[0][2])
        nearby.update(duration=12.,burst_gauge_mode=PROGRAMS[name]['mode'])
        nearby['enemy']['patterns']=copy.deepcopy(body['enemy']['patterns'])
        nearby['enemy']['patterns'][0]['until']['time']=20.
        nearby['enemy']['patterns'][-1].update(delay=0.,until=dict(time=20.),spec=dict(count=3,hp=1e30))
        nearby['reference_models']=copy.deepcopy(body['reference_models'])
        spec=nearby['reference_models']['typed_targets']
        spec['bindings'][0]['kind']=3;spec['bindings'][1]['kind']=2
        for shape in spec['geometry']['shapes']:shape.update(x=0.,y=0.,r=1000.)
        spec['logical_geometry']=[dict(label='__enemy__:typed-wave#'+str(i+1),shape=dict(x=x,y=0.,r=1.,z=-3.)) for i,x in enumerate((0.,10.,100.))]
        spec['nearby_rules']=[dict(owner='\uc77c\ub808\uadf8',effect='\uc1fc\ud2b8 2',base_count=3,base_radius=20.,body_shape=dict(x=-10.,y=0.,r=1.),selection='primary-center-edge-v1')]
        rows.append(('nearby-primary',nearby))
    if name=='ammo-cover-fixed-group':
        from portable_enemy_ammo_self_destruct_cases import fixtures
        for case in fixtures():
            scenario=case['contract']['scenario']
            if scenario not in ('coincident','reload-final'):continue
            body=copy.deepcopy(base);body['duration']=6
            body['enemy']['patterns']=copy.deepcopy(case['patterns'])
            body['reference_models']['enemy_ammo']=copy.deepcopy(case['enemy_ammo'])
            rows.append((scenario+'-final-queue',body))
        from detail_coverage import body_for
        names=['벨벳','사쿠라','벨로타','솔져 O.W.','드레이크']
        body=copy.deepcopy(base);body.update(squad=names,profile=body_for(names,15)['profile'],duration=15)
        body['reference_models']['cover_defense']=[dict(name=n,base_defense=1000.) for n in names]
        body['manual_cover_sequences']={names[3]:[dict(action='cover',t=.5,duration=.25)]}
        rows.append(('target-modifier-carriers',body))
        case=next(c for c in fixtures() if c['contract']['scenario']=='coincident')
        body=copy.deepcopy(body);body['duration']=6;body['enemy']['patterns']=copy.deepcopy(case['patterns'])
        body['reference_models']['enemy_ammo']=copy.deepcopy(case['enemy_ammo'])
        rows.append(('target-modifier-final-queue',body))
        names=['앤 : 미라클 페어리','벨벳','벨로타','솔져 O.W.','드레이크']
        body=copy.deepcopy(base);body.update(squad=names,profile=body_for(names,15)['profile'],duration=15)
        body['reference_models']['cover_defense']=[dict(name=n,base_defense=1000.) for n in names]
        body['manual_cover_sequences']={names[3]:[dict(action='cover',t=.5,duration=.25)]}
        times=[0.,.25,1.,2.]
        body['enemy']['patterns'] += [dict(id='ammo-heal-'+str(i),kind='idle',delay=t) for i,t in enumerate(times)]
        targets=[row['label'] for row in body['reference_models']['enemy_ammo'] if row['label']!='__enemy__']
        body['reference_models']['enemy_healing']=[dict(node='ammo-heal-'+str(i),targets=targets,amount=1000000.) for i in range(len(times))]
        rows.append(('healing-magazines',body))
        body=copy.deepcopy(body);body['duration']=6
        body['enemy']['patterns'][0]['spec'].update(self_destruct=True,attack_at=.25)
        body['enemy']['patterns'][0]['spec']['attack'].update(hits=3,interval=0.)
        rows.append(('healing-final-queue',body))
    if name is not None and name.startswith('typed-'):
        body=copy.deepcopy(rows[-1][1])
        from portable_original_identity_inventory import selected_profile_bodies
        owner='\uc720\ub2c8';healer='\uba54\uc5b4\ub9ac'
        original=selected_profile_bodies([owner],0)[0][2]
        body['squad']=[owner if n==healer else n for n in body['squad']]
        body['profile']['chars'][owner]=copy.deepcopy(original['profile']['chars'][owner])
        typed=body['reference_models']['typed_targets']
        motion=dict(precedence='disable-before-force',force_policy='snap-to-declared-center',recipient_policy='canonical-all-in-range',actors=[dict(label=row['label'],velocity=[v,0.],force_center=[0.,0.]) for row,v in zip(typed['logical_geometry'],[4.,-3.,-8.],strict=True)])
        body['reference_models']['enemy_movement']=dict(coord=copy.deepcopy(typed['coord']),logical_geometry=copy.deepcopy(typed['logical_geometry']),motion=motion)
        rows.append(('moving-nearby',body))
        body=copy.deepcopy(body);body['duration']=30.
        for pattern in body['enemy']['patterns']:
            if 'time' in pattern.get('until',{}):pattern['until']['time']=31.
        rows.append(('moving-long30',body))
    return rows
