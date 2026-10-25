"""Real sampled battle prerequisites; no static landing schedule or RNG table."""
import copy
from portable_coordinate_physical_cases import fixtures as original
def fixtures():
    rows=copy.deepcopy(original())
    for i,c in enumerate(rows):
        c['name']='coordinate-sampling-common/'+c['name'].rsplit('/',1)[1];c['duration']=.35;c['seed']=19+i
        pairs=[(e,o) for e,o in zip(c['effects'],c['owners']) if e['name']!='no-crit'];c['effects']=[e for e,o in pairs];c['owners']=[o for e,o in pairs]
    for label,point in [('core-centered',[0.,0.]),('core-offset',[2.,1.])]:
        c=copy.deepcopy(rows[5]);c['name']='coordinate-sampling-common/'+label;c['enemy']['core_px']=8;c['enemy']['coord']['auto_aim']=point;rows.append(c)
    c=copy.deepcopy(rows[0]);c['name']='coordinate-sampling-common/rotated-rectangle';s=c['patterns'][0]['targets'][0];s.pop('r');s.update(x=1.5,y=-1.,w=6.,h=3.,rotation=37.);rows.append(c)
    return rows
