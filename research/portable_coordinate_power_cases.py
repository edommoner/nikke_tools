"""Static bits for unit powers and landing's exact inverse exponent."""
import random
from portable_coordinate_numeric_v1 import bits,ONE
from portable_coordinate_power_v1 import MIN_EXPONENT,MAX_EXPONENT

def fixtures(samples=512):
    rows=[];ys=[MIN_EXPONENT,bits(2.**-16),bits(.25),bits(.5),bits(1.),bits(2.),bits(2.55),bits(1./2.55),bits(16.),MAX_EXPONENT]
    xs=[0,1,2,0xfffffffffffff,0x10000000000000,bits(2.**-1021),bits(2.**-400),bits(.01),bits(.25),bits(.5),ONE-2,ONE-1,ONE]
    for i,x in enumerate(xs):
        for j,y in enumerate(ys):rows.append((f'boundary/{i}/{j}',x,y))
    rng=random.Random(0x43505631)
    for i in range(samples):
        x=rng.randrange(ONE);y=rng.randrange(MIN_EXPONENT,MAX_EXPONENT+1);rows.append((f'random/{i}',x,y))
    for y in [bits(2.55),bits(1./2.55)]:
        for i in range(128):rows.append((f'landing/{y:x}/{i}',bits(rng.random()),y))
    return rows
