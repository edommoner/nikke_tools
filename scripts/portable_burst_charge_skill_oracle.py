"""Original simulate/skill handler with literal synthetic metadata/effects.

Only gauge is projected. Native damage totals/base stats are not an oracle here;
complete real profiles are checked independently after GPU readback.
"""
import copy
from unittest.mock import patch
import engine_worker
from calculator import timeline,buff_manager
from timer_registry_cases import NAMES


def observe(case):
    owner=case['burst_charge_skill_context']['owner'];name=NAMES[owner]
    assert case['script']==[[0,24,0,0,0,-1,0,0],[0,2,0,0,-1,0,0,0]]
    assert all(o==owner for o in case['owners'])
    assert all(not w.get('enabled',False) for i,w in enumerate(case['combat']['weapons']) if i!=owner)
    w=case['combat']['weapons'][owner];ref=case['environment']['burst_references'][owner]
    metadata=dict(timeline._NIKKE[name],weapon_type='AR',is_charge=False,input_type='DOWN',
        burst_energy=w['gauge'],fire_rate=1,fire_rate_max=1,damage_coeff=100,max_ammo=100,burst_stage='0')
    caster_metadata=dict(buff_manager._NIKKE[name],**ref)
    if 'burst_energy_raw' not in ref:caster_metadata.pop('burst_energy_raw',None)
    def register(bm):
        bm._effects=[(copy.deepcopy(e),name) for e in case['effects']]
        bm._build_notify_index()
    with patch.dict(timeline._NIKKE,{name:metadata}),patch.dict(buff_manager._NIKKE,{name:caster_metadata}),patch.object(buff_manager.BuffManager,'_register_all',register):
        result=timeline.simulate([dict(name=name,skill_levels={'1':10,'2':10,'3':10})],
            config=dict(duration=0,rng_mode='expected',burst_gauge_mode='accumulate'),
            enemy=dict(core_px=0,code=None,**{'def':0}),verbose=True)
    gauge=result.log.gauge_log[-1].gauge if result.log.gauge_log else 0
    return dict(queries=[dict(combat=dict(gauge=gauge))])
