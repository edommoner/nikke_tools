"""Version 2 profile-only L2. S18's oracle remains unchanged.

Switches: action_rate=1, burst_cycle=2, dynamic_targets=4, contexts=8.
Rules and approximation boundaries are recorded by build_s20.py. No truth
labels, learned coefficients or reference execution are used here.
"""
import json
import math
import pathlib
import l2_score as v1

SWITCHES = dict(action_rate=1, burst_cycle=2, dynamic_targets=4, contexts=8)


def condition(code, source, squad, chars):
    if code == 0:
        return True
    other = any(n != source and str(chars[n]['metadata'].get('burst_stage')) == '1' for n in squad)
    if code in (1, 2):
        return other == (code == 2)
    group = chars[source]['metadata'].get('squad')
    return bool(group) and any(n != source and chars[n]['metadata'].get('squad') == group for n in squad)


def cycle(squad, chars, duration):
    """Ordered-ready cycle with data-derived event CDR, stages and reentry.

    timeline.py:3472-3485,3548-3584,3610-3629,3641-3653,3967-4003,
    4135-4138. Frame quantization and unrepresented event triggers are omitted.
    """
    casts = dict.fromkeys(squad, 0)
    ready = dict.fromkeys(squad, 0.)
    stages = {}
    reentry = {}
    rules = {n: [(r if len(r)==7 else [*r,0]) for r in chars[n].get('mechanics_s20', []) if condition(r[2], n, squad, chars)] for n in squad}
    for n in squad:
        stage = str(chars[n]['metadata'].get('burst_stage', ''))
        if n == '레드 후드' and stage == 'A':
            stage = '3'
        for kind, event, cond, threshold, value, scope, limit in rules[n]:
            if kind == 1:
                stage = str(int(value))
        stages[n] = stage
        reentry[n] = any(r[0] == 2 for r in rules[n])
    if any(not any(stages[n] in (str(s), 'A') for n in squad) for s in (1, 2, 3)):
        return casts, 0., 0
    t = 3.
    fb = 0.
    cycles = 0

    used = {n: [0]*len(rules[n]) for n in squad}

    def emit(event, when, count, caster=None):
        for source in squad:
            if event == 1 and source != caster:
                continue
            for index, (kind, ev, cond, threshold, value, scope, limit) in enumerate(rules[source]):
                if kind != 0 or ev != event or count < threshold:
                    continue
                if limit and used[source][index] >= limit:
                    continue
                used[source][index] += 1
                for dest in (squad if scope else [source]):
                    ready[dest] = max(when, ready[dest]-value)

    emit(0, 0., 1)
    for _ in range(32):
        for stage in ('1', '2', '3'):
            candidates = [n for n in squad if stages[n] in (stage, 'A')]
            for slot in range(2):
                chosen = next((n for n in candidates if ready[n] <= t+1e-9), None)
                if chosen is None:
                    t = max(t, min(ready[n] for n in candidates))
                    chosen = next(n for n in candidates if ready[n] <= t+1e-9)
                if t >= duration:
                    return casts, fb, cycles
                casts[chosen] += 1
                ready[chosen] = t+float(chars[chosen]['metadata'].get('burst_cooldown', 40))
                emit(1, t, casts[chosen], chosen)
                emit(3+int(stage), t, cycles+1)
                if slot == 0 and reentry[chosen]:
                    t += .5
                    continue
                break
            t += .37 if stage == '3' else .1
        if t >= duration:
            break
        cycles += 1
        emit(2, t, cycles)
        extension = 0.
        for kind, event, cond, threshold, value, scope, limit in rules[chosen]:
            if kind == 3:
                extension += value
        length = max(1., 10.+extension)
        fb += min(length, duration-t)
        t += length
        if t >= duration:
            break
        emit(3, t, cycles)
        t += 2.
        if t >= duration:
            break
    return casts, fb, cycles


def action_rate(c, values):
    """Sustained weapon cycle approximation using reference arithmetic.

    timeline.py:95-104,1600-1608,1945-1957,3142-3204,3274-3286.
    Quantization is per compact mean input here; within-source covariance,
    finite-magazine boundaries, MG warmup and weapon swaps remain approximate.
    """
    m = c['metadata']
    w = c.get('weapon_cycle_s20', {})
    v = lambda k: values.get(k, 0.)
    base = float(m.get('max_ammo', 1))
    ammo = max(1., base+math.floor(base*(v('max_ammo_pct')/100.)+.5)+round(v('max_ammo_flat')))
    reload = float(m.get('reload_time', 0.))*max(0., 1.-v('reload_speed_pct')/100.)
    refill = min(1., (1./float(m.get('clip_count', 1)))*max(0., 1.+v('reload_ratio_pct')/100.))
    gain = max(1, math.floor(ammo*refill+.5))
    reload *= max(1, math.ceil(ammo/gain))
    rate = float(w.get('fire_rate_max') or w.get('fire_rate') or m.get('fire_rate') or 1.)
    if m.get('is_charge'):
        charge = float(w.get('charge_time_base') or m.get('charge_time') or 0.)
        cut = math.floor((charge*(v('charge_speed_pct')/100.))/.01+.5)*.01
        charge = max(0., max(0., charge-cut)+v('charge_time_flat'))
        delay = float(w.get('post_fire_delay') or 0.)
        interval = max(1./rate if m.get('input_type') == 'DOWN_Charge' else 0., charge+delay, 1./60.)
    else:
        interval = 1./(rate*max(.01, 1.+v('attack_speed_pct')/100.))
    return 1./(interval+reload/ammo)


