"""Native full-profile witness; only read existing ready and instant frames."""
import importlib.util,inspect,sys
from pathlib import Path
import engine_worker
from calculator.buff_manager import BuffManager


def plain_observe(case):
    spec=importlib.util.spec_from_file_location('manual_swap_real_oracle',Path(__file__).resolve().parent/'verify-world-projectile-rosters.py');real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
    return real.native_reference(case['body'])


def observe(case):
    ready_code=inspect.unwrap(BuffManager.manual_swap_ready).__code__;instant_code=inspect.unwrap(BuffManager._dispatch_instant).__code__
    ready=[];calls=[];pending={};previous=sys.getprofile()
    def profile(frame,event,arg):
        if previous is not None:previous(frame,event,arg)
        if event=='return' and frame.f_code is ready_code and frame.f_locals['caster']==case['character'] and arg:ready.append(frame.f_locals['t'])
        if frame.f_code is instant_code and frame.f_locals['eff'].get('stat')=='squad_ammo_consume_as':
            local=frame.f_locals
            if event=='call':pending[id(frame)]=len(calls);calls.append(dict(time=local['t'],caster=local['caster'],name=local['eff']['name']))
            elif event=='return':calls[pending.pop(id(frame))]['value']=local.get('val')
    sys.setprofile(profile)
    try:native,trace=plain_observe(case)
    finally:sys.setprofile(previous)
    native['manual_swap_roster']=dict(ready=ready,calls=calls,physical_shots=len(trace))
    return native,trace
