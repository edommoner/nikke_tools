"""Explicit attack groups, independent target/order quantities; no battle trace input."""
import argparse,copy,hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a
from calculator.buff_manager import BuffManager
from gpu_selector import Cuda
from attack_group_runtime import begin,finish,seal,dispatch
from effect_runtime import publish_impact,pool,state
from impact_specs import ActorHandle,ActorKind,HitFamily,HitOutcome,Impact,impact_command
import detail_gpu as g
spec=importlib.util.spec_from_file_location('attack_group_oracles',ROOT/'scripts/verify-gauge-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
E=v.effect;N=v.NAMES

def effects():
    es=[E('no critical','buff','crit_rate',-15,'all_allies'),E('first','buff','atk_pct',10,event='multi_hit:2'),
        E('second','buff','atk_pct',20,event='multi_hit:1'),E('duplicate threshold','buff','atk_pct',5,event='multi_hit:2'),
        E('ordered damage','damage','damage',100,'target',event='multi_hit:3'),E('two timings','buff','atk_pct',7,event='multi_hit:3',max_stack=10),
        E('group count','buff','',0,event='multi_hit:2',max_stack=100)]
    es[-2]['trigger']['timing'].append('multi_hit:2')
    return [(e,N[0]) for e in es]+[(E('other owner','buff','atk_pct',3,event='multi_hit:1'),N[1])]

def packet(owner,identity,kind,actor,generation=1,outcome=2,credit=1):return Impact(N[owner],ActorHandle(kind,actor,generation),HitFamily.WEAPON,outcome,10 if outcome==2 else 0,credit,identity)

def cases():
    # ('query', owner, attack, independent first six fields and target handles)
    for name in ('duplicates-policy-outcomes','generation','notification-order'):
        mask=33 if name=='duplicates-policy-outcomes' else 32
        actions=[('begin',0,7,mask,1)]
        if name=='duplicates-policy-outcomes':
            impacts=[packet(0,7,0,0)]*12+[packet(0,7,1,1),packet(1,7,5,1),packet(0,7,5,1,outcome=0,credit=0),packet(0,7,5,2,outcome=1)]
            targets=[(0,0,1),(5,2,1)];want=[42,0,1]
        elif name=='generation':impacts=[packet(0,7,5,0),packet(0,7,5,0,2)];targets=[(5,0,1),(5,0,2)];want=[42,0,1]
        else:impacts=[packet(0,7,5,i) for i in range(3)];targets=[(5,i,1) for i in range(3)];want=[49,1420,1]
        actions += [('impact',p) for p in impacts]+[('query',0,7,[1,1,len(targets),mask,1,1],targets),('finish',0,7,1),('query',0,7,[0,0,0,0,0,1],[])]
        yield name,actions,want,None
    actions=[('begin',0,7,32,1),('begin',1,7,32,2),('impact',packet(0,7,5,0)),('impact',packet(1,7,5,1)),('impact',packet(1,7,5,2)),
             ('finish',0,7,1),('query',1,7,[1,2,2,32,1,2],[(5,1,1),(5,2,1)]),('begin',0,7,32,3),('impact',packet(0,7,5,0,2)),('finish',0,7,3),('finish',1,7,2)]
    yield 'owner-and-epoch-isolation',actions,[20,0,0],3
    targets=[(5,i,1) for i in range(17)]
    actions=[('begin',0,7,32,1)]+[('impact',packet(0,7,5,i)) for i in range(17)]+[('seal',0,7,1),('begin',0,7,32,2),('impact',packet(0,7,5,99,2)),
        ('sealed_query',0,7,1,0,[1,1,17,32,1,2],targets),('sealed_query',0,7,1,1,[1,1,17,32,1,2],targets),
        ('seal',0,7,2),('dispatch',0,7,2),('sealed_query',0,7,1,0,[1,1,17,32,0,2],targets),
        ('dispatch',0,7,1),('sealed_query',0,7,1,0,[0,0,0,0,0,2],[])]
    # The child's single-stack +20 refreshes at the parent's threshold1;
    # it is not an additional +20 stack in the final quantity.
    yield 'retained-parent-child-and-pages',actions,[49,1420,1],None

def independent(device,backend):
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in N];stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in N};rows=[]
    for name,actions,want,other in cases():
        es=effects();program=g.compile_effects(chars,es)
        class BM(BuffManager):
            def _register_all(self):self._effects=copy.deepcopy(es);self._build_notify_index()
        bm=BM(chars,state=dict(base_stats=stats,enemy={'def':0},full_burst=False,hp_pct={n:100 for n in N}));damage=[0]
        bm.register_damage_handler(lambda effect,owner,t:damage.__setitem__(0,damage[0]+int(1000*(1+bm.get_buffs(owner,'__enemy__',t).get('atk_pct',0)/100)*effect['fixed_value']/100)))
        bm.notify('battle_start',0,N[0]);script=[[0,0,0,0,0,-1,0,0]];expected=[];frames={};sealed={}
        for action in actions:
            kind,*args=action
            if kind=='begin':
                owner,identity,mask,epoch=args;frames[owner,identity]=begin(bm,N[owner],identity,0,kinds=[k for k in ActorKind if mask&(1<<k)])
                assert frames[owner,identity].key.epoch==epoch;script.append([0,10,mask,owner,identity,-1,epoch,0])
            elif kind=='impact':publish_impact(bm,args[0],0);script.append(impact_command(0,args[0],N))
            elif kind=='finish':
                owner,identity,epoch=args;assert frames[owner,identity].key.epoch==epoch;finish(bm,frames[owner,identity],0);script.append([0,11,0,owner,identity,-1,epoch,0])
            elif kind=='seal':
                owner,identity,epoch=args;ticket=seal(bm,frames[owner,identity],0);assert ticket.result.key.epoch==epoch
                sealed[owner,identity,epoch]=ticket;script.append([0,12,0,owner,identity,-1,epoch,0])
            elif kind=='dispatch':
                owner,identity,epoch=args;dispatch(bm,sealed.pop((owner,identity,epoch)),0);script.append([0,13,0,owner,identity,-1,epoch,0])
            elif kind=='sealed_query':
                owner,identity,epoch,page,head,targets=args;ticket=sealed.get((owner,identity,epoch))
                actual=[int(ticket is not None),ticket.result.key.epoch if ticket else 0,len(ticket.result.targets) if ticket else 0,32 if ticket else 0,len(pool(bm,'attack_groups')),state(bm).attack_group_epoch]
                assert actual==head and ([] if ticket is None else [(int(t.kind),t.identity,t.generation) for t in ticket.result.targets])==targets
                row=head+[v for target in targets[page*14:(page+1)*14] for v in target];expected.append(row+[0]*(48-len(row)));script.append([0,2,132,owner,identity,len(expected)-1,epoch,page])
            else:
                owner,identity,head,targets=args;frame=pool(bm,'attack_groups').get((N[owner],identity));actual=[int(frame is not None),frame.key.epoch if frame else 0,len(frame.targets) if frame else 0,sum(1<<k for k in frame.kinds) if frame else 0,len(pool(bm,'attack_groups')),state(bm).attack_group_epoch]
                assert actual==head and ([] if frame is None else [(int(t.kind),t.identity,t.generation) for t in frame.targets])==targets
                row=head+[v for target in targets for v in target];expected.append(row+[0]*(48-len(row)));script.append([0,2,131,owner,identity,len(expected)-1,0,0])
        cpu=[bm.get_buffs(N[0],'__enemy__',0).get('atk_pct',0),damage[0],bm.ref_count(N[0],'group count') or 0];assert cpu==want,(name,cpu,want)
        index=len(expected);script.append([0,2,0,0,program['states']['group count'],index,0,0])
        if other is not None:script.append([0,2,103,1,0,index+1,0,0])
        result=g.run(device,[program],script,[[0,0]],[stats],module_backend=backend)
        assert result['queries'][0][:index]==expected,(name,'target snapshots',result['queries'][0][:index],expected)
        q=result['queries'][0][index];actual=[q[0],q[38],q[37]];assert actual==want,(name,actual,want)
        if other is not None:
            assert result['queries'][0][-1][0]==other
        rows.append(dict(name=name,passed=True,cpu=cpu,gpu=actual,independent_expected=want,workspace_bytes=result['workspace_bytes']));print(json.dumps(rows[-1]),flush=True)
    # Bounds and stale epochs must fail as statuses, not alias another group.
    program=g.compile_effects(chars,[])
    for name,commands in [('group-capacity',[[0,10,32,0,i,-1,i,0] for i in range(1,34)]),
                          ('target-capacity',[[0,10,32,0,1,-1,1,0]]+[impact_command(0,packet(0,1,5,i),N) for i in range(129)]),
                          ('stale-epoch',[[0,10,32,0,1,-1,1,0],[0,11,0,0,1,-1,1,0],[0,10,32,0,1,-1,2,0],[0,11,0,0,1,-1,1,0]]),
                          ('retained-capacity',sum(([[0,10,32,0,1,-1,i,0],[0,12,0,0,1,-1,i,0]] for i in range(1,33)),[])+[[0,10,32,0,1,-1,33,0]]),
                          ('double-dispatch',[[0,10,32,0,1,-1,1,0],[0,12,0,0,1,-1,1,0],[0,13,0,0,1,-1,1,0],[0,13,0,0,1,-1,1,0]])]:
        try:g.run(device,[program],commands+[[0,2,131,0,1,0,0,0]],[[0,0]],[stats],module_backend=backend)
        except RuntimeError as error:assert 'result rejected: [8]' in str(error),(name,str(error))
        else:raise AssertionError(name+' was not rejected')
        rows.append(dict(name=name,passed=True,expected_status=8));print(json.dumps(rows[-1]),flush=True)
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');ap.add_argument('--output');args=ap.parse_args();files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+[ROOT/'app/detail_effects.cu']
    files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};start=time.perf_counter();device=Cuda()
    try:rows=independent(device,args.backend)
    finally:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,cases=rows,source_sha256=before,source_stable=True,cpu_trace_used_as_gpu_input=False,autonomous_producer_connected=False,character_admission_changed=False,seconds=time.perf_counter()-start)
    (ROOT/(args.output or f'research/attack-groups-{args.backend}.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
