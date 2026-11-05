"""Complete original Heavyarms profiles; no removed lock/projectile definitions."""
import copy
from portable_heavyarms_lock_cases import fixtures as original

def fixtures():
    rows=copy.deepcopy(original())
    for case in rows:case['name']=case['name'].replace('heavyarms-lock-marker/','heavyarms-target-count-query/')
    return rows
