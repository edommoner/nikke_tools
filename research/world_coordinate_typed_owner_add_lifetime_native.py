"""Passive actor visibility witnesses at the existing world frame boundary."""
from unittest.mock import patch
from coordinate_typed_owner_runtime import OwnerQueries,TYPED
from destructible_world_runtime import DestructibleWorld
from portable_coordinate_typed_owner_add_lifetime_cases import prepare
from world_coordinate_typed_owner_native import observe as original

def observe(row):
    c=row if 'original_run' in row else prepare(row)[0];data={};owners=[];visibility=[];last={}
    project=OwnerQueries.project;synchronize=DestructibleWorld.synchronize
    def query(self,actor,role):
        owner=project(self,actor,role)
        if actor.kind in TYPED:
            data['value']=self.data;w=self.data['worlds'][-1];snap=w.registry.exact(owner)
            owners.append(dict(time=w.last,owner=[int(owner.kind),owner.identity,owner.generation],alive=snap.alive,role=role))
        return owner
    def sync(world,t,**kwargs):
        result=synchronize(world,t,**kwargs)
        if 'value' not in data or world not in data['value']['worlds']:return result
        from enemy_recipient_runtime import snapshot,visible
        for manager in data['value']['managers']:
            for carrier in manager._active:
                if carrier.effect.get('name')!='typed-owner-audit-field':continue
                key=getattr(carrier,'enemy_recipient_key',None)
                if key is None:raise ValueError('Owned field lost its immutable recipient key')
                for binding in key.bindings:
                    current=snapshot(manager,binding.label);shown=visible(manager,carrier,binding.label)
                    stamp=(current.handle,current.alive,shown)
                    if last.get(carrier.uid)==stamp:continue
                    last[carrier.uid]=stamp
                    visibility.append(dict(time=float(t),field_actor=[int(binding.actor.kind),binding.actor.identity,binding.actor.generation],current_actor=[int(current.handle.kind),current.handle.identity,current.handle.generation],current_alive=current.alive,visible=shown))
        return result
    with patch.object(OwnerQueries,'project',query),patch.object(DestructibleWorld,'synchronize',sync):native,trace=original(c)
    native['owner_add_lifetime']=dict(owner_queries=owners,field_visibility_transitions=visibility)
    return native,trace
