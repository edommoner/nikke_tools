"""Declared cover quantities, authored percentages, ULP and overflow boundaries."""
import math,hashlib,json
from pathlib import Path

def original_values():
    from portable_original_identity_inventory import selected_prepared_profiles
    _,_,p=next(selected_prepared_profiles(['솔져 O.W.'],0))
    rows=[(i,r) for i,r in enumerate(p['effects']) if r['owner']=='솔져 O.W.' and r['effect'].get('stat')=='cover_def_pct']
    assert len(rows)==1
    index,row=rows[0];effect=row['effect']
    return dict(row=index,owner=row['owner'],name=effect['name'],effect_sha256=hashlib.sha256(json.dumps(effect,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),values=effect['values'])

def fixtures():
    rows=[]
    def add(label,*values):rows.append(dict(name='cover-defense-numeric/'+label,quantities=list(values)))
    for base in (0.,100.,1e-300,1e30):
        for percent in (-100.,-25.,0.,128.57,1000.):
            for attack in (0.,math.nextafter(100.,0.),100.,1000.,1e30):
                for received in (-100.,-5.,0.,25.):add(f'grid/{len(rows)}',attack,100.,base,percent,received,100.)
    original=original_values()
    for level,value in original['values'].items():
        for body in (0.,1e6):add(f'original/{level}/{body}',100000.,125.,1000.,float(value),0.,body)
    for base in (100.,1e12):
        defense=base*(1.+128.57/100.)
        for i,attack in enumerate((math.nextafter(defense,0.),defense,math.nextafter(defense,math.inf),defense+1.)):
            add(f'edge/{base}/{i}',attack,100.,base,128.57,0.,0.)
    for i,values in enumerate([(1e308,1000.,100.,0.,0.,0.),(100.,100.,1e308,1e308,0.,0.),(1e308,100.,0.,0.,1e308,0.),(1e308,100.,0.,0.,0.,-1e308),(5e-324,100.,5e-324,-100.,0.,-0.),(0.,0.,0.,-200.,0.,0.)]):add(f'extreme/{i}',*values)
    # Preserve the executed corpus exactly without host libm pow/uniform work.
    frozen=json.loads(Path(__file__).with_name('cover-defense-random-inputs-v1.json').read_text())
    if frozen.get('schema')!='cover-defense-random-inputs-v1' or frozen.get('input_only') is not True or len(frozen.get('rows',[]))!=128:raise ValueError('Frozen input-only corpus required')
    for i,row in enumerate(frozen['rows']):
        if set(row)!={'name','quantities'} or row['name']!=f'cover-defense-numeric/random/{i}' or len(row['quantities'])!=6:raise ValueError('Frozen vector identity mismatch')
        values=[float.fromhex(v) for v in row['quantities']]
        if not all(map(math.isfinite,values)):raise ValueError('Finite frozen inputs required')
        rows.append(dict(name=row['name'],quantities=values))
    return rows
