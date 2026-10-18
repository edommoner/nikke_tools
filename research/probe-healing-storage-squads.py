"""Actual CPU simulations exercise the new buffer, never a GPU parity claim."""
import hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
g=load('storage_runtime','scripts/staged-healing-storage-runtime.py').install()
v=load('storage_cpu_squad_oracle','scripts/verify-survival-scaling.py');N=v.N;B=v.B;E=v.E;BM=v.BuffManager
rows=[];fill=BM.fill_heal_storage;absorb=BM.absorb_heal_storage
# body_heal uses the bridge's pure fill function; observe committed snapshots
# at snapshot/query exits without additional stat queries or RNG calls.
original_heal=BM.apply_storage_body_heal;original_notify=BM.notify
def fixtures():
    for case in ('empty','overflow','damage','drain','expiry','stacked','refresh','shield-before-storage'):
        b=v.body(1.2);x={n:[] for n in N};kw={}
        if case=='expiry':kw['duration']=.35
        if case=='stacked':kw.update(event='every:0.1s',max_stack=3)
        if case=='refresh':kw.update(event='every:0.4s')
        x[N[0]].append(B('stored recovery','heal_overcharge_store',5,**kw))
        if case!='empty':x[N[1]].append(E('heal body','instant','heal_hp_pct',20,N[0],event='every:0.3s' if case=='refresh' else 'every:0.2s',max_trigger=3 if case=='refresh' else 1))
        if case in ('damage','shield-before-storage'):b['enemy']['patterns']=[dict(id='storage hit',kind='attack',delay=.3,until={'time':.7},spec=dict(coeff=100,atk=100000,target='slot:1',hits=2,interval=.2,pierce=False))]
        if case=='shield-before-storage':x[N[0]].append(B('outer shield','shield_from_max_hp_pct',20))
        if case=='drain':x[N[0]].append(E('body drain','instant','current_hp_reduce',2,event='every:0.3s',max_trigger=1))
        yield 'storage-'+case,b,x
    for subject,favorite in [('앵커 : 이노센트 메이드',0),('센티',0),('센티',3),('소라',0),('마르차나',0)]:
        names=[subject,'라푼젤' if subject=='센티' else '프리카','리타','앨리스','모더니아'];b=v.body(30,True,names);b['burst_gauge_mode']='accumulate'
        b['enemy']['patterns']=[dict(id='small incoming',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=60000,target='all',hits=50,interval=.5,pierce=True))]
        if favorite:b['profile']['chars'][subject].update(favorite_stage=favorite,collection_stage='SR15')
        x={}
        if subject=='소라':
            b['enemy']['parts']=[dict(name='storage-trigger-part'+str(i),hp=5,reach=(i%5)+1) for i in range(6)]
            x={'리타':[E('authored part-destruction stimulus','damage','damage',100,'all_enemies',event='every:0.5s',max_trigger=1,hits_parts=True)]}
        yield 'raw-storage-'+subject+('-favorite3' if favorite else ''),b,x
def main():
    for name,b,x in fixtures():
        heals=[];spends=[];subject_cast=[0]
        def observe_notify(self,event,t,caster,*args,**kwargs):
            subject=event=='burst_cast' and caster==b['squad'][0]
            if subject:subject_cast[0]+=1
            try:return original_notify(self,event,t,caster,*args,**kwargs)
            finally:
                if subject:subject_cast[0]-=1
        def observe_heal(self,who,amount,t):
            result=original_heal(self,who,amount,t);heals.append(dict(time=t,recipient=who,amount=amount,reserve=sum(getattr(a,'heal_store_current',{}).get(who,0) for a in self._active),during_subject_burst=bool(subject_cast[0])));return result
        def observe_absorb(self,who,amount,t):
            result=absorb(self,who,amount,t);spends.append(dict(time=t,recipient=who,amount=amount,used=amount-result));return result
        try:
            with v.s.v.context(name,x),patch.object(BM,'apply_storage_body_heal',observe_heal),patch.object(BM,'absorb_heal_storage',observe_absorb),patch.object(BM,'notify',observe_notify):
                compiled=v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True});cpu=v.s.v.v.a.evaluate(b)
            positive=any(h['reserve']>0 for h in heals);used=any(h['used']>0 for h in spends)
            expected_empty=name in ('storage-empty','raw-storage-센티')
            checks=dict(compile=True,positive_buffer=not positive if expected_empty else positive)
            storage_rows=sum(q[1]==0 and q[2]==74 for q in compiled['program']['effects'])
            if name.startswith('raw-storage-센티'):checks['favorite_gates_storage_definition']=bool(storage_rows)==name.endswith('-favorite3')
            if name=='raw-storage-마르차나':
                checks['same_cast_S2_heal_fills_storage']=any(h['during_subject_burst'] and h['reserve']>0 for h in heals)
                store=[i for i,q in enumerate(compiled['program']['effects']) if q[0]==0 and q[1]==0 and q[2]==74];healing=[i for i,q in enumerate(compiled['program']['effects']) if q[0]==0 and q[1]==6]
                checks['GPU_definitions_put_storage_before_S2_heal']=bool(store and healing and min(store)<min(healing))
            if name=='storage-damage':checks['damage_spends_reserve']=used
            if name=='storage-drain':checks['drain_preserves_body_before_reserve_exhaustion']=used
            if name=='storage-shield-before-storage':checks['shield_blocks_before_reserve']=not used
            rows.append(dict(name=name,passed=all(checks.values()),checks=checks,total=cpu['total_damage'],heals=heals,spends=spends,raw_skills_retained=name.startswith('raw-'),authored_part_stimulus='소라' in name,effect_rows=len(compiled['program']['effects']),storage_rows=storage_rows))
        except Exception as e:rows.append(dict(name=name,passed=False,error=repr(e)))
        print(json.dumps({k:y for k,y in rows[-1].items() if k not in ('heals','spends')},ensure_ascii=True),flush=True)
    files=['research/probe-healing-storage-squads.py','scripts/staged-healing-storage-runtime.py','research/staging/v40/app/healing_storage_compat.py','research/staging/v40/app/detail_gpu.py','app/engine_worker.py','app/engine_compat.py','app/outgoing_healing_compat.py','scripts/verify-survival-scaling.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
    r=dict(passed=all(x['passed'] for x in rows),gpu_verified=False,objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
    (ROOT/'research/detail-healing-storage-cpu-squads.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)

if __name__=='__main__':main()
