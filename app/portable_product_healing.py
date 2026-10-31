"""Product adapter to the existing shared finite-ADD healing consumer."""
import copy,math,struct
from portable_enemy_healing_wire import LAYOUT as H,OUTPUT as O,INPUT_WORDS,MAGIC,VERSION,compiler_policy,pack,validate,check_schema
from portable_specs import LIMITS as L

def required(prepared):
    if prepared.get('reference_models',{}).get('enemy_healing'):return True
    from portable_enemy_specs import damage_plan
    for row in prepared['effects']:
        effect=row['effect']
        if effect.get('type')!='buff' or effect.get('stat')!='heal_received_pct':continue
        try:damage_plan(dict(stat='damage',target=effect.get('target','self')))
        except ValueError:continue
        return True
    return False

def compile_product(prepared,producer):
    from portable_runtime import UnsupportedPortable
    from calculator.boss_pattern import validate as patterns_for
    from portable_actor_specs import compile_registry
    check_schema();declarations=copy.deepcopy(prepared.get('reference_models',{}))
    inner=dict(prepared,_product_healing_compiled=True);inner.pop('reference_models',None)
    with compiler_policy():source,iw,ow,words,metadata=producer(inner)
    if source not in ('gpu/product_battle_entry.slang','gpu/product_fixed_battle_entry.slang') or iw!=104400 or ow!=786432:
        raise UnsupportedPortable('Enemy healing product composition requires the plain shared battle entry; group/target/ADD-attack composition is not yet connected')
    raw=prepared['enemy'].get('patterns') or [dict(id='portable-empty-world',kind='idle')]
    patterns=patterns_for(copy.deepcopy(raw));_,bindings=compile_registry(patterns,pools=True)
    padded=list(words)+[0]*(H['BASE']-len(words));spec=declarations.get('enemy_healing')
    if spec:
        bank=pack(spec,patterns,bindings)
        from portable_world_schedule_specs import INPUT_WORDS as SCHEDULE_WORDS
        at=L['WORLD_FRAME_INPUT_BASE'];validate(bank,padded,patterns,bindings,padded[at:at+SCHEDULE_WORDS])
    else:
        # No authored healing sources is a real stationary-boss condition,
        # while heal_received_pct remains a live, consumable enemy field.
        bank=[0]*H['WORDS'];bank[:5]=[MAGIC,VERSION,0,len(patterns),len(bindings)]
    metadata['product_enemy_healing']=dict(declarations=declarations,nodes=[p.id for p in patterns],
        bindings=[dict(kind=int(b.kind),identity=b.identity,label=b.label,run=b.run) for b in bindings],
        cpu_health_generations_or_schedule_supplied=False)
    return ('gpu/product_healing_fixed_battle_entry.slang' if 'fixed_' in source else 'gpu/product_healing_battle_entry.slang',INPUT_WORDS,O['OUTPUT_WORDS'],padded+bank,metadata)

