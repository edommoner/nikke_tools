"""Product connection to the existing common movement/coordinate executor."""
import copy,math,struct
from portable_runtime import UnsupportedPortable
from portable_enemy_movement_wire import INPUT,OUTPUT,OUT,STATE,STATE_WORDS,FRAMES,FRAME_WORDS,SEGMENTS,SEGMENT_WORDS,END,CAPACITY,MAGIC


def required(prepared):
    return 'enemy_movement' in prepared.get('reference_models',{}) or any(r['effect'].get('stat') in ('enemy_movement_disable','force_move') for r in prepared['effects'])


def compile_product(prepared):
    from portable_enemy_movement_wire import compile_battle,check_schema
    from calculator.boss_pattern import validate
    from calculator.timeline import CharState,_when_label
    declarations=copy.deepcopy(prepared.get('reference_models',{}))
    if set(declarations)!={'enemy_movement'}:
        error=UnsupportedPortable('Movement requires explicit reference_models.enemy_movement geometry and policies; composition is not connected')
        for row in prepared['effects']:
            e=row['effect']
            if e.get('stat') in ('enemy_movement_disable','force_move'):
                error.effect_context=dict(character=row['owner'],effect=e.get('name',''),stat=e['stat'],target=e.get('target',''))
                break
        raise error
    if prepared['policies']['config'].get('burst_gauge_mode')!='accumulate':
        raise UnsupportedPortable('Movement with fixed burst requires a combined coordinate product control header')
    if any(a.get('action')=='cover' for c in prepared['chars'] for a in c.get('control',{}).get('sequence',[])):
        raise UnsupportedPortable('Movement with manual cover requires the combined coordinate control consumer')
    spec=declarations['enemy_movement'];check_schema()
    words,meta,bindings,scene=compile_battle(dict(prepared,_product_native_equipment_carriers=True),spec['logical_geometry'],spec['motion'])
    meta['product_enemy_movement']=dict(declarations=declarations,bindings=[dict(kind=int(b.kind),identity=b.identity,label=b.label,run=b.run) for b in bindings],cpu_state_or_schedule_supplied=False)
    meta['product_control_labels']=[
        [dict(mode=e['mode'],producer=_when_label(e)) for e in CharState(c,atk,prepared['enemy'].get('code'))._click_sched]
        for c,atk in zip(prepared['chars'],prepared['base_atk'])]
    nodes=validate(copy.deepcopy(prepared['enemy'].get('patterns') or []),coord=True)
    meta['product_world']=dict(nodes=[dict(id=p.id,kind=p.kind) for p in nodes],literal_pattern_identity_only=True,cpu_schedule_or_state_supplied=False)
    return 'gpu/product_movement_battle_entry.slang',INPUT,OUTPUT,words,meta


def read_result(block,meta,duration):
    """Decode every movement word; reject gaps, reserved data or partial history."""
    def fail():raise UnsupportedPortable('Invalid or incomplete product movement history')
    if len(block)!=OUTPUT or block[0]!=0:fail()
    n,m=block[OUT+1:OUT+3]
    if block[OUT]!=MAGIC or n>CAPACITY or m>CAPACITY:fail()
    info=meta['product_enemy_movement'];spec=info['declarations']['enemy_movement']
    bindings=info['bindings'];labels={r['label'] for r in spec['motion']['actors']}
    canonical=[0]*(END-OUT);canonical[:3]=[MAGIC,n,m]
    def num(at):
        x=struct.unpack('<d',struct.pack('<II',*block[OUT+at:OUT+at+2]))[0]
        if not math.isfinite(x):fail()
        canonical[at:at+2]=block[OUT+at:OUT+at+2];return x
    frames=[];generations=[];last={};cursor=0;previous=0.
    for i in range(n):
        at=FRAMES+i*FRAME_WORDS;slot,gen,alive,first,count=block[OUT+at:OUT+at+5]
        if not 0<slot<len(bindings) or bindings[slot]['kind']!=5 or bindings[slot]['label'] not in labels or gen==0 or alive not in (0,1) or first!=cursor or cursor+count>m:fail()
        canonical[at:at+5]=[slot,gen,alive,first,count]
        time=num(at+6);position=[num(at+8),num(at+10)]
        if not previous<=time<=duration:fail()
        previous=time;binding=bindings[slot];actor=[5,binding['identity'],gen];prior=last.get(slot)
        if prior is None or prior['actor']!=actor:
            if count or prior is not None and gen<=prior['actor'][2]:fail()
            generations.append(dict(label=binding['label'],actor=actor,time=time,position=list(position)))
            left=time;before=position
        else:
            if time<=prior['time']:fail()
            left=prior['time'];before=prior['position']
        segments=[]
        for j in range(count):
            out=SEGMENTS+cursor*SEGMENT_WORDS;cursor+=1
            s,g,flags=block[OUT+out:OUT+out+3]
            if (s,g)!=(slot,gen) or flags>3:fail()
            canonical[out:out+3]=[s,g,flags]
            start,end=num(out+4),num(out+6);origin=[num(out+8),num(out+10)];after=[num(out+12),num(out+14)]
            if not alive or start!=left or not start<end<=time or origin!=before:fail()
            segments.append(dict(start=start,end=end,disabled=bool(flags&1),forced=bool(flags&2),before=origin,after=after))
            left=end;before=after
        if before!=position or alive and left!=time:fail()
        frame=dict(time=time,label=binding['label'],actor=actor,alive=bool(alive),position=position,segments=segments)
        frames.append(frame);last[slot]=frame
    if cursor!=m:fail()
    for slot,frame in last.items():
        at=STATE+slot*STATE_WORDS;canonical[at:at+2]=[frame['actor'][2],int(frame['alive'])];canonical[at+8]=1
        for offset,value in ((2,frame['time']),(4,frame['position'][0]),(6,frame['position'][1])):
            canonical[at+offset:at+offset+2]=struct.unpack('<II',struct.pack('<d',value))
    if list(block[OUT:END])!=canonical:fail()
    data=dict(model='declared-add-motion-v1',policies={k:spec['motion'][k] for k in ('precedence','force_policy','recipient_policy')},generations=generations,frames=frames)
    return dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(info['declarations']),enemy_movement=data)
