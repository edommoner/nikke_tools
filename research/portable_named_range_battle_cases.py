"""Complete original Asuka/Rei roster, explicit geometry and radial bases."""
import copy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import engine_worker
from detail_coverage import body_for
OWNER='아스카 : WILLE';SUPPORT='레이 (가칭)';EFFECT='섬멸 태세 추가 효과'

def fixtures():
    roster=[OWNER,SUPPORT,'미란다','도라','메어리'];rows=[]
    for label,base,delay,hp in [('expanded',1.,0.,1e30),('small-base-control',.1,0.,1e30),('late-spawn',1.,7.,1e30),('retirement',1.,0.,1.)]:
        body=copy.deepcopy(dict(body_for(roster,15),burst_gauge_mode='accumulate',seed=4701))
        patterns=[dict(id='range-wave',kind='summon',delay=delay,spec=dict(count=3,hp=hp))]
        body['enemy'].update(has_parts=False,patterns=copy.deepcopy(patterns))
        geometry=[dict(label='__enemy__:range-wave#'+str(i+1),shape=dict(x=x,y=0.,r=.25,z=float(i+1))) for i,x in enumerate((0.,2.,20.))]
        rules=[dict(owner=OWNER,effect=EFFECT,base_radius=base,base_count=2,body_shape=dict(x=0.,y=0.,r=.25))]
        rows.append(dict(name='named-range-battle/Asuka-Rei/'+label,body=body,patterns=patterns,logical_geometry=geometry,named_range_rules=rules,coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),contract=dict(scenario=label,original_support_name=SUPPORT)))
    return rows
