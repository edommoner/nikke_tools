"""Passive observation of canonical physical coordinate packets.

No selection, probability, damage, rounding or grouping is reimplemented here.
The existing native observer still supplies the whole battle and traces.
"""
import dataclasses
import sys


def observe(case):
    import engine_worker
    from calculator import timeline
    # The legacy projectile observer requires one equal-damage packet per
    # logical pellet. Coordinate shots intentionally do not have that shape.
    # Reuse the full battle/team/control observer before that narrow layer.
    from world_charge_control_native import observe as original
    code = timeline.CharState._coord_pellet.__code__
    rows = []
    errors = []
    previous = sys.getprofile()
    def profile(frame, event, answer):
        if previous is not None:
            previous(frame, event, answer)
        if frame.f_code is not code or event != 'return':
            return
        try:
            values = frame.f_locals
            packets, part, body, core, critical = answer
            landing = values.get('L')
            rows.append(dict(owner=values['self'].name, time=values['t'],
                aim=[values['ax'], values['ay']], spread_radius=values['R'],
                grow=values['grow'], expected=values['expected'],
                geometry=[dict(name=g.name, kind=g.kind) for g in values['tg']],
                landing=None if landing is None else dataclasses.asdict(landing),
                part_fraction=part, body_fraction=body, core_fraction=core,
                critical_fraction=critical,
                packets=[dataclasses.asdict(packet) for packet in packets]))
        except (KeyError, TypeError, AttributeError, ValueError) as error:
            errors.append(type(error).__name__ + ': ' + str(error))
    sys.setprofile(profile)
    try:
        battle, trace = original(case)
    finally:
        sys.setprofile(previous)
    if errors:
        raise ValueError('Physical coordinate observation failed: ' + str(errors))
    return dict(battle=battle, skill_trace=trace, physical_pellets=rows,
                scope='Canonical expected-mode physical observations only; no GPU or group proof')
