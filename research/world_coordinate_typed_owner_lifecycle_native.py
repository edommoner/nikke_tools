"""Passive ownership-query lifetime observation; no new simulation engine."""
from unittest.mock import patch
from coordinate_typed_owner_runtime import OwnerQueries,TYPED
from portable_coordinate_typed_owner_lifecycle_cases import prepare
from world_coordinate_typed_owner_native import observe as original

def observe(row):
    c=row if 'original_run' in row else prepare(row)[0];seen=[];project=OwnerQueries.project
    def query(self,actor,role):
        if actor.kind in TYPED:
            world=self.data['worlds'][-1];snap=world.registry.exact(actor)
            seen.append(dict(time=world.last,physical=[int(actor.kind),actor.identity,actor.generation],alive=snap.alive,role=role))
        return project(self,actor,role)
    with patch.object(OwnerQueries,'project',query):native,trace=original(c)
    native['owner_query_lifetimes']=seen
    return native,trace
