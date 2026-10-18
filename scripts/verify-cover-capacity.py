"""Whole-squad v37 parity for caster-maximum-HP cover capacity."""
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
import sys
sys.path.insert(0,str(ROOT/'app'))
import engine_worker
import detail_gpu as g
v=load('capacity_independent_oracle','scripts/verify-survival-scaling.py');N=v.N;B=v.B;E=v.E;BuffManager=v.BuffManager

def fixtures():
    variants=['caster-not-recipient','caster-max-increases','caster-max-expires','base-pct-plus-flat','stacked-capacity','lost-HP-source-maximum','broken-cover-no-revive','revive-after-capacity-change','cover-runtime-gate','source-down','source-revives','ordered-duplicates','lazy-recipients','plain-bullet-stacks','flat-bullet-stacks']
    for case in variants:
        b=v.body(2);extra={n:[] for n in N};kw={};target=N[1]
        if case=='ordered-duplicates':target=[N[1],'all_allies',N[1]]
        if case=='lazy-recipients':target='allies_lowest_hp:2'
        if case=='stacked-capacity':kw.update(event='every:0.1s',max_stack=3,duration=.25)
        if case.endswith('bullet-stacks'):kw.update(event='every:0.1s',max_stack=3,duration_bullets=2);target='all_allies'
        e=B('caster cover capacity','cover_hp_pct',20,target,**kw)
        if case!='plain-bullet-stacks':e['scaling']='max_hp'
        if case=='cover-runtime-gate':e['trigger']['condition']=['self_cover_alive'];e['trigger']['timing']=['passive']
        extra[N[0]].append(e)
        if case=='caster-max-increases':extra[N[0]].append(B('later maximum','max_hp_pct',50,event='every:0.2s',max_trigger=1))
        if case=='caster-max-expires':extra[N[0]].append(B('temporary maximum','max_hp_pct',50,duration=.4))
        if case=='base-pct-plus-flat':extra[N[2]].append(B('ordinary cover pct','cover_hp_pct',50,'all_allies'))
        if case=='lost-HP-source-maximum':
            extra[N[0]]+=[B('HP-dependent maximum','max_hp_only_pct',1.5,scaling='lost_hp_pct'),E('source health loss','instant','current_hp_reduce',50,event='every:0.2s',max_trigger=1)]
        if case in ('broken-cover-no-revive','revive-after-capacity-change','cover-runtime-gate'):
            extra[N[0]].append(E('take cover','instant','force_reload',0,'all_allies'))
            b['enemy']['patterns']=[dict(id='break cover',kind='attack',delay=.1,until={'time':1},spec=dict(coeff=100,atk=6000000,target='all',hits=1,interval=.5))]
            if case!='broken-cover-no-revive':extra[N[2]].append(E('restore broken cover','instant','cover_revive',50,'all_allies',event='every:0.4s',max_trigger=1))
            if case=='revive-after-capacity-change':extra[N[0]].append(B('larger source','max_hp_pct',100,event='every:0.3s',max_trigger=1))
        if case in ('source-down','source-revives'):
            b['enemy']['patterns']=[v.s.lethal('slot:1',at=.2)]
            if case=='source-revives':extra[N[2]].append(E('bring source back','instant','revive',50,'allies_down_top_atk_excl:1',event='event:ally_down',max_trigger=1))
        yield 'capacity-'+case,b,extra

def real_fixtures():
    for case in ('no-shots','incoming','accumulate','owned-cover-cube','reordered','revival'):
        names=['티아',N[0],N[1],N[3],N[2]]
        if case=='revival':names=['라푼젤',N[0],N[1],'티아',N[3]]
        b=v.body(30,True,names);extra={n:[] for n in names}
        b['burst_gauge_mode']='accumulate' if case=='accumulate' else 'fixed'
        if case in ('incoming','accumulate','owned-cover-cube','reordered'):
            b['enemy']['patterns']=[dict(id='survivable cover damage',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=300000,target='all',hits=6,interval=4))]
        if case=='owned-cover-cube':
            c=b['profile']['chars']['티아'];c.update(core_enhancement=2,breakthrough=3,affinity=20,skill_levels={'1':7,'2':5,'3':9},collection_stage='SR15',cube={'name':'렐릭 커버 큐브','level':4})
            c['equip_skills'].update(atk_pct=[11.11,11.11,12.34],charge_speed_pct=[2.34,2.34,4.3]);b['stat_deltas']={'티아':{'atk':12000,'hp':100000,'def':250}}
        if case=='reordered':b['squad']=list(reversed(b['squad']))
        if case=='revival':b['enemy']['patterns']=[v.s.lethal('slot:4',at=2.8)]
        yield 'raw-Tia-capacity-'+case,b,extra

def compare(device,name,b,extra,backend):
    changes=[];original=BuffManager.sync_cover_hp
    def sync(self,who,t):
        before=(self.state['cover_hp'][who],self.state['cover_max_hp'][who]);out=original(self,who,t)
        after=(self.state['cover_hp'][who],self.state['cover_max_hp'][who])
        if before!=after:changes.append(dict(time=t,character=who,before=before,after=after,base=self.state['cover_base_hp'][who]))
        return out
    with patch.object(BuffManager,'sync_cover_hp',sync):r=v.compare(device,name,b,extra,backend)
    r['checks']['capacity_change_exercised']=any(c['after'][1]!=c['base'] for c in changes)
    if name=='capacity-caster-max-expires':r['checks']['capacity_expiry_exercised']=any(c['after'][1]<c['before'][1] for c in changes)
    if name=='capacity-broken-cover-no-revive':r['checks']['broken_capacity_stays_broken']=all(c['after'][0]==0 for c in changes if c['before'][0]==0)
    r.update(cpu_capacity_changes=changes,passed=all(r['checks'].values()))
    print(json.dumps(dict(name=name,passed=r['passed'],failed=[k for k,ok in r['checks'].items() if not ok],capacity_changes=len(changes))),flush=True);return r

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--real',action='store_true');ap.add_argument('--output',required=True);ap.add_argument('--fail-fast',action='store_true');args=ap.parse_args()
    files=['scripts/verify-cover-capacity.py','scripts/verify-survival-scaling.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','app/detail_world.py','app/detail_boss.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']+['app/'+n for n in (['detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json'] if args.backend=='ptx' else ['detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'])]
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};planned=list(real_fixtures() if args.real else fixtures());rows=[];device=v.s.v.v.v.Cuda()
    try:
        for name,b,extra in planned:
            try:r=compare(device,name,b,extra,args.backend)
            except Exception as exc:r=dict(name=name,passed=False,error=repr(exc));print(json.dumps(r),flush=True)
            rows.append(r)
            if args.fail_fast and not r['passed']:break
    finally:device.close()
    assert hashes=={p:sha(p) for p in files}
    r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(x['passed'] for x in rows),stage_only=False,objective_complete=False,abi=g.DETAIL_ABI,backend=args.backend,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
    (ROOT/args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
