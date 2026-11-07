"""L2 v3 profile-only temporal occupancy and state-gated hit counts.

16: burst-sourced supply per phase exposure, including observed self supply.
32: structural conditions also gate observed own supply.
64: unambiguous burst-state-gated damage families follow personal casts.
128: plain nonstacking source effects respect their game-data upper bound.
No detailed truth is loaded. The v1/v2 oracles remain unchanged.
"""
import math
import l2_score as v1
import l2_score_s20 as v2

SWITCHES=dict(phase_occupancy=16,own_conditions=32,burst_state_hits=64,effect_bounds=128)


class Score(v2.Score):
    def __init__(self,profiles):
        super().__init__(profiles)
        self.v3=profiles['s22']['switches']

    def member_scores(self,squad):
        chars=self.chars;switches=self.switches;v3=self.v3
        casts,fb,cycles=(v2.cycle if switches&2 else v1.cycle)(squad,chars,self.duration)
        stats={};static={n:[{},{}] for n in squad}

        def scale_for(source,q):
            p=chars[source]
            if not v1.burst_dependent(q['effect']):return 1.
            scale=casts[source]/max(p['reference']['casts'],1)
            if v3&16:
                phase=int(q['phase']);exposure=fb if phase else self.duration-fb
                scale*=p['reference']['phase_seconds'][phase]/max(exposure,1e-9)
            return scale

        def amount(source,q,k,value):
            if k=='atk_flat' and 'caster_atk_coefficient' in q:
                return q['caster_atk_coefficient']*chars[source]['base_stats']['atk']
            return value

        def scaled_amount(source,q,k,value,scale):
            value=amount(source,q,k,value)*scale
            cap=q.get('caps_s22',{}).get(k)
            return min(value,cap) if v3&128 and cap is not None else value

        def supply(emission,dynamic=False,own=False):
            for source in squad:
                p=chars[source]
                for q in p['buffs']:
                    valid=not(switches&2) or v2.condition(q.get('condition_s20',0),source,squad,chars)
                    scale=scale_for(source,q)
                    d=q['effect']
                    if valid:
                        dests=v2.recipients(d['target'],source,squad,chars,stats) if dynamic else v1.recipients(d['target'],source,squad,chars)
                        for dest in dests:
                            if dest==source:continue
                            out=emission[dest][int(q['phase'])]
                            for k,value in q['amount'].items():
                                out[k]=out.get(k,0.)+scaled_amount(source,q,k,value,scale)
                    # Only explicitly observed self supply can be removed or
                    # rescaled. Unknown/unobserved effects are never fabricated.
                    if own and source in q.get('recipients',[]):
                        correction=0.
                        if v3&32 and not valid:correction=-1.
                        elif v3&16 and v1.burst_dependent(d):correction=scale-1.
                        if correction or v3&128 and q.get('caps_s22'):
                            out=emission[source][int(q['phase'])]
                            for k,value in q['amount'].items():
                                if v3&32 and not valid:
                                    delta=-amount(source,q,k,value)
                                elif v3&128 and q.get('caps_s22'):
                                    own_scale=scale if v3&16 and v1.burst_dependent(d) else 1.
                                    delta=scaled_amount(source,q,k,value,own_scale)-amount(source,q,k,value)
                                else:delta=amount(source,q,k,value)*correction
                                out[k]=out.get(k,0.)+delta
        if switches&4:
            supply(static,own=bool(v3&32 or v3&16))
            for n in squad:
                p=chars[n];merged=dict(p.get('rank_own_s20',{}))
                for k,value in static[n][1].items():merged[k]=merged.get(k,0.)+value
                base=p['base_stats'];atk=base['atk']*(1.+merged.get('atk_pct',0.)/100.)+merged.get('atk_flat',0.)
                stats[n]=(atk,100.,base.get('hp',0.),base.get('def',0.))
        emission={n:[{},{}] for n in squad}
        supply(emission,bool(switches&4),own=True)
        direct={}
        for n in squad:
            p=chars[n];value=0.
            for g in p['groups']:
                phase=int(g['phase']);own=dict(g['own'])
                for k,v in emission[n][phase].items():own[k]=own.get(k,0.)+v
                exposure=fb if phase else self.duration-fb
                scale=exposure/max(p['reference']['phase_seconds'][phase],1e-9)
                if g['flags'].get('is_burst_damage') or switches&2 and g.get('cast_scaled_s20') or v3&64 and g.get('cast_scaled_s22'):
                    scale=casts[n]/max(p['reference']['casts'],1)
                if switches&1 and g.get('action_eligible_s20',bool(g['flags'].get('is_normal_atk'))):
                    scale*=v2.action_rate(p,own)/max(g.get('action_rate_s20',1.),1e-9)
                formed=v1.buckets(g,own);base=self.base[id(g)]
                combined=[s+(new-old) for s,new,old in zip(g.get('self_buckets',base),formed,base)]
                combined[1]=max(0.,combined[1])
                unit=g.get('context_unit_s20',g['unit']) if switches&8 else g['unit']
                value+=unit*math.prod(combined)*scale
            direct[n]=max(0.,value)
        total=sum(direct.values());result=dict(direct)
        for n in squad:
            for d in chars[n]['dependencies']:
                if d['kind'] in ('dealt_fixed_damage','accum_split_damage'):
                    result[n]+=d['ratio']*(total if d['scope']=='team' else direct[n])
        return result
