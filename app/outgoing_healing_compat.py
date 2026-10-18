"""Explicit CPU model extension for parsed outgoing_heal_pct (upstream missing).

Body healing = original amount * recipient multiplier * source multiplier.
The source of ordinary healing is the original caster; for lifesteal it is the
attacker, following the pinned engine's existing heal_source convention.
Cover/shield/decoy repair and resurrection are outside this body-heal model.
No source files in the pinned checkout are changed. This is a declared model,
not independent proof of in-game interaction rules.
"""
import ast,inspect,textwrap
from functools import wraps

def install():
    from calculator import timeline
    from calculator import buff_manager as module
    BuffManager=module.BuffManager
    if getattr(BuffManager.heal_received_mult,'_nikke_outgoing_healing',False):return
    original=BuffManager.heal_received_mult
    @wraps(original)
    def healing(self,name,t,*,heal_source=None):
        received=original(self,name,t)
        if heal_source is None:return received
        return received*max(0.0,1.0+self._live_sum(heal_source,'outgoing_heal_pct',t)/100.0)

    # Preserve all original line locations, including the frame-end location
    # consumed by the independent CPU trace observer.
    def instrument(fn,source):
        lines,first=inspect.getsourcelines(fn)
        tree=ast.parse(textwrap.dedent(''.join(lines)));calls=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='heal_received_mult':
                assert len(node.args)==2 and not node.keywords
                value=ast.parse(source,mode='eval').body
                node.keywords.append(ast.keyword(arg='heal_source',value=value));calls.append(node)
        assert len(calls)==1,(fn.__name__,len(calls))
        ast.fix_missing_locations(tree);ast.increment_lineno(tree,first-1)
        scope={};exec(compile(tree,inspect.getsourcefile(fn),'exec'),fn.__globals__,scope)
        result=scope[fn.__name__];result.__defaults__=fn.__defaults__;result.__kwdefaults__=fn.__kwdefaults__
        return result

    from runner import sim
    assert sim.simulate is timeline.simulate
    register=instrument(timeline._register_instant_handlers,'caster')
    simulate=instrument(timeline.simulate,'ev.caster')
    healing._nikke_outgoing_healing=True
    module._DIRECT_READ_STATS=module._DIRECT_READ_STATS|{'outgoing_heal_pct'}
    # Enable only this now-modeled cube; keep every other unsupported entry.
    from runner import spec
    cube='렐릭 힐링 큐브'
    for table in (module._CUBE,spec._CUBE_TABLE):
        entry=dict(table[cube]);assert entry['stat']=='outgoing_heal_pct'
        entry.pop('unsupported',None);table[cube]=entry
    spec.CUBES[cube]=spec._CUBE_TABLE[cube]
    BuffManager.heal_received_mult=healing
    timeline._register_instant_handlers=register;timeline.simulate=simulate
    sim.simulate=simulate
