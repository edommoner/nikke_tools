"""Directed MPFR audit of the common integer interval algorithm."""
import hashlib,time
from pathlib import Path
import gmpy2
import portable_coordinate_power_v1 as p
from portable_coordinate_power_cases import fixtures

def mpfr(x,y):
    endpoints=[]
    for direction in (gmpy2.RoundDown,gmpy2.RoundUp):
        with gmpy2.context(precision=256,round=direction):value=gmpy2.mpfr(p.number(x))**gmpy2.mpfr(p.number(y))
        endpoints.append(p.bits(float(value)))
    assert endpoints[0]==endpoints[1],('MPFR oracle precision unresolved',x,y)
    return endpoints[0]
def audit(root,samples=512):
    if type(samples) is not int or not 0<=samples<=10000:raise ValueError('Samples must be 0..10000')
    root=Path(root);p.check_schema(root);start=time.monotonic();rows=fixtures(samples);digest=hashlib.sha256()
    for name,x,y in rows:
        answer=p.evaluate(x,y);expected=mpfr(x,y);assert answer==expected,(name,x,y,answer,expected)
        digest.update(f'{x:016x}{y:016x}{answer:016x}\n'.encode())
    sources=['app/portable_coordinate_power_v1.py','gpu/core_probability.slang','gpu/coordinate_power_v1.slang','research/coordinate_power_accuracy.py','research/portable_coordinate_power_cases.py']
    return dict(kind='coordinate-unit-power-directed-mpfr-v1',contract=p.PROFILE,inputs=len(rows),samples=samples,accuracy_verified=True,max_ulp=0,
        source_sha256={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in sources},comparison_sha256=digest.hexdigest(),
        oracle='MPFR256 directed down/up; both binary64 endpoints must agree',mpfr_version=gmpy2.mpfr_version(),
        all_domain_no_unresolved_rounding_claim=False,gpu_executions=0,elapsed_seconds=time.monotonic()-start)
