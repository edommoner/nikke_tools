"""Native ammo boundaries including Python integer/round and signed cartridges."""
import math,random


def fixtures():
    rows=[]
    def add(kind,capacity,current,value,label):rows.append(dict(name='ammo-numeric/'+label,kind=kind,capacity=capacity,current=current,value=value))
    for capacity in (1,10,16,65535,2147483647):
        for current in (-2147483648,-3,0,min(3,capacity),capacity):
            for value in (-1e308,-1e30,-1000.,-100.,-25.,-15.,-5.,-2.95,-0.,5.,15.,25.,100.,1000.,1e30,1e308):
                add(13,capacity,current,value,f'pct/{capacity}/{current}/{value}')
        for current in (-2147483648,-3,0,capacity):
            for value in (-1e30,-2147483648.,-1.75,-0.,.75,2.,2147483647.,1e30):add(14,capacity,current,value,f'flat/{capacity}/{current}/{value}')
        for threshold in (.5,1.5,2.5):
            value=threshold*100/capacity
            for j,v in enumerate((math.nextafter(value,-math.inf),value,math.nextafter(value,math.inf))):add(13,capacity,0,v,f'tie/{capacity}/{threshold}/{j}')
    rng=random.Random(4961)
    for i in range(100):
        capacity=rng.randint(1,2147483647);kind=13 if i%2 else 14
        add(kind,capacity,rng.randint(-2147483648,capacity),rng.uniform(-300.,300.) if kind==13 else rng.uniform(-1e12,1e12),f'random/{i}')
    return rows
