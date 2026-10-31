"""Literal product lock binding to the existing shared original/typed executor."""
import copy,struct
from pathlib import Path
from types import SimpleNamespace
from portable_runtime import UnsupportedPortable
from portable_lock_typed_layout import INPUT,OUTPUT
from product_lock_model import normalize,validate_effects

SOURCE='gpu/product_lock_battle_entry.slang'


def required(prepared):
    return 'lock_on' in prepared.get('reference_models',{}) or any(r['effect'].get('stat')=='lock_on' for r in prepared['effects'])


def compile_product(prepared):
    from portable_projectile_roster_input import compile_projectile_battle
    from portable_effect_target_count_shot_specs import compile_case as pack_count
    from effect_target_count_policy import MODEL
    from portable_charge_clock_specs import normalize_static_clock
    from calculator.timeline import CharState,_when_label
    from calculator.boss_pattern import validate
    from portable_actor_specs import compile_registry
    from destructible_world_runtime import compile_bindings
    from portable_original_lock_layout import check
    from portable_lock_typed_layout import check as check_locks
    declarations=copy.deepcopy(prepared.get('reference_models',{}))
    if set(declarations)!={'lock_on'}:
        error=UnsupportedPortable('Lock On requires explicit reference_models.lock_on candidate/delivery policies and typed bindings; composition is not connected')
        for r in prepared['effects']:
            e=r['effect']
            if e.get('stat')=='lock_on':error.effect_context=dict(character=r['owner'],effect=e.get('name',''),stat='lock_on',target=e.get('target',''));break
        raise error
    if prepared['policies']['config'].get('burst_gauge_mode')!='accumulate':raise UnsupportedPortable('Lock On with fixed burst requires the combined fixed product header')
    if prepared['enemy'].get('coord') is not None:raise UnsupportedPortable('Coordinate Lock On needs a combined declared coordinate consumer')
    spec=normalize(declarations['lock_on']);effects=[r['effect'] for r in prepared['effects']];owners=[r['owner'] for r in prepared['effects']]
    pulse,packet,typed=validate_effects(effects,owners,spec)
    names=[c['name'] for c in prepared['chars']]
    patterns=copy.deepcopy(prepared['enemy'].get('patterns') or [dict(id='portable-empty-world',kind='idle')])
    parsed=validate(copy.deepcopy(patterns));_,bindings=compile_registry(parsed,pools=True)
    typed_rows=compile_bindings([dict(id=p['id']) for p in patterns],spec['typed_bindings'])[2] if spec['typed_bindings'] else ()
    root=Path(__file__).resolve().parents[1];check(root);check_locks(root)
    case=dict(names=names,base_atk=prepared['base_atk'],effects=copy.deepcopy(effects),owners=[names.index(n) for n in owners],
        skill_levels=[c['skill_levels'] for c in prepared['chars']],enemy=prepared['enemy'],
        post_fire_delays=normalize_static_clock(prepared['chars'],prepared['base_atk'],prepared['enemy']),original_run=dict(prepared=prepared))
    case['effects'][pulse]=dict(case['effects'][pulse],stat='')
    def world(c):
        lowered=copy.deepcopy(prepared)
        lowered['effects']=[dict(effect=copy.deepcopy(e),owner=names[o]) for e,o in zip(c['effects'],c['owners'],strict=True)]
        lowered['effects'][typed]['effect']['target']='boss'
        lowered['_product_native_equipment_carriers']=True
        if any(a.get('action')=='cover' for ch in prepared['chars'] for a in ch.get('control',{}).get('sequence',[])):lowered['_product_manual_cover']=True
        words,meta=compile_projectile_battle(lowered,trace='full')
        return words,meta,bindings
    words,meta,bindings=pack_count(SimpleNamespace(compile_case=world),case,model=MODEL)
    pulse_rows=[i for i,source in enumerate(meta['binding_source_indices']) if source==pulse]
    typed_bound=[i for i,source in enumerate(meta['binding_source_indices']) if source==typed]
    if len(pulse_rows)!=1 or len(typed_bound)!=1:raise UnsupportedPortable('Unique statically bound original lock/projectile rows required')
    meta['physical_lock_pulse_row']=pulse_rows[0]
    extra=[0]*5136;extra[2320]=len(typed_rows)
    for i,r in enumerate(typed_rows):
        at=2328+i*12;owner=[0xffffffff,0,0] if r.owner is None else [int(r.owner.kind),r.owner.identity,r.owner.generation]
        extra[at:at+8]=[r.node,int(r.handle.kind),r.handle.identity,*struct.unpack('<II',struct.pack('<d',r.capacity)),*owner]
    extra[5120:5124]=[typed_bound[0],128,1,0x44425431];words.extend(extra)
    if len(words)!=INPUT or set(meta['binding_source_indices'])!=set(range(len(effects))):raise UnsupportedPortable('Complete original Lock On definitions and wire required')
    meta['product_lock_on']=dict(declarations=declarations,names=names,packet_source=packet,typed_source=typed,
        bindings=[dict(kind=int(b.kind),identity=b.identity,label=b.label,run=b.run) for b in bindings],
        typed_case=dict(names=names,effects=copy.deepcopy(effects),owners=[names.index(n) for n in owners],skill_levels=[c['skill_levels'] for c in prepared['chars']],typed_bindings=spec['typed_bindings'],max_attacks=128),cpu_state_or_schedule_supplied=False)
    meta['product_control_labels']=[[dict(mode=e['mode'],producer=_when_label(e)) for e in CharState(c,atk,prepared['enemy'].get('code'))._click_sched] for c,atk in zip(prepared['chars'],prepared['base_atk'])]
    meta['product_world']=dict(nodes=[dict(id=p.id,kind=p.kind) for p in parsed],literal_pattern_identity_only=True,cpu_schedule_or_state_supplied=False)
    return SOURCE,INPUT,OUTPUT,words,meta


