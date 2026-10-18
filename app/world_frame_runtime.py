"""One world transition per timestamp, including initialization and frame0."""
from functools import wraps

def install():
    from calculator.boss_pattern import BossScript
    if getattr(BossScript,'_nikke_world_frame_once',False):return
    original=BossScript.begin_frame
    @wraps(original)
    def begin_frame(self,t,enemy):
        previous=getattr(self,'_nikke_world_frame_time',None)
        if previous is not None:
            if t<previous:raise ValueError('World frame times must be monotonic')
            if t==previous:return []
        result=original(self,t,enemy)
        self._nikke_world_frame_time=t
        return result
    BossScript.begin_frame=begin_frame
    BossScript._nikke_world_frame_once=True
