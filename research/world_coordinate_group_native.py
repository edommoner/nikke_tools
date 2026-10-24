"""Real expanded shot identities and receipt-owned groups in common-policy CPU.

This scope adds only group boundary/identity, with canonical landing and existing
BODY/ADD collector deciding membership. It does not recompute packet damage.
"""
from battle_attack_group_runtime import battle_attack_groups
from world_coordinate_physical_common import observe as physical


def observe(case):
    with battle_attack_groups(routing='native',coordinate_packets=True) as data:
        native=physical(case)
    handle=lambda h:[int(h.kind),h.identity,h.generation]
    groups=[dict(row,targets=[handle(h) for h in row['targets']]) for row in data['groups']]
    notices=[dict(row,key=[row['key'].caster,row['key'].identity,row['key'].epoch],targets=[handle(h) for h in row['targets']]) for row in data['notifications']]
    receipts=[dict(row,target=handle(row['target'])) for row in data['physical_receipts']]
    children=[dict(row,targets=[handle(h) for h in row['targets']]) for row in data['children']]
    child_landings=[dict(row,target=handle(row['target'])) for row in data['child_landings']]
    trace=native.pop('skill_trace')
    native.update(groups=groups,group_shots=data['shots'],group_notices=notices,group_receipts=receipts,group_children=children,group_child_landings=child_landings)
    return native,trace
