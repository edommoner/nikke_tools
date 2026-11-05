"""Original coordinate firing plus explicit typed targets and a declared attack."""
import copy
from original_modifier_probe_cases import fixtures as original_probes
from portable_coordinate_original_cases import fixtures as originals

def fixtures():
    control=copy.deepcopy(originals()[0]);control['name']='coordinate-typed/control/original-Marciana-3s';rows=[control]
    for old in original_probes():
        # Elegg's nearby selector has no coordinate reference contract yet.
        # Retain that explicit blocker instead of applying the closed-world shortcut.
        if old['character']=='일레그':continue
        if old['body']['duration']!=3 and (old['character'],old['body']['duration']) not in [('클레이',12),('미사토',30)]:continue
        if old.get('zero_projectile_modifier') or old.get('projectile_negative'):continue
        row=copy.deepcopy(old);row['name']='coordinate-typed/'+old['name'];row['coord']=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.);row['patterns']=copy.deepcopy(old['body']['enemy']['patterns']);rows.append(row)
    return rows
