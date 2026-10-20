"""Original simulate() and its original skill handler, with authored data only.

No damage handler or firing method is replaced. Raw metadata/effect registration
are fixture inputs. Gauge observations do not become GPU inputs.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from calculator import timeline,buff_manager
from timer_registry_cases import NAMES


def fixtures(owner,scenario):
    def effect(name,kind,stat,value,target,timing,**kw):
        return dict(name=name,source='스킬1',type=kind,stat=stat,fixed_value=value,
            target=target,trigger=dict(timing=[timing],condition=[]),**kw)
    buff=effect('speed','buff','burst_charge_speed_pct',100,'self',
        'hit_count:packet:1' if scenario=='named-activation' else 'battle_start',duration=-1)
    damage=effect('packet','damage','damage:3',100,'boss',
        'on_attack' if scenario.startswith('mode-') or scenario=='base-enter-mode' else 'battle_start')
    rows=[buff,damage]
    if scenario=='named-removal':
        rows.append(effect('remove','instant','remove_named_buff',0,'self','hit_count:packet:1',target_effect='speed'))
    if scenario.startswith('mode-') or scenario=='base-enter-mode':
        rows.insert(0,dict(name='mode',source='스킬1',type='weapon_change',weapon_type='AR',
            damage_coeff={'10':100},max_ammo=-1,fire_rate=1,charge=False,pellets=1,muzzles=1,
            post_fire_delay=0,burst_energy=5,core_dmg_mult=200,target='self',duration=.5,
            trigger=dict(timing=['battle_start'],condition=[])))
        if scenario=='mode-remove':
            rows.insert(2,effect('remove-mode','instant','remove_named_buff',0,'self','on_attack',target_effect='mode'))
        elif scenario=='mode-limit':
            rows[0].pop('duration');rows[0]['duration_bullets']=1
            damage['trigger']['timing']=['event:state_end:mode']
        elif scenario=='mode-switch':
            changed=copy.deepcopy(rows[0]);changed.update(name='next-mode',burst_energy=7)
            changed['trigger']['timing']=['on_attack'];rows.insert(2,changed)
        elif scenario=='base-enter-mode':rows[0]['trigger']['timing']=['on_attack']
    return rows


def main():
    rows=[]
    for owner,name in enumerate(NAMES):
        metadata=dict(timeline._NIKKE[name],weapon_type='AR',is_charge=False,input_type='DOWN',
            burst_energy=2,burst_energy_raw=.25,fire_rate=1,fire_rate_max=1,
            damage_coeff=100,max_ammo=100,burst_stage='0')
        for scenario,expected in [('initial',6.75),('named-activation',6),('named-removal',6.75),('mode-skill',21),
                                  ('mode-remove',21),('mode-limit',12),('mode-switch',21),('base-enter-mode',12)]:
            effects=fixtures(owner,scenario)
            def register(bm):
                bm._effects=[(copy.deepcopy(e),name) for e in effects]
                bm._build_notify_index()
            with patch.dict(timeline._NIKKE,{name:metadata}),patch.dict(buff_manager._NIKKE,{name:metadata}),patch.object(buff_manager.BuffManager,'_register_all',register):
                result=timeline.simulate([dict(name=name,skill_levels={'1':10,'2':10,'3':10})],
                    config=dict(duration=0,rng_mode='expected',burst_gauge_mode='accumulate'),
                    enemy=dict(core_px=0,code=None,**{'def':0}),verbose=True)
            log=[vars(e) for e in result.log.gauge_log]
            skill=[e for e in log if e['source']=='skill:packet']
            assert len(skill)==1 and skill[0]['amount']==expected,(name,scenario,expected,log)
            rows.append(dict(owner=owner,scenario=scenario,expected_skill_gain=expected,actual_skill_gain=skill[0]['amount'],gauge_log=log))
    paths=['research/characterize-burst-charge-skills.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
    report=dict(passed=True,cpu_only=True,cases=rows,
        scope='40 original simulate/skill-handler cases, duration0, authored metadata/effects. Not GPU certification or a complete battle.',
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    (ROOT/'research/portable-burst-charge-skills-native.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(len(rows),'original native skill-handler cases passed')


if __name__=='__main__':main()
