"""Reuse immutable expected fingerprints, never native values or GPU results."""
import hashlib,json,re
from pathlib import Path
from portable_product_programs import configuration as product_configuration

SCHEMA='development-native-expectations-v1'
SCOPE='Expected fingerprints only; no runtime oracle values or saved GPU calculation reuse'
KEYS={'schema','baseline_package_id','baseline_manifest_sha256','candidate_files_sha256','fingerprints_sha256','source_sha256','retained_cases','changed_gpu_sources','verified_slang_ledgers','native_battles_recomputed_during_package','fresh_native_preflight_required','independent_seal_required','gpu_calls','calculation_verified','scope'}

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def safe(path):return isinstance(path,str) and '\\' not in path and all(p not in ('','.','..') for p in path.split('/'))
def gpu(path):return safe(path) and path.startswith('gpu/') and path.endswith('.slang')

def _ledger_baseline(root,name,row,style):
    """Reconstruct one exact before-image, checking current bytes first."""
    if not isinstance(row,dict):raise ValueError('Invalid source ledger row')
    current=(root/name).read_bytes().decode('utf-8')
    if style=='sources':
        if set(row)!={'baseline','baseline_sha256','current','current_sha256'}:raise ValueError('Unknown source ledger row')
        before,after=row['baseline'],row['current'];before_sha,after_sha=row['baseline_sha256'],row['current_sha256']
    elif set(row)=={'before','after','before_sha256','after_sha256'}:
        before,after=row['before'],row['after'];before_sha,after_sha=row['before_sha256'],row['after_sha256']
    elif set(row)=={'before_sha256','after_sha256','hunks'}:
        before_sha,after_sha=row['before_sha256'],row['after_sha256'];after=current;before=current
        if not isinstance(row['hunks'],list):raise ValueError('Invalid source ledger hunks')
        for h in reversed(row['hunks']):
            if (not isinstance(h,dict) or set(h)!={'before','after'} or not isinstance(h['before'],str)
                or not isinstance(h['after'],str) or not h['after'] or before.count(h['after'])!=1):
                raise ValueError('Ambiguous source ledger inverse')
            before=before.replace(h['after'],h['before'],1)
    else:raise ValueError('Unknown source ledger row')
    if not isinstance(before,str) or not isinstance(after,str) or after!=current:raise ValueError('Source ledger current text differs')
    for text,expected in ((before,before_sha),(after,after_sha)):
        if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected) or hashlib.sha256(text.encode()).hexdigest()!=expected:
            raise ValueError('Source ledger byte hash differs')
    return before

def ledger_change(old_root,new_root,path):
    """Only known Slang ledger current-text/hash changes; baselines stay fixed."""
    if not safe(path) or not path.startswith('tests/fixtures/') or not path.endswith('source-delta.json'):return False
    old=json.loads((old_root/path).read_text(encoding='utf-8'));new=json.loads((new_root/path).read_text(encoding='utf-8'))
    if not isinstance(old,dict) or not isinstance(new,dict):return False
    if set(old)!=set(new):return False
    style='sources' if 'sources' in old else 'files'
    allowed={'sources','added_sources'} if style=='sources' else {'files','added_sources','schema','baseline_commit','base_commit','normalizer_changed'}
    if set(old)-allowed:return False
    if any(old[k]!=new[k] for k in old if k not in (style,'added_sources')):return False
    if old.get('normalizer_changed',False) is not False:return False
    if not isinstance(old.get(style),dict) or not isinstance(new.get(style),dict):return False
    if set(old[style])!=set(new[style]):return False
    for name,before in old[style].items():
        after=new[style][name]
        if not safe(name):return False
        if not isinstance(before,dict) or not isinstance(after,dict):return False
        if not gpu(name):
            if before!=after:return False
            continue
        if set(before)!=set(after):return False
        try:
            if _ledger_baseline(old_root,name,before,style)!=_ledger_baseline(new_root,name,after,style):return False
        except (OSError,UnicodeError,ValueError,TypeError):return False
    a=old.get('added_sources',{});b=new.get('added_sources',{})
    if not isinstance(a,dict) or not isinstance(b,dict) or set(a)!=set(b):return False
    for name,expected in a.items():
        if not safe(name):return False
        if not gpu(name):
            if expected!=b[name]:return False
            continue
        if hashlib.sha256((old_root/name).read_bytes()).hexdigest()!=expected:return False
        if hashlib.sha256((new_root/name).read_bytes()).hexdigest()!=b[name]:return False
    return True

