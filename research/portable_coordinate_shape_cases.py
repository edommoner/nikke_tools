"""Authored static shapes and literal probe positions; never selected targets."""
import math

def fixtures():
    from calculator.aim import Shape
    shapes=[Shape(0,0,r=2),Shape(12+1e-9,0,r=2),Shape(math.nextafter(12+1e-9,math.inf),0,r=2),Shape(14,0,w=10,h=2),Shape(14,0,w=10,h=2,rot=45),Shape(14,0,w=10,h=2,rot=-45),Shape(14,0,w=10,h=2,rot=90),Shape(1e200,0,r=1e199),Shape(2e-310,0,r=1e-310),Shape(2e-310,0,w=2e-310,h=1e-310,rot=45)]
    return [dict(name='coordinate-shape/'+str(i)+'/'+str(j)+'/'+str(k),shape=shape,point=point,grow=grow) for i,shape in enumerate(shapes) for j,point in enumerate([(0.,0.),(12+1e-9,0.),(15.,0.),(-1e308,1e308),(.5,1.)]) for k,grow in enumerate([0.,10.,30.])]
