"""Source-bound comparator-only correction; no oracle or GPU calculation reuse."""
import copy,json
from pathlib import Path
NAME='coordinate-original-projectile-history-v1'
def baseline(api,suite,source,records):
    if suite!='coordinate-original':raise ValueError('Original roster suite required')
    with api.forbid_gpu():
        old=api.verify_saved_package(source)
        if old.get('purpose')!='development' or old.get('selected_cases')!=[] or old['suite']!=suite:raise ValueError('Full original development package required')
        spec_path='tests/fixtures/portable-original-history-repackage.json'
        spec=api.load(api.ROOT/spec_path)
        before={r['path']:r['sha256'] for r in old['files']};after={r['path']:r['sha256'] for r in records}
        changed={p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)}
        code={p for p in changed if not p.startswith('tests/')}
        if code!=set(spec['code']):raise ValueError('Unexpected comparator refresh code changes')
        tests={p for p in changed if p.startswith('tests/') and p!=spec_path}
        if tests!=set(spec.get('tests',{})):raise ValueError('Unexpected comparator refresh test changes')
        for p,row in {**spec['code'],**spec.get('tests',{})}.items():
            if before.get(p)!=row['before'] or after.get(p)!=row['after']:raise ValueError('Unreviewed comparator refresh source: '+p)
        # Every implementation, reference, transport, test and GPU byte outside
        # the exact reviewed comparator/control additions is fixed.
        a=api.open_suite(dict(suite=suite));entries,data=api.prepare_entries(a,dict(suite=suite,selected_cases=[]));g=copy.deepcopy(old['golden']);iw=a.suite.INPUT*4
        if len(entries)!=len(g['entries']) or api.sha(data)!=g['input_sha256']:raise ValueError('Comparator refresh changed input')
        for i,(name,w,domain) in enumerate(entries):
            if name!=g['entries'][i]['name'] or api.sha(data[4+i*iw:4+(i+1)*iw])!=g['entries'][i]['input_sha256']:raise ValueError('Comparator refresh changed a case')
        receipt=dict(name=NAME,code=spec['code'],prepared_inputs=len(entries),native_reference_changed=False,golden_unchanged=True)
        return g,dict(source_package_id=old['package_id'],source_package=str(Path(source).resolve()),receipt=receipt,native_domains_recomputed=0,retained_fingerprints=len(entries),full_fresh_saved_replay_required=True,gpu_calls=0,calculation_verified=False)
