"""Declared physical projectile/HP-shield model around existing CPU consumers."""
import copy
from contextlib import contextmanager
from product_coordinate_model import normalize as coordinate_spec
from coordinate_typed_aim_runtime import normalize as aim_spec
from coordinate_typed_actor_policy import normalize as actor_spec,validate_bindings,FIELD_MODE
from portable_typed_geometry_specs import normalize as geometry_spec


def normalize_product(value):
    required={'coord','bindings','geometry','aim_policy','actor_policy'}
    if type(value) is not dict or set(value)!=required:raise ValueError('Typed targets require explicit coord, bindings, geometry, aim and actor policies')
    spec=copy.deepcopy(value);coordinate=coordinate_spec(spec['coord'],[],allow_empty=True);spec['coord']=coordinate['coord']
    aim_spec(spec['aim_policy']);actor_spec(spec['actor_policy'])
    if spec['actor_policy']!={'mode':FIELD_MODE}:raise ValueError('Product typed targets require declared BODY-owned current fields')
    rows=spec['bindings']
    if type(rows) is not list or not 1<=len(rows)<=128:raise ValueError('One to128 typed bindings required')
    from destructible_target_state import DestructibleTargets
    from impact_specs import ActorHandle
    targets=DestructibleTargets(len(rows));labels=set();kinds=set()
    for i,row in enumerate(rows):
        if type(row) is not dict or set(row)!={'node','kind','identity','capacity','owner','label'}:raise ValueError('Complete literal typed binding required')
        if type(row['kind']) is not int or row['kind'] not in (2,3):raise ValueError('Product typed target kind must be projectile or HP shield')
        if type(row['node']) is not str or not row['node'] or type(row['label']) is not str or not row['label'] or row['label'] in labels or row['label'].startswith('__enemy__') or row['label']=='core':raise ValueError('Distinct typed labels and source nodes required')
        labels.add(row['label']);kinds.add(row['kind']);targets.spawn(i,ActorHandle(row['kind'],row['identity']),row['capacity'],owner=ActorHandle(*row['owner']))
    validate_bindings(spec['actor_policy'],rows)
    if len(kinds)!=1:raise ValueError('Mixed projectile/shield geometry requires a combined checked typed consumer')
    geometry_spec(spec['geometry'],len(rows),next(iter(kinds)))
    if spec['geometry'].get('point_source')!='caster_aim' or spec['geometry'].get('grow',0)!=0:raise ValueError('Typed product weapons require declared live caster aim and zero authored growth')
    return spec


def public_from_words(spec,state,rows,names,duration):
    """One public format for native receipts and shared GPU readback."""
    import struct,hashlib,array
    def number(row,at):return struct.unpack('<d',struct.pack('<II',*row[at:at+2]))[0]
    packets=[]
    for row in rows:
        packets.append(dict(attack_id=row[0],owner=names[row[1]],actor=row[2:5],slot=row[5],time=number(row,6),coefficient=number(row,8),damage=number(row,10),took=number(row,12),delivered=bool(row[14]),broken=bool(row[15]),family=row[16],extra=bool(row[17]),critical=bool(row[18]),mode_skill=bool(row[19]),shot_identity=row[20],pellet=row[21]))
    raw=array.array('I',(word for row in rows for word in row))
    if __import__('sys').byteorder!='little':raw.byteswap()
    return dict(policy='declared-typed-before-body-v1',time=duration,finished=True,state=copy.deepcopy(state),packet_count=len(rows),packet_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),weapon_packets=packets,in_game_rules_verified=False)


