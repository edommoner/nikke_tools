"""CPU-only study of caster-based burst-charge conversion; no GPU admission."""
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','tests')]
from test_target_counter_runtime import manager,NAMES
from calculator import buff_manager as native
from portable_weapon_oracle import authored_weapon,authored_weapon_state
import engine_worker
import copy


def main():
    rows=[]
    references=[dict(burst_energy=2.0,burst_energy_raw=.25),dict(burst_energy=4.0,burst_energy_raw=1.5),dict(burst_energy=2.0)]
    for owner in range(5):
        for reference in references:
            for pct in (-50,0,100):
                effect=dict(name='caster-charge',source='스킬1',type='buff',stat='burst_charge_speed_pct',
                    fixed_value=pct,target='all_allies',duration=-1,trigger=dict(timing=['battle_start'],condition=[]))
                metadata=dict(native._NIKKE[NAMES[owner]],**reference)
                if 'burst_energy_raw' not in reference:metadata.pop('burst_energy_raw',None)
                with patch.dict(native._NIKKE,{NAMES[owner]:metadata}):
                    bm=manager([effect],[owner]);bm.notify('battle_start',0,NAMES[owner])
                    observations=[]
                    raw=reference.get('burst_energy_raw',reference['burst_energy']/2)
                    for phase,expected in [('initial',raw*pct/100),('other-landed',raw*pct/100),
                                           ('caster-landed',reference['burst_energy']*pct/100),('gauge-reset',reference['burst_energy']*pct/100)]:
                        if phase=='other-landed':bm.mark_normal_attack_landed(NAMES[(owner+1)%5])
                        elif phase=='caster-landed':bm.mark_normal_attack_landed(NAMES[owner])
                        elif phase=='gauge-reset':bm.state['burst_gauge']=0
                        actual=[bm.get_buffs(n,'__enemy__',0)['burst_charge_speed_flat'] for n in NAMES]
                        assert actual==[expected]*5,(owner,reference,pct,phase,actual,expected)
                        observations.append(dict(phase=phase,expected_flat_per_hit=expected,actual=actual))
                rows.append(dict(owner=owner,reference=reference,pct=pct,observations=observations))
    gains=[]
    for coefficient in (.5,5):
        for flat in (-.25,0,.5):
            for hits in (1,10):
                for full in (False,True):
                    char=dict(name=NAMES[0],skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[NAMES[0]]))
                    w=dict(base_weapon_type='SR',gauge=coefficient,full_charge_mult=300,capacity=10)
                    authored_weapon(char,w);st=authored_weapon_state(char,w)
                    actual=st._burst_gain(dict(burst_charge_speed_flat=flat),hits,full_charge=full)
                    expected=coefficient*hits*(3 if full else 1)+hits*flat
                    assert actual==expected
                    gains.append(dict(weapon_energy=coefficient,flat=flat,hits=hits,full_charge=full,actual=actual,expected=expected))
    paths=['research/characterize-burst-charge-speed.py','tests/test_target_counter_runtime.py','scripts/portable_weapon_oracle.py',
        'research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
    report=dict(passed=True,cpu_only=True,gpu_execution_performed=False,gpu_admission_enabled_by_study=False,
        reference_cases=rows,gain_cases=gains,rules=[
            'Convert percentage using original caster CDN energy,not recipient or active weapon energy',
            'Before first caster normal hit use burst_energy_raw,falling back to burst_energy/2',
            'First caster normal hit switches to burst_energy for remainder of battle,including after gauge reset',
            'Flat per-hit addition is outside recipient full-charge multiplier'],
        scope='45 caster/reference/value cases,5 recipients,4 phases;24 direct native gain cases. No complete battle,fullburst-disabled gain,geometry or GPU certification.',
        source_review_note='Native physical hit marks normal landing before gauge buff lookup,including outside the charge window;skill-damage weapon modes do not mark it. Future GPU integration must verify this actual call order and read actual BuffManager gauge,not reconstruct it after weapon restoration.',
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    (ROOT/'research/portable-burst-charge-speed-native-study.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    assert len(rows)==45 and len(gains)==24
    print('CPU only:45 caster reference cases and24 gain cases passed;GPU admission unchanged')


if __name__=='__main__':main()
