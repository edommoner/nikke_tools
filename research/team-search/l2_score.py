"""Profile-only S18 bucket arithmetic; no truth data or fitted coefficients.

Units follow calculator/damage.py:_factor1..7. The cycle is the static
fixed-gauge/ordered-ready subset of timeline.BurstController. Dynamic cooldown,
reentry, stage overrides, timing controls and hit-count changes stay flagged.
"""
from __future__ import annotations
import json, math, pathlib

ENEMY={'enemy','all_enemies','target','target_body','same_target','boss','enemies_in_range','enemies_nearest_in_range'}
STATIC={'self','all_allies','all_allies_excl_self','allies_burst3','allies_squad'}
PREFIX=('allies:', 'allies_adjacent:', 'allies_right:', 'allies_weapon:', 'allies_weapon_excl_self:',
        'allies_class:', 'allies_code:', 'allies_code_excl_self:', 'allies_code_weapon:', 'allies_code_weapon_leftmost:', 'allies_top_base_charge_time:')

def target_supported(rule,names=()):
    if isinstance(rule,list):return all(target_supported(r,names) for r in rule)
    return isinstance(rule,str) and (rule in STATIC|ENEMY or rule in names or rule.startswith(PREFIX))


def recipients(rule,source,squad,characters):
    """Static subset of BuffManager._resolve_target_raw, 5149–5388.

    Dynamic final-ATK/HP/buff-state/random selection is deliberately unmodelled.
    Unknown rules return no recipients; profiles retain explicit flags for them.
    """
    if isinstance(rule,list):return set().union(*(recipients(r,source,squad,characters) for r in rule))
    if rule in ENEMY or rule=='all_allies':return set(squad)
    if rule=='self':return {source}
    if rule=='all_allies_excl_self':return set(squad)-{source}
    if rule in squad:return {rule}
    meta=lambda n:characters[n]['metadata']
    if rule=='allies_burst3':return {n for n in squad if str(meta(n).get('burst_stage'))=='3'}
    if rule=='allies_squad':
        group=meta(source).get('squad');return {n for n in squad if n==source or group and meta(n).get('squad')==group}
    p=rule.split(':') if isinstance(rule,str) else []
    if not p:return set()
    prefix=p[0];pool=list(squad)
    if prefix=='allies':return set(pool[:int(p[1])])
    if prefix=='allies_adjacent':
        i=pool.index(source);adj=([pool[i-1]] if i else [])+([pool[i+1]] if i+1<len(pool) else [])
        return {source,*adj[:int(p[1])]}
    if prefix=='allies_right':
        i=pool.index(source);return set(pool[i+1:i+1+int(p[1])])
    if prefix in ('allies_weapon','allies_weapon_excl_self'):
        return {n for n in pool if meta(n).get('weapon_type')==p[1] and (prefix!='allies_weapon_excl_self' or n!=source)}
    if prefix=='allies_class':
        pool=[n for n in pool if meta(n).get('class')==p[1]];return set(pool[:int(p[2])] if len(p)>2 else pool)
    if prefix in ('allies_code','allies_code_excl_self'):
        return {n for n in pool if meta(n).get('element_code')==p[1] and (prefix!='allies_code_excl_self' or n!=source)}
    if prefix in ('allies_code_weapon','allies_code_weapon_leftmost'):
        pool=[n for n in pool if meta(n).get('element_code')==p[1] and meta(n).get('weapon_type')==p[2]]
        return set(pool[:int(p[3])] if prefix.endswith('leftmost') else pool)
    if prefix=='allies_top_base_charge_time':
        pool=[n for n in pool if (meta(n).get('charge_time') or 0)>0]
        return set(sorted(pool,key=lambda n:-(meta(n).get('charge_time') or 0))[:int(p[1])])
    return set()


def buckets(g, b):
    """Independent arithmetic transcription, expected damage mode only."""
    h=g['flags'];w=g['weapon'];v=lambda k:b.get(k,0.)
    coeff=h.get('coeff');coeff=w['damage_coeff'] if coeff is None else coeff
    f1=coeff*(1+v('normal_atk_dmg_pct')/100) if h.get('is_normal_atk') else coeff
    defense=0. if h.get('is_armor_break_damage') else max(g['enemy_def']*(1+v('enemy_def_down_pct')/100)+v('enemy_def_down_flat'),0)*(1-v('def_ignore_pct')/100)
    f2=max(g['base_atk']*(1+v('atk_pct')/100)+v('atk_flat')-defense,0)
    normal=h.get('is_normal_atk');rate=v('crit_rate' if normal else 'crit_rate_skill');cd=v('crit_dmg' if normal else 'crit_dmg_skill')
    f3=1+min(1,max(0,rate))*max(0,.5+cd/100)+.5*bool(h.get('is_full_burst'))
    if normal and h.get('is_optimal_range'):f3+=.3
    cp=h.get('core_prob');core=float(h.get('is_core',False)) if cp is None else cp
    if normal or h.get('is_core_damage') or h.get('is_weapon_mode_skill'):f3+=core*((w.get('core_dmg_mult',200)-100)/100+v('core_dmg_pct')/100)
    f4=w.get('full_charge_mult',100)/100*(1+v('charge_dmg_mag_pct')/100)+v('charge_dmg_pct')/100 if h.get('is_full_charge') else 1.
    f5=1+v('atk_dmg_pct')/100
    types={'is_burst_damage':'burst_dmg_pct','is_pierce_damage':'pierce_dmg_pct','is_armor_break_damage':'armor_break_dmg_pct','is_dot':'dot_dmg_pct','is_projectile_explosion':'projectile_explosion_dmg','is_projectile_attachment':'projectile_attachment_dmg','is_sequential':'sequential_dmg_pct','is_part':'part_dmg_pct','is_intercept':'intercept_dmg_pct'}
    f5+=sum(v(k)/100 for flag,k in types.items() if h.get(flag))
    if h.get('is_burst_damage'):
        if h.get('is_aoe_burst'):f5+=v('burst_dmg_aoe_pct')/100
        if h.get('is_single_burst'):f5+=v('burst_dmg_single_pct')/100
    f6=1+v('received_dmg')/100+(v('split_dmg_pct')/100 if h.get('is_split') else 0)
    f7=1.1+v('element_bonus_pct')/100 if b.get('is_element_match') else 1.
    return [f1,f2,f3,f4,f5,f6,f7]


