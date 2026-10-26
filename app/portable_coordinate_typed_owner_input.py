"""Private explicit-owner extension of the logical counter predicate validator."""
from contextlib import contextmanager
from unittest.mock import patch
from coordinate_typed_actor_policy import FIELD_MODE,validate_bindings

@contextmanager
def compiler_policy(bindings,policy=None):
    import detail_gpu
    policy={'mode':FIELD_MODE} if policy is None else policy
    validate_bindings(policy,bindings)
    allowed={(b['kind'],b['identity']):b['owner'] for b in bindings};original=detail_gpu.validate_target_predicate_policies
    def validate(rows):
        # Only this logical-policy validation view projects declared typed
        # counters to BODY. The compiled rows and physical handles never change.
        projected=[]
        for row in rows:
            view=row
            if row[1]==0 and row[2]==87 and row[296] in (2,3,4):
                if (row[296],row[297]) not in allowed:raise ValueError('Typed counter predicate requires a declared BODY-owned actor')
                view=list(row);view[296:299]=allowed[row[296],row[297]]
            projected.append(view)
        return original(projected)
    with patch.object(detail_gpu,'validate_target_predicate_policies',validate):yield
