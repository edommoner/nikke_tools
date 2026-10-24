"""Versioned deterministic geometry math: one polynomial IR for CPU/Slang.

No host transcendental functions. IEEE binary64 operations are rounded after
each IR instruction. Integer reduction/sqrt have independent CPU algorithms.
The full geometry/battle profile is not yet connected or certified.
"""
from fractions import Fraction
from decimal import Context, Decimal, localcontext, ROUND_HALF_EVEN
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import struct
from types import MappingProxyType

PROFILE='coordinate-binary64-v1'
MAGIC=0x434e5631
SIGN=1<<63
MASK=(1<<52)-1
ONE=0x3ff0000000000000
PI=0x400921fb54442d18
HALF_PI=0x3ff921fb54442d18
QUARTER_PI=0x3fe921fb54442d18
TAU=0x401921fb54442d18
DEG_RAD=0x3f91df46a2529d39
TAN_EIGHTH=0x3fda827999fcef32
SECTORS=((45,True,0),(135,False,1),(225,True,2),(315,False,3))
QUADRANTS=(('s',False,'c',False),('c',False,'s',True),
           ('s',True,'c',True),('c',True,'s',False),('s',False,'c',False))

def bits(value):return struct.unpack('<Q',struct.pack('<d',value))[0]
def number(value):return struct.unpack('<d',struct.pack('<Q',value))[0]
def finite(value):return value&~SIGN<0x7ff0000000000000
def zero(value):return value&~SIGN==0
def add(a,b):return bits(number(a)+number(b))
def sub(a,b):return add(a,b^SIGN)
def mul(a,b):return bits(number(a)*number(b))
def div(a,b):return bits(number(a)/number(b))

@lru_cache(None)
def high_precision_pi():
    # Independent Machin identity; used only to author split constants/audits.
    with localcontext(Context(prec=190,rounding=ROUND_HALF_EVEN)):
        def atan_inverse(n):
            x=Decimal(1)/n;power=x;total=x;index=1
            while True:
                power*=-(x*x);term=power/(2*index+1);total+=term
                if abs(term)<Decimal('1e-185'):return +total
                index+=1
        return +(16*atan_inverse(5)-4*atan_inverse(239))

@lru_cache(None)
def half_pi_chunks():
    with localcontext(Context(prec=180,rounding=ROUND_HALF_EVEN)):
        remaining=high_precision_pi()/2;out=[]
        for _ in range(6):
            value=bits(float(remaining))&~((1<<29)-1) # 24 significant bits
            out.append(value);remaining-=Decimal.from_float(number(value))
        return tuple(out)

@lru_cache(None)
def polynomial(kind):
    maximum={'sin':19,'cos':20,'atan':63}[kind]
    minimum=2 if kind=='cos' else 3
    constants={};ops=[];last=None
    for degree in range(maximum,minimum-1,-2):
        n=degree//2
        coefficient=Fraction((-1)**n,degree if kind=='atan' else math.factorial(degree))
        name=f'{kind}_k{degree}';constants[name]=bits(float(coefficient))
        if last is None:last=name
        else:
            t=f'{kind}_m{degree}';v=f'{kind}_a{degree}'
            ops.extend([(t,'mul',last,'z2'),(v,'add',t,name)]);last=v
    if kind=='cos':ops.extend([('cos_tail','mul','z2',last),('cos_result','add','one','cos_tail')])
    else:ops.extend([(kind+'_cube','mul','z','z2'),(kind+'_tail','mul',kind+'_cube',last),(kind+'_result','add','z',kind+'_tail')])
    return MappingProxyType(constants),tuple(ops),kind+'_result'

def evaluate(kind,z):
    constants,ops,result=polynomial(kind);env={**constants,'z':z,'z2':mul(z,z),'one':ONE}
    for name,op,a,b in ops:env[name]={'add':add,'mul':mul}[op](env[a],env[b])
    return env[result]

def positive_remainder(value,period=360):
    x=Fraction.from_float(number(value&~SIGN));r=x%period
    return bits(float(r))

def quadrant_pair(q,s,c,negative,axis_zeros):
    env={'s':s,'c':c};sn,ss,cn,cs=QUADRANTS[q]
    s=env[sn]^(SIGN if ss else 0)^(SIGN if negative else 0);c=env[cn]^(SIGN if cs else 0)
    if axis_zeros:
        if zero(s):s=SIGN if negative else 0
        if zero(c):c=0
    return s,c

