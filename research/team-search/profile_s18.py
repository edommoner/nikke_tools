"""S18 external source observer and compact per-character profile construction.

No reference edits. BucketLog owns the scalar/event wrappers. An additional scoped
line tracer observes ORIGINAL get_buffs loop boundaries, and return wrappers keep
caster metadata for folded plan tuples. All original objects/results are returned.
"""
from __future__ import annotations
import ast, collections, contextlib, functools, inspect, json, math, pathlib, sys, time
from unittest.mock import patch
import bucket_log as b

# Only scalar damage inputs, in reference units (crit probability is fractional).
KEYS = ('normal_atk_dmg_pct atk_pct atk_flat enemy_def_down_pct enemy_def_down_flat '
        'def_ignore_pct crit_rate crit_rate_skill crit_dmg crit_dmg_skill core_dmg_pct '
        'charge_dmg_pct charge_dmg_mag_pct atk_dmg_pct burst_dmg_pct burst_dmg_aoe_pct '
        'burst_dmg_single_pct pierce_dmg_pct armor_break_dmg_pct dot_dmg_pct '
        'projectile_explosion_dmg projectile_attachment_dmg sequential_dmg_pct '
        'part_dmg_pct intercept_dmg_pct received_dmg split_dmg_pct element_bonus_pct').split()
PARTS = {k:k+'_parts' for k in ('crit_rate','crit_rate_skill','crit_dmg','crit_dmg_skill')}


def descriptor(ab):
    e=ab.effect
    return dict(caster=ab.caster, name=e.get('name',''), stat=e.get('stat',''),
                target=e.get('target','self'), trigger=e.get('trigger',{}), source=e.get('source'),
                scaling=e.get('scaling'), target_effect=e.get('target_effect'))


def token(d): return json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def snapshot(loc):
    buffs=loc.get('buffs',{}); out={k:buffs.get(k,0.) for k in KEYS}
    for k,v in PARTS.items():
        if v in loc:out[k]=sum(loc[v])
    return out


def factors(base, buffs, weapon, ht, enemy_def):
    from calculator import damage as d
    return [d._factor1(weapon,buffs,ht),d._factor2(base,enemy_def,buffs,ht),
            d._factor3(weapon,buffs,ht,True)[0],d._factor4(weapon,buffs,ht),
            d._factor5(buffs,ht),d._factor6(buffs,ht),d._factor7(buffs)]


