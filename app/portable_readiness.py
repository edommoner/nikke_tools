"""Static, per-definition admission diagnostics; never GPU/battle certification.

Each effect is independently lowered and validated. A validator can report only
its first failure for that effect; hidden downstream requirements remain unknown.
Whole-program compilation is retained as the authoritative packing check.
"""
from collections import Counter, defaultdict
import json


def issue(error, effect=None, *, phase='effect'):
    effect = effect or {}
    message = str(error)
    if getattr(error, 'reason', None) is not None: category = error.reason
    elif 'field' in message.lower(): category = 'fields'
    elif any(word in message.lower() for word in ('recipient', 'selector', 'target:')): category = 'recipient'
    elif any(word in message.lower() for word in ('trigger', 'event', 'predicate', 'condition')): category = 'trigger'
    elif any(word in message.lower() for word in ('capacity', 'overflow')): category = 'capacity'
    else: category = 'effect' if phase == 'effect' else 'program'
    # Structured semantic coordinates, rather than unstable exception text, group
    # independently actionable operators. Preserve the original diagnostic too.
    signature = dict(phase=phase, category=category, kind=effect.get('type'),
                     stat=effect.get('stat'), target=effect.get('target', 'self'),
                     scaling=effect.get('scaling'))
    if category == 'trigger':
        operator = getattr(error, 'operator', None)
        # Preserve exact descriptor parameters and opaque event names. Only the
        # failing descriptor belongs here, never the effect's unrelated triggers.
        signature['operator'] = operator if operator is not None else dict(diagnostic=message)
    if phase=='program':signature['reason']=message
    if message.startswith('Unported effect fields: '):
        signature['fields'] = message.split(': ', 1)[1].split(', ')
    return dict(signature, code=json.dumps(signature, sort_keys=True, ensure_ascii=False),
                diagnostic_source='structured_reason' if getattr(error,'reason',None) is not None else 'message_fallback',
                error_type=type(error).__name__, message=message)


def diagnostic_sources(rows):
    """Count actual observations, including program failures hidden by priorities.

    A definition failure and a whole-program failure can describe the same
    missing feature; these counts are diagnostics, never distinct blockers.
    """
    counts={phase:Counter() for phase in ('effect','program')}
    for row in rows:
        for entry in row.get('effect_blockers',[]):
            counts['effect'][entry['issue']['diagnostic_source']]+=1
        if row.get('program_issue'):
            counts['program'][row['program_issue']['diagnostic_source']]+=1
    return {phase:{name:counter[name] for name in ('structured_reason','message_fallback')}
            for phase,counter in counts.items()}


def inspect_effects(prepared):
    from portable_world_overlay_specs import compiler_effect
    from portable_target_counter_program import compiler_effects
    from portable_runtime import validate_effect
    result = []
    for index, item in enumerate(prepared['effects']):
        effect = item['effect']
        try:
            lowered = compiler_effects([compiler_effect(effect)])[0]
            validate_effect(lowered, combat={}, world_frame=True)
        except (ValueError, KeyError, TypeError) as error:
            result.append(dict(index=index, owner=item['owner'], name=effect.get('name'),
                               issue=issue(error, effect)))
    return result


def summarize(rows):
    groups = defaultdict(lambda: dict(profiles=set(), definitions=0, sole=set(), sample=None, messages=set()))
    for row in rows:
        blockers=row.get('effect_blockers', [])
        if not blockers and row.get('program_issue'):blockers=[dict(issue=row['program_issue'])]
        codes = {entry['issue']['code'] for entry in blockers}
        for entry in blockers:
            i = entry['issue']; group = groups[i['code']]
            identity = (row['character'], row['favorite_stage'])
            group['profiles'].add(identity); group['definitions'] += 1
            group['messages'].add(i['message'])
            if group['sample'] is None or i['message'] < group['sample']['message']:group['sample'] = i
            if len(codes) == 1: group['sole'].add(identity)
    ranked = [dict(issue=g['sample'], messages=sorted(g['messages']), affected_profiles=len(g['profiles']),
                   blocked_definitions=g['definitions'],
                   single_observed_category_profiles=len(g['sole'])) for g in groups.values()]
    return sorted(ranked, key=lambda r:(-r['single_observed_category_profiles'], -r['affected_profiles'], r['issue']['code']))
