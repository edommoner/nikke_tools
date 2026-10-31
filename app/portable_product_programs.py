"""One product CLI family, with explicit kernel and immutable baseline selection.

Program identifiers are data, never import paths supplied by a packet. Legacy
packets without product_program retain their exact registered configuration.
"""
import copy
import json
from pathlib import Path

FAMILY = 'product-detail'
GOLDEN = 'research/portable-product-programs-v4-expected.json'
_registry=json.loads((Path(__file__).resolve().parents[1]/'data/portable-product-programs.json').read_text(encoding='utf-8'))
if type(_registry) is not dict or set(_registry)!={'schema','programs'} or type(_registry['schema']) is not int or _registry['schema']!=1 or type(_registry['programs']) is not dict:
    raise ValueError('Invalid product program registry')
PROGRAMS=_registry['programs']
for _name,_program in PROGRAMS.items():
    if type(_program) is not dict or set(_program)!={'source','input_words','output_words','mode','kind'}:
        raise ValueError('Invalid product program declaration')
    _mode,_kind=_program['mode'],_program['kind']
    _add=_name.startswith('add-');_healing=_name.startswith('healing-');_weighted=_name.startswith('weighted-');_cover=_name.startswith('cover-')
    _prefix='add-' if _add else 'healing-' if _healing else 'weighted-' if _weighted else 'cover-' if _cover else ''
    if _mode not in ('fixed','accumulate') or _kind not in ('','group','target','group-target') or (_healing or _weighted or _cover) and _kind!='' or _name!=_prefix+_mode+('-'+_kind if _kind else ''):
        raise ValueError('Invalid product program identity')
    _stem=('fixed_' if _mode=='fixed' else '')+(_kind.replace('-','_')+'_' if _kind else '')
    if _program['source']!='gpu/product_'+('add_' if _add else 'healing_' if _healing else 'weighted_' if _weighted else 'cover_' if _cover else '')+_stem+'battle_entry.slang' or any(type(_program[k]) is not int or _program[k]<=0 for k in ('input_words','output_words')):
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
                input_words=program['input_words'], output_words=program['output_words'])


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
    if name is not None and name.startswith('cover-'):
        from portable_cover_defense_battle_cases import fixtures
        case=fixtures()[0];body=copy.deepcopy(case['body'])
        body['reference_models']={'cover_defense':copy.deepcopy(case['cover_defense'])}
        body['manual_cover_sequences']=copy.deepcopy(case['declared_manual_sequences'])
    elif name is not None and name.startswith('weighted-'):
        from portable_weighted_battle_cases import fixtures
        case=fixtures()[0];body=copy.deepcopy(case['body'])
        body['reference_models']={'weighted_incoming':copy.deepcopy(case['allocation'])}
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
