"""Original Mari modifier plus explicit derived lifetime/numeric/shape cases."""
import copy,json
from pathlib import Path

def original():
    data=json.loads((Path(__file__).resolve().parent/'upstream/nikke-calc-master/data/parsed_skills.json').read_text())
    rows=[(name,e) for name,effects in data.items() for e in effects if e.get('stat')=='effect_range_pct']
    if len(rows)!=1 or rows[0][1]['fixed_value']!=500.:raise ValueError('Re-audit original range definitions')
    return copy.deepcopy(rows[0])

def fixtures():
    name,e=original();marker=e['target_effect'];tag=dict(type='buff',name='섬멸 태세',stat='',target='self',duration=-1,fixed_value=1,trigger=dict(timing=['battle_start'],condition=[]))
    shapes=[[1,0.,0.,.5,0.,0.,0.],[1,2.5,0.,.5,0.,0.,0.],[1,6.5,0.,.5,0.,0.,0.],[1,7.,0.,.5,0.,0.,0.],[2,4.,4.,0.,2.,2.,45.]]
    rows=[];start=[0.,0,0,1,0,-1,0,0];burst=[0.,0,1,0,0,-1,0,0]
    def add(label,effects,owners,script,t=.1,who=1,ref=marker,base=1.,targets=None):
        rows.append(dict(name='named-range/'+label,effects=copy.deepcopy(effects),owners=list(owners),script=copy.deepcopy(script),selection=dict(who=who,marker=ref,time=t,base_radius=base,aim=[0.,0.],targets=copy.deepcopy(targets or shapes))))
    add('original-Mari-marked-recipient',[tag,e],[1,0],[start,burst])
    add('original-Mari-unmarked-recipient',[tag,e],[1,0],[start,burst],who=2)
    add('original-Mari-exact-expiry',[tag,e],[1,0],[start,burst],t=9.)
    add('original-Mari-wrong-effect-name',[tag,e],[1,0],[start,burst],ref='unrelated')
    add('original-Mari-before-expiry',[tag,e],[1,0],[start,burst],t=8.999999)
    f=dict(e,target='all_allies',fixed_value=12.5)
    add('derived-fractional-allies',[f],[0],[burst],who=4)
    add('derived-ordered-addition',[dict(f,name='first',fixed_value=100.),dict(f,name='second',fixed_value=12.5)],[0,1],[burst,[0.,0,1,1,0,-1,0,0]])
    add('derived-negative-half',[dict(f,fixed_value=-50.)],[0],[burst])
    add('derived-zero-radius',[f],[0],[burst],base=0.)
    add('derived-empty-radius-boundary',[f],[0],[burst],base=0.,targets=[[1,1.,0.,1.,0.,0.,0.],[1,1.000000002,0.,1.,0.,0.,0.]])
    removal=dict(name='remove-range',type='instant',stat='remove_named_buff',target='all_allies',target_effect=f['name'],trigger=dict(timing=['on_attack'],condition=[]))
    add('derived-named-removal',[f,removal],[0,0],[burst,[.2,0,7,0,0,-1,0,0]],t=.3)
    add('derived-refresh',[f],[0],[burst,[8.,0,1,0,0,-1,0,0]],t=9.)
    return rows

def native(case):
    from test_target_counter_runtime import manager,NAMES
    from effect_range_policy import query,MODEL
    from coordinate_geometry_reference import evaluate
    bm=manager(case['effects'],case['owners'])
    for c in case['script']:
        t=c[0];bm.tick(t);bm.notify({0:'battle_start',1:'full_burst_start',7:'on_attack'}[c[2]],t,NAMES[c[3]])
    q=case['selection'];bm.tick(q['time'])
    value=query(bm,NAMES[q['who']],q['marker'],q['time'],base_radius=q['base_radius'],model=MODEL)
    distances=[];selected=[]
    for i,shape in enumerate(q['targets']):
        g=evaluate((*shape,*q['aim'],0.,value['radius']));distances.append(g['distance'])
        if g['contains']:selected.append(i)
    return dict(value,distances=distances,selected=selected)
