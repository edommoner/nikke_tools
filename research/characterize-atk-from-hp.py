"""Next-family CPU study only; no GPU admission for atk_from_hp_pct."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from timer_registry_cases import NAMES


def main():
    rows=[]
    base_hp=[10000+2000*i for i in range(5)]
    for owner in range(5):
        for target in ('self','all_allies'):
            for pct in (-5,0,12.5):
                for duration in (-1,2):
                    effects=[dict(name='hp-to-attack',source='스킬1',type='buff',stat='atk_from_hp_pct',fixed_value=pct,
                        target=target,duration=duration,trigger=dict(timing=['battle_start'],condition=[])),
                        dict(name='temporary-hp',source='스킬1',type='buff',stat='max_hp_pct',fixed_value=50,
                        target='all_allies',duration=.5,trigger=dict(timing=['on_attack'],condition=[]))]
                    class BM(BuffManager):
                        def _register_all(self):
                            self._effects=[(copy.deepcopy(e),NAMES[owner]) for e in effects];self._build_notify_index()
                    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
                    bm=BM(chars,state=dict(base_stats={n:dict(atk=1000,hp=hp,**{'def':100}) for n,hp in zip(NAMES,base_hp)},
                        hp=dict(zip(NAMES,base_hp)),hp_pct={n:100 for n in NAMES},enemy={'def':0,'core_px':0},full_burst=False,rng_acc={}))
                    bm.notify('battle_start',0,NAMES[owner]);observed=[]
                    for phase,t,multiplier in [('initial',0,1),('max-hp-up',.2,1.5),('low-current-hp',.3,1.5),('hp-expired',.7,1)]:
                        if phase=='max-hp-up':bm.notify('on_attack',t,NAMES[owner])
                        elif phase=='low-current-hp':
                            for n in NAMES:bm.state['hp'][n]=1;bm.sync_hp(n)
                        bm.tick(t)
                        expected=[hp*multiplier*(pct/100) if target=='all_allies' or i==owner else 0 for i,hp in enumerate(base_hp)]
                        actual=[bm.get_buffs(n,'__enemy__',t).get('atk_flat',0) for n in NAMES]
                        assert actual==expected,(owner,target,pct,duration,phase,actual,expected)
                        observed.append(dict(phase=phase,expected_flat=expected,actual_flat=actual))
                    rows.append(dict(owner=owner,target=target,pct=pct,duration=duration,observations=observed))
    paths=['research/characterize-atk-from-hp.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','app/detail_gpu.py']
    report=dict(passed=True,cpu_only=True,cases=rows,gpu_admission_enabled=False,gpu_execution_performed=False,
        rules=['Use recipient final maximum HP,not caster HP or current HP','Re-evaluate when maximum HP changes,including finite grant duration','Native multiplication is final_hp*(value/100),with division first','Native adds HP-derived attack after ordinary scalar buff accumulation'],
        layout_note='Legacy compiler uses kind4 with HP flag241 for this family;portable kind4 is a burst-stage override. Do not admit it by only adding a buff/stat name.',
        scope='60 BuffManager cases with5 recipients and4 phases;no damage,battle,GPU or catalog certification',
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    (ROOT/'research/portable-atk-from-hp-native-study.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(len(rows),'native HP-derived attack cases passed;GPU admission unchanged')


if __name__=='__main__':main()
