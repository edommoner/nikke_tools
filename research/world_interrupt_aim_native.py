"""Observe private receipts from actual native target landings, before lifesteal."""
from dataclasses import asdict
from portable_interrupt_runtime import capture_interrupt_landings
from world_focus_aim_native import observe as focus_observe


def observe(case):
    with capture_interrupt_landings() as receipts:native,trace=focus_observe(case)
    native['interrupt_landings']=[asdict(row) for row in receipts]
    return native,trace
