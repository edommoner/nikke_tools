"""Observe actual native pool before finish; canonical geometry projects that pool."""
import copy,sys
from calculator.boss_pattern import BossScript,validate
from world_parts_skill_native import observe as original_observe
from portable_coordinate_scene_specs import compile_scene

def observe(case):
    previous=sys.getprofile();snapshots=[]
    _,meta=compile_scene(case['coordinate_sidecar']);rows={r['label']:r for r in meta['rows']}
    def profile(frame,event,arg):
        if previous is not None:previous(frame,event,arg)
        if event!='call' or frame.f_code is not BossScript.finish.__code__:return
        boss=frame.f_locals['self']
        # A separate read-only projection: no changes to the battle BossScript.
        patterns=validate(copy.deepcopy(case['coordinate_sidecar']['patterns']),coord=True)
        shadow=BossScript(patterns,dict(coord={},core_px=0),lambda *_:False)
        shadow._runs=copy.deepcopy(boss._runs)
        for run in shadow._runs:
            run.p=patterns[run.p.idx]
            for i,target in enumerate(run.targets):target.spec=run.p.targets[i]
        shadow._apply_geom([r for r in shadow._runs if r.active],{})
        def handle(g):
            r=rows[g.name];return [r['slot'],r['kind'],r['identity'],boss._runs[r['pattern']].opens]
        snapshots.append(dict(time=case['duration'],all=[handle(g) for g in shadow.geom.targets],parts=[handle(g) for g in shadow.geom.targets if g.kind=='parts']))
    sys.setprofile(profile)
    try:native,trace=original_observe(case)
    finally:sys.setprofile(previous)
    if len(snapshots)!=1:raise ValueError('Expected exactly one native pool finish boundary')
    for key in ('parts_skill_events','parts_skill_lifecycle','parts_skill_accounting'):native.pop(key,None)
    return dict(battle=native,skill_trace=trace,coordinate_pool=snapshots[0])
