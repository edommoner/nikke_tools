"""Strict full-coverage aggregation of fresh, GPU-forbidden comparison groups."""
import os

SCHEMA='independent-metal-audit-groups-v1'
CUDA_SCHEMA='independent-cuda-audit-groups-v1'


def selection(count,indices):
    if type(count) is not int or count<=0:raise ValueError('Nonempty comparison required')
    if indices is None:return list(range(count))
    if not isinstance(indices,list) or not indices or any(type(i) is not int or not 0<=i<count for i in indices) or indices!=sorted(set(indices)):
        raise ValueError('Comparison indices must be unique, ordered and in range')
    return indices


def partition(count,size):
    if type(size) is not int or size<=0:raise ValueError('Positive comparison group size required')
    selection(count,None)
    return [list(range(start,min(start+size,count))) for start in range(0,count,size)]


def planned(count,size,groups=None):
    """Bounded explicit groups, keeping every input exactly once in order."""
    default=partition(count,size)
    if groups is None:return default
    if (type(groups) is not list or not groups or len(groups)>count
        or any(type(part) is not list or not 1<=len(part)<=size for part in groups)):
        raise ValueError('Explicit native groups must be nonempty and within group size')
    for part in groups:selection(count,part)
    if [i for part in groups for i in part]!=list(range(count)):
        raise ValueError('Explicit native groups must cover every input exactly once in order')
    return [part[:] for part in groups]


def read_plan(path,expected_sha256):
    """External file hash pins a grouping recipe, never native result data."""
    import hashlib,json
    from pathlib import Path
    from portable_admission_snapshot import hex_string
    path=Path(path)
    if not hex_string(expected_sha256,64) or path.is_symlink() or not path.is_file() or path.stat().st_size>4*1024**2:raise ValueError('Pinned native group plan required')
    raw=path.read_bytes()
    if len(raw)>4*1024**2 or hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('Native group plan SHA mismatch')
    groups=json.loads(raw)
    if type(groups) is not list or not groups or any(type(p) is not list for p in groups):raise ValueError('Native group plan must contain only index groups')
    count=sum(len(p) for p in groups)
    if not 1<=count<=65536:raise ValueError('Native group plan input count out of bounds')
    return planned(count,65536,groups)


