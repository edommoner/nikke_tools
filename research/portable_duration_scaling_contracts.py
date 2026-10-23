"""Ordered native duration references; no portable admission claim."""
import hashlib,json,math,struct
from pathlib import Path

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def summary(native):
    data=native['duration_scaling'];checks=data['checks']
    return dict(checks=len(checks),reference_reads=sum(len(c['reads']) for c in checks),checks_sha256=digest(checks),carriers=data['carriers'],definitions=data['definitions'],battle_sha256=digest({k:v for k,v in native.items() if k!='duration_scaling'}),trace_sha256=data['trace_sha256'])

def verify(case,native):
    checks=native['duration_scaling']['checks'];values=[r['value'] for c in checks for r in c['reads']]
    assert values==case['contract']['reference_values'],(case['name'],values,case['contract'])
    for row in checks:
        duration=row['duration']
        if duration is None and row['duration_values'] is not None:duration=float(row['duration_values'].get('10',0))
        if duration is None or duration==-1:
            assert row['reads']==[] and row['expires_at']==math.inf
        else:
            assert len(row['reads'])==1
            r=row['reads'][0];assert r['owner']==row['owner'] and r['name']==row['reference']
            count=0 if r['value'] is None else r['value']
            expected=row['time']+float(duration)*count
            assert struct.pack('<d',row['expires_at'])==struct.pack('<d',expected),(case['name'],row)
    actual=summary(native)
    frozen=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/portable-duration-scaling-native.json').read_text())[case['name']]
    assert actual==frozen,(case['name'],{k:(frozen[k],actual[k]) for k in frozen if frozen[k]!=actual[k]})
    return dict(verified=True,reference_model_gap=False,**actual)
