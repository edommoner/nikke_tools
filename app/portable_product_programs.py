"""One product CLI family, with explicit kernel and immutable baseline selection.

Program identifiers are data, never import paths supplied by a packet. Legacy
packets without product_program retain their exact registered configuration.
"""
import copy
import json
from pathlib import Path

FAMILY = 'product-detail'
GOLDEN = 'research/portable-product-programs-v1-expected.json'
_registry=json.loads((Path(__file__).resolve().parents[1]/'data/portable-product-programs.json').read_text(encoding='utf-8'))
if type(_registry) is not dict or set(_registry)!={'schema','programs'} or type(_registry['schema']) is not int or _registry['schema']!=1 or type(_registry['programs']) is not dict:
    raise ValueError('Invalid product program registry')
PROGRAMS=_registry['programs']
for _name,_program in PROGRAMS.items():
    if type(_program) is not dict or set(_program)!={'source','input_words','output_words','mode','kind'}:
        raise ValueError('Invalid product program declaration')
    _mode,_kind=_program['mode'],_program['kind']
    if _mode not in ('fixed','accumulate') or _kind not in ('','group','target','group-target') or _name!=_mode+('-'+_kind if _kind else ''):
        raise ValueError('Invalid product program identity')
    _stem=('fixed_' if _mode=='fixed' else '')+(_kind.replace('-','_')+'_' if _kind else '')
    if _program['source']!='gpu/product_'+_stem+'battle_entry.slang' or any(type(_program[k]) is not int or _program[k]<=0 for k in ('input_words','output_words')):
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
    if program['kind'] in ('group', 'target'):
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
    return body
