"""World predicates read the sampled frame, not a mutable live-target scan.

Thresholds are inclusive, following the authored above/below contract. Physical
parts do not increase the logical enemy count. Finite effects latch activation;
permanent effects use the existing runtime-condition lifecycle.
"""
import re
from impact_specs import ActorKind,TARGET_EVENT_PREFIXES

ENEMY_COUNT_ABOVE = 40
ENEMY_COUNT_BELOW = 41
TARGET_IS_BOSS = 42
TARGET_IS_ADD = 43


def count_condition(condition):
    match = re.fullmatch(r'enemy_count_(above|below):([+-]?[0-9]+)', condition)
    if not match:
        raise ValueError('Enemy-count condition requires an integer threshold')
    threshold = int(match[2])
    if abs(threshold) > 2**31 - 1:
        raise ValueError('Enemy-count threshold exceeds the supported integer range')
    return (ENEMY_COUNT_ABOVE if match[1] == 'above' else ENEMY_COUNT_BELOW), threshold


def specialize_static_counts(rows, *, has_add_sources):
    """Fold only when the validated world cannot change the logical count.

    This uses configured source kinds, never the currently live population:
    a delayed wave must keep its dynamic predicates even while no adds exist.
    The existing constant predicate preserves finite/persistent lifecycle flags.
    """
    if type(has_add_sources) is not bool:
        raise ValueError('Static-count specialization requires a proven source flag')
    if has_add_sources:
        return 0
    folded = 0
    for row in rows:
        for j in range(int(row[14])):
            at = 15 + j*3
            kind,_,threshold = row[at:at+3]
            if kind in (ENEMY_COUNT_ABOVE,ENEMY_COUNT_BELOW):
                row[at:at+3] = [22,0,int(1>=threshold if kind==ENEMY_COUNT_ABOVE else 1<=threshold)]
                folded += 1
            elif kind in (TARGET_IS_BOSS,TARGET_IS_ADD):
                row[at:at+3] = [25,0,int(kind==TARGET_IS_BOSS)]
                folded += 1
    return folded


def validate_target_predicate_policies(rows):
    observed=any(row[15+j*3] in (TARGET_IS_BOSS,TARGET_IS_ADD) for row in rows for j in range(int(row[14])))
    if observed and any(row[1]==0 and row[2]==87 and row[296] not in (int(ActorKind.BODY),int(ActorKind.PART),int(ActorKind.ADD)) for row in rows):
        raise ValueError('Logical target predicates for projectile/shield counters require an explicit actor policy')


def target_inheritance_events():
    return [code for _,code in TARGET_EVENT_PREFIXES]+[47,55,56,57,61]




BEGIN = '// BEGIN GENERATED WORLD CONDITIONS\n'
END = '// END GENERATED WORLD CONDITIONS\n'
