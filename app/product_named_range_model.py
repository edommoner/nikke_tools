"""Declared named range/count consumer at original skill creation."""
from contextlib import contextmanager
from unittest.mock import patch
import copy


def normalize(value):
    from product_coordinate_model import normalize as coordinates
    from named_range_battle import normalize as rules
    if type(value) is not dict or set(value)!={'coord','logical_geometry','rules'}:
        raise ValueError('Named range requires coord, logical_geometry and rules')
    result=coordinates(value['coord'],value['logical_geometry'])
    result['rules'],_=rules(value['rules'],result['logical_geometry'])
    return result


def public(data):
    """Actual cast quantities and recipient counts, not private candidate probes."""
    result=[]
    keys=('owner','effect','time','aim','percent','factor','base_radius','radius','base_count','additional_targets','capacity')
    for row in data['casts']:
        out={k:copy.deepcopy(row[k]) for k in keys}
        out['body_position']=next((i+1 for i,r in enumerate(row['recipients']) if r['handle'][0]==0),0)
        out['add_count']=sum(r['handle'][0]==5 for r in row['recipients'])
        result.append(out)
    return dict(casts=result)


@contextmanager
def execution(spec):
    # Resolve the common geometry provider before any checked rewrite.
    import engine_worker
    from named_range_battle import named_range_battle
    from product_coordinate_model import execution as coordinates
    from calculator.buff_manager import BuffManager
    initialize=BuffManager.__init__
    def checked(manager,*args,**kwargs):
        initialize(manager,*args,**kwargs)
        for rule in spec['rules']:
            found=[e for e,owner in manager._effects if owner==rule['owner'] and e.get('name')==rule['effect']]
            if len(found)!=1:raise ValueError('Exact original named range owner/effect binding required')
            effect=found[0]
            if (effect.get('type')!='damage' or effect.get('stat')!='damage' or effect.get('target')!='enemies_nearest:'+str(rule['base_count'])
                or effect.get('tick_interval') or effect.get('hits_parts')):raise ValueError('Plain original nearest damage binding required')
    with patch.object(BuffManager,'__init__',checked),named_range_battle(spec['rules'],spec['logical_geometry']) as data,coordinates(spec):yield data
