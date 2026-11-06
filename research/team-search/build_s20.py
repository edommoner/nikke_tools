"""Build versioned profile inputs from reference effects and paired observations.

No S9/S1 truth is read. Skill values use the unchanged S1 growth profile.
"""
import argparse
import copy
import json
import pathlib
import statistics
from l2_score_s20 import action_rate


def condition_code(effect, effects):
    conditions = effect.get('trigger', {}).get('condition', [])
    if not conditions:
        return 0
    if len(conditions) != 1:
        return None
    c = conditions[0]
    if c in ('no_burst1_ally', 'has_burst1_ally', 'squad_ally_exists'):
        return {'no_burst1_ally': 1, 'has_burst1_ally': 2, 'squad_ally_exists': 3}[c]
    if c.startswith('self_state:'):
        name = c.split(':', 1)[1]
        markers = [e for e in effects if e.get('name') == name and
                   'battle_start' in e.get('trigger', {}).get('timing', [])]
        if len(markers) == 1:
            return condition_code(markers[0], [])
    return None


def mechanics(c, growth):
    result = []
    omitted = []
    effects = c['effects']
    for e in effects:
        stat = e.get('stat', '')
        if stat not in ('burst_cooldown_reduce', 'burst_cooldown', 'burst_reentry', 'fullburst_duration') and not stat.startswith('burst_stage_override:'):
            continue
        cond = condition_code(e, effects)
        if cond is None or e.get('target') not in ('self', 'all_allies'):
            omitted.append(e)
            continue
        skill = str(e.get('source', '스킬1')).replace('스킬', '')
        level = str(growth.get('skill_levels', {}).get(skill, 1))
        value = float(e.get('fixed_value', e.get('values', {}).get(level, 0.)))
        kind = 0
        if stat.startswith('burst_stage_override:reenter') or stat == 'burst_reentry':
            kind = 2
        elif stat.startswith('burst_stage_override:'):
            kind = 1
            value = float(stat.split(':')[1])
        elif stat == 'fullburst_duration':
            kind = 3
        accepted = False
        limit = int(e.get('max_trigger') or 0)
        if limit and len(e.get('trigger', {}).get('timing', [])) != 1:
            omitted.append(e)
            continue
        for timing in e.get('trigger', {}).get('timing', []):
            event = {'battle_start': 0, 'burst_cast': 1, 'full_burst_start': 2,
                     'full_burst_end': 3, 'squad_burst_cast:1': 4,
                     'squad_burst_cast:2': 5, 'squad_burst_cast:3': 6}.get(timing)
            threshold = 1
            if timing.startswith('full_burst_start_count:'):
                event = 2
                threshold = int(timing.split(':')[1])
            # A cover-heal triggered persistent CD buff can be supplied by
            # the same caster's burst-triggered self cover heal (Tia). Its
            # first application is retroactive at full-burst entry. Represent
            # that single cast-linked reduction; independent cover heals and
            # additional stacks remain omitted rather than invented.
            if timing == 'event:cover_healed' and stat == 'burst_cooldown':
                if any(x.get('stat') == 'cover_heal_pct' and x.get('target') == 'self'
                       and x.get('trigger', {}).get('timing') == ['burst_cast'] for x in effects):
                    event = 1
            if event is None:
                continue
            if kind == 3 and timing != 'burst_cast':
                continue
            if kind == 1 and timing not in ('battle_start', 'full_burst_end'):
                continue
            if kind in (1, 2) and accepted:
                continue
            result.append([kind, event, cond, threshold, value, int(e.get('target') == 'all_allies'), limit])
            accepted = True
        if not accepted:
            omitted.append(e)
    return result, omitted