class ProfileLog(b.BucketLog):
    def __init__(self, target, duration):
        super().__init__(); self.target=target;self.duration=duration
        self.folded={};self.buff_cache=collections.OrderedDict();self.latest={}
        self.effects={};self.samples={};self.integrals=collections.defaultdict(lambda:collections.Counter())
        self.phase_seconds=collections.Counter();self.residual=[0.]*7;self.raw_residual=collections.Counter()
        self.effect_catalog=[];self.dependencies=collections.Counter();self.dep_sources={}
        self.trace_calls=0

    def meta(self, ab):
        if ab is None:return None
        d=descriptor(ab);key=token(d);self.effects[key]=d;return key

    def record_interval(self, recipient, when, phase, contrib):
        old=self.samples.get(recipient)
        if old and when>=old[0]:
            t,p,c=old;dt=when-t
            self.phase_seconds[(recipient,p)]+=dt
            for eff,values in c.items():
                if self.effects[eff]['caster']==self.target:
                    for k,v in values.items():self.integrals[(recipient,p,eff)][k]+=v*dt
        self.samples[recipient]=(when,phase,contrib)

    def __enter__(self):
        super().__enter__()
        from calculator import buff_manager as bm
        orig=bm.BuffManager.get_buffs; code=inspect.unwrap(orig).__code__
        source,start=inspect.getsourcelines(orig);tree=ast.parse(inspect.cleandoc(''.join(source)))
        # AST line positions relative to the def, including decorator-free source.
        plan_loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and ast.unparse(n.iter)=='plan')
        first=start+plan_loop.body[0].lineno-1; end=start+plan_loop.end_lineno-1
        # Supplemental attribution for caster-ATK / HP transfers and named received amplification.
        special=set()
        for n in ast.walk(tree):
            if isinstance(n,ast.Assign) and n.lineno>plan_loop.end_lineno:
                lhs=ast.unparse(n.targets[0])
                if lhs in ("buffs['atk_flat']", "buffs['received_dmg']"):
                    special.add(start+n.lineno-1)
        original_step=bm.BuffManager._plan_step
        @functools.wraps(original_step)
        def step(manager, ab, *a, **kw):
            result=original_step(manager,ab,*a,**kw)
            if result is not None:self.folded[id(result)]=(result,self.meta(ab))
            return result
        self.stack.enter_context(patch.object(bm.BuffManager,'_plan_step',step))
        original_init=bm.BuffManager.__init__
        def initialize(manager,*a,**kw):
            original_init(manager,*a,**kw)
            self.effect_catalog=[dict(e,owner=owner) for e,owner in manager._effects if owner==self.target]
        self.stack.enter_context(patch.object(bm.BuffManager,'__init__',initialize))
        @functools.wraps(orig)
        def get(manager,*a,**kw):
            previous=sys.gettrace(); state=dict(index=-1,owner=None,before=None,parts={},pending=None)
            def add(owner,before,after):
                if owner is None:return
                dst=state['parts'].setdefault(owner,collections.Counter())
                for k in KEYS:
                    delta=after.get(k,0)-before.get(k,0)
                    if delta:dst[k]+=delta
            def trace(frame,event,arg):
                if frame.f_code is not code:return None
                loc=frame.f_locals
                if state['pending'] is not None:
                    owner,before=state['pending'];add(owner,before,snapshot(loc));state['pending']=None
                if event=='line':
                    line=frame.f_lineno
                    if line==first or (state['before'] is not None and line>end):
                        current=snapshot(loc)
                        if state['before'] is not None:add(state['owner'],state['before'],current)
                        state['before']=None
                        if line==first:
                            state['index']+=1;item=loc['plan'][state['index']]
                            if item[0]==bm._PLAN_LIVE:owner=self.meta(item[1])
                            else:
                                pair=self.folded.get(id(item));owner=pair[1] if pair and pair[0] is item else None
                            state.update(owner=owner,before=current)
                    if line in special:
                        state['pending']=(self.meta(loc.get('ab')),snapshot(loc))
                elif event=='return' and isinstance(arg,dict):
                    self.trace_calls+=1
                    if loc.get('cached') is None:
                        parts={k:dict(v) for k,v in state['parts'].items() if any(v.values())}
                        self.buff_cache[id(arg)]=(arg,parts)
                        if len(self.buff_cache)>2048:self.buff_cache.popitem(last=False)
                    else:
                        pair=self.buff_cache.get(id(arg));parts=pair[1] if pair and pair[0] is arg else {}
                    recipient=loc['caster'];when=loc['t'];phase=bool(manager.state.get('full_burst'))
                    self.latest[recipient]=(when,parts)
                    self.record_interval(recipient,when,phase,parts)
                return trace
            sys.settrace(trace)
            try:return orig(manager,*a,**kw)
            finally:sys.settrace(previous)
        self.stack.enter_context(patch.object(bm.BuffManager,'get_buffs',get))
        return self

    def scalar(self, frame, result):
        super().scalar(frame,result);r=self.scalars[-1];loc=frame.f_locals
        actual={k:loc['buffs'].get(k,0.) for k in KEYS}
        actual['is_element_match']=bool(loc['buffs'].get('is_element_match'))
        pair=self.buff_cache.get(id(loc['buffs']))
        parts=pair[1] if pair and pair[0] is loc['buffs'] else self.latest.get(r['attacker'],(None,{}))[1]
        from calculator.buff_manager import _BUFFS_ZERO
        attributed={k:_BUFFS_ZERO.get(k,0.)+sum(v.get(k,0.) for v in parts.values()) for k in KEYS}
        attributed['crit_rate']+=.15;attributed['crit_rate_skill']+=.15
        attributed['is_element_match']=actual['is_element_match']
        observed=r['factors'];reformed=factors(loc['base_atk'],attributed,loc['weapon'],loc['hit_type'],loc['enemy_def'])
        r['reconciliation']=[abs(x-y)/max(abs(x),1e-12) for x,y in zip(observed,reformed)]
        r['raw_residual']={k:actual[k]-attributed[k] for k in KEYS if abs(actual[k]-attributed[k])>1e-8}
        own=dict(actual)
        for key,values in parts.items():
            if self.effects[key]['caster']!=r['attacker']:
                for k,v in values.items():own[k]-=v
        r.update(own=own,base_atk=loc['base_atk'],weapon=dict(loc['weapon']),enemy_def=loc['enemy_def'])

    def compact(self,payload):
        # Integrate last returned sample to battle end. This is piecewise-constant
        # query-time observation, not a claim of exact between-query activation time.
        for recipient,(when,phase,parts) in list(self.samples.items()):
            self.record_interval(recipient,self.duration,phase,parts)
        groups={};uncovered=collections.Counter();total=collections.Counter();hits=0
        for h in self.hits:
            total[h.caster]+=h.damage;pair=self.events.get(id(h));r=pair[1] if pair and pair[0] is h else None
            if r:
                for i,v in enumerate(r['reconciliation']):self.residual[i]=max(self.residual[i],v)
                for k,v in r['raw_residual'].items():self.raw_residual[k]=max(self.raw_residual[k],abs(v))
            if h.caster!=self.target:continue
            hits+=1
            if r is None:uncovered[h.hit_tag]+=h.damage;continue
            key=(h.hit_tag,r['full_burst'])
            if key not in groups:
                groups[key]=dict(kind=h.hit_tag,phase=r['full_burst'],hits=0,unit=0.,damage=0,
                     own={k:0. for k in r['own']},self_buckets=[0.]*7,weapon=r['weapon'],flags=r['flags'],base_atk=r['base_atk'],enemy_def=r['enemy_def'])
            g=groups[key];g['hits']+=1;g['damage']+=h.damage
            product=math.prod(r['factors'])
            if product:g['unit']+=h.damage/product
            for k,v in r['own'].items():g['own'][k]+=v
            fs=factors(r['base_atk'],r['own'],r['weapon'],r['flags'],r['enemy_def'])
            for i,v in enumerate(fs):g['self_buckets'][i]+=v
        expected={m['name']:m['damage'] for m in payload['members'] if m['damage']}
        if dict(total)!=expected or sum(total.values())!=payload['total_damage']:raise AssertionError('Landed hit totals')
        for g in groups.values():
            for k in g['own']:g['own'][k]/=g['hits']
            g['self_buckets']=[v/g['hits'] for v in g['self_buckets']]
        buffs=[]
        for (recipient,phase,eff),values in self.integrals.items():
            exposure=self.phase_seconds[(recipient,phase)]
            if exposure:buffs.append(dict(recipient=recipient,phase=phase,effect=self.effects[eff],amount={k:v/exposure for k,v in values.items()},seconds=exposure))
        direct=sum(g['damage'] for g in groups.values())
        # Source dependency scope is encoded by the actual accumulator effects.
        scopes={e.get('stat') for e in self.effect_catalog}
        deps=[]
        for kind,amount in uncovered.items():
            scope='team' if kind=='accum_split_damage' and 'dmg_accum_received_atk_pct' in scopes else 'self'
            source=sum(total.values()) if scope=='team' else direct
            deps.append(dict(kind=kind,scope=scope,ratio=amount/max(source,1),observed_damage=amount,
                             flags=['observed_proportional_ratio','accumulator_cap_and_window_unmodelled'] if kind=='accum_split_damage' else ['observed_source_hit_mix']))
        starts=[e['time'] for e in payload['burst_timeline'] if e['event']=='full_burst 시작']
        ends=[e['time'] for e in payload['burst_timeline'] if e['event']=='full_burst 종료']
        fb=sum(min(self.duration,next((e for e in ends if e>s),self.duration))-s for s in starts)
        casts=sum(e['character']==self.target and '사용' in e['event'] for e in payload['burst_timeline'])
        return dict(groups=list(groups.values()),buffs=buffs,effects=self.effect_catalog,dependencies=deps,
             phase_seconds=[self.duration-fb,fb],casts=casts,cycles=len(starts),landed_hits=len(self.hits),own_hits=hits,
             reconciliation=self.residual,raw_residual=dict(self.raw_residual),observed_queries=self.trace_calls,
             member_damage=dict(total),uncovered=dict(uncovered),base_stats=payload['base_stats'][self.target],
             burst_timeline=payload['burst_timeline'])


def worker(request):
    import engine_worker
    started=time.perf_counter();body=request['body']
    if request.get('logged'):
        with ProfileLog(request['target'],body['duration']) as observer:payload=engine_worker.evaluate(body)
        profile=observer.compact(payload)
    else:payload=engine_worker.evaluate(body);profile=None
    return dict(payload=payload,profile=profile,seconds=time.perf_counter()-started,payload_digest=b.digest(payload))

if __name__=='__main__':print(json.dumps(worker(json.load(sys.stdin)),ensure_ascii=False,allow_nan=False))
