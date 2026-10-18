"""CPU-only charge/discharge witnesses; actual skills are retained in full."""
import hashlib,importlib.util,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('charge_definitions',ROOT/'research/heal-charge-fixtures.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
BM=d.v.BuffManager;original_collect=BM.collect_heal_charge;original_take=BM.take_heal_charge;original_notify=BM.notify;original_plan=BM.heal_share_plan;original_fill=BM.fill_heal_storage;rows=[]
def main():
    for name,b,x in [*d.fixtures(),*d.real_fixtures()]:
        deposits=[];releases=[];notifications=[];split_heals=[];filled=[]
        def plan(self,who,t):
            result=original_plan(self,who,t)
            if len(result)>1:split_heals.append(dict(time=t,original=who,weights=result))
            return result
        def fill(self,who,amount,t):
            result=original_fill(self,who,amount,t)
            if result>0:filled.append(dict(time=t,recipient=who,filled=result))
            return result
        def collect(self,who,amount,t):
            before=sum(getattr(a,'heal_charge_current',0) for a in self._active);result=original_collect(self,who,amount,t);after=sum(getattr(a,'heal_charge_current',0) for a in self._active)
            if after>before:deposits.append(dict(time=t,recipient=who,amount=amount,added=after-before))
            return result
        def take(self,target,caster,t):
            result=original_take(self,target,caster,t);releases.append(dict(time=t,name=target,caster=caster,amount=result));return result
        def notify(self,event,t,caster,*args,**kwargs):
            if event=='event:heal_received':notifications.append(dict(time=t,recipient=caster,source=kwargs.get('heal_source')))
            return original_notify(self,event,t,caster,*args,**kwargs)
        try:
            with d.v.s.v.context(name,x),patch.object(BM,'collect_heal_charge',collect),patch.object(BM,'take_heal_charge',take),patch.object(BM,'notify',notify),patch.object(BM,'heal_share_plan',plan),patch.object(BM,'fill_heal_storage',fill):
                compiled=d.v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True});cpu=d.v.s.v.v.a.evaluate(b)
            empty=name in ('charge-empty','raw-charge-taunter-negative');no_release=empty or name in ('charge-cleanse-no-release','charge-down-source')
            checks=dict(compile=True,deposit_positive_control=bool(deposits)!=empty,release_positive_control=any(r['amount']>0 for r in releases)!=no_release)
            if name=='raw-charge-healer':checks['Crown_receives_real_Delta_release']=any(n['recipient']=='크라운' and n['source']=='델타 : 닌자 시프' for n in notifications)
            if name in ('charge-shared-heal','raw-charge-Rem-sharing'):checks['nontrivial_healing_share_really_active']=bool(split_heals)
            if name in ('charge-storage','raw-charge-Marciana-storage'):checks['overheal_reserve_really_filled']=bool(filled)
            if name.startswith('raw-'):checks['all_three_raw_charge_families_retained']=all(any(q[1]==kind and q[2]==stat for q in compiled['program']['effects']) for kind,stat in [(0,76),(0,77),(32,0)])
            rows.append(dict(name=name,passed=all(checks.values()),checks=checks,total=cpu['total_damage'],deposits=deposits,releases=releases,notifications=notifications,nontrivial_share_events=len(split_heals),overheal_fill_events=len(filled),raw_skills_retained=name.startswith('raw-')))
        except Exception as e:rows.append(dict(name=name,passed=False,error=repr(e)))
        print(json.dumps({k:v for k,v in rows[-1].items() if k not in ('deposits','releases','notifications')},ensure_ascii=True),flush=True)
    files=['research/probe-heal-charge-squads.py','research/heal-charge-fixtures.py','scripts/staged-heal-charge-runtime.py','research/staging/v42/app/heal_charge_compat.py','app/engine_compat.py','app/heal_sharing_compat.py','app/healing_storage_compat.py','app/outgoing_healing_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']
    files+= ['research/staging/v42/app/detail_gpu.py']+[p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('*.py')]
    r=dict(passed=all(x['passed'] for x in rows),stage_only=True,gpu_verified=False,whole_squad_CPU_only=True,cpu_model_extended=True,in_game_rules_verified=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
    (ROOT/'research/detail-heal-charge-cpu-squads.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
if __name__=='__main__':main()