def cycle(squad,chars,duration):
    # timeline.py:3415,3499,3579,3584,3629,3782,3839,3944.
    stages={str(s):[] for s in (1,2,3)}
    for n in squad:
        stage=str(chars[n]['metadata'].get('burst_stage',''))
        if n=='레드 후드' and stage=='A':stage='3'  # explicit upstream default
        for s in stages:
            if stage in (s,'A'):stages[s].append(n)
    casts=dict.fromkeys(squad,0);ready=dict.fromkeys(squad,0.);t=3.;fb=0.;cycles=0
    if any(not ns for ns in stages.values()):return casts,fb,cycles
    for _ in range(32):
        for s,ns in stages.items():
            chosen=next((n for n in ns if ready[n]<=t+1e-9),None)
            if chosen is None:
                t=max(t,min(ready[n] for n in ns));chosen=next(n for n in ns if ready[n]<=t+1e-9)
            if t>=duration:return casts,fb,cycles
            casts[chosen]+=1;ready[chosen]=t+float(chars[chosen]['metadata'].get('burst_cooldown',40))
            t+=.37 if s=='3' else .1
        if t>=duration:break
        cycles+=1;fb+=min(10.,duration-t);t+=12.
        if t>=duration:break
    return casts,fb,cycles


def burst_dependent(effect):
    tr=effect.get('trigger',{});raw=json.dumps(tr)
    return 'burst_cast' in raw or 'burst_enter' in raw


class Score:
    def __init__(self,profiles):
        self.profiles=profiles;self.chars=profiles['characters'];self.duration=profiles['settings']['duration']
        self.base={id(g):buckets(g,g['own']) for p in self.chars.values() for g in p['groups']}

    @classmethod
    def load(cls,path):return cls(json.loads(pathlib.Path(path).read_text()))

    def member_scores(self,squad):
        chars=self.chars;casts,fb,cycles=cycle(squad,chars,self.duration)
        emission={n:[{},{}] for n in squad}
        for source in squad:
            p=chars[source]
            for q in p['buffs']:
                d=q['effect'];phase=int(q['phase']);scale=1.
                if burst_dependent(d):scale=casts[source]/max(p['reference']['casts'],1)
                for dest in recipients(d['target'],source,squad,chars):
                    if dest==source:continue # own values already include self supply
                    out=emission[dest][phase]
                    for k,v in q['amount'].items():
                        if k=='atk_flat' and 'caster_atk_coefficient' in q:v=q['caster_atk_coefficient']*chars[source]['base_stats']['atk']
                        out[k]=out.get(k,0.)+v*scale
        direct={}
        for n in squad:
            p=chars[n];value=0.
            for g in p['groups']:
                phase=int(g['phase']);own=dict(g['own'])
                for k,v in emission[n][phase].items():own[k]=own.get(k,0.)+v
                exposure=fb if phase else self.duration-fb
                scale=exposure/max(p['reference']['phase_seconds'][phase],1e-9)
                if g['flags'].get('is_burst_damage'):scale=casts[n]/max(p['reference']['casts'],1)
                formed=buckets(g,own);base=self.base[id(g)]
                # Measured self factors retain within-kind mean coefficients and
                # own-input covariance. Foreign inputs contribute bucket deltas.
                own_factors=g.get('self_buckets',base)
                combined=[s+(new-old) for s,new,old in zip(own_factors,formed,base)]
                combined[1]=max(0.,combined[1])
                value+=g['unit']*math.prod(combined)*scale
            direct[n]=max(0.,value)
        # One dependency pass; never multiply derived hits by seven factors again.
        total=sum(direct.values());result=dict(direct)
        for n in squad:
            for d in chars[n]['dependencies']:
                if d['kind'] not in ('dealt_fixed_damage','accum_split_damage'):continue
                result[n]+=d['ratio']*(total if d['scope']=='team' else direct[n])
        return result

    def __call__(self,squad):return max(sum(self.member_scores(squad).values()),1.)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profiles',type=pathlib.Path,required=True)
    parser.add_argument('squad',nargs=5)
    args=parser.parse_args();scorer=Score.load(args.profiles)
    values=scorer.member_scores(args.squad)
    print(json.dumps(dict(total_damage=sum(values.values()),members=values),ensure_ascii=False))
