"""Reject literal base clocks that disagree with the existing static normalizer."""
from unittest.mock import patch

def validate(case):
    from calculator import timeline
    from world_frame_native import authored_metadata,roster_names
    from world_authored_roster import skill_levels
    from portable_charge_clock_specs import normalize_static_clock
    chars=[dict(name=n,skill_levels=level,control=control) for n,level,control in zip(roster_names(case),skill_levels(case),case['controls'],strict=True)]
    with patch.dict(timeline._NIKKE,authored_metadata(case)),patch.dict(timeline._DELAYS['_exceptions'],{},clear=True),patch.dict(timeline._DELAYS['_defaults_by_weapon_type'],{'AR':{'post_reload_delay':0}},clear=True):
        expected=normalize_static_clock(chars,case['base_atk'],case['enemy'])
    if case.get('post_fire_delays')!=expected:raise ValueError('Authored base post-fire delay conflicts with canonical static weapon')
    return expected