def native_public(spec,data,names,duration):
    import struct
    def bits(v):return list(struct.unpack('<II',struct.pack('<d',v)))
    if len(data['worlds'])!=1 or len(data['managers'])!=1 :raise ValueError('Typed product requires one original weapon world; original skill routing needs its own checked consumer')
    world=data['worlds'][0]
    if not world.finished or world.last!=duration:raise ValueError('Typed product world did not finish')
    state=[]
    for target in world.targets.rows:
        state.append(None if target is None else dict(handle=[int(target.handle.kind),target.handle.identity,target.handle.generation],alive=target.alive,remaining=target.remaining,capacity=target.capacity,expires=target.expires,owner=None if target.owner is None else [int(target.owner.kind),target.owner.identity,target.owner.generation]))
    rows=[]
    for a in data['coordinate_weapon_attacks']:
        if len(a['receipts'])!=1 or not a['completed']:raise ValueError('Incomplete physical typed receipt')
        slot,handle,receipt=a['receipts'][0];tag=a['hit_tag'];pellet=int(tag.rsplit(':',1)[1]) if 'pellet:' in tag else 0
        rows.append([a['attack_id'],names.index(a['caster']),int(handle.kind),handle.identity,handle.generation,slot,*bits(a['time']),*bits(a['coefficient']),*bits(a['damage']),*bits(receipt['took']),int(receipt['delivered']),int(receipt['broken']),a['family'],int(a['extra']),int(a['critical']),int(a['weapon_mode_skill']),a['shot_identity'],pellet,0,0])
    result=public_from_words(spec,state,rows,names,duration);result['shot_count']=len(data['coordinate_weapon_shots'])
    result['aim_state']=aim_public(spec,data['coordinate_typed_aim_frames'])
    result['skill_attacks']=[dict(attack_id=a['attack_id'],owner=a['caster'],name=a['name'],time=a['time'],damage=a['damage'],completed=a['completed'],receipts=[dict(slot=slot,actor=[int(handle.kind),handle.identity,handle.generation],**receipt) for slot,handle,receipt in a['receipts']]) for a in data['attacks']]
    return result


@contextmanager
def execution(spec,names,*,runtime=None):
    from product_coordinate_model import execution as coordinates
    from destructible_battle_runtime import typed_battle
    from runner import sim
    from unittest.mock import patch
    result={};duration=[];original=None
    def run(value,*args,**kwargs):
        duration.append(value.config['duration']);return original(value,*args,**kwargs)
    with coordinates(dict(coord=spec['coord'],logical_geometry=[]),configure_run=True,typed_packets=True),typed_battle(spec['bindings'],modifier_model=True,typed_geometry=spec['geometry'],coordinate_weapon_targets=True,typed_aim_policy=spec['aim_policy'],typed_actor_policy=spec['actor_policy']) as data:
        original=sim.execute
        if runtime is not None:
            if type(runtime) is not dict or runtime:raise ValueError('Fresh internal typed runtime holder required')
            runtime.update(data=data,bindings=copy.deepcopy(spec['bindings']),active=True)
        try:
            with patch.object(sim,'execute',run):yield result
        finally:
            if runtime is not None:runtime['active']=False
    if len(duration)!=1:raise ValueError('One original typed product battle required')
    result.update(native_public(spec,data,names,duration[0]))


def aim_public(spec,frames):
    """Existing frame fingerprint and exact final candidates, not a new aim rule."""
    import struct
    if not frames:raise ValueError('Typed aim frame stream missing')
    slots={b['label']:129+i for i,b in enumerate(spec['bindings'])};a=0xcbf29ce484222325;b=0x84222325cbf29ce4;mask=(1<<64)-1
    for frame in frames:
        rows=[[slots[c['label']],c['handle'][2],c['key'][2],c['handle'][1]] for c in frame['candidates']]
        values=[*struct.unpack('<II',struct.pack('<d',frame['time'])),len(rows),int(frame['canonical_has_adds']),*(word for row in rows for word in row)]
        for word in values:a=((a^word)*0x100000001b3)&mask;b=(((b<<7)|(b>>57))^(word*0x9e3779b185ebca87))&mask
    last=frames[-1]
    return dict(frames=len(frames),time=last['time'],candidate=slots[last['candidate']] if last['candidate'] else 0,canonical_has_adds=bool(last['canonical_has_adds']),rows=rows,stream_fingerprints=[format(a,'016x'),format(b,'016x')])