def recipients(rule, source, squad, chars, stats):
    if isinstance(rule, list):
        return set().union(*(recipients(r, source, squad, chars, stats) for r in rule))
    p = rule.split(':') if isinstance(rule, str) else []
    prefix = p[0] if p else ''
    pool = list(squad)
    if prefix in ('allies_top_atk_excl', 'allies_lowest_hp_excl'):
        pool.remove(source)
    if prefix == 'allies_weapon_top_atk':
        pool = [n for n in pool if chars[n]['metadata'].get('weapon_type') == p[1]]
    if prefix in ('allies_top_atk', 'allies_top_atk_excl', 'allies_weapon_top_atk'):
        return set(sorted(pool, key=lambda n: -stats[n][0])[:int(p[-1])])
    if prefix in ('allies_lowest_hp', 'allies_lowest_hp_excl'):
        return set(sorted(pool, key=lambda n: stats[n][1])[:int(p[-1])])
    if prefix in ('allies_top_hp', 'allies_top_def'):
        k = 2 if prefix == 'allies_top_hp' else 3
        return set(sorted(pool, key=lambda n: -stats[n][k])[:int(p[-1])])
    if rule == 'allies_below_def':
        return {n for n in pool if stats[n][3] < stats[source][3]}
    return v1.recipients(rule, source, squad, chars)


class Score(v1.Score):
    def __init__(self, profiles):
        super().__init__(profiles)
        self.switches = profiles.get('s20', {}).get('switches', 0)

    def member_scores(self, squad):
        chars = self.chars
        switches = self.switches
        casts, fb, cycles = (cycle if switches & 2 else v1.cycle)(squad, chars, self.duration)
        # One deterministic prediction pass: own profile inputs plus all static
        # incoming supply. Dynamic effects do not rank themselves recursively.
        stats = {}
        static = {n: [{}, {}] for n in squad}

        def supply(emission, dynamic=False):
            for source in squad:
                p = chars[source]
                for q in p['buffs']:
                    d = q['effect']
                    if switches & 2 and not condition(q.get('condition_s20', 0), source, squad, chars):
                        continue
                    scale = casts[source]/max(p['reference']['casts'], 1) if v1.burst_dependent(d) else 1.
                    dests = recipients(d['target'], source, squad, chars, stats) if dynamic else v1.recipients(d['target'], source, squad, chars)
                    for dest in dests:
                        if dest == source:
                            continue
                        out = emission[dest][int(q['phase'])]
                        for k, v in q['amount'].items():
                            if k == 'atk_flat' and 'caster_atk_coefficient' in q:
                                v = q['caster_atk_coefficient']*p['base_stats']['atk']
                            out[k] = out.get(k, 0.)+v*scale
        if switches & 4:
            supply(static)
            for n in squad:
                p = chars[n]
                own = p.get('rank_own_s20', {})
                merged = dict(own)
                for k, v in static[n][1].items():
                    merged[k] = merged.get(k, 0.)+v
                base = p['base_stats']
                atk = base['atk']*(1.+merged.get('atk_pct', 0.)/100.)+merged.get('atk_flat', 0.)
                stats[n] = (atk, 100., base.get('hp', 0.), base.get('def', 0.))
        emission = {n: [{}, {}] for n in squad}
        supply(emission, bool(switches & 4))
        direct = {}
        for n in squad:
            p = chars[n]
            value = 0.
            for g in p['groups']:
                phase = int(g['phase'])
                own = dict(g['own'])
                for k, v in emission[n][phase].items():
                    own[k] = own.get(k, 0.)+v
                exposure = fb if phase else self.duration-fb
                scale = exposure/max(p['reference']['phase_seconds'][phase], 1e-9)
                if g['flags'].get('is_burst_damage') or switches & 2 and g.get('cast_scaled_s20'):
                    scale = casts[n]/max(p['reference']['casts'], 1)
                if switches & 1 and g.get('action_eligible_s20', bool(g['flags'].get('is_normal_atk'))):
                    scale *= action_rate(p, own)/max(g.get('action_rate_s20', 1.), 1e-9)
                formed = v1.buckets(g, own)
                base = self.base[id(g)]
                own_factors = g.get('self_buckets', base)
                combined = [s+(new-old) for s, new, old in zip(own_factors, formed, base)]
                combined[1] = max(0., combined[1])
                unit = g.get('context_unit_s20', g['unit']) if switches & 8 else g['unit']
                value += unit*math.prod(combined)*scale
            direct[n] = max(0., value)
        total = sum(direct.values())
        result = dict(direct)
        for n in squad:
            for d in chars[n]['dependencies']:
                if d['kind'] in ('dealt_fixed_damage', 'accum_split_damage'):
                    result[n] += d['ratio']*(total if d['scope'] == 'team' else direct[n])
        return result