def read_result(block,metadata,names,duration):
    """Use GPU receipts/pools only, with complete bounds/order/reserved checks."""
    from portable_runtime import UnsupportedPortable
    from product_reference_models import healing_public
    info=metadata['product_enemy_healing'];head=O['OUTPUT_BASE']
    def fail():raise UnsupportedPortable('Invalid or incomplete product enemy healing readback')
    if len(block)!=O['OUTPUT_WORDS'] or block[head]!=MAGIC or block[head+1]>O['RECEIPTS'] or any(block[head+3:head+16]):fail()
    def number(at):
        x=struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
        if not math.isfinite(x) or x<0:fail()
        return x
    nodes=info['nodes'];bindings=info['bindings'];slots={b['label']:i for i,b in enumerate(bindings)}
    pool=L['WORLD_ACTOR_POOL_OUTPUT_BASE']
    if block[pool]!=0x57485031 or block[pool+1]!=len(bindings):fail()
    rules={nodes.index(r['node']):r for r in info['declarations'].get('enemy_healing',[])}
    seen=[0]*32;receipts=[];sources=[];index=0;previous=0.
    while index<block[head+1]:
        at=head+O['RECEIPT_BASE']+index*O['RECEIPT_WORDS'];node,gen=block[at:at+2]
        if node not in rules or gen!=seen[node]+1:fail()
        when=number(at+6);rule=rules[node]
        if not previous<=when<=duration or index+len(rule['targets'])>block[head+1]:fail()
        previous=when;seen[node]=gen;sources.append(dict(node=nodes[node],generation=gen,time=when))
        for label in rule['targets']:
            at=head+O['RECEIPT_BASE']+index*O['RECEIPT_WORDS'];index+=1
            slot=slots[label];actor_gen,status=block[at+3:at+5]
            if (list(block[at:at+3])!=[node,gen,slot] or status not in (1,2,3) or block[at+5]
                or number(at+6)!=when or number(at+8)!=rule['amount'] or any(block[at+26:at+32])):fail()
            if (status==1)!=(actor_gen==0):fail()
            row=dict(node=nodes[node],source_generation=gen,time=when,target=label,base_amount=rule['amount'],
                actor=[5,bindings[slot]['identity'],actor_gen] if actor_gen else None,status={1:'not-spawned',2:'dead-or-inactive',3:'healed'}[status])
            if status!=3:
                if any(block[at+10:at+26]):fail()
            else:
                for offset,key in [(10,'multiplier'),(12,'requested'),(14,'dealt_before'),(16,'dealt_after'),(18,'applied'),(20,'effective_gain'),(22,'max_hp')]:row[key]=number(at+offset)
                row.update(hits_before=block[at+24],hits_after=block[at+25])
                if (row['hits_before']!=row['hits_after'] or row['hits_before']>0x7fffffff
                    or row['requested']!=row['base_amount']*row['multiplier'] or row['applied']!=min(row['requested'],row['dealt_before'])
                    or row['dealt_after']!=row['dealt_before']-row['applied'] or row['effective_gain']!=row['dealt_before']-row['dealt_after']
                    or row['dealt_before']>row['max_hp'] or row['dealt_after']>row['max_hp']):fail()
                row.update(hp_before=row['max_hp']-row['dealt_before'],hp_after=row['max_hp']-row['dealt_after'])
            receipts.append(row)
    if block[head+2]!=len(sources) or list(block[head+16:head+48])!=seen:fail()
    end=head+O['RECEIPT_BASE']+index*O['RECEIPT_WORDS']
    if any(block[end:head+O['RECEIPT_BASE']+O['RECEIPTS']*O['RECEIPT_WORDS']]):fail()
    for node in rules:
        if seen[node]!=block[L['WORLD_FRAME_OUTPUT_BASE']+16+node*24+1]:fail()
    if not info['declarations']:
        if receipts or sources:fail()
        return None
    adds=[]
    for slot,binding in enumerate(bindings):
        if binding['kind']!=5:continue
        at=L['WORLD_ACTOR_POOL_STATE_BASE']+slot*16;gen=block[at]
        row=dict(label=binding['label'],generation=gen)
        if gen==0:
            if any(block[at:at+16]):fail()
        else:
            if block[at+1]>1 or block[at+2]>3 or block[at+3]>0x7fffffff or any(block[at+11:at+16]):fail()
            row.update(alive=bool(block[at+1]),gone={0:'',1:'처치',2:'퇴장',3:'자폭'}[block[at+2]],
                dealt=number(at+4),hits=block[at+3],born=number(at+8),order=block[at+10])
        adds.append(row)
    scored={n:number(L['DAMAGE_ACCOUNTING_STATE_BASE']+30+i*2) for i,n in enumerate(names)}
    overkill=number(L['WORLD_ACTOR_POOL_OUTPUT_BASE']+16);rounded={n:round(v) for n,v in scored.items()}
    data=dict(receipts=receipts,sources=sources,final_adds=adds,final_scored_damage=scored,final_overkill=overkill,
        public_summary=dict(add_char_total=rounded,add_total=sum(rounded.values()),add_overkill=round(overkill)))
    return dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(info['declarations']),enemy_healing=healing_public(data))
