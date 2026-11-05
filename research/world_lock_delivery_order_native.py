"""Actual shot/skill/gauge ordering, before any new delivery policy is installed."""
import copy,importlib.util
from pathlib import Path

def observe_order():
    spec=importlib.util.spec_from_file_location('delivery_order_physical',Path(__file__).with_name('verify-physical-locks.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    from world_frame_native import roster_names
    case=module.fixtures()[0];source=module.source_definitions();original=[]
    for index in (4,8,9):
        case['effects'].append(copy.deepcopy(source[index]));case['owners'].append(0);original.append(dict(index=index,definition=copy.deepcopy(source[index])))
    caster=roster_names(case)[0];events=[]
    def notified(manager,event,t,who):
        if who==caster and event in ('on_attack','full_charge_fire','hit_count','hit_count:'+source[8]['name']):
            events.append(dict(event=event,time=t,gauge=manager.state.get('gauges',{}).get(who,{}).get(source[4]['gauge_id'],0)))
    native=module.observe(case,notification_observer=notified)
    return dict(events=events,shots=native['lock_shots'],clears=native['lock_clears'],original_definitions=original,
        native_order_observed=True,delivery_policy_installed=False,sequential_target_selection_verified=False,full25_verified=False)
