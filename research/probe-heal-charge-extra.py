"""Independent CPU positive witnesses for the additional lifecycle scenarios."""
import hashlib,importlib.util,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
d=load('charge_definitions','research/heal-charge-fixtures.py');extra=load('charge_extra','research/heal-charge-extra-fixtures.py');BM=d.v.BuffManager
original_take=BM.take_heal_charge;original_collect=BM.collect_heal_charge;rows=[]
for name,b,x in extra.fixtures(d):
    releases=[];deposits=[]
    def take(self,key,owner,t):
        amount=original_take(self,key,owner,t);releases.append(dict(time=t,key=key,owner=owner,amount=amount));return amount
    def collect(self,who,amount,t):
        result=original_collect(self,who,amount,t)
        for ab in self._by_stat('heal_overcharge_store_atk_pct'):
            if hasattr(ab,'heal_charge_current'):deposits.append(dict(time=t,key=ab.effect.get('name'),owner=ab.caster,current=ab.heal_charge_current,base_cap=ab.heal_charge_base_cap))
        return result
    try:
        with d.v.s.v.context(name,x),patch.object(BM,'take_heal_charge',take),patch.object(BM,'collect_heal_charge',collect):
            compiled=d.v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True});cpu=d.v.s.v.v.a.evaluate(b)
        checks=dict(compile=True,positive_charge=any(r['current']>0 for r in deposits))
        if name.endswith('same-name-two-owners'):checks['both_owners_release']=len({r['owner'] for r in releases if r['amount']>0})==2
        if name.endswith('expiry-recreate-before-release'):checks['recreation_does_not_lose_previous_quantity']=any(r['amount']>0 for r in releases)
        if name.endswith('cleanse-then-new-same-name'):checks['later_end_does_not_resurrect_old_quantity']=releases and all(r['amount']==0 for r in releases)
        if name.endswith('expired-boost-keeps-collected'):checks['above_base_quantity_survives_bonus_expiry']=any(r['time']>.42 and r['current']>r['base_cap'] for r in deposits)
        if name.endswith(('zero-cap-companion','negative-cap-companion')):checks['nonpositive_pool_never_collects']=all(r['current']==0 and r['base_cap']==0 for r in deposits if r['key']=='nonpositive companion')
        if name.endswith('release-inside-HP-edge'):checks['edge_release_occurs_before_expiry']=any(r['amount']>0 and r['time']<.6 for r in releases)
        if name.endswith('live-second-pool-receives-release'):checks['new_pool_collects_first_release']=any(r['key']=='secondary pool' and r['amount']>0 for r in releases)
        if name.endswith('other-caster-capacity-bonus'):checks['bonus_from_other_caster_applies']=any(r['current']>r['base_cap'] for r in deposits)
        rows.append(dict(name=name,passed=all(checks.values()),checks=checks,total=cpu['total_damage'],deposits=deposits,releases=releases))
    except Exception as e:rows.append(dict(name=name,passed=False,error=repr(e)))
    print(json.dumps({k:v for k,v in rows[-1].items() if k not in ('deposits','releases')},ensure_ascii=True),flush=True)
files=['research/probe-heal-charge-extra.py','research/heal-charge-extra-fixtures.py','research/heal-charge-fixtures.py','research/staging/v42/app/heal_charge_compat.py','research/staging/v42/app/detail_gpu.py','scripts/staged-heal-charge-runtime.py','app/engine_worker.py','app/engine_compat.py','app/heal_sharing_compat.py','app/healing_storage_compat.py']
r=dict(passed=all(r['passed'] for r in rows),stage_only=True,gpu_verified=False,objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-heal-charge-extra-cpu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
