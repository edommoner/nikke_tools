"""Source-bound comparator-only correction; no oracle or GPU calculation reuse."""
import ast,copy,json
from pathlib import Path
NAME='coordinate-original-projectile-history-v1'
COUNTER_NAME='coordinate-owner-counter-field-decoder-v1'
COUNTER_SOURCE='dcd09db2434b77873a93c0f8d1109f5cbea990f9d1d49cd330d86ef8a573be67'
def changed_functions(before,after):
    def functions(source):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    old=functions(before);new=functions(after)
    return {n for n in old.keys()|new.keys() if old.get(n)!=new.get(n)}

def baseline(api,suite,source,records,*,name=NAME):
    counter=name==COUNTER_NAME
    if name not in (NAME,COUNTER_NAME) or suite!=('coordinate-typed-owner-lifecycle' if counter else 'coordinate-original'):raise ValueError('Reviewed comparator refresh suite required')
    with api.forbid_gpu():
        old=api.verify_saved_package(source)
        if old.get('purpose')!='development' or old.get('selected_cases')!=[] or old['suite']!=suite:raise ValueError('Full original development package required')
        if counter and old['package_id']!=COUNTER_SOURCE:raise ValueError('Exact lifecycle source package required')
        spec_path='tests/fixtures/portable-owner-counter-field-decoder-refresh.json' if counter else 'tests/fixtures/portable-original-history-repackage.json'
        spec=api.load(api.ROOT/spec_path)
        if counter and (set(spec['code'])!={'research/verify-world-actor-fields.py','research/verify-world-actor-recipients.py','app/portable_cache_fs_compression.py','app/portable_original_history_repackage.py','scripts/nikke_gpu.py'} or set(spec.get('tests',{}))!={'tests/test_portable_cache_fs_compression.py','tests/test_counter_field_decoder.py'}):raise ValueError('Unreviewed comparator refresh scope')
        before={r['path']:r['sha256'] for r in old['files']};after={r['path']:r['sha256'] for r in records}
        changed={p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)}
        code={p for p in changed if not p.startswith('tests/')}
        if code!=set(spec['code']):raise ValueError('Unexpected comparator refresh code changes')
        tests={p for p in changed if p.startswith('tests/') and p!=spec_path}
        if tests!=set(spec.get('tests',{})):raise ValueError('Unexpected comparator refresh test changes')
        for p,row in {**spec['code'],**spec.get('tests',{})}.items():
            if before.get(p)!=row['before'] or after.get(p)!=row['after']:raise ValueError('Unreviewed comparator refresh source: '+p)
        if counter:
            for path in ('research/verify-world-actor-fields.py','research/verify-world-actor-recipients.py'):
                if changed_functions((Path(source)/path).read_text(),(api.ROOT/path).read_text())!={'decoded'}:raise ValueError('Native/packing functions changed in decoder refresh')
            if changed_functions((Path(source)/'scripts/nikke_gpu.py').read_text(),(api.ROOT/'scripts/nikke_gpu.py').read_text())!={'main','make_package','migrated_development_baseline'}:raise ValueError('Unreviewed controller calculation change')
        # Every implementation, reference, transport, test and GPU byte outside
        # the exact reviewed comparator/control additions is fixed.
        a=api.open_suite(dict(suite=suite));entries,data=api.prepare_entries(a,dict(suite=suite,selected_cases=[]));g=copy.deepcopy(old['golden']);iw=a.suite.INPUT*4
        if len(entries)!=len(g['entries']) or api.sha(data)!=g['input_sha256']:raise ValueError('Comparator refresh changed input')
        for i,(name,w,domain) in enumerate(entries):
            if name!=g['entries'][i]['name'] or api.sha(data[4+i*iw:4+(i+1)*iw])!=g['entries'][i]['input_sha256']:raise ValueError('Comparator refresh changed a case')
        receipt=dict(name=name,code=spec['code'],prepared_inputs=len(entries),native_reference_changed=False,golden_unchanged=True)
        return g,dict(source_package_id=old['package_id'],source_package=str(Path(source).resolve()),receipt=receipt,native_domains_recomputed=0,retained_fingerprints=len(entries),full_fresh_saved_replay_required=True,gpu_calls=0,calculation_verified=False)
