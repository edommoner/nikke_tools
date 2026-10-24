"""Original BossScript operations and Geometry ordering, no GPU lowering."""
from calculator.boss_pattern import BossScript,validate
from calculator.sim_result import HitEvent

def observe(case):
    patterns=validate(case['patterns'],coord=True);enemy=dict(coord={},core_px=0,has_parts=False,def_=0);boss=BossScript(patterns,enemy,lambda *_:False)
    counts={1:0,6:0};rows=[]
    for p in patterns:
        for ordinal,t in enumerate(p.targets):
            kind=1 if p.kind=='parts' else 6;rows.append(dict(kind=kind,identity=counts[kind],pattern=p.idx,ordinal=ordinal,label=t.name));counts[kind]+=1
    slots={(r['kind'],r['identity']):i+1 for i,r in enumerate(sorted(rows,key=lambda r:(r['kind'],r['identity'])))}
    by_name={r['label']:r for r in rows};snapshots=[]
    for op,time,index,amount in case['commands']:
        if op=='open':
            run=boss._runs[index];assert not run.active;boss._open(run,time,'start',[])
        elif op=='close':
            run=boss._runs[index];assert run.active;boss._close(run,time,'expired',[])
        elif op=='hit':boss.hit_target(HitEvent(t=time,caster='source',damage=amount,is_crit=False,hit_tag='skill',skill_name='coordinate-source',target=rows[index]['label']),time)
        boss._apply(enemy)
        if op=='capture':
            def handle(g):
                r=by_name[g.name];return [slots[r['kind'],r['identity']],r['kind'],r['identity'],boss._runs[r['pattern']].opens]
            snapshots.append(dict(time=time,all=[handle(g) for g in boss.geom.targets],parts=[handle(g) for g in boss.geom.targets if g.kind=='parts']))
    states=[]
    for r in rows:
        run=boss._runs[r['pattern']];target=run.targets[r['ordinal']] if run.targets else None
        states.append(dict(generation=run.opens,alive=bool(run.active and target is not None and not target.destroyed),dealt=target.dealt if target else 0.,start=run.start_t,hits=target.hits if target else 0))
    return dict(states=states,snapshots=snapshots),[]
