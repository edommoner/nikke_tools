"""Global team-hit counters and attacker attribution, independent CPU oracle."""
import argparse,copy,hashlib,importlib.util,json,math,random,sys
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from detail_gpu import run,evaluate_full
from gpu_selector import Cuda
from gpu_service import resolve_verification
from calculator.buff_manager import BuffManager
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
oracle=load('team_hit_oracle','scripts/verify-detail.py')
p=load('team_hit_periodic','scripts/verify-periodic-detail.py')
raw=load('team_hit_injection','scripts/verify-cleanse-detail.py')
E=p.effect
oracle.EVENT={**oracle.EVENT,'squad_part_hit':44,'squad_body_hit':45}

@contextmanager
def manual_team_events():
    original=BuffManager.notify
    def route(self,event,t,caster,*args,**kwargs):
        if event in ('squad_part_hit','squad_body_hit'):return self.notify_team_hit(event,t,caster)
        return original(self,event,t,caster,*args,**kwargs)
    with patch.object(BuffManager,'notify',route):yield

def primitives():
    refs=json.loads((ROOT/'research/detail-team-hits-cpu-references.json').read_text(encoding='utf-8'))
    for i,ref in enumerate(refs['cases']):
        commands=[(0,0,j) for j in range(5)]
        for step,attacker in enumerate((1,2,1,4,2,3),1):
            t=step/10
            commands.append((t,44 if ref['event']=='squad_part_hit' else 45,attacker))
            commands.extend((t+.0001,'query',j) for j in range(5))
        commands.extend((2,'query',j) for j in range(5))
        yield 'reference-'+str(i),ref['chars'],ref['effects'],ref['base_stats'],commands
    names=refs['cases'][0]['chars'];names=copy.deepcopy(names)
    roster=[c['name'] for c in names];stats=refs['cases'][0]['base_stats']
    for condition in ([],['has_defender_ally'],['no_defender_ally'],['back_row'],['prob:50']):
        # Source is slot 1, so back_row is true even for a front-row attacker.
        source=roster[1]
        for target in ('self','allies_right:1','all_allies'):
            effect=E('shared team budget','buff','atk_pct',7,target,event='body_hit_count:1',condition=condition,max_trigger=3,max_stack=10,duration=1)
            commands=[(0,0,j) for j in range(5)]
            for k,attacker in enumerate((4,0,2,3,1,4,0),1):
                commands.append((k/10,45,attacker));commands.extend((k/10+.0001,'query',j) for j in range(5))
            yield 'budget-'+str(condition)+'-'+target,names,[(effect,source)],stats,commands
    for kind,stat in [('damage','bonus_damage'),('instant','current_hp_reduce')]:
        effect=E('team '+kind,kind,stat,3,'target_body' if kind=='damage' else 'self',event='part_hit_count:2',max_trigger=3)
        commands=[(0,0,j) for j in range(5)]
        for k,attacker in enumerate((1,3,2,4,2,0),1):
            commands.append((k/10,44,attacker));commands.extend((k/10+.0001,'query',j) for j in range(5))
        effects=[(effect,roster[0])]
        if kind=='instant':effects.append((E('HP witness','buff','atk_pct',9,'all_allies',event='passive',condition=['ally_hp_below:99']),roster[0]))
        yield 'kind-'+kind,names,effects,stats,commands

def verify_primitives(device,backend):
    rows=[]
    for name,chars,effects,stats,commands in primitives():
        program=oracle.program(copy.deepcopy(chars),effects);script=[];index=0
        for t,event,who in commands:
            script.append([t,2 if event=='query' else 0,0 if event=='query' else event,who,-1,index if event=='query' else -1,0,0])
            if event=='query':index+=1
        # Initialize HP just as the full timeline does, without changing handlers.
        init=BuffManager.__init__
        def initialize(self,*args,**kwargs):
            init(self,*args,**kwargs);self.state['hp']={n:stats[n]['hp'] for n in self.squad_names};self.state['hp_pct']={n:100.0 for n in self.squad_names}
        with manual_team_events(),patch.object(BuffManager,'__init__',initialize):cpu,totals=oracle.oracle(program,script,[31784,5],stats,timeline_handlers=True)
        gpu=run(device,[program],script,[[31784,5]],[stats],module_backend=backend)
        errors=[]
        assert len(cpu)==len(gpu['queries'][0])==index
        for i,(x,y) in enumerate(zip(cpu,gpu['queries'][0])):
            for k in [k for k in range(32) if k!=26]+[36]:
                if not math.isclose(x[k],y[k],abs_tol=1e-9,rel_tol=1e-12):errors.append([i,k,x[k],y[k]])
        if totals!=gpu['totals'][0]:errors.append(['totals',totals,gpu['totals'][0]])
        row=dict(name=name,backend=backend,kind='primitive',passed=not errors,errors=errors,cpu_flat_atk=[q[1] for q in cpu],gpu_flat_atk=[q[1] for q in gpu['queries'][0]])
        rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
    return rows

