"""CPU-only empirical accuracy gate against an independent Decimal oracle."""
import hashlib,time
from pathlib import Path
import portable_coordinate_numeric_v1 as n
from portable_coordinate_numeric_cases import fixtures
from coordinate_decimal_oracle import reference,ulp_distance

SOURCES=('app/portable_coordinate_numeric_v1.py','gpu/coordinate_numeric_v1.slang',
         'research/coordinate_numeric_accuracy.py','research/coordinate_decimal_oracle.py',
         'research/portable_coordinate_numeric_cases.py')
NAMES={1:'sincos-degrees',2:'sincos-bounded-radians',3:'atan2',4:'acos',5:'sqrt'}

def common(op,a,b):
    return (n.sincos_degrees(a) if op==1 else n.sincos_radians(a) if op==2 else
            (n.atan2_bits(a,b),0) if op==3 else (n.acos_bits(a),0) if op==4 else (n.sqrt_bits(a),0))

def audit(root,samples=512):
    if type(samples) is not int or not 0<=samples<=10000:raise ValueError('Samples must be 0..10000 per operation')
    root=Path(root);n.check_schema(root);start=time.monotonic()
    groups={op:dict(inputs=0,compared_outputs=0,max_ulp=0,worst=None,gate_ulp=0 if op==5 else 4) for op in NAMES}
    for label,op,a,b in fixtures(samples):
        actual=common(op,a,b);expected=reference(op,a,b);group=groups[op];group['inputs']+=1
        for lane in range(2 if op in (1,2) else 1):
            assert n.finite(actual[lane]),('Nonfinite common result',label,lane)
            distance=ulp_distance(actual[lane],expected[lane]);group['compared_outputs']+=1
            if distance>group['max_ulp']:
                group['max_ulp']=distance;group['worst']=dict(label=label,lane=lane,input=[f'{a:016x}',f'{b:016x}'],actual=f'{actual[lane]:016x}',oracle=f'{expected[lane]:016x}')
            assert distance<=group['gate_ulp'],('Independent numeric accuracy gate',label,lane,distance,group['gate_ulp'])
    return dict(kind='coordinate-numeric-independent-accuracy-v1',contract=n.PROFILE,contract_sha256=n.contract_sha256(),
        source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in SOURCES},
        samples_per_operation=samples,inputs=sum(g['inputs'] for g in groups.values()),
        operations={NAMES[k]:v for k,v in groups.items()},accuracy_verified=True,
        oracle='Decimal190; independent AGM210 pi; convergent series; alternate acos reduction',
        empirical_only=True,correct_rounding_claim=False,battle_connected=False,
        gpu_executions=0,elapsed_seconds=time.monotonic()-start)
