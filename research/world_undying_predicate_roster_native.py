"""Original whole-roster oracle plus read-only undying predicate capture."""
import importlib.util
from pathlib import Path
import engine_worker
from world_undying_predicate_native import capture_queries


def plain_observe(case):
    spec=importlib.util.spec_from_file_location('undying_roster_oracle',Path(__file__).resolve().parent/'verify-world-projectile-rosters.py');real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
    return real.native_reference(case['body'])


def observe(case):
    with capture_queries(case['body']['squad'],case['effect_name']) as (checks,managers):native,trace=plain_observe(case)
    native['undying_predicate_roster']=dict(checks=checks,physical_shots=len(trace))
    return native,trace