def read_result(block,meta,duration):
    """Read full lock/typed histories from GPU counts, without a CPU oracle."""
    import math
    from portable_specs import LIMITS as L
    import portable_physical_lock_layout as physical
    import portable_lock_packet_layout as packet
    import portable_original_lock_layout as banks
    import portable_packet_fates as fates
    from portable_lock_typed_layout import OFFSET,LOCK_END
    from portable_effect_target_count_shot_specs import HEAD as QUOTA_HEAD,decode as quotas
    def fail():raise UnsupportedPortable('Invalid or incomplete product Lock On history')
    if len(block)!=OUTPUT or block[0]!=0:fail()
    info=meta['product_lock_on'];bindings=info['bindings'];spec=info['declarations']['lock_on']
    owner=info['names'].index(spec['owner'])
    def number(at):
        value=struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
        if not math.isfinite(value):fail()
        return value
    def time(at):
        value=number(at)
        if not 0<=value<=duration:fail()
        return value
    def bank(start,width,count,capacity):
        if count>capacity or any(block[start+count*width:start+capacity*width]):fail()
        return [list(block[start+i*width:start+(i+1)*width]) for i in range(count)]
    h=physical.HEAD+OFFSET;header=list(block[h:h+16]);n,shots,clears=header[1:4]
    if header!=[0x504c3031,n,shots,clears,owner,meta['physical_lock_pulse_row']]+[0]*10 or shots>physical.SHOT_CAPACITY or clears>0x7fffffff:fail()
    rows=bank(banks.PULSES,16,n,banks.PULSE_CAPACITY);pulses=[];previous=0.;revision=0
    for i,row in enumerate(rows):
        capacity,count,rev,kind,identity,generation,removed,magic=row[:8]
        when=time(banks.PULSES+i*16+8)
        if (capacity>128 or count>128 or not revision<=rev<=0x7fffffff or removed>128 or magic!=0x474c3031
            or when<previous or any(row[10:]) or kind not in (0,5,0xffffffff)):fail()
        if kind==0xffffffff:
            if identity or generation:fail()
        elif generation==0 or not any(b['kind']==kind and b['identity']==identity for b in bindings):fail()
        pulses.append(dict(time=when,receipt=row[:8]));previous=when;revision=rev
    # Extended banks own all rows. Old bank words must remain empty.
    if any(block[physical.PULSES+OFFSET:physical.CANDIDATE+OFFSET]):fail()
    def actor_set(at,*,candidate=False):
        raw=list(block[at:at+physical.SET_WORDS]);count=raw[0]
        if count>128 or raw[5]!=int(candidate) or raw[6]!=(0 if candidate else 0x474c3031) or raw[7]>0x7fffffff:fail()
        if candidate and raw[7]:fail()
        mask=[0]*4;handles=[];seen=set()
        for i in range(count):
            slot,gen,kind,identity=raw[8+i*4:12+i*4]
            if slot>=len(bindings) or slot>=128 or slot in seen or gen==0 or kind not in (0,5) or (kind,identity)!=(bindings[slot]['kind'],bindings[slot]['identity']):fail()
            seen.add(slot);mask[slot//32]|=1<<(slot%32);handles.append([kind,identity,gen])
        if raw[1:5]!=mask or any(raw[8+count*4:]):fail()
        return raw[7],handles
    candidate=physical.CANDIDATE+OFFSET
    if n:actor_set(candidate,candidate=True)
    elif any(block[candidate:candidate+physical.SET_WORDS]):fail()
    snapshots=[];previous=0.;revision=0
    for i in range(shots):
        rev,handles=actor_set(physical.SNAPSHOTS+OFFSET+i*physical.SET_WORDS)
        when=time(packet.SHOT_TIMES+OFFSET+i*2)
        if when<previous or rev<revision:fail()
        previous=when;revision=rev;snapshots.append(dict(time=when,revision=rev,handles=handles))
    if any(block[physical.SNAPSHOTS+OFFSET+shots*physical.SET_WORDS:physical.END+OFFSET]):fail()
    if any(block[packet.TOKENS+OFFSET:packet.SHOT_TIMES+OFFSET]) or any(block[packet.SHOT_TIMES+OFFSET+shots*2:packet.HEAD+OFFSET]):fail()
    ph=packet.HEAD+OFFSET;pr=list(block[ph:ph+16]);pn,stores,loads=pr[1:4]
    if pr!=[packet.MAGIC,pn,stores,loads]+[0]*12 or stores!=loads or pn!=stores+loads:fail()
    packet_rows=bank(banks.PACKETS,16,pn,banks.PACKET_CAPACITY)
    for i,row in enumerate(packet_rows):
        phase,index,source,hit,hits,token,rev,count=row[:8]
        if (phase not in (0,1) or index>=packet.QUEUE_CAPACITY or source>=len(meta['binding_source_indices'])
            or meta['binding_source_indices'][source]!=info['packet_source'] or not 1<=hit<=hits<=128
            or not 1<=token<=shots or count!=len(snapshots[token-1]['handles']) or rev!=snapshots[token-1]['revision']
            or row[15]!=packet.MAGIC or row[14]>1):fail()
        if time(banks.PACKETS+i*16+8)!=snapshots[token-1]['time']:fail()
    if any(block[packet.TRACE+OFFSET:LOCK_END]):fail()
    qcount=block[QUOTA_HEAD+2];qrows=bank(banks.QUOTAS,20,qcount,banks.QUOTA_CAPACITY)
    try:quota=quotas(block,meta,trace_rows=qrows)
    except (ValueError,IndexError,struct.error):fail()
    for row in quota:
        if not 0<=row['time']<=duration or not math.isfinite(row['time']):fail()
        for side in ('before','after'):
            v=row[side]
            if not 0<=v['capacity']<=128 or v['remaining']>0x7fffffff or any(not math.isfinite(v[k]) for k in ('additional','activated')):fail()
    for start,capacity,head,events in ((banks.FRACTIONS,banks.FRACTION_CAPACITY,L['WORLD_FRACTION_HEAD_BASE'],(22,23)),(banks.TEAMS,banks.TEAM_CAPACITY,L['WORLD_TEAM_HEAD_BASE'],(44,45))):
        rows=bank(start,8,block[head+1],capacity)
        for i,row in enumerate(rows):
            if row[0] not in events or row[1]>31 or (row[1]&7)>=5:fail()
            time(start+i*8+2)
            if number(start+i*8+4)<0 or number(start+i*8+6)<0:fail()
    if any(block[banks.END:]):fail()
    skill_count=block[L['WORLD_SKILL_HEAD_BASE']+1]
    if skill_count>fates.CAPACITY:fail()
    flags=list(block[fates.FLAGS:fates.FLAGS+skill_count]);suppressed=sum(flags)
    if any(v not in (0,1) for v in flags) or list(block[fates.HEAD:fates.FLAGS])!=[fates.MAGIC,suppressed,suppressed,suppressed]+[0]*12 or any(block[fates.FLAGS+skill_count:fates.END]):fail()
    from product_lock_model import typed_reader
    reader=typed_reader()
    try:typed=reader.decode(block,(info['typed_case'],meta,bindings))
    except (AssertionError,ValueError,IndexError,struct.error):fail()
    if not 0<=typed['time']<=duration or typed['finished'] is not True:fail()
    for row in typed['state']:
        if row is not None and any(not math.isfinite(row[k]) or row[k]<0 for k in ('remaining','capacity','expires')):fail()
    for row in typed['attacks']:
        if row['owner']>=len(info['names']) or row['completed'] is not True or any(not math.isfinite(row[k]) or row[k]<0 for k in ('time','damage')):fail()
        for receipt in row['receipts']:
            if not math.isfinite(receipt['took']) or receipt['took']<0:fail()
    return dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(info['declarations']),
        lock_on=dict(pulses=pulses,shots=snapshots,clears=clears,shot_quotas=quota,typed=typed))
