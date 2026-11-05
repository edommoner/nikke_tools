"""Unit-interval powers: reuse the certified Q128 core algorithm for variable y.

Domain x in [0,1], binary64 y in [2^-64,2^16]. Coefficients are exact dyadics.
Both interval endpoints must round identically; unresolved cases fail closed.
"""
from fractions import Fraction
from pathlib import Path
import hashlib,re
from portable_coordinate_numeric_v1 import bits,number,finite,SIGN,ONE
PROFILE='coordinate-unit-power-v1'
MIN_EXPONENT=bits(2.**-64);MAX_EXPONENT=bits(65536.)
SOURCE_SHA256='afa22590fd81f11ff88a300929efbc34e3818cbb3f1ebbc5d523a454728b5366'
Q=1<<128
LN2=0xb17217f7d1cf79abc9e3b39803f2f6af

def product(a,b):return a[0]*b[0]//Q,(a[1]*b[1]+Q-1)//Q
def divide(a,d):return a[0]//d,(a[1]+d-1)//d

def interval(x,y):
    if not finite(x) or x&SIGN and x&~SIGN or x&~SIGN>ONE or not finite(y) or y<MIN_EXPONENT or y>MAX_EXPONENT:raise ValueError('Unit-power domain')
    if x&~SIGN==0:return dict(bits=0,scale=0,lower=0,upper=0)
    if x==ONE:return dict(bits=ONE,scale=0,lower=Q,upper=Q)
    exp=(x>>52)&2047;s=x&((1<<52)-1)
    if exp:s|=1<<52
    else:
        exp=1;shift=53-s.bit_length();s<<=shift;exp-=shift
    numerator=(s-(1<<52))*Q;denominator=s+(1<<52)
    t=(numerator//denominator,(numerator+denominator-1)//denominator)
    square=product(t,t);power=t;log_m=t
    for i in range(1,64):
        power=product(power,square);term=divide(power,2*i+1);log_m=(log_m[0]+term[0],log_m[1]+term[1])
    log_m=(log_m[0]*2,log_m[1]*2+1);n=1023-exp
    z=(n*LN2-log_m[1],n*(LN2+1)-log_m[0])
    exact_y=Fraction.from_float(number(y))*Q;assert exact_y.denominator==1
    z=product(z,(int(exact_y),int(exact_y)));lo=0;hi=1<<27
    while hi-lo>1:
        mid=(lo+hi)//2
        if z[0]>=mid*(LN2+1):lo=mid
        else:hi=mid
    r=(z[0]-lo*(LN2+1),z[1]-lo*LN2)
    if not 0<=r[0]<=r[1]<Q:raise ValueError('Unit-power residual enclosure')
    term=(Q,Q);total=term
    for i in range(1,48):
        term=divide(product(term,r),i)
        total=(total[0]-term[1],total[1]-term[0]) if i&1 else (total[0]+term[0],total[1]+term[1])
    total=(total[0],total[1]+1)
    def rounded(v):return 0 if lo>1075 else bits(float(Fraction(v,1<<(128+lo))))
    lower,upper=map(rounded,total)
    if lower!=upper:raise ValueError('Unit-power rounding unresolved')
    return dict(bits=lower,scale=lo,lower=total[0],upper=total[1])

def evaluate(x,y):return interval(x,y)['bits']

def shader_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1]);source=(root/'gpu/core_probability.slang').read_text()
    assert hashlib.sha256(source.encode()).hexdigest()==SOURCE_SHA256,'Review changed certified power algorithm'
    body=source[source.index('[noinline]\nuint64_t coreProbability'):]
    body=body.replace('coreProbability(uint64_t x, out uint status)','coordinateUnitPower(uint64_t x, uint64_t exponentBits, out uint status)',1)
    guard='    status = 0;\n'
    body=body.replace(guard,guard+'    if (!f64Finite(exponentBits) || exponentBits < (uint64_t(0x3bf00000U)<<32) || exponentBits > (uint64_t(0x40f00000U)<<32) || f64Less(uint64_t(1023)<<52,x)) { status=2;return 0; }\n',1)
    old='    // Exact binary64 2.55, not the rational 51/20.\n    Bounds y; y.lo = wideSmall(0); y.lo.limb[2] = 0xccccc000; y.lo.limb[3] = 0x8ccccccc; y.lo.limb[4] = 2; y.hi = y.lo;'
    new='''    // Exact binary64 exponent: all significand bits fit Q128 on this domain.
    int ye;uint64_t ys;f64Unpack(exponentBits,ye,ys);uint shift=uint(ye-1075+128);
    Bounds y;y.lo=wideSmall(0);
    for(uint bit=0;bit<53;bit++)if((ys&(uint64_t(1)<<bit))!=0)y.lo.limb[(bit+shift)/32]|=1U<<((bit+shift)%32);
    y.hi=y.lo;'''
    assert body.count(old)==1;body=body.replace(old,new,1).replace('hi = 4096','hi = 134217728',1)
    return '// Generated variable-exponent specialization; pinned algorithm SHA256 '+SOURCE_SHA256+'\n#ifndef COORDINATE_UNIT_POWER_V1\n#define COORDINATE_UNIT_POWER_V1\n'+body+'\n#endif\n'

def check_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1]);assert (root/'gpu/coordinate_power_v1.slang').read_text()==shader_schema(root),'Unit-power source drift'
