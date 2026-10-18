"""Bind the reference's existing maximum-HP snapshots to shared instance state.

Numerical activation and current-HP updates remain in the pinned reference;
the registered carrier is the same object subsequently updated by that code.
"""
from effect_runtime import CATALOG,Handler,pool,active_carrier

def activate(manager,effect,caster,t):
    if effect.get('type')!='buff' or effect.get('stat')!='max_hp_from_max_hp_pct':return
    carrier=active_carrier(manager,effect,caster)
    if carrier is not None:pool(manager,'max_hp_snapshot')[carrier.uid]=carrier

def install():
    if 'max_hp_snapshot' in CATALOG.handlers:return
    CATALOG.register('max_hp_snapshot',Handler(activate=activate,resource_kind='max_hp_snapshot'))
