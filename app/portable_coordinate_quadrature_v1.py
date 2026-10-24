"""Versioned GL10 nodes/weights, authored with Decimal Newton iteration."""
from decimal import Decimal,Context,localcontext,ROUND_HALF_EVEN
from functools import lru_cache
from pathlib import Path
from portable_coordinate_numeric_v1 import bits,number
PROFILE='coordinate-gauss-legendre-10-v1'
def legendre(x):
    a,b=Decimal(1),x
    for k in range(2,11):a,b=b,((2*k-1)*x*b-(k-1)*a)/k
    return b,10*(x*b-a)/(x*x-1)
@lru_cache(None)
def nodes():
    with localcontext(Context(prec=160,rounding=ROUND_HALF_EVEN)):
        positive=[]
        for seed in ['.97','.86','.68','.43','.15']:
            x=Decimal(seed)
            for _ in range(50):
                p,dp=legendre(x);step=p/dp;x-=step
                if abs(step)<Decimal('1e-145'):break
            else:raise AssertionError('GL10 Newton did not converge')
            _,dp=legendre(x);positive.append((x,2/((1-x*x)*dp*dp)))
        return tuple((bits(float(x)),bits(float(w))) for x,w in positive+ [(-x,w) for x,w in reversed(positive)])
def shader_schema():
    out=['// Generated GL10, Decimal160 roots; '+PROFILE,'#ifndef COORDINATE_QUADRATURE_V1','#define COORDINATE_QUADRATURE_V1']
    for lane,name in [(0,'coordinateGaussX'),(1,'coordinateGaussWeight')]:
        out+=['uint64_t '+name+'(uint index){switch(index){']
        for i,pair in enumerate(nodes()):
            value=pair[lane];out+=[f'case {i}:return (uint64_t(0x{value>>32:08x}U)<<32)|uint64_t(0x{value&0xffffffff:08x}U);']
        out+=['default:return 0;}}']
    return '\n'.join(out+['#endif',''])
def check_schema(root=None):assert (Path(root or Path(__file__).resolve().parents[1])/'gpu/coordinate_quadrature_v1.slang').read_text()==shader_schema(),'GL10 source drift'
