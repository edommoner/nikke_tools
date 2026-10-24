"""Independent high-precision geometry oracle, not the common recipe.

AGM pi, convergent Decimal series and alternate acos/atan reductions do not
use host libm or the Slang/CPU polynomial coefficients and split constants.
"""
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
from fractions import Fraction
from functools import lru_cache
import struct

SIGN=1<<63
def bits(value):return struct.unpack('<Q',struct.pack('<d',value))[0]
def number(value):return struct.unpack('<d',struct.pack('<Q',value))[0]

@lru_cache(None)
def pi():
    with localcontext() as ctx:
        ctx.prec=210;ctx.rounding=ROUND_HALF_EVEN;a=Decimal(1);b=1/Decimal(2).sqrt();t=Decimal(1)/4;p=Decimal(1)
        for _ in range(12):
            next_a=(a+b)/2;b=(a*b).sqrt();t-=p*(a-next_a)**2;a=next_a;p*=2
        return +((a+b)**2/(4*t))

def sincos(x):
    term_s=x;term_c=Decimal(1);s=term_s;c=term_c;xx=x*x;k=1
    while True:
        term_s*= -xx/((2*k)*(2*k+1));term_c*= -xx/((2*k-1)*(2*k))
        s+=term_s;c+=term_c
        if abs(term_s)<Decimal('1e-175') and abs(term_c)<Decimal('1e-175'):return s,c
        k+=1

def atan(value):
    if not value:return Decimal(0)
    if value>1:return pi()/2-atan(1/value)
    scale=1
    while value>Decimal('.1'):
        value=value/(1+(1+value*value).sqrt());scale*=2
    term=value;total=value;xx=value*value;k=1
    while True:
        term*= -xx;part=term/(2*k+1);total+=part
        if abs(part)<abs(total)*Decimal('1e-175'):return total*scale
        k+=1

def reference(op,a,b=0):
    x=number(a);y=number(b)
    with localcontext() as ctx:
        ctx.prec=190;ctx.rounding=ROUND_HALF_EVEN
        if op==1:
            r=abs(Fraction.from_float(x))%360
            axes={0:(0.,1.),90:(1.,0.),180:(0.,-1.),270:(-1.,0.)}
            if r in axes:
                s,c=axes[r];return bits(-s if a&SIGN else s),bits(c)
            if r>180:r-=360
            z=(Decimal(r.numerator)/Decimal(r.denominator))*pi()/180
            s,c=sincos(z)
            return bits(float(s))^(a&SIGN),bits(float(c))
        if op==2:
            z=Decimal.from_float(abs(x))
            if z>pi():z-=2*pi()
            s,c=sincos(z)
            return bits(float(s))^(a&SIGN),bits(float(c))
        if op==3:
            # Inputs are (y,x), matching atan2's argument order.
            yy=Decimal.from_float(abs(x));xx=Decimal.from_float(abs(y))
            if not yy:angle=pi() if b&SIGN else Decimal(0)
            elif not xx:angle=pi()/2
            else:
                angle=atan(yy/xx)
                if b&SIGN:angle=pi()-angle
            return bits(float(angle))|(a&SIGN),0
        if op==4:
            z=Decimal.from_float(x)
            value=pi() if z==-1 else 2*atan(((1-z)/(1+z)).sqrt())
            return bits(float(value)),0
        if op==5:return bits(float(Decimal.from_float(x).sqrt())),0
        raise ValueError('Unknown decimal reference operation')

def ulp_distance(a,b):
    if a&~SIGN==0 and b&~SIGN==0:return 0
    key=lambda x:(~x&((1<<64)-1)) if x&SIGN else x|SIGN
    return abs(key(a)-key(b))
