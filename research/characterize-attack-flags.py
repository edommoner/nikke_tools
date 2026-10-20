"""Observe unported physical attack flags without changing GPU admission."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','tests')]
from test_target_counter_runtime import manager,NAMES
from portable_weapon_oracle import observe as physical


def effect(stat,value=None,*,duration=-1,conditions=None,timing='on_attack',target='self',name=None):
    row=dict(name=name or stat,source='스킬1',type='buff',stat=stat,duration=duration,target=target,
             trigger=dict(timing=[timing],condition=conditions or []))
    if value is not None:row['fixed_value']=value
    return row


def main():
    flags=('pierce_enabled','armor_break_enabled');presence=[];expiry=[];runtime=[]
    for owner in range(5):
        for stat in flags:
            for value in (None,0,-100,100):
                bm=manager([effect(stat,value)],[owner]);bm.notify('on_attack',0,NAMES[owner])
                actual=[bm.get_buffs(n,'__enemy__',0)[stat] for n in NAMES]
                assert actual==[i==owner for i in range(5)]
                presence.append(dict(owner=owner,stat=stat,literal_value=value,actual=actual))
            for t,expected in ((.999999,True),(1.,False),(1.000001,False)):
                bm=manager([effect(stat,0,duration=1)],[owner]);bm.notify('on_attack',0,NAMES[owner]);bm.tick(t)
                actual=bm.get_buffs(NAMES[owner],'__enemy__',t)[stat];assert actual==expected
                expiry.append(dict(owner=owner,stat=stat,time=t,actual=actual))
            for duration in (-1,2):
                marker=effect(None,duration=.5,timing='battle_start',name='state')
                bm=manager([marker,effect(stat,0,duration=duration,conditions=['self_state:state'])],[owner,owner])
                bm.notify('battle_start',0,NAMES[owner]);bm.notify('on_attack',.1,NAMES[owner])
                before=bm.get_buffs(NAMES[owner],'__enemy__',.1)[stat]
                bm.tick(.5);after=bm.get_buffs(NAMES[owner],'__enemy__',.5)[stat]
                assert before and after==(duration!=-1)
                runtime.append(dict(owner=owner,stat=stat,duration=duration,before=before,after=after))
    hits=[]
    for weapon,mode in [('AR','auto'),('SR','charge'),('RL','charge')]:
        for pierce,armor,expected in [(False,False,900),(True,False,1350),(False,True,1400),(True,True,1900)]:
            buffs=[effect('crit_rate',-15,timing='passive'),effect('pierce_dmg_pct',50,timing='passive'),effect('armor_break_dmg_pct',40,timing='passive')]
            if pierce:buffs.append(effect('pierce_enabled',0,timing='passive'))
            if armor:buffs.append(effect('armor_break_enabled',-100,timing='passive'))
            w=dict(enabled=True,base_weapon_type=weapon,mode=mode,coefficient=100,capacity=100,
                   interval=1,charge=.5,full_charge_mult=100,reload=1,gauge=0)
            case=dict(effects=buffs,owners=[0]*len(buffs),combat=dict(weapons=[w]+[dict(enabled=False) for _ in range(4)],
                      targets=[dict(hp=1000000,defense=100)]),script=[[1.5,24,0,0,0,-1,0,0],[1.5,2,0,0,0,0,0,0]])
            queries,weapon_state=physical(case);q=queries[-1];shots=q['combat']['weapons'][0]['shots'];assert shots>0
            assert q['damage'][0]==shots*expected,(weapon,pierce,armor,q)
            hits.append(dict(weapon=weapon,mode=mode,pierce=pierce,armor=armor,shots=shots,damage=q['damage'][0],
                             expected_damage_per_shot=expected,native=queries,weapon_state=weapon_state))
    paths=['research/characterize-attack-flags.py','tests/test_target_counter_runtime.py','scripts/portable_weapon_oracle.py',
           'research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py',
           'research/upstream/nikke-calc-master/calculator/damage.py']
    report=dict(passed=True,cpu_only=True,gpu_execution_performed=False,gpu_admission_enabled=False,
        presence=presence,expiry=expiry,runtime_conditions=runtime,physical_cases=hits,
        physical_crit_rate_reduction_pct=-15,physical_expected_crit_rate=0,
        rules=['Boolean buffs are presence markers:missing,zero and negative values still enable them',
               'Finite/infinite conditions follow native query/expiry rules',
               'Physical AR/SR/RL attacks receive pierce/armor classification and their distinct damage bonuses;crit_rate-15 removes the native15percent baseline',
               'Armor flag removes defense before attack-minus-defense;both damage bonuses add in the same layer'],
        source_review_note='Pinned timeline physical attacks read boolean buffs;skill handler5015/5016 sets flags from damage family. Do not apply physical flags to every normal-type skill. Skill routing is source review here,not a full native-handler execution proof.',
        scope='40 presence+30 expiry+20 runtime gates and12 simple-boss physical cases;no coordinate piercing/parts/add geometry certification',
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    (ROOT/'research/portable-attack-flags-native.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Native flags40 presence,30 expiry,20 runtime and12 physical cases verified;GPU admission remains disabled')


if __name__=='__main__':main()