def reuse(cli,suite,baseline,records,cases,*,product_program=None):
    baseline=Path(baseline).resolve();current=Path(cli.ROOT)
    # This verifier reads bytes; it does not execute the baseline's CLI.
    cli.file_records(baseline,['gpu-package.json'])
    old=cli.verify_package(baseline)
    if old['suite']!=suite or old.get('purpose','sealed') not in ('sealed','development') or old.get('selected_cases',[])!=list(cases):raise ValueError('Matching native baseline suite/case selection required')
    if old.get('product_program')!=product_program:raise ValueError('Matching native baseline product program required')
    if old.get('baseline_migration'):raise ValueError('Observation migration cannot provide native expectations')
    previous={r['path']:r for r in old['files']};candidate={r['path']:r for r in records};ledgers=[];changed_gpu=[]
    for name in sorted(previous.keys()|candidate.keys()):
        if previous.get(name)==candidate.get(name):continue
        if gpu(name):changed_gpu.append(name);continue
        if name in previous and name in candidate and ledger_change(baseline,current,name):ledgers.append(name);continue
        raise ValueError('Native baseline dependency differs: '+name)
    m=dict(suite=suite,purpose='development',selected_cases=list(cases))
    if product_program is not None:m['product_program']=product_program
    with cli.forbid_gpu():
        adapter=cli.open_suite(m);entries,data=cli.prepare_entries(adapter,m)
    golden=old['golden'];iw=adapter.suite.INPUT*4
    if not entries or cli.sha(data)!=golden['input_sha256'] or len(entries)!=len(golden['entries']):raise ValueError('Native baseline prepared input differs')
    rows=[]
    for i,(name,_,domain) in enumerate(entries):
        row=golden['entries'][i]
        if name!=row['name'] or cli.sha(data[4+i*iw:4+(i+1)*iw])!=row['input_sha256']:raise ValueError('Native baseline case/input differs: '+name)
        if not isinstance(row.get('native_sha256'),str) or not re.fullmatch('[0-9a-f]{64}',row['native_sha256']):raise ValueError('Native baseline fingerprint missing: '+name)
        rows.append({k:row[k] for k in ('name','input_sha256','native_sha256')})
    from portable_backend import source_hashes
    result=dict(input_sha256=cli.sha(data),source_sha256=source_hashes(product_configuration(cli.SUITES,m)['source']),entries=rows)
    receipt=dict(schema=SCHEMA,baseline_package_id=old['package_id'],baseline_manifest_sha256=cli.sha((baseline/'gpu-package.json').read_bytes()),
        candidate_files_sha256=digest(records),fingerprints_sha256=digest(rows),source_sha256=digest(result['source_sha256']),
        retained_cases=len(rows),changed_gpu_sources=changed_gpu,verified_slang_ledgers=ledgers,
        native_battles_recomputed_during_package=0,fresh_native_preflight_required=True,independent_seal_required=True,
        gpu_calls=0,calculation_verified=False,scope=SCOPE)
    return result,receipt

def validate(manifest):
    r=manifest['native_expectation_baseline'];g=manifest['golden']
    if manifest.get('purpose')!='development' or not isinstance(r,dict) or set(r)!=KEYS or r.get('schema')!=SCHEMA or r.get('scope')!=SCOPE:raise ValueError('Invalid native expectation baseline purpose/schema')
    if r.get('fresh_native_preflight_required') is not True or r.get('independent_seal_required') is not True or r.get('calculation_verified') is not False:raise ValueError('Native expectations cannot certify calculations or skip fresh checks')
    for key in ('gpu_calls','native_battles_recomputed_during_package'):
        if type(r.get(key)) is not int or r[key]!=0:raise ValueError('Native expectation receipt has an execution claim')
    for key in ('baseline_package_id','baseline_manifest_sha256'):
        if not isinstance(r.get(key),str) or not re.fullmatch('[0-9a-f]{64}',r[key]):raise ValueError('Native expectation baseline identity missing')
    if set(g)!={'input_sha256','source_sha256','entries'}:raise ValueError('Development expectations cannot retain output/generated goldens')
    if any(set(row)!={'name','input_sha256','native_sha256'} for row in g['entries']):raise ValueError('Native expectations contain runtime/output values')
    for key,check in (('changed_gpu_sources',gpu),('verified_slang_ledgers',lambda p:safe(p) and p.startswith('tests/fixtures/') and p.endswith('source-delta.json'))):
        values=r.get(key)
        if not isinstance(values,list) or not all(check(p) for p in values) or len(values)!=len(set(values)):raise ValueError('Invalid native expectation dependency list')
    if r.get('candidate_files_sha256')!=digest(manifest['files']) or r.get('fingerprints_sha256')!=digest(g['entries']) or r.get('source_sha256')!=digest(g['source_sha256']) or type(r.get('retained_cases')) is not int or r['retained_cases']!=len(g['entries']):raise ValueError('Native expectation receipt binding differs')
    return True
