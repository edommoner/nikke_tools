"""Read actual native retained named-skill accumulator keys, without formulas."""
def before_finish(manager,names):
    return sorted([dict(owner=names.index(owner),name=key[len('skill_crit:'):],value=value)
                   for (key,owner),value in manager.state['rng_acc'].items()
                   if key.startswith('skill_crit:') and owner in names],key=lambda r:(r['owner'],r['name']))
