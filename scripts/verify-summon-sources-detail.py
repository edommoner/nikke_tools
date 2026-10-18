"""Autonomous GPU source lifecycles and actual pool-clipped landing receipts."""
import argparse,copy,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a
from detail_boss import compile_world
from detail_world import patterns_for,packed_enemy
from calculator.boss_pattern import BossScript,validate,ADD_PREFIX
from calculator.sim_result import HitEvent
from effect_runtime import state
from impact_runtime import land_add
from impact_specs import ActorHandle,Impact,ImpactTrace,impact_command
from world_actor_runtime import registry_for
from world_actor_specs import bindings
from test_target_counter_runtime import manager,NAMES
from summon_source_cases import cases
from gpu_selector import Cuda
import detail_gpu as g

def counter(name,event):return dict(name=name,source='스킬1',type='buff',stat='',fixed_value=0,target='self',duration=-1,max_stack=10000,trigger=dict(timing=[event],condition=[]))

def prepare(raw,parts=None,effects=None):
    bm=manager([counter('source-spawns','event:enemy_spawn'),counter('source-deaths','enemy_death')] if effects is None else effects);enemy={'def':0,'core_px':0}
    expected=patterns_for(parts or [])+copy.deepcopy(raw)
    boss=BossScript(validate(expected),enemy,lambda *_:True)
    state(bm).impact_trace=ImpactTrace();bm.state['enemy']=enemy
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in NAMES]
    program=g.compile_effects(chars,bm._effects)
    program['world'],metadata=compile_world({'def':0,'core_px':0,'patterns':expected},parts or [],{'enemy':{'patterns':raw}},program)
    return bm,boss,enemy,program

def compare(device,backend,name,raw,actions,want,parts=None,cpu_only=False):
    bm,boss,enemy,program=prepare(raw,parts);script=[[0,0,0,i,0,-1,0,0] for i in range(5)];expected=[];last=0;incoming=[];receiver_hp=10000
    source_indices={run.p.id:i for i,run in enumerate(r for r in boss._runs if r.p.id!='authored-live-parts')}
    for n in NAMES:bm.notify('battle_start',0,n)
    configured=[b for b in bindings([r.p for r in boss._runs]) if int(b.kind)==5]
    def query(t,event,arg,values):
        script.append([t,2,event,0,arg,len(expected),0,0]);expected.append(list(values)+[0]*(48-len(values)))
    for action in actions:
        t,kind,*args=action
        if kind=='frame':
            events=boss.begin_frame(t,enemy);bm.tick(t)
            for event in events:
                for n in NAMES:bm.notify(event,t,n)
            for hit in boss.attacks:
                spec=hit.spec
                # The existing incoming suite covers recipient/layer math.
                # Here use an independent stationary piercing receiver and the
                # real CPU source scheduler's order, time and source labels.
                assert spec.rule=='slot' and spec.slots==(0,) and spec.pierce
                damage=max((spec.atk-100)*spec.coeff/100,1);receiver_hp-=damage;assert receiver_hp>0
                source=-1
                if hit.source:
                    b=next(b for b in configured if boss._runs[b.run].p.id==hit.pattern and boss._runs[b.run].adds[b.slot].name==hit.source)
                    source=1+len(parts or [])+b.identity
                incoming.append([t,source_indices[hit.pattern],0,damage,1,0,0,0,damage,receiver_hp,0,source+1])
            boss.attacks.clear()
            script.append([t,15,0,0,0,-1,0,0])
        elif kind=='finish':boss.finish(t);script.append([t,5,0,0,0,-1,0,0])
        else:
            identity,damage,who,family=args;binding=configured[identity];run=boss._runs[binding.run];bm.tick(t)
            before=state(bm).impact_trace.count
            tag=('normal','bonus_damage','dot_damage')[family]
            land_add(bm,boss,HitEvent(t,NAMES[who],damage,False,tag),binding.label,t)
            last=state(bm).impact_trace.last.damage if state(bm).impact_trace.count>before else 0
            command=impact_command(t,Impact(NAMES[who],ActorHandle(5,identity,run.opens),family,2,damage),NAMES);command[1]=14;script.append(command)
        for b in configured:
            run=boss._runs[b.run];add=run.adds[b.slot] if run.opens else None
            row=[1,b.identity,run.opens,int(bool(add and run.active and add.alive)),({'':0,'처치':1,'퇴장':2,'자폭':3}[add.gone] if add else 2),add.dealt if add else 0,add.hits if add else 0,run.start_t if run.opens else -1,source_indices[run.p.id],b.slot,add.order if add else 0,boss.enemy_count,last,boss.add_overkill]+[boss.add_dealt.get(n,0) for n in NAMES]+[boss._carry.count('enemy_death')]
            query(t,134,b.identity,row)
        query(t,126,0,state(bm).impact_trace.fields(NAMES))
        for label in ('source-spawns','source-deaths'):
            values=[0]*48;values[37]=bm.ref_count(NAMES[0],label) or 0
            # The ordinary named-state query also contains other quantities;
            # compare only its ref-count column below.
            query(t,0,program['states'][label],values)
    t=actions[-1][0]
    for index in range(len(incoming)+1):query(t,117,index,(incoming[index] if index<len(incoming) else [0]*12)+[len(incoming)])
    query(t,119,0,[receiver_hp]+[10000]*4+[2000000]*10+[0])
    actual=dict(total=sum(boss.add_dealt.values()),overkill=boss.add_overkill,spawns=bm.ref_count(NAMES[0],'source-spawns') or 0,deaths=bm.ref_count(NAMES[0],'source-deaths') or 0,incoming=len(incoming),incoming_damage=sum(row[3] for row in incoming))
    for key,value in want.items():assert math.isclose(actual[key],value,abs_tol=1e-9),(name,key,actual,want)
    if name=='cleared-priority-and-followed':
        ends=[(e.pattern,e.outcome) for e in boss.log if e.event=='end' and math.isclose(e.t,.5)]
        assert ('wave','cleared') in ends and ('follower','followed') in ends,ends
    workspace=None
    if not cpu_only:
        result=g.run(device,[program],script,[packed_enemy({'def':0,'core_px':0},parts or [])],[bm.state['base_stats']],module_backend=backend)
        assert result['totals'][0]==[0]*5,'Add pool receipts must not manufacture boss damage'
        for index,(got,wanted) in enumerate(zip(result['queries'][0],expected)):
            fields=[37] if script_query(script,index)[2]==0 else range(48)
            for field in fields:assert math.isclose(got[field],wanted[field],rel_tol=1e-12,abs_tol=1e-8),(name,index,field,got[field],wanted[field])
        workspace=result['workspace_bytes']
    row=dict(name=name,passed=True,queries=len(expected),source_totals=actual,workspace_bytes=workspace,fixed_parts=len(parts or []),normal_summon_admission=False)
    print(json.dumps(row),flush=True);return row

