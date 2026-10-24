"""Static finite geometry inputs; no trig, roots or output calculation."""
import random
import sys
from portable_coordinate_numeric_v1 import bits,finite,TAU,HALF_PI,QUARTER_PI,ONE,SIGN,TAN_EIGHTH,number

def fixtures(samples=512):
    rows=[];rng=random.Random(0x434e5631)
    def add(name,op,a,b=0):rows.append((name,op,a,b))
    for index,v in enumerate([0,SIGN,1,SIGN|1,bits(sys.float_info.max),bits(-sys.float_info.max)]):
        add('degree-special/'+str(index),1,v)
    for i in range(-8,9):
        value=bits(float(i*45))
        for j,v in enumerate([value]+([value-1] if value else [])+[value+1]):
            if finite(v):add(f'degree-axis/{i}/{j}',1,v)
    for i in range(samples):
        v=rng.getrandbits(64)
        if finite(v):add('degree-random/'+str(i),1,v)
    for i in range(-8,9):
        value=bits(number(QUARTER_PI)*i)
        for j,v in enumerate([value]+([value-1] if value else [])+[value+1]):
            if finite(v) and v&~SIGN<=TAU:add(f'radian-axis/{i}/{j}',2,v)
    for i in range(samples):
        value=bits((rng.getrandbits(53)/(1<<53))*number(TAU))
        add('radian-random/'+str(i),2,value|(SIGN if i&1 else 0))
    axes=[0,SIGN,ONE,ONE|SIGN,1,1|SIGN,bits(sys.float_info.max),bits(-sys.float_info.max)]
    for i,y in enumerate(axes):
        for j,x in enumerate(axes):add(f'atan-axis/{i}/{j}',3,y,x)
    for i,t in enumerate([TAN_EIGHTH-1,TAN_EIGHTH,TAN_EIGHTH+1,ONE-1,ONE,ONE+1]):
        for j in range(4):add(f'atan-reduction/{i}/{j}',3,t|(SIGN if j&1 else 0),ONE|(SIGN if j&2 else 0))
    for i in range(samples):
        a,b=rng.getrandbits(64),rng.getrandbits(64)
        if finite(a) and finite(b):add('atan-random/'+str(i),3,a,b)
    for i,v in enumerate([0,SIGN,1,1|SIGN,ONE,ONE|SIGN,ONE-1,(ONE-1)|SIGN]):add('acos-special/'+str(i),4,v)
    for i in range(samples):add('acos-random/'+str(i),4,bits(2*(rng.getrandbits(53)/(1<<53))-1))
    for i,v in enumerate([0,SIGN,1,2,0xfffffffffffff,0x10000000000000,0x10000000000001,ONE-1,ONE,ONE+1,bits(4.)-1,bits(4.),bits(4.)+1,bits(sys.float_info.max)]):add('root-special/'+str(i),5,v)
    for i in range(samples):
        v=rng.getrandbits(63)
        if finite(v):add('root-random/'+str(i),5,v)
    return rows
