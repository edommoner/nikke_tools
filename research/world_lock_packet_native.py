"""Passive observations of actual emission lists and actual native _land calls."""
import sys,copy
from contextlib import contextmanager
from dataclasses import replace
from unittest.mock import patch
from lock_delivery_policy import select,MODEL
from named_generation_locks import registry_views
from effect_runtime import state
from world_coordinate_manual_native import capture as capture_manual
from world_physical_locks_native import capture as capture_physical,baseline
from live_lock_delivery_policy import select_live,MODEL as LIVE_MODEL

@contextmanager
def capture(case,*,candidate_observer=None,delivery_model=None,diagnostics=True,enemy_carrier=False):
    if delivery_model not in (None,LIVE_MODEL):raise ValueError('Unknown declared lock delivery model')
    name=case['packet_skill'];snaps=[];events=[];starts={};packets={};manual={}
    def shot(manager,t,snapshot):snaps.append((t,snapshot))
    def emit(phase,entry):
        if not diagnostics:return
        manager=entry['manager'];boss,registry=state(manager).world_actor_registry
        from world_actor_pool_native import actor_bindings
        bindings=actor_bindings(boss);selected=select(entry['snapshot'],entry['hit'],entry['hits'],registry_views(registry),model=MODEL)
        handle=selected.handle
        slot=next(i for i,b in enumerate(bindings) if int(b.kind)==int(handle.kind) and b.identity==handle.identity)+1 if handle else 0
        events.append(dict(phase=phase,packet=entry['packet'],source=entry['source'],hit=entry['hit'],hits=entry['hits'],token=entry['token'],revision=entry['snapshot'].revision,count=len(entry['snapshot'].handles),time=entry['time'],ordinal=selected.index,slot=slot,generation=handle.generation if handle else 0,current=selected.current_generation,status=selected.status))
    @contextmanager
    def primary():
        with capture_manual(case) as observed:
            previous=sys.getprofile()
            def profile(frame,event,arg):
                if previous is not None:previous(frame,event,arg)
                if frame.f_code.co_name=='_handle_damage_eff' and frame.f_locals.get('eff',{}).get('name')==name:
                    queued=frame.f_locals.get('_dot_events',[])
                    if event=='call':starts[id(frame)]=len(queued)
                    elif event=='return':
                        first=starts.pop(id(frame),len(queued));own=[(i,e) for i,e in enumerate(queued) if i>=first and e.skill_name==name]
                        for hit,(index,ev) in enumerate(own,1):
                            if not snaps or snaps[-1][0]!=ev.t:raise AssertionError('Emission has no same-shot immutable snapshot')
                            entry=dict(manager=frame.f_locals['bm'],packet=index,source=next(i for i,e in enumerate(case['effects']) if e.get('name')==name),hit=hit,hits=len(own),token=len(snaps),snapshot=snaps[-1][1],time=ev.t)
                            if delivery_model is not None:
                                # Explicit missing-selector lowering only. Force route() even if all ADDs die;
                                # otherwise native _land falls through to BODY when has_adds becomes false.
                                ev=replace(ev,to=());queued[index]=ev
                            packets[id(ev)]=entry;emit(0,entry)
                if frame.f_code.co_name=='_land':
                    ev=frame.f_locals.get('ev')
                    if ev is not None and ev.skill_name==name:
                        if id(ev) not in packets:raise AssertionError('Actual landing has no captured queue emission')
                        if event=='call':emit(1,packets[id(ev)])
                        elif event=='return':packets.pop(id(ev))
            sys.setprofile(profile)
            try:yield
            finally:sys.setprofile(previous)
        manual.update(observed)
    from calculator.boss_pattern import BossScript
    original=BossScript.route
    def route(boss,ev,*a,**kw):
        if delivery_model is None or ev.skill_name!=name:return original(boss,ev,*a,**kw)
        entry=packets.get(id(ev))
        if entry is None:raise AssertionError('Lock routing has no live packet association')
        _,registry=state(entry['manager']).world_actor_registry
        selected=select_live(entry['snapshot'],entry['hit'],entry['hits'],registry_views(registry),model=delivery_model)
        if selected.handle is None:return []
        from world_actor_pool_native import actor_bindings
        h=selected.handle
        binding=next(b for b in actor_bindings(boss) if int(b.kind)==int(h.kind) and b.identity==h.identity)
        return [(binding.label,1.0)]
    with patch.object(BossScript,'route',route),capture_physical(case,candidate_observer=candidate_observer,shot_observer=shot,primary_observer=primary(),enemy_carrier=enemy_carrier) as result:
        yield result
    if packets:raise AssertionError('Unconsumed native packet observations')
    result.update(manual);result['lock_packet_trace']=events

def observe(case,*,candidate_observer=None,delivery_model=None):
    before=copy.deepcopy(case)
    with capture(case,candidate_observer=candidate_observer,delivery_model=delivery_model) as result:
        native,trace=baseline(case)
    if delivery_model is None:
        plain,plain_trace=baseline(case)
    else:
        # Fresh independent model state, with packet diagnostics absent. The explicit
        # lowering changes recipients; this is NOT canonical battle equivalence.
        with capture(case,delivery_model=delivery_model,diagnostics=False):plain,plain_trace=baseline(case)
    if native!=plain or trace!=plain_trace or case!=before:raise AssertionError('Packet diagnostics changed complete battle/trace/input')
    result.update(battle=native,skill_trace=trace)
    return result
