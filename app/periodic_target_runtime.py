"""One instant timer executor with detached aim and registration ownership."""
import ast
from functools import wraps
from world_actor_runtime import set_control_aim,sample_control_aim
from reference_rewrite import rewrite_reference
from timer_registry_runtime import tick_instant as tick,tick_damage,TimerRegistry


class TimerPass(ast.NodeTransformer):
    def __init__(self):self.counts=dict(timer_pass=0,damage_pass=0)
    def visit_If(self,node):
        if ast.unparse(node.test)=='self._instant_timers':
            self.counts['timer_pass']+=1
            return ast.copy_location(ast.parse('self.tick_periodic_instants(t)').body[0],node)
        if ast.unparse(node.test)=='self._damage_handler and self._dot_timers':
            self.counts['damage_pass']+=1
            return ast.copy_location(ast.parse('self.tick_periodic_damage(t)').body[0],node)
        return self.generic_visit(node)


def install():
    from calculator.buff_manager import BuffManager
    if getattr(BuffManager,'_nikke_periodic_targets',False):return
    BuffManager.set_control_aim=set_control_aim;BuffManager.sample_control_aim=sample_control_aim;BuffManager.tick_periodic_instants=tick
    BuffManager.tick_periodic_damage=tick_damage
    initialize=BuffManager.__init__
    @wraps(initialize)
    def init(self,*args,**kwargs):
        initialize(self,*args,**kwargs)
        self._dot_timers=TimerRegistry(self._dot_timers,preserve_phase=lambda eid:self._eff_by_id.get(eid,{}).get('stat')=='dot_damage' and not self._eff_by_id[eid].get('ramp_interval'))
    BuffManager.__init__=init
    BuffManager.tick=rewrite_reference(BuffManager.tick,TimerPass(),dict(timer_pass=1,damage_pass=1),compose=True)
    BuffManager._nikke_periodic_targets=True