def script_query(script,index):return next(row for row in script if row[1]==2 and row[5]==index)

def stale_controls(device,backend):
    raw=[dict(id='wave',kind='summon',spec=dict(count=1,hp=1),until=dict(time=.1),after=['start','wave'],repeat=2)]
    bm,boss,enemy,program=prepare(raw)
    prefix=[[0,15,0,0,0,-1,0,0]]
    first=impact_command(.01,Impact(NAMES[0],ActorHandle(5,0),0,2,1),NAMES);first[1]=14
    prefix += [first,[.1,15,0,0,0,-1,0,0]]
    for identity,generation in ((0,1),(1,2)):
        bad=impact_command(.11,Impact(NAMES[0],ActorHandle(5,identity,generation),0,2,1),NAMES);bad[1]=14
        script=prefix+[bad,[.12,5,0,0,0,-1,0,0],[.12,2,134,0,0,0,0,0]]
        try:g.run(device,[program],script,[[0,0]],[bm.state['base_stats']],module_backend=backend)
        except RuntimeError as error:assert 'result rejected: [8]' in str(error),str(error)
        else:raise AssertionError('A stale/unknown source handle was accepted')
    result=g.run(device,[program],prefix+[[.12,5,0,0,0,-1,0,0],[.12,2,134,0,0,0,0,0]],[[0,0]],[bm.state['base_stats']],module_backend=backend)
    assert result['queries'][0][0][2]==2 and result['queries'][0][0][5]==0
    return dict(name='stale-and-unknown-generation-rejected',passed=True,rejections=2,context_reused=True,workspace_bytes=result['workspace_bytes'])

def attack_capacity(device,backend):
    raw=[dict(id='wave',kind='summon',spec=dict(count=2,hp=13,attack=dict(coeff=100,atk=200,target='slot:1',pierce=True,hits=600,interval=0)))]
    bm,boss,enemy,program=prepare(raw)
    script=[[0,15,0,0,0,-1,0,0],[1,5,0,0,0,-1,0,0],[1,2,134,0,0,0,0,0]]
    try:g.run(device,[program],script,[[0,0]],[bm.state['base_stats']],module_backend=backend)
    except RuntimeError as error:assert 'result rejected: [512]' in str(error),str(error)
    else:raise AssertionError('Source attack queue overflow was silently truncated')
    return dict(name='source-attack-queue-capacity',passed=True,expected_status=512)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');ap.add_argument('--cpu-preflight',action='store_true');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[ROOT/'scripts'/n for n in ('verify-summon-sources-detail.py','summon_source_cases.py','detail_coverage.py')]+[ROOT/'tests/test_target_counter_runtime.py',ROOT/'app/detail_effects.cu',ROOT/'data/engine-effect-overrides.json']
    if not args.cpu_preflight:files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};start=time.perf_counter();device=None if args.cpu_preflight else Cuda()
    try:
        rows=[compare(device,args.backend,*case,cpu_only=args.cpu_preflight) for case in cases()]
        if not args.cpu_preflight:rows += [attack_capacity(device,args.backend),stale_controls(device,args.backend)]
    finally:
        if device:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,cases=rows,source_sha256=before,source_stable=True,seconds=time.perf_counter()-start,cpu_trace_used_as_gpu_input=False,normal_summon_admission=False,scope='Source lifecycle and CPU AttackHit order/time/source compared with independent stationary piercing receiver quantities. Existing incoming layer math is reused. Autonomous outgoing routing and multi_hit remain pending.')
    suffix='cpu-preflight' if args.cpu_preflight else args.backend
    (ROOT/f'research/summon-sources-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
