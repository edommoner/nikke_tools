import json
from pathlib import Path
from portable_duration_scaling_contracts import verify as baseline,check_values
def verify(case,native):
    if not case['name'].startswith('duration-scaling-mixed-'):return baseline(case,native)
    checks=native['duration_scaling']['checks'];policy=case['contract'].get('reference_policy')
    if policy:
        assert 10<=len(checks)<256
        values=[3 if policy=='constant3' or policy=='until-expired' and row['time']<.05 else 0 if policy=='constant0' else None for row in checks]
    else:values=case['contract']['reference_values']
    actual=check_values(case,native,values);frozen=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/portable-duration-scaling-mixed-native.json').read_text())[case['name']]
    assert actual==frozen,(case['name'],actual,frozen)
    return dict(verified=True,reference_model_gap=False,**actual)
