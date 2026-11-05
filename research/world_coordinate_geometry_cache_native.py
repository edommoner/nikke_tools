"""Passive real Geometry object/cache observation; never evaluate a new landing."""
from contextlib import contextmanager
from unittest.mock import patch
import struct

def bits(value):return struct.unpack('<Q',struct.pack('<d',float(value)))[0]
def key_bits(key):return [0 if value==0 else bits(value) for value in key]
def value_bits(value):return [bits(value.core_open),bits(value.core_under),*[bits(x) for x in value.front],*[bits(x) for x in value.reach]]

@contextmanager
def capture():
    import engine_worker
    from calculator.boss_pattern import Geometry
    initialize=Geometry.__init__;landing=Geometry.landing;objects=[];queries=[];data={}
    def initialized(self,*args,**kwargs):
        initialize(self,*args,**kwargs);objects.append(self)
    def observed(self,ax,ay,radius,grow=0.):
        identity=next((i for i,obj in enumerate(objects) if obj is self),None)
        if identity is None:raise ValueError('Unobserved Geometry object')
        key=(round(ax,6),round(ay,6),round(radius,6),round(grow,6));hit=key in self._cache;prior=self._cache.get(key)
        result=landing(self,ax,ay,radius,grow)
        if hit and result is not prior:raise ValueError('Canonical Geometry changed first-result reuse')
        queries.append(dict(geometry=identity+1,key=key_bits(key),request_bits=[bits(x) for x in (ax,ay,radius,grow)],hit=hit,value=value_bits(result)))
        return result
    with patch.object(Geometry,'__init__',initialized),patch.object(Geometry,'landing',observed):
        try:yield data
        finally:
            final=objects[-1] if objects else None
            data['final_geometry']=dict(target_names=[g.name for g in final.targets],must_break=list(final.must_break),core_bits=[bits(final.core.x),bits(final.core.y),bits(final.core.r)] if final.core is not None else [0,0,0],auto_bits=[bits(x) for x in final.auto_aim]) if final else dict(target_names=[],must_break=[],core_bits=[0,0,0],auto_bits=[0,0])
            data.update(geometries=len(objects),queries=queries,hits=sum(q['hit'] for q in queries),misses=sum(not q['hit'] for q in queries),peak_entries=max((len(obj._cache) for obj in objects),default=0),final_target_count=len(final.targets) if final else 0,final_entries=[dict(key=key_bits(k),value=value_bits(v)) for k,v in final._cache.items()] if final else [])