def build(previous, contexts=None):
    profiles = json.loads((previous/'profiles.json').read_text())
    body = json.loads((previous/'body.json').read_text())
    profiles['schema'] = 2
    profiles['s20'] = dict(version=2, switches=0, no_truth_fitting=True,
        approximations=['sustained mean-input weapon cycle', 'one-pass final-ATK ranking',
                        'HP percentages default to full health', 'unrepresented event CDR omitted'])
    runs = {}
    if contexts:
        for path in sorted((contexts/'runs').glob('*.json')):
            r = json.loads(path.read_text())
            if not r['non_interference'] or r['payload_digest'] != r['baseline_digest']:
                raise AssertionError('Non-interference required')
            runs.setdefault(r['selection']['target'], []).append(r)
        if len(runs) != len(profiles['characters']):
            raise ValueError('Incomplete observation contexts')
    for name, c in profiles['characters'].items():
        c['mechanics_s20'], c['mechanics_omitted_s20'] = mechanics(c, body['profile']['chars'][name])
        observed = runs.get(name, [])
        if observed:
            expected = 4 if name in ('티아','아니스 : 스타','신데렐라','홍련 : 신살','디젤 : 윈터 스위츠') else 1
            if len(observed) != expected:
                raise ValueError(f'Incomplete contexts for {name}: {len(observed)}/{expected}')
            primary = next(r for r in observed if r['selection']['context'] == 'primary')
            p = primary['profile']
            c['groups'] = p['groups']
            # Keep S18 damage supply order/amounts intact. Add action-only
            # attributed supply, with the same maximum-recipient convention.
            import profile_s18
            from observe_s20 import ACTION_KEYS
            action = {}
            for b in p['buffs']:
                amounts = {k: v for k, v in b['amount'].items() if k in ACTION_KEYS}
                if not amounts:
                    continue
                key = (profile_s18.token(b['effect']), b['phase'])
                q = action.setdefault(key, dict(effect=b['effect'], phase=b['phase'], amount={}))
                for k, v in amounts.items():
                    if abs(v) > abs(q['amount'].get(k, 0.)):
                        q['amount'][k] = v
            c['buffs'].extend(action.values())
            c['weapon_cycle_s20'] = p['weapon_cycle']
        for q in c['buffs']:
            code = condition_code(q['effect'], c['effects'])
            q['condition_s20'] = code if code is not None else 0
        own = [g for g in c['groups'] if g['phase']]
        if not own:
            own = c['groups']
        c['rank_own_s20'] = {k: statistics.mean(g['own'].get(k, 0.) for g in own) if own else 0.
                              for k in ('atk_pct', 'atk_flat')}
        for g in c['groups']:
            # Auto-damage uses normal attack arithmetic but its fixed tick
            # timer is not a weapon magazine/charge cycle (timeline auto-hit
            # path). An unambiguous cast-triggered effect family follows
            # personal casts even when HitEvent's is_burst_damage is false.
            family = [e for e in c['effects'] if
                      (g['kind'] == 'normal_skill' and e.get('stat') == 'auto_damage') or
                      (g['kind'] == 'sequential_damage' and e.get('stat', '').startswith('sequential_damage'))]
            g['cast_scaled_s20'] = bool(family) and all(e.get('trigger', {}).get('timing') == ['burst_cast'] for e in family)
            g['action_eligible_s20'] = bool(g['flags'].get('is_normal_atk')) and g['kind'] != 'normal_skill'
            g['action_rate_s20'] = action_rate(c, g.get('action_received', g['own']))
            # Context candidate estimates intrinsic unit cadence after removing
            # received action-rate changes. Uses profile quantities only.
            units = []
            for r in observed:
                p = r['profile']
                for other in p['groups']:
                    if (other['kind'], other['phase']) != (g['kind'], g['phase']):
                        continue
                    if other['flags'].get('is_burst_damage') or g['cast_scaled_s20']:
                        exposure = max(p['casts'], 1)
                        base_exposure = max(c['reference']['casts'], 1)
                    else:
                        exposure = max(p['phase_seconds'][int(g['phase'])], 1e-9)
                        base_exposure = c['reference']['phase_seconds'][int(g['phase'])]
                    unit = other['unit']/exposure*base_exposure
                    if g['action_eligible_s20']:
                        rate = action_rate(c, other.get('action_received', other['own']))
                        unit *= g['action_rate_s20']/max(rate, 1e-9)
                    units.append(unit)
            g['context_unit_s20'] = statistics.median(units) if len(observed)>1 and units else g['unit']
        c['contexts_s20'] = [r['selection'] for r in observed]
        standards = list(c['standard_squads'])
        for r in observed:
            if r['selection']['members'] not in standards:
                standards.append(r['selection']['members'])
        if len(standards) > 4:
            raise ValueError('At most four distinct standard contexts')
        c['standard_squads'] = standards
        c['flags_s20'] = ['mean_action_inputs', 'single_pass_dynamic_stats',
                          'HP_percentage_state_unmodelled', 'DEF_buff_state_unmodelled']
        if c['mechanics_omitted_s20']:
            c['flags_s20'].append('omitted_cycle_effects_retained')
    return profiles


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous', type=pathlib.Path, required=True)
    p.add_argument('--contexts', type=pathlib.Path)
    p.add_argument('--output', type=pathlib.Path, required=True)
    a = p.parse_args()
    a.output.write_text(json.dumps(build(a.previous, a.contexts), ensure_ascii=False, separators=(',', ':'), allow_nan=False)+'\n')
