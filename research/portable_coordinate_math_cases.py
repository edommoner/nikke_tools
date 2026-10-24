"""Literal binary64 vectors; packing never evaluates their norm."""
import math,struct
MASK=(1<<64)-1
INF=0x7ff0000000000000
NAN=0x7ff8000000000000
def bits(x):return struct.unpack('<Q',struct.pack('<d',x))[0]
def number(x):return struct.unpack('<d',struct.pack('<Q',x))[0]
def vectors():
    rows=[]
    special=[0,1,2,3,4,0xfffffffffffff,0x10000000000000,0x10000000000001,bits(1.),bits(2.),bits(3.),bits(4.),bits(5.),bits(math.nextafter(1.,0.)),bits(math.nextafter(1.,2.)),0x7fefffffffffffff,INF,NAN,0x7ff0000000000001]
    for a in special:
        for b in special:rows.append((a,b))
    for exponent in [-1074,-1073,-1050,-1023,-1022,-1000,-1,0,1,500,1023]:
        for gap in [0,1,26,27,28,29,53]:
            a=math.ldexp(1.5,exponent) if exponent>-1074 else number(1)
            b=math.ldexp(1.75,exponent-gap) if exponent-gap>=-1074 else number(1)
            rows.append((bits(a),bits(b)))
            rows.append((bits(a)|1<<63,bits(b)|1<<63))
    # Hard corrections around sqrt(1+2^-52), including both neighbors.
    for exponent in [-1022,0,1023]:
        for gap in [25,26,27,28,29,52,53]:
            a=math.ldexp(1.,exponent);center=bits(math.ldexp(1.,exponent-gap))
            for delta in [-2,-1,0,1,2]:rows.append((bits(a),max(0,center+delta)))
    seed=0x4e494b4b454d3548
    for _ in range(256):
        seed=(seed*6364136223846793005+1442695040888963407)&MASK
        exponent=(seed>>52)%2047;gap=(seed>>47)%29
        a=(exponent<<52)|(seed&((1<<52)-1))
        seed=(seed*6364136223846793005+1442695040888963407)&MASK
        b=(max(0,exponent-gap)<<52)|(seed&((1<<52)-1));rows.append((a,b))
    while len(rows)<1024:
        seed=(seed*6364136223846793005+1442695040888963407)&MASK;a=seed
        seed=(seed*6364136223846793005+1442695040888963407)&MASK;b=seed
        rows.append((a,b))
    assert len(rows)==1024
    return rows

def native_bits(a,b):
    value=math.hypot(number(a),number(b))
    return NAN if math.isnan(value) else bits(value)

def exact_bits(a,b,*,normal_precision=False):
    """Independent arbitrary-integer square-root oracle, all binary64 inputs."""
    a&=(1<<63)-1;b&=(1<<63)-1
    if a==INF or b==INF:return INF
    if a>INF or b>INF:return NAN
    def decode(x):
        e=x>>52;m=x&((1<<52)-1)
        return ((m|(1<<52),e-1075) if e else (m,-1074))
    ma,pa=decode(a);mb,pb=decode(b);base=min(pa,pb)
    square=(ma*ma<<(2*(pa-base)))+(mb*mb<<(2*(pb-base)))
    if not square:return 0
    exponent=(square.bit_length()-1)//2+base;quantum=exponent-52 if normal_precision else max(-1074,exponent-52);shift=quantum-base
    if shift>=0:
        q=math.isqrt(square)>>shift;left=square*4;right=(2*q+1)**2<<(2*shift)
    else:
        scaled=square<<(-2*shift);q=math.isqrt(scaled);left=scaled*4;right=(2*q+1)**2
    q+=left>right or left==right and q%2
    try:return bits(math.ldexp(float(q),quantum))
    except OverflowError:return INF

def compatible_bits(a,b):
    # CPython vector_norm rounds its scaled normal result before rescaling.
    return exact_bits(a,b,normal_precision=True)
