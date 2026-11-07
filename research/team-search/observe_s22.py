"""External S22 all-member hit/bucket observation, preserving full payloads."""
import json
import math
import sys
import time
import observe_s20


class Observer(observe_s20.Observer):
    def scalar(self, frame, result):
        super().scalar(frame, result)
        buffs = frame.f_locals['buffs']
        self.scalars[-1]['received_s22'] = {
            k:buffs.get(k,0.) for k in observe_s20.old.KEYS}

    def compact(self, payload):
        primary = super().compact(payload)
        target = self.target
        members = {}
        for name in (m['name'] for m in payload['members']):
            self.target = name
            # The original trace attributes own inputs for every attacker.
            # Foreign-supply integrals and action methods remain primary-only.
            part = super().compact(payload)
            members[name] = dict(groups=part['groups'], uncovered=part['uncovered'])
        self.target = target
        primary['all_members'] = members
        primary['buckets'] = observe_s20.old.b.BucketLog.aggregate(self, payload)
        groups = {}
        for hit in self.hits:
            pair = self.events.get(id(hit))
            r = pair[1] if pair and pair[0] is hit else None
            if r is None:continue
            key = (hit.caster,hit.hit_tag,r['full_burst'])
            if key not in groups:
                groups[key] = dict(member=key[0],kind=key[1],phase=key[2],
                    hits=0,damage=0,prefix_sums=[0.]*8,received={})
            g=groups[key];g['hits']+=1;g['damage']+=hit.damage
            product=math.prod(r['factors'])
            prefix=hit.damage/product if product else 0.
            g['prefix_sums'][0]+=prefix
            for i,factor in enumerate(r['factors']):
                prefix*=factor;g['prefix_sums'][i+1]+=prefix
            for name,value in r['received_s22'].items():
                stat=g['received'].setdefault(name,dict(sum=0.,min=value,max=value))
                stat['sum']+=value;stat['min']=min(stat['min'],value);stat['max']=max(stat['max'],value)
        for g in groups.values():
            g['effective_buckets']=[b/a if a else None for a,b in zip(g['prefix_sums'],g['prefix_sums'][1:])]
            for stat in g['received'].values():stat['mean']=stat.pop('sum')/g['hits']
        primary['factor_groups_s22']=list(groups.values())
        return primary


def worker(request):
    import engine_worker
    body = request['body']
    started = time.perf_counter()
    if request.get('logged'):
        with Observer(request['target'], body['duration']) as observer:
            payload = engine_worker.evaluate(body)
        profile = observer.compact(payload)
    else:
        payload = engine_worker.evaluate(body)
        profile = None
    return dict(payload=payload, profile=profile, seconds=time.perf_counter()-started,
                payload_digest=observe_s20.old.b.digest(payload))


if __name__ == '__main__':
    print(json.dumps(worker(json.load(sys.stdin)), ensure_ascii=False, allow_nan=False))
