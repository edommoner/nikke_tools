"""Validate the native name index across registration's pre-append capture.
Keep its cached lookup and exact gauge/feather/first-carrier precedence.
"""
from functools import wraps

def install():
    from calculator.buff_manager import BuffManager
    original=BuffManager.ref_count
    if getattr(original,'_nikke_live_reference_lookup',False):return
    @wraps(original)
    def live_reference(self,caster,ref):
        # Native invalidation precedes capture and append. Length catches the
        # subsequent append; identity/version catch list replacement/removal.
        stamp=(id(self._active),len(self._active),self._cache_version)
        if getattr(self,'_nikke_reference_index_stamp',None)!=stamp:
            self._name_index_cache.clear();self._nikke_reference_index_stamp=stamp
        return original(self,caster,ref)
    live_reference._nikke_live_reference_lookup=True
    BuffManager.ref_count=live_reference

    original_register=BuffManager.register_damage_handler
    @wraps(original_register)
    def register_damage(self,handler):
        if handler is None:return original_register(self,None)
        @wraps(handler)
        def scoped(effect,caster,t,*args,**kwargs):
            previous=self._cur_t;self._cur_t=t
            try:return handler(effect,caster,t,*args,**kwargs)
            finally:self._cur_t=previous
        return original_register(self,scoped)
    register_damage._nikke_reference_damage_time=True
    BuffManager.register_damage_handler=register_damage