def sincos_degrees(value):
    if not finite(value):raise ValueError('Finite degree input required')
    r=positive_remainder(value);q=4
    for limit,inclusive,sector in SECTORS:
        bound=bits(float(limit))
        if r<bound or inclusive and r==bound:q=sector;break
    z=mul(sub(r,bits(float(q*90))),DEG_RAD)
    return quadrant_pair(q,evaluate('sin',z),evaluate('cos',z),bool(value&SIGN),True)

def sincos_radians(value):
    if not finite(value) or value&~SIGN>TAU:raise ValueError('Radians outside bounded geometry domain')
    x=value&~SIGN;q=round(number(div(x,HALF_PI)));z=x
    for chunk in half_pi_chunks():z=sub(z,mul(bits(float(q)),chunk))
    return quadrant_pair(q,evaluate('sin',z),evaluate('cos',z),bool(value&SIGN),False)

def sqrt_bits(value):
    if not finite(value) or value&SIGN and not zero(value):raise ValueError('Finite nonnegative root input required')
    if zero(value):return value
    exponent=(value>>52)&2047;s=value&MASK
    if exponent:s|=1<<52
    else:
        exponent=1;shift=53-s.bit_length();s<<=shift;exponent-=shift
    e=exponent-1023;root_exp=e//2;radicand=s<<(52+e-2*root_exp)
    root=math.isqrt(radicand);delta=4*radicand-(2*root+1)**2
    if delta>0 or delta==0 and root&1:root+=1
    if root==1<<53:root>>=1;root_exp+=1
    return ((root_exp+1023)<<52)|(root&MASK)

def atan2_bits(y,x):
    if not finite(x) or not finite(y):raise ValueError('Finite atan2 inputs required')
    ax=x&~SIGN;ay=y&~SIGN;sign=y&SIGN
    if ay==0:return sign|(PI if x&SIGN else 0)
    if ax==0:return sign|HALF_PI
    swapped=ay>ax;t=div(ax,ay) if swapped else div(ay,ax)
    angle=(add(QUARTER_PI,evaluate('atan',div(sub(t,ONE),add(t,ONE))))
           if t>TAN_EIGHTH else evaluate('atan',t))
    if swapped:angle=sub(HALF_PI,angle)
    if x&SIGN:angle=sub(PI,angle)
    return angle|sign

def acos_bits(x):
    if not finite(x) or x&~SIGN>ONE:raise ValueError('Acos input outside[-1,1]')
    return atan2_bits(sqrt_bits(mul(sub(ONE,x),add(ONE,x))),x)

def contract():
    return dict(profile=PROFILE,version=1,magic=MAGIC,
        rounding='binary64 nearest/even after every operation; gradual underflow; no fused operations',
        degree_reduction='exact remainder of magnitude modulo360; nearest90-degree sector; canonical axis zeros',
        radians_domain='finite magnitude<=binary64 tau; six24-bit pi/2 chunks',
        half_pi_chunks=[f'{v:016x}' for v in half_pi_chunks()],degree_radians=f'{DEG_RAD:016x}',
        polynomials={kind:dict(constants={k:f'{v:016x}' for k,v in polynomial(kind)[0].items()},operations=polynomial(kind)[1],result=polynomial(kind)[2]) for kind in ('sin','cos','atan')},
        sqrt='exact integer midpoint comparison, ties/even',atan2='finite operands, signed axes, min/max ratio',
        acos='atan2(sqrt((1-x)*(1+x)),x), finite[-1,1]',
        validation_gate_ulp=4,correct_rounding_claim=False,
        battle_connected=False,full_numeric_policy_implemented=False)