def aggregate(manifest,groups,planned,timeout,*,backend='metal'):
    """Never accept saved/live-parent oracles, missing rejects, overlaps or gaps."""
    if backend not in ('metal','cuda'):raise ValueError('Explicit Metal or CUDA audit backend required')
    expected=manifest['golden']['entries'];count=len(expected)
    if not groups or len(groups)!=len(planned) or [i for part in planned for i in part]!=list(range(count)):
        raise ValueError('Comparison groups must cover every input exactly once')
    common=None;entries=[];native=0;pids=[];facts=[];audit=None
    for group,indices in zip(groups,planned,strict=True):
        selection(count,indices);r=group['comparison'];selection(count,r.get('case_indices'));a=group['audit'];pid=group['child_pid'];seconds=group['elapsed_seconds']
        if type(pid) is not int or pid<=0 or pid==os.getpid() or pid in pids or group.get('live_parent_receipt_present') is not False:
            raise ValueError('Fresh independent comparison child required')
        if type(seconds) not in (int,float) or not 0<=seconds<=timeout+1:raise ValueError('Comparison group exceeded its bound')
        if group['package_id']!=manifest['package_id'] or r.get('case_indices')!=indices or r.get('total_input_count')!=count or type(r.get('input_count')) is not int or r.get('input_count')!=len(indices) or len(r.get('entries',[]))!=len(indices):
            raise ValueError('Comparison group input identity/count mismatch')
        if r.get('comparison_subset_verified') is not True or r.get('calculation_verified') is not False or r.get('mismatches')!=[] or 'parent_oracles' in r or r.get('audit_gpu_calls')!=0:
            raise ValueError('Comparison group is incomplete, failed or reused')
        envelope_verified=a.get('transport_verified') is True
        if backend=='cuda':
            preservation=a.get('preservation_verified')
            envelope_verified=(a.get('transport_core_verified') is True and a.get('containment_verified') is True
                and type(preservation) is bool and a.get('transport_verified') is preservation)
        if not envelope_verified or a.get('calculation_verified') is not False or a.get('passed') is not False or a.get('comparison_error') is not None:
            raise ValueError('Independent capture envelope not verified')
        shared={k:r[k] for k in ('input_sha256','output_sha256','generated_normalized')}
        if shared['input_sha256']!=manifest['golden']['input_sha256']:raise ValueError('Comparison input fingerprint mismatch')
        if common is None:common=shared
        if common!=shared:raise ValueError('Comparison groups used different capture bytes')
        # All non-comparison transport facts must agree across fresh children.
        envelope={k:v for k,v in a.items() if k not in r and k not in ('calculation_verified','passed')}
        if audit is None:audit=envelope
        if audit!=envelope:raise ValueError('Comparison groups have different transport facts')
        for i,row in zip(indices,r['entries'],strict=True):
            want=expected[i]
            if set(row)!={'name','input_sha256','output_sha256','native_sha256'} or any(row.get(k)!=v for k,v in want.items()):raise ValueError('Comparison group case fingerprint mismatch')
            entries.append(row)
        n=r.get('native_oracles')
        if type(n) is not int or not 0<=n<=len(indices):raise ValueError('Comparison group native count missing')
        native+=n;pids.append(pid);facts.append(dict(child_pid=pid,case_indices=indices,input_count=len(indices),native_cases=n,elapsed_seconds=seconds))
    if 'output_sha256' in manifest['golden'] and common['output_sha256']!=manifest['golden']['output_sha256']:raise ValueError('Full output fingerprint mismatch')
    if 'generated_normalized' in manifest['golden'] and common['generated_normalized']!=manifest['golden']['generated_normalized']:raise ValueError('Generated code fingerprint mismatch')
    comparison=dict(common,entries=entries,mismatches=[],input_count=count,native_oracles=native,calculation_verified=True,audit_gpu_calls=0)
    final_audit=dict(audit,calculation_verified=True,passed=backend=='metal' or audit['preservation_verified'] is True)
    if audit.get('mode')=='saved-metal-replay':final_audit.update(comparison)
    return dict(comparison=comparison,audit=final_audit,independent_comparison=dict(schema=SCHEMA if backend=='metal' else CUDA_SCHEMA,child_pids=pids,groups=facts,input_count=count,native_cases=native,live_parent_receipt_present=False,per_group_timeout_seconds=timeout))


def validate_facts(facts,count,timeout,*,backend='metal'):
    if backend not in ('metal','cuda'):raise ValueError('Explicit Metal or CUDA audit backend required')
    if facts.get('schema')!=(SCHEMA if backend=='metal' else CUDA_SCHEMA) or facts.get('input_count')!=count or facts.get('live_parent_receipt_present') is not False or facts.get('per_group_timeout_seconds')!=timeout:
        raise ValueError('Independent grouped receipt identity mismatch')
    rows=facts.get('groups');pids=facts.get('child_pids')
    if not isinstance(rows,list) or not rows or not isinstance(pids,list) or len(rows)!=len(pids) or [r.get('child_pid') for r in rows]!=pids or len(set(pids))!=len(pids) or any(type(p) is not int or p<=0 or p==os.getpid() for p in pids):raise ValueError('Fresh independent comparison child required')
    if any(not isinstance(r.get('case_indices'),list) for r in rows):raise ValueError('Grouped receipt indices missing')
    if [i for r in rows for i in selection(count,r.get('case_indices'))]!=list(range(count)):raise ValueError('Grouped receipt must cover every input exactly once')
    for row in rows:
        n=row.get('native_cases');seconds=row.get('elapsed_seconds')
        if type(row.get('input_count')) is not int or row['input_count']!=len(row['case_indices']) or type(n) is not int or not 0<=n<=row['input_count'] or type(seconds) not in (int,float) or not 0<=seconds<=timeout+1:raise ValueError('Grouped receipt counts/bounds mismatch')
    if type(facts.get('input_count')) is not int or type(facts.get('native_cases')) is not int or facts['native_cases']!=sum(r['native_cases'] for r in rows):raise ValueError('Grouped receipt total mismatch')
    return True