def bodies(quick=False):
    for subject in ('D : 킬러 와이프','루마니'):
        for world in (('none','live') if quick else ('none','legacy','live','clear')):
            for shooting in (('auto',) if quick else ('auto','character')):
                for mode in (('fixed',) if quick else ('fixed','accumulate')):
                    body=body_for([subject,'리타','크라운','앨리스','모더니아'],16 if quick else 20,True)
                    for i,c in enumerate(body['profile']['chars'].values()):c['skill_levels']={'1':3+i,'2':9-i,'3':3+i}
                    body.update(seed=12345,shooting_policy=shooting,burst_policy='rules',burst_gauge_mode=mode,_debug_random_state=True)
                    if shooting=='character':
                        body['profile']['chars']['베스티']=body['profile']['chars'].pop('모더니아')
                        body['squad'][3:]=['베스티','앨리스']
                    body['enemy']['core_px']=5
                    if world=='legacy':body['enemy']['has_parts']=True
                    if world=='live':body['enemy']['parts']=[dict(name='armor',hp=0,reach=1),dict(name='cannon',hp=300000,reach=2)]
                    extra={}
                    if world=='clear':
                        body['enemy']['parts']=[dict(name='a',hp=100000000,reach=1),dict(name='b',hp=100000000,reach=2)]
                        extra={'리타':[E('authored clear','damage','damage',1000000,'all_enemies',event='every:8s',max_trigger=1,hits_parts=True)]}
                    yield subject+'-'+world,body,world,extra

def verify_battles(device,backend,quick=False):
    rows=[]
    for name,body,world,extra in bodies(quick):
        counts={};managers=[];b3_calls=[];original=BuffManager.notify_team_hit;init=BuffManager.__init__;register=BuffManager.register_damage_handler
        def observe(self,event,t,attacker):
            counts[event]=counts.get(event,0)+1
            return original(self,event,t,attacker)
        def initialize(self,*args,**kwargs):init(self,*args,**kwargs);managers.append(self)
        def register_damage(self,handler):
            def observed(eff,caster,t,*args,**kwargs):
                if caster=='베스티' and eff.get('stat')=='bonus_damage' and 'burst_cast' in eff.get('trigger',{}).get('timing',[]):b3_calls.append(eff.get('name'))
                return handler(eff,caster,t,*args,**kwargs)
            return register(self,observed)
        with raw.injected_effects(extra):
            compiled=a.evaluate({**body,'_compile_gpu_detail':True});gpu=evaluate_full(device,compiled,module_backend=backend)
            with patch.object(BuffManager,'notify_team_hit',observe),patch.object(BuffManager,'__init__',initialize),patch.object(BuffManager,'register_damage_handler',register_damage):cpu=a.evaluate(body)
            rng=list(random.getstate()[1]);bm=managers[-1]
            hp={n:dict(hp=bm.state['hp'][n],hp_pct=bm.state['hp_pct'][n],max_hp=bm.effective_max_hp(n)) for n in body['squad']}
        result=resolve_verification(gpu,cpu);checks=result['compute']['cpu_verification'].copy()
        checks.update(actual_gpu=result['compute']['backend']=='cuda_detail',final_random_state=rng==gpu['_random_state'])
        checks['final_hp']=all(math.isclose(v,gpu['compute']['final_hp'][n][k],abs_tol=1e-7,rel_tol=1e-12) for n,data in hp.items() for k,v in data.items())
        checks['team_hit_exercised']=counts.get('squad_part_hit' if world in ('legacy','live') else 'squad_body_hit',0)>0
        if '베스티' in body['squad']:checks['b3_bonus_exercised']=bool(b3_calls)
        if world=='clear':checks['phase_change_exercised']=counts.get('squad_part_hit',0)>0 and counts.get('squad_body_hit',0)>0 and all(p['destroyed'] for p in cpu['parts_state'])
        row=dict(name=name,kind='battle',backend=backend,mode=body['burst_gauge_mode'],shooting=body['shooting_policy'],passed=all(checks.values()),checks=checks,cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],team_notifications=counts,b3_bonus_dispatches=b3_calls,raw_skills_retained=True)
        if not row['passed']:row.update(cpu_members=cpu['members'],gpu_members=gpu['members'],cpu_parts=cpu.get('parts_state'),gpu_parts=gpu.get('parts_state'))
        rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
    return rows

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx','both'],default='both');ap.add_argument('--quick',action='store_true');ap.add_argument('--output',default='research/detail-team-hits-verification.json');args=ap.parse_args()
    files=['scripts/verify-team-hits-detail.py','research/detail-team-hits-cpu-references.json','app/detail_gpu.py','app/detail_world.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files};device=Cuda()
    try:rows=[row for b in (('native','ptx') if args.backend=='both' else (args.backend,)) for row in verify_primitives(device,b)+verify_battles(device,b,args.quick)]
    finally:device.close()
    assert hashes=={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},'Sources changed during verification'
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=bool(rows) and all(r['passed'] for r in rows),objective_complete=False,cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False,scope='Global counters, attacker definitions, owner conditions, shared budgets, raw D Killer Wife and Rumani squads; static and authored live parts. Not all characters/effects.')
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
