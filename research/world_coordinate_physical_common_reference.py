"""Adapt the passive common-policy observation to the shared reference CLI."""
from world_coordinate_physical_common import observe as physical


def observe(case):
    result = physical(case)
    trace = result.pop('skill_trace')
    return result, trace
