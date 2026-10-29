"""One sampled pellet and owning frame for moving logical and typed geometry.

The explicit attachment model translates shapes only while the exact declared
ADD owner generation is live. It changes physical visibility, never target HP,
ownership, a clock, hit routing, or a stale generation into a new one.
"""
import copy,math
from contextlib import contextmanager
from unittest.mock import patch
from impact_specs import ActorKind
from enemy_movement_model import enemy_movement_runtime
from coordinate_logical_actor_geometry import logical_actor_geometry
from world_actor_runtime import registry_for

MODE='visible-with-moving-owner-v1'

def normalize(spec,movement):
    if type(spec) is not dict or set(spec)!={'mode','bindings'} or spec['mode']!=MODE or type(spec['bindings']) is not list or not spec['bindings']:
        raise ValueError('Explicit moving-owner visibility and attachment declarations required')
    actors={r['label'] for r in movement['actors']};seen=set();rows=[]
    for row in spec['bindings']:
        if type(row) is not dict or set(row)!={'typed_label','actor_label'} or any(type(v) is not str or not v for v in row.values()):raise ValueError('Explicit typed label and configured moving actor required')
        if row['typed_label'] in seen or row['actor_label'] not in actors:raise ValueError('Ambiguous typed attachment or unknown moving actor')
        seen.add(row['typed_label']);rows.append(dict(row))
    return dict(mode=MODE,bindings=rows)

class MovingTypedGeometry:
    def __init__(self,motion,spec):
        self.motion=motion;self.spec=normalize(spec,motion.spec);self.links={r['typed_label']:r['actor_label'] for r in self.spec['bindings']}
        self.data=dict(policy=copy.deepcopy(self.spec),queries=[])

    def validate_world(self,world):
        labels={b.label for b in world.bindings}
        if set(self.links)-labels:raise ValueError('Attachment must name an actual typed binding')
        logical=self.motion.geometry
        if logical is None or logical.boss is not world.clock:raise ValueError('Typed attachment must share the logical owner clock')
        for b in world.bindings:
            label=self.links.get(b.label)
            if label is None:
                if b.owner is not None and b.owner.kind==ActorKind.ADD:raise ValueError('Every ADD-owned typed binding needs an explicit attachment')
                continue
            owner=logical.bindings[label]
            if b.owner is None or b.owner.kind!=ActorKind.ADD or b.owner.identity!=owner.identity:raise ValueError('Attachment cannot replace the typed binding owner')

    def position(self,world,slot,shape):
        binding=world.bindings[slot];label=self.links.get(binding.label)
        if label is None:return shape
        motion=self.motion
        if motion.last_time!=world.last or motion.manager is None:raise ValueError('Movement must precede typed geometry capture')
        state=motion.states.get(label);owner=binding.owner;visible=False;result=None;current=None
        if state is not None:
            current=registry_for(motion.manager,world.clock).view(ActorKind.ADD,label)
            if current.handle!=state['handle']:raise ValueError('Movement and actor pool generations differ')
            visible=current.alive and current.handle==owner
            if visible:
                initial=motion.initial[label];result=dict(shape)
                result['x']=shape['x']+(state['position'][0]-initial['x'])
                result['y']=shape['y']+(state['position'][1]-initial['y'])
                if not math.isfinite(result['x']) or not math.isfinite(result['y']):raise ValueError('Typed attachment coordinate overflow')
        if len(self.data['queries'])>=262144:raise ValueError('Attachment observation capacity exceeded')
        self.data['queries'].append(dict(time=world.last,typed_slot=slot,typed_label=binding.label,owner=[int(owner.kind),owner.identity,owner.generation],
            observed_owner=None if current is None else [int(current.handle.kind),current.handle.identity,current.handle.generation],
            observed_owner_alive=False if current is None else current.alive,visible=bool(visible),position=None if result is None else [result['x'],result['y']]))
        return result

@contextmanager
def moving_typed_geometry(logical_spec,movement_spec,attachment_spec):
    import coordinate_typed_geometry_runtime as geometry
    from coordinate_typed_aim_runtime import TypedCoordinateAim
    from coordinate_typed_weapon_runtime import CoordinateWeaponShots
    from calculator import aim,boss_pattern
    live_rows=geometry.live_rows;capture=TypedCoordinateAim.capture;take=CoordinateWeaponShots.take
    with enemy_movement_runtime(movement_spec) as motion,logical_actor_geometry(logical_spec,typed_weapon_union=True) as logical:
        runtime=MovingTypedGeometry(motion,attachment_spec)
        def frame(aim_runtime,boss,t,enemy):
            if not aim_runtime.data['managers']:raise ValueError('Typed movement needs its registered owning manager')
            motion.advance(aim_runtime.data['managers'][-1],boss,t)
            return capture(aim_runtime,boss,t,enemy)
        def rows(world,geom,spec):
            runtime.validate_world(world)
            original,typed,base=live_rows(world,geom,spec)
            own=motion.geometry.shared_rows(motion.manager,base,world.last)
            out=[row for row in original if id(row[1]) not in typed] if own is None else list(own)
            selected={}
            for rank,g in original:
                item=typed.get(id(g))
                if item is None:continue
                slot,handle=item;shape={k:getattr(g.shape,k) for k in ('x','y','r','w','h','rot')}
                shape=runtime.position(world,slot,shape)
                if shape is None:continue
                target=boss_pattern.GeomTarget(g.name,g.kind,aim.Shape(**shape))
                out.append((rank,target));selected[id(target)]=(slot,handle)
            out.sort(key=lambda row:row[0],reverse=True)
            return out,selected,base
        def packet(shots,event):
            context=take(shots,event)
            if context is None and shots.frames:
                shot=shots.frames[-1]['shot']
                if shot['world'].clock is not motion.boss:raise ValueError('Logical packet cannot change its typed clock')
                motion.geometry.shared_packet(event,shot['manager'])
            return context
        # Aim imports live_rows by value; physical snapshots import it on use.
        import coordinate_typed_aim_runtime as aim_runtime
        with patch.object(geometry,'live_rows',rows),patch.object(aim_runtime,'live_rows',rows),patch.object(TypedCoordinateAim,'capture',frame),patch.object(CoordinateWeaponShots,'take',packet):
            yield dict(movement=motion.data,logical_geometry=logical,typed_attachments=runtime.data)
