"""One explicit native-observer migration; never a generic mismatch waiver."""
import copy,hashlib,json
NAME='parts-cleared-v1'
CASE='native/parts-lifecycle-reopened-same-labels'
SOURCES={
 'research/world_frame_native.py':('e51212b7412f0b0922dff8c194eed31e52381072cc1c73473696275234effb10','55b51a7d1f704be53b6f28dccf52edeb1097a806ca0cc4da66d0eb701f84f0fa'),
 'research/world_schedule_native.py':('8a6d9b3dad5674065a0e1c313699af9bad2730597638c73bf3bae161f5a69123','5f0bd88cdabf7d1e8120d44d2e2b0c46d13f497b496bd424f4caacb8708a6478')}
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def verify(name,original,current,reference):
    if name!=NAME or original['suite']!=current['suite'] or current['suite']!='parts-skill-world':raise ValueError('Unknown native observation migration')
    before={r['path']:r['sha256'] for r in original['files']};after={r['path']:r['sha256'] for r in current['files']}
    for path,(old,new) in SOURCES.items():
        if before.get(path)!=old or after.get(path)!=new:raise ValueError('Native observation migration source mismatch')
    for path in before.keys()|after.keys():
        if path.startswith('research/') and path.endswith('native.py') and path not in SOURCES and before.get(path)!=after.get(path):raise ValueError('Unreviewed native observer change')
    old=original['golden'];new=current['golden'];expected=copy.deepcopy(old)
    indices=[i for i,e in enumerate(old['entries']) if e['name']==CASE]
    if len(indices)!=1:raise ValueError('Native observation migration case missing')
    i=indices[0];row=new['entries'][i]
    if reference['battle']['graph_states'][0][6]!=1 or reference['battle']['graph_states'][0][1]!=2:raise ValueError('Native cleared/open lifetime not observed')
    prior=copy.deepcopy(reference);prior['battle']['graph_states'][0][6]=0
    if digest(prior)!=old['entries'][i]['native_sha256'] or digest(reference)!=row['native_sha256']:raise ValueError('Native observation migration changed other state')
    expected['entries'][i]['native_sha256']=row['native_sha256']
    if expected!=new:raise ValueError('Native observation migration changed another baseline')
    return dict(kind=NAME,case=CASE,path=['battle','graph_states',0,6],old_placeholder=0,new_observed=1,all_other_native_fields_equal=True,all_other_baselines_equal=True,gpu_calls=0)
