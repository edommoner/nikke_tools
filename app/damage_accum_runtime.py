"""Register existing damage carriers and their retained quantities in shared state.

The pinned activation already snapshots cap and clears the live amount. Its
legacy fallback ledger must start the same lifetime at zero too; otherwise a
refresh followed by expiry without hits can release an earlier lifetime's data.
This consistency correction is independently tested, not hidden CPU parity.
"""
from effect_runtime import CATALOG,Handler,pool,state,active_carrier

STATS=frozenset(('dmg_accum_dealt_atk_pct','dmg_accum_received_atk_pct'))

def activate(manager,effect,caster,t):
    if effect.get('type')!='buff' or effect.get('stat') not in STATS:return
    carrier=active_carrier(manager,effect,caster)
    if carrier is None:return
    pool(manager,'damage_accumulation')[carrier.uid]=carrier
    ledger=state(manager).archive('damage_accumulation',manager._accum_last)
    name=effect.get('name','')
    if name:ledger[name]=carrier.accum

def install():
    if 'damage_accumulation' in CATALOG.handlers:return
    CATALOG.register('damage_accumulation',Handler(activate=activate,resource_kind='damage_accumulation'))
