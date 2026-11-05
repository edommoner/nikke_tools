"""World-pool integration stimuli; coordinate sidecars never replace battle input."""
import copy
from portable_parts_skill_cases import fixtures as parts_cases

def fixtures():
    source={c['name']:c for c in parts_cases()};rows=[]
    for name in ('true','false','unbreakable-part','parts-and-interrupt','two-hits','destroy-before-second'):
        c=copy.deepcopy(source['parts-skill-'+name]);c['name']='coordinate-pool/'+name;rows.append(c)
    for reverse in (False,True):
        c=copy.deepcopy(source['parts-skill-parts-and-interrupt']);c['name']='coordinate-pool/depth-'+str(reverse);c['reverse_depth']=reverse;rows.append(c)
    c=copy.deepcopy(source['parts-skill-false']);c['name']='coordinate-pool/reopen-live';c['patterns'][0].update(delay=.01,until=dict(time=.15),after=['start','parts'],repeat=2);rows.append(c)
    c=copy.deepcopy(source['parts-skill-parts-and-interrupt']);c['name']='coordinate-pool/later-birth';c['effects'][-1]['hits_parts']=False;c['patterns'][0]['delay']=.1;c['equal_depth']=True;rows.append(c)
    c=copy.deepcopy(source['parts-skill-false']);c['name']='coordinate-pool/same-pattern-ordinal';c['equal_depth']=True;rows.append(c)
    for c in rows:
        patterns=copy.deepcopy(c['patterns'])
        for p in patterns:
            for i,t in enumerate(p.get('targets',[])):
                t.pop('reach',None);t.update(x=30*i,y=-i,r=2,z=(0 if c.get('equal_depth') else i if c.get('reverse_depth') else -i))
        c['coordinate_sidecar']=dict(name=c['name'],patterns=patterns,commands=[('capture',c['duration'],0,0)])
    return rows
