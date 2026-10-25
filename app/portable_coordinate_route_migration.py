"""One source-bound passive ADD-label correction, never a mismatch waiver."""
import copy,hashlib,json
NAME='coordinate-healing-routed-adds-v1'
CASE='coordinate-healing/mixed-actors-store'
SOURCES={
 'research/world_coordinate_sampled_delivery_native.py':('4533742bb9201f2140af446efaa98e0b5678728a737b2fc59d2544650fce70a7','7bbf736f6132e80d7876b5b0ebc6948526371a2f335c21e27ca90e400b944373'),
 'research/portable_coordinate_healing_cases.py':('6156c2884ddc37fe4043f8b01783e65ff6eff1a821c17d0d824948b597700bb0','c63ce5c7e2681860e3c452ed6a4306c0a161a995dcad3b4387a01a5287bda958')}
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def verify(name,original,current,reference):
    if name!=NAME or original['suite']!=current['suite'] or current['suite']!='coordinate-healing':raise ValueError('Unknown routed observation migration')
    before={r['path']:r['sha256'] for r in original['files']};after={r['path']:r['sha256'] for r in current['files']}
    for p,(old,new) in SOURCES.items():
        if before.get(p)!=old or after.get(p)!=new:raise ValueError('Routed observation source mismatch')
    for p in before.keys()|after.keys():
        if p.startswith('research/') and p.endswith('native.py') and p not in SOURCES and before.get(p)!=after.get(p):raise ValueError('Unreviewed native observer change')
    old=original['golden'];new=current['golden'];indices=[i for i,r in enumerate(old['entries']) if r['name']==CASE]
    if len(indices)!=1:raise ValueError('Routed observation case missing')
    i=indices[0];prior=copy.deepcopy(reference);targets=set();corrected=0
    for row in prior['landed_packets']:
        label=row.pop('label');target='' if label=='__enemy__' else label
        if row['target']!=target or type(row['generation']) is not int or row['generation']<1:raise ValueError('Unbound actual landing label')
        if target.startswith('__enemy__:healing-adds#'):
            targets.add(target);row['target']='';corrected+=1
    if targets!={'__enemy__:healing-adds#1','__enemy__:healing-adds#2'} or corrected<2:raise ValueError('Actual ADD recipients missing')
    if digest(prior)!=old['entries'][i]['native_sha256'] or digest(reference)!=new['entries'][i]['native_sha256']:raise ValueError('Routed observation changed other native state')
    expected=copy.deepcopy(old);expected['entries'][i]['native_sha256']=new['entries'][i]['native_sha256']
    if expected!=new:raise ValueError('Routed observation changed another baseline')
    return dict(kind=NAME,case=CASE,corrected_packets=corrected,actual_add_targets=sorted(targets),all_other_native_fields_equal=True,all_other_baselines_equal=True,gpu_calls=0)
