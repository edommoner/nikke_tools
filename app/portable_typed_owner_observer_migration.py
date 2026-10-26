"""One exact additive empty CPU witness; full fresh replay stays mandatory."""
import copy,hashlib,json
from pathlib import Path
NAME='coordinate-typed-owner-status-witness-v1'
SUITE='coordinate-typed-owner'
SOURCE_PACKAGE_ID='cf44aa642396474aa712eb9c4b2ed5a2cd6be4892833ef906db3f9666988a6fb'
SPEC='tests/fixtures/portable-typed-owner-observer-migration.json'
PATH=('battle','enemy_fields','nonzero_immunity_used')
ALLOWED_CHANGES=frozenset(('app/portable_typed_owner_observer_migration.py','research/portable_coordinate_typed_owner_cases.py','scripts/nikke_gpu.py','tests/test_coordinate_typed_owner_gpu.py','tests/test_typed_owner_observer_migration.py'))
CASE_PAIR=('19ec3fdf6a82254509262c88d56b14aaea7a17b35f0a905b2f8f160276ab815c', 'c10aa432eb2037bcbb93fd737df4dd1191d79faea5fe5b40f7be157046fb28dc')

def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def check_sources(root,old,current):
    if old['package_id']!=SOURCE_PACKAGE_ID or old.get('purpose')!='development' or old.get('selected_cases')!=[] or old['suite']!=SUITE or current['suite']!=SUITE:raise ValueError('Exact full typed owner source package required')
    spec=json.loads((Path(root)/SPEC).read_bytes());before={r['path']:r['sha256'] for r in old['files']};after={r['path']:r['sha256'] for r in current['files']}
    if set(spec)!= {'changes','case_names'} or len(spec['case_names'])!=5 or len(set(spec['case_names']))!=5 or any(not n.startswith('coordinate-typed-owner/') for n in spec['case_names']):raise ValueError('Exact five owner witness cases required')
    if set(spec['changes'])!=ALLOWED_CHANGES:raise ValueError('Witness migration cannot change GPU, canonical or other dependencies')
    pair=spec['changes']['research/portable_coordinate_typed_owner_cases.py']
    if (pair['before'],pair['after'])!=CASE_PAIR:raise ValueError('Only the exact additive empty witness observer is reviewed')
    changed={n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)}
    if changed!=set(spec['changes'])|{SPEC}:raise ValueError('Unreviewed witness migration dependency change')
    for n,pair in spec['changes'].items():
        if set(pair)!= {'before','after'} or before.get(n)!=pair['before'] or after.get(n)!=pair['after']:raise ValueError('Unreviewed witness migration source: '+n)
    return spec

def receipt(old,current,spec):
    oldg=old['golden'];newg=current['golden'];expected=copy.deepcopy(oldg);rows=[]
    for name in spec['case_names']:
        indices=[i for i,r in enumerate(oldg['entries']) if r['name']==name]
        if len(indices)!=1:raise ValueError('Owner witness case missing')
        i=indices[0];before=oldg['entries'][i];after=newg['entries'][i]
        expected['entries'][i]['native_sha256']=after['native_sha256']
        rows.append(dict(name=name,old_native_sha256=before['native_sha256'],new_native_sha256=after['native_sha256'],observed=[]))
    if expected!=newg:raise ValueError('Witness migration changed another golden/input/source')
    return dict(kind=NAME,path=list(PATH),cases=rows,all_other_native_fields_equal=True,all_other_baselines_equal=True,fresh_complete_comparison_required=True,gpu_calls=0)

def baseline(api,suite,source,records):
    old=api.verify_saved_package(source);current=dict(suite=suite,files=records)
    spec=check_sources(api.ROOT,old,current)
    with api.forbid_gpu():
        a=api.open_suite(dict(suite=suite));entries,data=api.prepare_entries(a,dict(suite=suite,selected_cases=[]));g=copy.deepcopy(old['golden']);iw=a.suite.INPUT*4
        if len(entries)!=len(g['entries']) or api.sha(data)!=g['input_sha256']:raise ValueError('Witness migration changed input')
        for i,(name,words,domain) in enumerate(entries):
            row=g['entries'][i]
            if name!=row['name'] or api.sha(data[4+i*iw:4+(i+1)*iw])!=row['input_sha256']:raise ValueError('Witness migration changed a case')
            if name not in spec['case_names']:continue
            native=api.native_value(a,domain);prior=copy.deepcopy(native)
            if prior['battle']['enemy_fields'].pop('nonzero_immunity_used')!=[]:raise ValueError('Owner witness is not empty')
            if digest(prior)!=row['native_sha256']:raise ValueError('Witness changed another native value')
            row['native_sha256']=digest(native)
    current['golden']=g;r=receipt(old,current,spec)
    return g,dict(source_package_id=old['package_id'],source_package=str(Path(source).resolve()),receipt=r,native_domains_recomputed=5,retained_fingerprints=len(entries)-5,full_fresh_saved_replay_required=True,gpu_calls=0,calculation_verified=False)

def verify(api,old,current):
    spec=check_sources(api.ROOT,old,current);expected=receipt(old,current,spec)
    provenance=current.get('baseline_migration',{})
    if provenance.get('source_package_id')!=SOURCE_PACKAGE_ID or provenance.get('receipt')!=expected or provenance.get('native_domains_recomputed')!=5 or provenance.get('retained_fingerprints')!=len(current['golden']['entries'])-5 or provenance.get('full_fresh_saved_replay_required') is not True or provenance.get('gpu_calls')!=0 or provenance.get('calculation_verified') is not False:
        raise ValueError('Owner witness migration receipt mismatch')
    # This validates only the source-bound additive observation mapping. The
    # replay/seal still recomputes every native domain in fresh child groups.
    return expected
