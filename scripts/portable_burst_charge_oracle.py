"""Native actual firing oracle; no post-restoration gauge reconstruction."""
import copy
from unittest.mock import patch
import engine_worker
from calculator import buff_manager as native
from portable_weapon_oracle import authored_weapon,authored_weapon_state
from timer_registry_cases import NAMES


def observe(case):
    who=case['burst_charge_context']['shooter']
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES]
    w=case['combat']['weapons'][who];authored_weapon(chars[who],w)
    effects=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case['owners'])]
    class BM(native.BuffManager):
        def _register_all(self):self._effects=effects;self._build_notify_index()
    metadata={}
    for name,ref in zip(NAMES,case['environment']['burst_references']):
        metadata[name]=dict(native._NIKKE[name],**ref)
        if 'burst_energy_raw' not in ref:metadata[name].pop('burst_energy_raw',None)
    with patch.dict(native._NIKKE,metadata):
        enemy=dict(core_px=0,code=None,**{'def':0})
        bm=BM(chars,state=dict(base_stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in NAMES},
            enemy=enemy,full_burst=False,rng_acc={},rng_expected=True,
            camera={NAMES[who]} if case['burst_charge_context']['camera'] else set(),
            burst_gauge=case['combat'].get('initial_gauge',0),burst_gauge_charging=True))
        st=authored_weapon_state(chars[who],w)
        for n in NAMES:bm.notify('battle_start',0,n)
        st.ammo=st._full_ammo(bm,0)
        frame=0;queries=[]
        for t,op,*rest in case['script']:
            if op==24:
                while frame/60<=t:
                    now=frame/60;bm.tick(now);st.tick(now,bm,enemy,{'rng_mode':'expected'});frame+=1
            elif op==2:queries.append(dict(combat=dict(gauge=bm.state['burst_gauge'])))
            else:raise ValueError('Burst charge oracle requires frame/query commands')
        return dict(queries=queries)
