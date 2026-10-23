"""Pinned CPU consumer receipts, independent of portable packing/results."""
import hashlib,json
from pathlib import Path


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def summary(native,trace):
    data=native['partial_query'];shots=native['nonfull_charge'];queries=data['queries'];samples=data['samples']
    return dict(reads=len(data['reads']),read_sha256=digest(data['reads']),queries=len(queries),cache_hits=sum(q['hit'] for q in queries),query_sha256=digest(queries),samples=len(samples),direct_samples=sum(not s['lazy'] for s in samples),sample_sha256=digest(samples),partial=sum(s['kind']=='shot' and not s['full'] for s in shots),full=sum(s['kind']=='shot' and s['full'] for s in shots),notice_sha256=digest(shots),battle_sha256=digest({k:v for k,v in native.items() if k not in ('nonfull_charge','partial_query')}),trace_sha256=digest(trace) if trace is not None else data['trace_sha256'])


def verify(case,native,trace=None):
    expected=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/portable-partial-query-native.json').read_text())[case['name']]
    actual=summary(native,trace)
    assert actual==expected,(case['name'],{k:(expected[k],actual[k]) for k in expected if expected[k]!=actual[k]})
    for q in native['partial_query']['queries']:
        if q['hit']:assert not q['sample_indices'] and q['before_index']==q['after_index'],'cache hit consumed RNG'
    return dict(verified=True,**actual)
