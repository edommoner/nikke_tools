"""Periodic instants sample their detached target context at execution time."""
from enemy_recipient_specs import EnemySelector

AIM_COMMAND=17
TARGET_CONDITIONS=frozenset((16,17,23,42,43))


def periodic_instant(row):return row[258]==1 and row[59]>0


def required_aim_owners(rows,has_add_sources):
    if type(has_add_sources) is not bool:raise ValueError('Periodic aim validation requires a proven source flag')
    if any(periodic_instant(r) and not 0<=r[0]<5 for r in rows):raise ValueError('Periodic instants require a squad owner')
    if not has_add_sources:return set()
    return {int(r[0]) for r in rows if periodic_instant(r) and (
        r[4]==4 and r[48]==EnemySelector.CURRENT or any(r[15+j*3] in TARGET_CONDITIONS for j in range(int(r[14]))))}
