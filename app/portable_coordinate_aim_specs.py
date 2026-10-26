"""Static authored aim IR, before shared runtime admission; no frame decisions.

All native windows and anchors are retained as runtime expressions. This is a
lowering contract, not a connected GPU caller or a precomputed aim schedule.
"""
import math
from portable_coordinate_scene_specs import bits

PROFILE = 'coordinate-authored-aim-v1'
WINDOWS = ('always', 'burst_charge', 'burst_chain', 'own_full_burst')
ANCHORS = ('combat_start', 'fb_end', 'own_fb_end', 'next_fb_start', 'own_buff_end')
CAPACITY_PER_OWNER = 8


def compile_aim(case, descriptors, *, names, typed_targets=None):
    from calculator import timeline
    from calculator.boss_pattern import coord_spec
    if len(names) != 5 or len(set(names)) != 5:
        raise ValueError('Five distinct roster names required')
    controls = case.get('controls', [{} for _ in range(5)])
    mode = case.get('control_mode', 'solo')
    if len(controls) != 5 or mode not in ('solo', 'warn', 'strict'):
        raise ValueError('Five authored controls and a valid control mode required')
    if coord_spec(case['enemy'].get('coord')) is None:
        raise ValueError('Manual aim requires coordinate mode')
    labels = [r['label'] for r in descriptors['rows']]
    if len(labels) != len(set(labels)) or 'core' in labels:
        raise ValueError('Unambiguous target labels distinct from reserved core required')
    targets = {r['label']: r['slot'] for r in descriptors['rows']}
    slots = list(targets.values())
    if len(slots) != len(set(slots)) or any(type(s) is not int or not 1 <= s <= 127 for s in slots):
        raise ValueError('Distinct non-body coordinate target slots required')
    if typed_targets is not None:
        if isinstance(typed_targets,dict) and set(typed_targets)&{'__enemy__','__enemy__:*'}:raise ValueError('Typed aim label cannot alias logical enemy')
        if not isinstance(typed_targets,dict) or set(typed_targets)&set(targets) or 'core' in typed_targets or any(not isinstance(k,str) or not k or type(v) is not int or not 129<=v<=256 for k,v in typed_targets.items()) or len(set(typed_targets.values()))!=len(typed_targets):raise ValueError('Distinct declared typed aim slots 129..256 required')
        targets.update(typed_targets)
    owners = []
    for who, control in enumerate(controls):
        timeline.validate_control(control, names[who])
        entries = control.get('aim', [])
        if len(entries) > CAPACITY_PER_OWNER:
            raise ValueError('Authored aim capacity exceeded')
        rows = []
        for raw in entries:
            e = timeline._norm_aim_entry(raw, names[who])
            if e['at'] != 'core' and e['at'] not in targets:
                raise ValueError('Unknown authored coordinate aim target')
            priority = e.get('priority')
            if priority is None:
                priority = control.get('priority')
            # -1 means live must_break membership decides HIGH30 versus MID20.
            if priority is None:
                priority = -1
            else:
                priority = timeline._parse_prio(priority, 0, names[who])
                if not 0 <= priority <= 99:
                    raise ValueError('Authored aim priority outside private bound')
            when = dict(kind=0, code=WINDOWS.index(e['window'])) if 'window' in e else dict(kind=1, code=ANCHORS.index(e['anchor']))
            if when['kind'] == 1:
                for key in ('offset', 'len'):
                    value = e[key]
                    if not math.isfinite(value) or abs(value) > 180 or key == 'len' and value <= 0:
                        raise ValueError('Finite bounded authored aim span required')
                    when[key + '_words'] = bits(value)
                when.update(minus=int(e.get('minus') == 'reload_total'), buff_name=e.get('buff', ''))
            gate = e.get('gate')
            when.update(gate_stage=int(gate['burst_stage']) if gate else 0,
                        gate_mask=(1 << names.index(gate['burst_user'])) if gate and gate['burst_user'] in names else 0)
            rows.append(dict(target_kind=0 if e['at'] == 'core' else 1,
                             target_slot=0 if e['at'] == 'core' else targets[e['at']],
                             priority=priority, when=when))
        owners.append(dict(entries=rows, other_control_axes=[k for k, v in control.items() if v and k not in ('aim', 'priority')]))
    return dict(profile=PROFILE, version=1, mode=('solo', 'warn', 'strict').index(mode),
                owners=owners, requires_shared_squad_sequence=bool(case.get('sequence')),
                gpu_execution_connected=False)
