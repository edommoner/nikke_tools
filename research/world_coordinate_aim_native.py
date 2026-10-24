"""Passive frame aims, actual control requests and actual window/anchor returns.

Only observes calls already made by canonical simulate. No added aim resolution,
window query, arbitration, schedule, packet production or geometry calculation.
"""
import copy
import sys
from unittest.mock import patch
from world_coordinate_physical_common import observe as physical
from world_coordinate_matrix_common import common_policy
from world_frame_native import roster_names


def observe(case):
    import engine_worker
    from calculator import timeline
    names = roster_names(case)
    frames, requests, windows, anchors, queries = [], [], [], [], []
    tick = timeline.CharState.tick
    request = timeline.CharState._wants_control
    window = timeline.CharState._when_open
    anchor = timeline.CharState._anchor_at
    point = timeline.CharState._aim_point

    def state(bm):
        s = bm.state
        return dict(camera_mask=sum(1 << names.index(n) for n in s['camera']),
                    owner=names.index(s['ctrl_owner']) if s['ctrl_owner'] else -1,
                    full_burst=bool(s['full_burst']), charging=bool(s['burst_gauge_charging']),
                    cast_mask=sum(1 << names.index(n) for n in names if s.get('burst_casted', {}).get(n)),
                    users={k: sorted(v) for k, v in s.get('burst_cycle_users', {}).items()})

    def observed_tick(cs, t, bm, enemy, cfg):
        if not frames or frames[-1]['time'] != t:
            geom = bm.state['enemy'].get(timeline.GEOM_KEY)
            if geom is None:
                raise ValueError('Coordinate aim reference requires live geometry')
            centers = {g.name: [g.shape.x, g.shape.y] for g in geom.targets}
            if geom.core is not None:
                centers['core'] = [geom.core.x, geom.core.y]
            frames.append(dict(time=t, **state(bm),
                aims=[dict(point=list(bm.state['aim'][n][0]), target=bm.state['aim'][n][1]) for n in names],
                centers=centers, auto=list(geom.auto_aim), must_break=list(geom.must_break)))
        return tick(cs, t, bm, enemy, cfg)

    def observed_request(cs, t, bm):
        result = request(cs, t, bm)
        requests.append(dict(time=t, who=names.index(cs.name), request=result))
        return result

    def observed_window(cs, entry, t, bm):
        result = window(cs, entry, t, bm)
        # Ignore other control axes; an aim entry retains its authored `at`.
        if 'at' in entry:
            windows.append(dict(time=t, who=names.index(cs.name), entry=copy.deepcopy(entry),
                                opened=result, **state(bm)))
        return result

    def observed_anchor(cs, entry, t, bm):
        result = anchor(cs, entry, t, bm)
        if 'at' in entry:
            anchors.append(dict(time=t, who=names.index(cs.name), entry=copy.deepcopy(entry),
                                resolved=None if result is None else list(result), **state(bm)))
        return result

    def observed_point(cs, bm, geom):
        result = point(cs, bm, geom)
        caller = sys._getframe(1)
        selected = bm.state.get('aim', {}).get(cs.name)
        queries.append(dict(who=names.index(cs.name), time=caller.f_locals.get('t'),
                            caller=caller.f_code.co_name, point=list(result),
                            last_resolved_frame=frames[-1]['time'] if frames else None,
                            selected_target=selected[1] if selected else None,
                            selected_point=list(selected[0]) if selected else None,
                            fallback_auto=list(geom.auto_aim)))
        return result

    with patch.object(timeline.CharState, 'tick', observed_tick), \
         patch.object(timeline.CharState, '_wants_control', observed_request), \
         patch.object(timeline.CharState, '_when_open', observed_window), \
         patch.object(timeline.CharState, '_anchor_at', observed_anchor), \
         patch.object(timeline.CharState, '_aim_point', observed_point), common_policy():
        result = physical(case)
    trace = result.pop('skill_trace')
    result['coordinate_aim'] = dict(frames=frames, requests=requests, windows=windows, anchors=anchors, queries=queries,
                                   producer='canonical simulate._resolve_aims after arbitration before character ticks')
    return result, trace
