"""Read actual native carrier snapshots; no reconstructed selection or HP math."""
def before_finish(manager,names):
    rows=[]
    for carrier in manager._active:
        effect=carrier.effect
        if effect.get('stat') not in ('atk_copy','hp_copy'):continue
        rows.append(dict(name=effect.get('name',''),stat=effect['stat'],owner=names.index(carrier.caster),
            recipients=sorted(names.index(n) for n in carrier.target_chars or []),stacks=carrier.stack,
            basis=carrier.copy_basis,source=None if carrier.copy_source is None else names.index(carrier.copy_source),
            gift=getattr(carrier,'copy_last_gift',0)))
    return sorted(rows,key=lambda r:(r['owner'],r['name'],r['stat'],r['recipients']))
