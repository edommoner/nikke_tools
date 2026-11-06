"""Paired hit audit. Per-hit traces stay in IPC/memory; only aggregates saved.

Fresh unwrapped child for EVERY traced body proves full-payload identity.
Actual bucket changes are observations, not input-knob predictions.
"""
import argparse, collections, json, pathlib, subprocess, sys, time
sys.dont_write_bytecode=True
import bucket_log as b
import measure_s17 as measure


class Trace(b.BucketLog):
    def scalar(self,frame,result):
        super().scalar(frame,result)
        loc=frame.f_locals
        self.scalars[-1]['inputs']={k:loc['buffs'].get(k,0.) for k in ('atk_pct','atk_flat','crit_dmg','crit_dmg_skill','crit_rate','crit_rate_skill')}
        self.scalars[-1]['inputs']['base_atk']=loc['base_atk']


def trace(body):
    import engine_worker
    with Trace() as log:payload=engine_worker.evaluate(body)
    trace=[]
    for hit in log.hits:
        pair=log.events.get(id(hit));r=pair[1] if pair and pair[0] is hit else None
        if r:trace.append(dict(attacker=hit.caster,time=hit.t,kind=hit.hit_tag,damage=hit.damage,
                              factors=r['factors'],slopes=r['slopes'],inputs=r['inputs']))
        else:trace.append(dict(attacker=hit.caster,time=hit.t,kind=hit.hit_tag,damage=hit.damage,factors=None))
    return dict(payload=payload,trace=trace,reconciliation=log.aggregate(payload)['reconciliation'])


def child(body):
    r=subprocess.run([sys.executable,__file__,'--trace'],input=json.dumps(body),capture_output=True,text=True,check=True)
    traced=json.loads(r.stdout)
    plain=measure.evaluate(body,False)
    if traced['payload']!=plain['payload']:raise AssertionError('Trace interfered')
    return traced


def audit(out,results):
    cases=[(7720,'atk',1000),(2080,'atk',1000),(852,'crit_dmg',1)]
    rows=[]
    for identity,knob,magnitude in cases:
        started=time.perf_counter();r=json.loads((results/(str(identity)+'.json')).read_text())
        body=json.loads((results/'body.json').read_text());body['squad']=r['selection']['members']
        before=child(body);after=child(b.perturb(body,knob,magnitude));sums=collections.defaultdict(collections.Counter)
        if len(before['trace'])!=len(after['trace']):raise AssertionError('Hit shape changed')
        axes=collections.Counter();residual=0.;observed_prediction=0.;first=0.
        for x,y in zip(before['trace'],after['trace']):
            if (x['attacker'],x['time'],x['kind'])!=(y['attacker'],y['time'],y['kind']):raise AssertionError('Hit identity changed')
            g=sums[x['attacker']];g['actual_change']+=y['damage']-x['damage'];g['hits']+=1
            if x['factors'] is None or y['factors'] is None:continue
            group=b.KNOBS[knob][0]-1;bx=x['factors'];by=y['factors']
            for i in range(7):
                if bx[i]!=by[i]:axes[i+1]+=1
            if bx[group]:
                frozen=x['damage']*x['slopes'][knob]*magnitude/bx[group]
                observed=x['damage']*(by[group]/bx[group]-1)
                first+=frozen;observed_prediction+=observed
                g['frozen_prediction']+=frozen;g['observed_bucket_prediction']+=observed
            g['extra_bucket_units']+=by[group]-bx[group]-x['slopes'][knob]*magnitude
            for key in x['inputs']:
                g['delta_'+key]+=y['inputs'][key]-x['inputs'][key]
        rows.append(dict(id=identity,knob=knob,magnitude=magnitude,non_interference_count=2,
                         matched_hits=len(before['trace']),changed_bucket_hit_counts=dict(axes),
                         actual_change=after['payload']['total_damage']-before['payload']['total_damage'],
                         frozen_prediction=first,observed_bucket_prediction=observed_prediction,
                         by_attacker=dict(sums),seconds=time.perf_counter()-started))
    measure.save(out,rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',action='store_true');p.add_argument('--results',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path);a=p.parse_args()
    if a.trace:print(json.dumps(trace(json.load(sys.stdin)),ensure_ascii=False))
    else:audit(a.out,a.results)
if __name__=='__main__':main()
