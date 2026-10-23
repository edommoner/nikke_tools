"""CPU-only condition/context contracts; never portable activation decisions."""
import hashlib,json
from pathlib import Path


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def summary(native,trace=None):
    c=native['not_core_condition'];rows=c['checks']
    return dict(checks=len(rows),passed_checks=sum(r['result'] for r in rows),context_present=sum(r['core_fraction'] is not None for r in rows),context_absent=sum(r['core_fraction'] is None for r in rows),checks_sha256=digest(rows),states=c['states'],carriers=c['carriers'],instant_calls=len(c['instant_calls']),instant_calls_sha256=digest(c['instant_calls']),definitions=c['definitions'],expected_mode=c['expected_mode'],battle_sha256=digest({k:v for k,v in native.items() if k!='not_core_condition'}),trace_sha256=digest(trace) if trace is not None else c['trace_sha256'])


def verify(case,native):
    expected=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/portable-not-core-native.json').read_text())[case['name']]
    actual=summary(native)
    assert actual==expected,(case['name'],{k:(expected[k],actual[k]) for k in expected if expected[k]!=actual[k]})
    assert actual['expected_mode'],'Only canonical expected mode is covered'
    for row in native['not_core_condition']['checks']:
        assert row['core_fraction'] is None or 0<=row['core_fraction']<=1
        assert row['event']=='hit_count' or row['core_fraction'] is None,'Only physical hit_count carries core_frac in these producers'
        assert all(0<=value['value']<1 for value in row['after'].values())
    return dict(verified=True,reference_model_gap=False,**actual)