def contract_sha256():return hashlib.sha256(json.dumps(contract(),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def shader_schema():
    def literal(value):return f'(uint64_t(0x{value>>32:08x}U)<<32|uint64_t(0x{value&0xffffffff:08x}U))'
    out=['// Generated from portable_coordinate_numeric_v1; contract '+contract_sha256(),
        '// Requires binary64, coordinate_math and coordinate_arc_scalar helpers.',
        '#ifndef PORTABLE_COORDINATE_NUMERIC_V1','#define PORTABLE_COORDINATE_NUMERIC_V1']
    for kind in ('sin','cos','atan'):
        constants,ops,result=polynomial(kind);out+=['[noinline]',f'uint64_t coordinateKernel_{kind}(uint64_t z)','{','    uint64_t z2=f64Mul(z,z),one='+literal(ONE)+';']
        out+=['    uint64_t '+name+'='+literal(value)+';' for name,value in constants.items()]
        out+=['    uint64_t '+name+'=f64'+op.title()+'('+a+','+b+');' for name,op,a,b in ops]
        out+=['    return '+result+';','}']
    out+=['void coordinateQuadrantPair(uint q,uint64_t z,bool negative,bool axisZeros,out uint64_t sine,out uint64_t cosine)','{',
          '    uint64_t s=coordinateKernel_sin(z),c=coordinateKernel_cos(z);']
    for i,(sn,ss,cn,cs) in enumerate(QUADRANTS):
        out+=[('    if' if i==0 else '    else if')+f'(q=={i})'+'{sine='+sn+('^F64_SIGN' if ss else '')+';cosine='+cn+('^F64_SIGN' if cs else '')+';}']
    out+=['    if(negative)sine^=F64_SIGN;',
          '    if(axisZeros){if(f64Zero(sine))sine=negative?F64_SIGN:0;if(f64Zero(cosine))cosine=0;}','}',
          '[noinline]','void coordinateSinCosDegrees(uint64_t degrees,out uint64_t sine,out uint64_t cosine)','{',
          '    uint64_t r=coordinatePositiveModulo(f64Abs(degrees),'+literal(bits(360.))+');uint q=4;']
    for i,(bound,inclusive,q) in enumerate(SECTORS):out+=[('    if' if i==0 else '    else if')+f'(r{ "<=" if inclusive else "<" }'+literal(bits(float(bound)))+f')q={q};']
    out+=['    uint64_t z=f64Mul(f64Add(r,f64FromI64(q*90)^F64_SIGN),'+literal(DEG_RAD)+');',
          '    coordinateQuadrantPair(q,z,(degrees&F64_SIGN)!=0,true,sine,cosine);','}',
          '[noinline]','void coordinateSinCosRadians(uint64_t radians,out uint64_t sine,out uint64_t cosine)','{',
          '    uint64_t x=f64Abs(radians);uint status;uint q=uint(f64ToI64(f64Integral(f64Div(x,'+literal(HALF_PI)+'),0),1,status));uint64_t z=x;']
    for chunk in half_pi_chunks():out+=['    z=f64Add(z,f64Mul(f64FromI64(q),'+literal(chunk)+')^F64_SIGN);']
    out+=['    coordinateQuadrantPair(q,z,(radians&F64_SIGN)!=0,false,sine,cosine);','}',
          '[noinline]','uint64_t coordinateSqrt(uint64_t x)','{',
          '    if(f64Zero(x))return x;int exponent;uint64_t s;f64Unpack(x,exponent,s);',
          '    int e=exponent-1023,rootExponent=e/2;if(e<0&&e%2!=0)rootExponent--;',
          '    CoordinateWide radicand=cmShift(cmWide(0,s),uint(52+e-2*rootExponent));uint64_t root=0;',
          '    for(int bit=52;bit>=0;bit--){uint64_t candidate=root|(uint64_t(1)<<uint(bit));if(!cmLess(radicand,cmSquare(candidate,0)))root=candidate;}',
          '    CoordinateWide four=cmShift(radicand,2),mid=cmSquare(2*root+1,0);bool above=cmLess(mid,four),equal=!above&&!cmLess(four,mid);',
          '    if(above||(equal&&(root&1)!=0))root++;return f64Pack(0,rootExponent+1023,root<<3);','}',
          '[noinline]','uint64_t coordinateAtan2(uint64_t y,uint64_t x)','{',
          '    uint64_t ax=f64Abs(x),ay=f64Abs(y),sign=y&F64_SIGN;',
          '    if(ay==0)return sign|((x&F64_SIGN)!=0?'+literal(PI)+':0);',
          '    if(ax==0)return sign|'+literal(HALF_PI)+';',
          '    bool swapped=ay>ax;uint64_t t=swapped?f64Div(ax,ay):f64Div(ay,ax),one='+literal(ONE)+';',
          '    uint64_t angle=t>'+literal(TAN_EIGHTH)+'?f64Add('+literal(QUARTER_PI)+',coordinateKernel_atan(f64Div(f64Add(t,one^F64_SIGN),f64Add(t,one)))):coordinateKernel_atan(t);',
          '    if(swapped)angle=f64Add('+literal(HALF_PI)+',angle^F64_SIGN);if((x&F64_SIGN)!=0)angle=f64Add('+literal(PI)+',angle^F64_SIGN);return angle|sign;','}',
          'uint64_t coordinateAcos(uint64_t x){uint64_t one='+literal(ONE)+';return coordinateAtan2(coordinateSqrt(f64Mul(f64Add(one,x^F64_SIGN),f64Add(one,x))),x);}',
          '#endif']
    return '\n'.join(out)+'\n'

def check_schema(root=None):
    assert (Path(root or Path(__file__).resolve().parents[1])/'gpu/coordinate_numeric_v1.slang').read_text()==shader_schema(),'Shared coordinate numeric recipe/source drift'
