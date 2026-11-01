"""Declared named range/count consumer at original skill creation."""
from contextlib import contextmanager,nullcontext
from unittest.mock import patch
import copy


def normalize(value):
    from product_coordinate_model import normalize as coordinates
    from named_range_battle import normalize as rules
    if type(value) is not dict or set(value)!={'coord','logical_geometry','rules'}:
        raise ValueError('Named range requires coord, logical_geometry and rules')
    result=coordinates(value['coord'],value['logical_geometry'],allow_empty=True)
    result['rules'],_=rules(value['rules'],result['logical_geometry'],allow_empty=True)
    return result


def public(data):
    """Actual cast quantities and recipient counts, not private candidate probes."""
    result=[]
    keys=('owner','effect','time','aim','percent','factor','base_radius','radius','base_count','additional_targets','capacity')
    for row in data['casts']:
        out={k:copy.deepcopy(row[k]) for k in keys}
        if row.get('selection'):
            import hashlib,struct
            raw=b''.join(struct.pack('<IIII',*recipient['handle'],0) for recipient in row['recipients'])
            out.update(selection=row['selection'],split=row['split'],recipient_count=len(row['recipients']),recipient_sha256=hashlib.sha256(raw).hexdigest())
        out['body_position']=next((i+1 for i,r in enumerate(row['recipients']) if r['handle'][0]==0),0)
        out['add_count']=sum(r['handle'][0]==5 for r in row['recipients'])
        result.append(out)
    return dict(casts=result)


@contextmanager
def execution(spec,*,coordinate_context=True,geometry_provider=None):
    # Resolve the common geometry provider before any checked rewrite.
    import engine_worker
    from named_range_battle import named_range_battle
    from product_coordinate_model import execution as coordinates
    from calculator.buff_manager import BuffManager
    from runner import sim
    initialize=BuffManager.__init__;execute=sim.execute
    def checked_execute(run,*args,**kwargs):
        if not spec['logical_geometry']:
            from calculator.boss_pattern import validate
            from world_actor_specs import bindings
            if any(int(b.kind)==5 for b in bindings(validate(copy.deepcopy(run.enemy.get('patterns') or []),coord=True))):
                raise ValueError('Every configured ADD requires explicit named range geometry, including future spawns')
        return execute(run,*args,**kwargs)
    def checked(manager,*args,**kwargs):
        initialize(manager,*args,**kwargs)
        for rule in spec['rules']:
            found=[e for e,owner in manager._effects if owner==rule['owner'] and e.get('name')==rule['effect']]
            if len(found)!=1:raise ValueError('Exact original named range owner/effect binding required')
            effect=found[0]
            nearby=rule.get('selection')=='primary-center-edge-v1'
            selector='target_and_nearby:'+str(rule['base_count']-1) if nearby else 'enemies_nearest:'+str(rule['base_count'])
            if (effect.get('type')!='damage' or effect.get('stat') not in (('damage','split_damage') if nearby else ('damage',)) or effect.get('target')!=selector
                or effect.get('tick_interval') or effect.get('hits_parts')):raise ValueError('Exact original nearest/nearby damage binding required')
    with patch.object(sim,'execute',checked_execute),patch.object(BuffManager,'__init__',checked),named_range_battle(spec['rules'],spec['logical_geometry'],geometry_provider=geometry_provider,allow_empty=True) as data,(coordinates(spec) if coordinate_context else nullcontext()):yield data
