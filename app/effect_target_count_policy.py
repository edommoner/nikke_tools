"""Explicit named-effect capacity reader using existing native carrier rules.

This adds a model reader, not canonical admission or spatial lock selection.
Ordinary numeric readers, their namespaces and their caches stay untouched.
"""
import math,types
from destructible_damage_policy import _clone

STAT='effect_target_count_add'
MODEL='named-effect-target-count-v1'


def validate_effect(effect):
    if effect.get('stat')!=STAT:return False
    value=effect.get('fixed_value')
    if (effect.get('type')!='buff' or effect.get('target') not in ('self','all_allies')
        or not isinstance(effect.get('target_effect'),str) or not effect['target_effect']
        or type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=2147483647 or value!=int(value)
        or any(effect.get(k) is not None for k in ('scaling','scaling_ref','values','tick_interval','tick_start'))):
        raise ValueError('Named target-count model requires fixed integral allied modifiers')
    return True


def _reader(fn,expected,stat=STAT):
    """Retain native wrappers, including previously cloned modifier readers."""
    if fn.__code__ is not expected.__code__:
        raise ValueError('Unreviewed native target-count numeric reader')
    wrapped=getattr(expected,'__wrapped__',None)
    if wrapped is not None:
        cells=fn.__closure__ or ()
        positions=[i for i,cell in enumerate(cells) if isinstance(cell.cell_contents,types.FunctionType) and cell.cell_contents.__code__ is wrapped.__code__]
        if len(positions)!=1:raise ValueError('Unreviewed native target-count wrapper closure')
        index=positions[0];child=_reader(cells[index].cell_contents,wrapped,stat)
        return _clone(fn,fn.__globals__,tuple(types.CellType(child) if i==index else cell for i,cell in enumerate(cells)))
    scope=dict(fn.__globals__)
    if '_STAT_TO_BUFF' not in scope or '_BUFFS_ZERO' not in scope or stat in scope['_STAT_TO_BUFF'] or stat in scope['_BUFFS_ZERO']:
        raise ValueError('Native target-count consumer changed; re-audit explicit model')
    scope['_STAT_TO_BUFF']=dict(scope['_STAT_TO_BUFF'],**{stat:stat})
    scope['_BUFFS_ZERO']=dict(scope['_BUFFS_ZERO'],**{stat:0.})
    return _clone(fn,scope)


class _Query:
    """Ephemeral view: only matching carriers; no mutation of a live manager."""
    def __init__(self,manager,marker,stat=STAT):
        from calculator.buff_manager import BuffManager
        self._manager=manager
        self._active=[ab for ab in manager._active if ab.effect.get('stat')==stat and ab.effect.get('target_effect')==marker]
        self._plan_cache={};self._buffs_cache={}
        if type(manager)._build_plan is not BuffManager._build_plan:
            raise ValueError('Unreviewed native target-count plan builder')
        self._build_plan=types.MethodType(BuffManager._build_plan,self)
        self._plan_step=types.MethodType(_reader(type(manager)._plan_step,BuffManager._plan_step,stat),self)
        self.get_buffs=types.MethodType(_reader(type(manager).get_buffs,BuffManager.get_buffs,stat),self)
    def __getattr__(self,name):return getattr(self._manager,name)


def query(manager,caster,marker,when,*,base_count,capacity_limit,model):
    """Read exact-name capacity; selection, firing and world admission are separate."""
    from calculator.buff_manager import BuffManager
    if (model!=MODEL or not isinstance(manager,BuffManager) or caster not in manager.squad_names
        or not isinstance(marker,str) or not marker or type(when) not in (int,float) or not math.isfinite(when) or when<0
        or type(capacity_limit) is not int or not 1<=capacity_limit<=2147483647
        or type(base_count) is not int or not 0<=base_count<=capacity_limit):
        raise ValueError('Explicit finite named target-count context required')
    for effect,_ in manager._effects:validate_effect(effect)
    for ab in manager._active:
        if validate_effect(ab.effect) and ab.target_chars is None:
            raise ValueError('Lazy target-count recipients require a separate contract')
    view=_Query(manager,marker)
    value=view.get_buffs(caster,'__enemy__',when)[STAT]
    capacity=base_count+value
    if not math.isfinite(capacity) or not 0<=capacity<=capacity_limit or capacity!=int(capacity):
        raise ValueError('Target-count result outside exact integral capacity')
    return dict(model=MODEL,base_count=base_count,additional_targets=value,capacity=int(capacity),
        spatial_selection_verified=False,gpu_supported=False)
