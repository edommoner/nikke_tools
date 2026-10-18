"""v39 body-healing source/recipient and complete squad oracle verification."""
import argparse,copy,hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
sys.path.insert(0,str(ROOT/'app'))
import engine_worker
import detail_gpu as g
v=load('outgoing_survival_oracle','scripts/verify-survival-scaling.py');N=v.N;B=v.B;E=v.E;BuffManager=v.BuffManager

def fixtures():
    cases=['source-only','recipient-is-not-source','separate-layers','additive-sources','negative-source','negative-recipient','stacked-source','periodic','caster-max','duplicates','expired','lazy-target','conditional','lifesteal','lifesteal-negative','cover-unaffected','shield-unaffected','decoy-unaffected','registered-timer-source-down']
    for case in cases:
        b=v.body(1.2);extra={n:[] for n in N};source=N[1];recipient=N[0]
        extra[N[4]].append(B('room for body healing','max_hp_only_pct',100,'all_allies'))
        outgoing=B('source outgoing bonus','outgoing_heal_pct',50)
        if case=='recipient-is-not-source':outgoing['target']=recipient
        if case in ('negative-source','lifesteal-negative'):outgoing['fixed_value']=-150;outgoing.pop('values',None)
        if case=='additive-sources':extra[source].append(B('second source bonus','outgoing_heal_pct',25))
        if case=='stacked-source':outgoing.update(max_stack=3);outgoing['trigger']['timing']=['every:0.05s']
        if case=='expired':outgoing['duration']=.1
        if case=='lazy-target':outgoing['target']='allies_lowest_hp:2'
        if case=='conditional':outgoing['trigger']['condition']=['self_hp_below:80'];outgoing['trigger']['timing']=['passive']
        extra[source].append(outgoing)
        if case in ('separate-layers','negative-recipient'):extra[recipient].append(B('recipient incoming bonus','heal_received_pct',-150 if case=='negative-recipient' else 25))
        kw=dict(event='every:0.3s',max_trigger=1)
        if case=='periodic':kw=dict(tick_interval=.2,duration=1)
        if case=='caster-max':kw['scaling']='max_hp'
        target=[recipient,'all_allies',recipient] if case=='duplicates' else recipient
        if case.startswith('lifesteal'):
            extra[source].append(B('attack lifesteal','lifesteal_pct',1))
        elif case.endswith('-unaffected'):
            stat=case.split('-')[0];heal_stat=stat+'_heal_pct'
            if stat!='cover':extra[recipient].append(B('repair carrier','decoy' if stat=='decoy' else 'shield_from_max_hp_pct',10))
            extra[source].append(E('repair','instant',heal_stat,5,recipient,**kw))
        else:extra[source].append(E('body healing','instant','heal_hp_pct',2,target,**kw))
        if case=='registered-timer-source-down':
            extra[source][-1]=E('body healing timer','instant','heal_hp_pct',2,recipient,tick_interval=.3,duration=1)
            b['enemy']['patterns']=[v.s.lethal('slot:2',at=.15)]
        yield 'outgoing-'+case,b,extra

def real_fixtures(include_unsupported=False):
    for character in (('프리카','소라','백학','미사토') if include_unsupported else ('프리카','백학')):
        for case in ('incoming','owned-healing-cube'):
            names=[character,N[0],N[1],N[2],N[3]]
            # Each actual B1/B2 healer uses the other required burst-stage slot.
            names=list(dict.fromkeys(names));assert len(names)==5
            b=v.body(30,True,names);b['burst_gauge_mode']='accumulate'
            b['enemy']['patterns']=[dict(id='actual healing damage',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=100000,target='all',hits=50,interval=.5,pierce=True))]
            if case=='owned-healing-cube':
                p=b['profile']['chars'][character];p.update(skill_levels={'1':7,'2':5,'3':9},core_enhancement=2,breakthrough=3,affinity=20,collection_stage='SR15',cube={'name':'렐릭 힐링 큐브','level':4})
                b['stat_deltas']={character:{'atk':12000,'hp':100000,'def':250}}
            yield 'raw-outgoing-'+character+'-'+case,b,{}

def compare(device,name,b,extra,backend):
    calls=[];original=BuffManager.heal_received_mult
    def multiplier(self,who,t,**kwargs):
        result=original(self,who,t,**kwargs)
        calls.append(dict(recipient=who,source=kwargs.get('heal_source'),time=t,multiplier=result));return result
    with patch.object(BuffManager,'heal_received_mult',multiplier):row=v.compare(device,name,b,extra,backend)
    no_body=name.endswith(('-cover-unaffected','-shield-unaffected','-decoy-unaffected'))
    expected_zero=name.endswith(('-negative-source','-negative-recipient','-lifesteal-negative'))
    if no_body:row['checks']['repair_does_not_query_body_multiplier']=not calls
    elif not name.startswith('raw-'):
        row['checks']['body_healing_exercised']=bool(calls)
        if expected_zero:row['checks']['negative_bonus_clamps']=bool(calls) and all(x['multiplier']==0 for x in calls)
        if name.endswith(('source-only','separate-layers','additive-sources','stacked-source','periodic','caster-max','duplicates','conditional','lifesteal')):row['checks']['source_bonus_exercised']=any(x['multiplier']>1 for x in calls)
        if name.endswith(('recipient-is-not-source','expired')):row['checks']['bonus_absent_at_source_query']=bool(calls) and all(x['multiplier']==1 for x in calls)
    row.update(passed=all(row['checks'].values()),cpu_healing_queries=calls,cpu_model_extended=True)
    print(json.dumps(dict(name=name,passed=row['passed'],failed=[k for k,x in row['checks'].items() if not x],healing_queries=len(calls))),flush=True)
    return row

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--real',action='store_true');ap.add_argument('--fail-fast',action='store_true');ap.add_argument('--output',required=True);args=ap.parse_args()
    files=['scripts/verify-outgoing-healing.py','scripts/verify-survival-scaling.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','app/detail_world.py','app/detail_boss.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json','research/upstream/nikke-calc-master/runner/spec.py','research/upstream/nikke-calc-master/data/base_stat_tables/cube.json']
    files+=['app/'+n for n in (['outgoing_healing_compat.py','detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json'] if args.backend=='ptx' else ['outgoing_healing_compat.py','detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'])]
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};planned=list(real_fixtures() if args.real else fixtures());rows=[];device=v.s.v.v.v.Cuda()
    try:
        for name,b,extra in planned:
            try:row=compare(device,name,b,extra,args.backend)
            except Exception as exc:row=dict(name=name,passed=False,error=repr(exc));print(json.dumps(row),flush=True)
            rows.append(row)
            if args.fail_fast and not row['passed']:break
    finally:device.close()
    assert hashes=={p:sha(p) for p in files}
    r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(x['passed'] for x in rows),stage_only=False,objective_complete=False,abi=g.DETAIL_ABI,backend=args.backend,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False,cpu_model_extended=True,in_game_rules_verified=False)
    (ROOT/args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
