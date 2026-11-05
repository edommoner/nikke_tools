"""HP-derived attack is a native late pass, outside the64-slot stat vector."""
STAT=89

def enabled(effect):
    return effect.get('type')=='buff' and effect.get('stat')=='atk_from_hp_pct'
