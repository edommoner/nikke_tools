"""CPU squad witnesses for link activation, shares and notification separation."""
import hashlib,importlib.util,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('sharing_definitions',ROOT/'research/heal-sharing-fixtures.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
BM=d.v.BuffManager;rows=[]
original_heal=BM.apply_shared_body_heal;original_plan=BM.heal_share_plan;original_notify=BM.notify
def main():
    for name,b,x in [*d.fixtures(),*d.real_fixtures()]:
        plans=[];heals=[];notifications=[]
        def plan(self,who,t):
            result=original_plan(self,who,t);plans.append(dict(time=t,original=who,weights=result,live_carriers=[dict(caster=a.caster,name=a.effect.get('name')) for a in self._by_stat('heal_split') if any(not self.is_down(n) and self._live(a,n,t) for n in self.squad_names)]));return result
        def heal(self,who,amount,t):
            result=original_heal(self,who,amount,t);heals.append(dict(time=t,original=who,amount=amount));return result
        def notify(self,event,t,caster,*args,**kwargs):
            if event=='event:heal_received':notifications.append(dict(time=t,original=caster,source=kwargs.get('heal_source')))
            return original_notify(self,event,t,caster,*args,**kwargs)
        try:
            with d.v.s.v.context(name,x),patch.object(BM,'heal_share_plan',plan),patch.object(BM,'apply_shared_body_heal',heal),patch.object(BM,'notify',notify):
                compiled=d.v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True});cpu=d.v.s.v.v.a.evaluate(b)
            expected_shared=name not in ('sharing-no-links','sharing-single','sharing-expired')
            shared=any(len(p['weights'])>1 for p in plans)
            checks=dict(compile=True,notifications_once_per_original_heal=len(heals)==len(notifications),shared_positive_control=shared==expected_shared)
            if name=='sharing-notification-original-only':checks['no_notification_on_shared_recipient']=all(n['original']==b['squad'][0] for n in notifications)
            if name=='raw-sharing-Crown':checks['shared_Crown_is_not_notified_by_Rem']=not any(n['original']=='크라운' and n['source']=='렘' for n in notifications)
            if name=='sharing-nested-HP-heal':checks['nested_heal_really_executed']=any(h['original']==b['squad'][1] for h in heals)
            if name=='raw-sharing-Nayuta':checks['raw_Nayuta_links_really_active']=any(any(c['caster']=='나유타' for c in p['live_carriers']) for p in plans)
            if name=='raw-sharing-zero-RL':checks['actual_Rem_6_links']=any(sum(w for n,w in p['weights'])==6 for p in plans)
            if name=='raw-sharing-two-RL':checks['actual_Rem_8_links']=any(sum(w for n,w in p['weights'])==8 for p in plans)
            rows.append(dict(name=name,passed=all(checks.values()),checks=checks,total=cpu['total_damage'],share_rows=sum(q[1]==0 and q[2]==75 for q in compiled['program']['effects']),plans=plans,heals=heals,notifications=notifications,raw_skills_retained=name.startswith('raw-')))
        except Exception as e:rows.append(dict(name=name,passed=False,error=repr(e)))
        print(json.dumps({k:y for k,y in rows[-1].items() if k not in ('plans','heals','notifications')},ensure_ascii=True),flush=True)
    files=['research/probe-heal-sharing-squads.py','research/heal-sharing-fixtures.py','research/staging/v41/app/heal_sharing_compat.py','research/staging/v41/app/detail_gpu.py','scripts/staged-heal-sharing-runtime.py','app/healing_storage_compat.py','app/outgoing_healing_compat.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']
    report=dict(passed=all(r['passed'] for r in rows),stage_only=True,gpu_verified=False,cpu_model_extended=True,in_game_rules_verified=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
    (ROOT/'research/detail-heal-sharing-cpu-squads.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
