"""Literal independent cover bases into the existing shared product executor."""
import copy,math,struct
from portable_cover_defense_wire import LAYOUT as C,INPUT,OUTPUT,MAGIC,STAT,pack,check_schema,compiler_policy
from portable_runtime import UnsupportedPortable

def required(prepared):
    return ('cover_defense' in prepared.get('reference_models',{}) or
        any(r['effect'].get('stat')=='cover_def_pct' for r in prepared['effects']) or
        any(a.get('action')=='cover' for c in prepared['chars']
            for a in c.get('control',{}).get('sequence',[])))

def compile_product(prepared,producer):
    from portable_specs import LIMITS as L,FIELDS as F
    declarations=copy.deepcopy(prepared.get('reference_models',{}))
    unspecified='cover_defense' not in declarations
    from portable_product_world_contract import has_incoming_attacks
    typed_world='typed_targets' in declarations
    if unspecified and has_incoming_attacks(prepared) and (not typed_world or required(prepared)):
        raise UnsupportedPortable('Independent cover DEF requires explicit reference_models.cover_defense bases; no body DEF or level curve is inferred')
    combined_typed=set(declarations)-{'cover_defense'} in ({'typed_targets'},{'typed_targets','enemy_movement'},{'typed_targets','lock_on'},{'typed_targets','lock_on','enemy_movement'})
    combined_motion_range=set(declarations)-{'cover_defense'} in ({'enemy_movement','named_range'},{'enemy_ammo','enemy_healing'})
    if set(declarations)-{'coordinate','cover_defense','enemy_healing','enemy_ammo','enemy_movement','named_range','lock_on','typed_targets'} or len(set(declarations)-{'cover_defense'})>1 and not (combined_motion_range or combined_typed):
        raise UnsupportedPortable('Cover DEF product composition requires a matching combined consumer wire')
    check_schema();names=[c['name'] for c in prepared['chars']]
    # Product-only unavailable flag; zero payload is reserved padding, not a
    # guessed DEF. The device rejects any attempt to consume an absent base.
    bank=[MAGIC,1,5,1]+[0]*20 if unspecified else pack(declarations['cover_defense'],names)
    inner=dict(prepared,_product_cover_compiled=True);inner.pop('reference_models',None)
    consumers={k:v for k,v in declarations.items() if k!='cover_defense'}
    if consumers:inner['reference_models']=consumers
    cover_declarations={k:v for k,v in declarations.items() if k=='cover_defense'}
    from portable_product_fixed import lower as lower_fixed,attach as attach_fixed
    inner,fixed_values=lower_fixed(inner)
    with compiler_policy():source,iw,ow,words,meta=producer(inner)
    prefixes={
        '':(104400,786432), 'group':(104408,1048576),
        'target':(110112,1048576), 'group-target':(104672,1048576),
    }
    from portable_enemy_healing_wire import INPUT_WORDS as HEAL_INPUT,OUTPUT as HEAL_OUTPUT
    healing=source in ('gpu/product_healing_battle_entry.slang','gpu/product_healing_fixed_battle_entry.slang','gpu/product_healing_group_battle_entry.slang','gpu/product_healing_fixed_group_battle_entry.slang') and (iw,ow)==(HEAL_INPUT,HEAL_OUTPUT['OUTPUT_WORDS'])
    from portable_enemy_ammo_wire import LAYOUT as AMMO
    ammo=source in ('gpu/product_ammo_battle_entry.slang','gpu/product_ammo_fixed_battle_entry.slang','gpu/product_ammo_group_battle_entry.slang','gpu/product_ammo_fixed_group_battle_entry.slang','gpu/product_ammo_target_battle_entry.slang','gpu/product_ammo_fixed_target_battle_entry.slang') and (iw,ow)==(AMMO['INPUT_WORDS'],AMMO['OUTPUT_WORDS'])
    from portable_enemy_movement_wire import INPUT as MOVE_INPUT,OUTPUT as MOVE_OUTPUT
    movement=source in ('gpu/product_movement_battle_entry.slang','gpu/product_movement_fixed_battle_entry.slang') and (iw,ow)==(MOVE_INPUT,MOVE_OUTPUT)
    from portable_named_range_battle_wire import INPUT as RANGE_INPUT,OUTPUT as RANGE_OUTPUT
    named_range=source in ('gpu/product_named_range_battle_entry.slang','gpu/product_named_range_fixed_battle_entry.slang') and (iw,ow)==(RANGE_INPUT,RANGE_OUTPUT)
    from portable_lock_typed_layout import INPUT as LOCK_INPUT,OUTPUT as LOCK_OUTPUT
    locks=source in ('gpu/product_lock_battle_entry.slang','gpu/product_lock_fixed_battle_entry.slang') and (iw,ow)==(LOCK_INPUT,LOCK_OUTPUT)
    from portable_product_movement_range import INPUT as MR_INPUT,OUTPUT as MR_OUTPUT,COVER_OUT,COVER_END,check_cover_schema
    movement_range=source in ('gpu/product_movement_range_battle_entry.slang','gpu/product_movement_range_fixed_battle_entry.slang') and (iw,ow)==(MR_INPUT,MR_OUTPUT)
    if movement_range:check_cover_schema()
    from portable_product_typed import BASE_INPUT as TYPED_INPUT,BASE_OUTPUT as TYPED_OUTPUT,COVER_INPUT as TYPED_COVER_INPUT,COVER_OUTPUT as TYPED_COVER_OUTPUT
    typed=source in ('gpu/product_typed_battle_entry.slang','gpu/product_typed_fixed_battle_entry.slang') and (iw,ow)==(TYPED_INPUT,TYPED_OUTPUT)
    from portable_product_typed_lock import BASE_INPUT as TL_INPUT,BASE_OUTPUT as TL_OUTPUT,COVER_INPUT as TL_COVER_INPUT,COVER_OUTPUT as TL_COVER_OUTPUT
    typed_lock=source in ('gpu/product_typed_lock_battle_entry.slang','gpu/product_typed_lock_fixed_battle_entry.slang') and (iw,ow)==(TL_INPUT,TL_OUTPUT)
    from portable_cover_defense_wire import COMPOSED_STAT
    cover_stat=COMPOSED_STAT if named_range or locks or movement_range or typed or typed_lock else STAT
    if named_range or movement_range or typed or typed_lock:
        from portable_named_range_battle_wire import COUNT_STAT,RANGE_STAT
        # Reject semantic aliasing before a claim or device call, including
        # requests with no incoming hit that would otherwise mask the error.
        if len({cover_stat,COUNT_STAT,RANGE_STAT})!=3:
            raise ValueError('Cover DEF, target count and named range require disjoint stat identifiers')
    coordinate=source in ('gpu/product_coordinate_battle_entry.slang','gpu/product_coordinate_fixed_battle_entry.slang') and (iw,ow)==(115680,2032000)
    kind='typed_lock' if typed_lock else 'typed' if typed else 'coordinate' if coordinate else 'movement_range' if movement_range else 'healing' if healing else 'ammo' if ammo else 'movement' if movement else 'named_range' if named_range else 'lock' if locks else None
    if locks:
        from portable_product_locks import check_cover_history
        from pathlib import Path
        check_cover_history(Path(__file__).resolve().parents[1])
        from portable_named_range_battle_wire import COUNT_STAT
        if cover_stat==COUNT_STAT:raise ValueError('Lock target count and cover DEF require disjoint stat identifiers')
    for candidate,wire in prefixes.items():
        stem=(candidate.replace('-','_')+'_') if candidate else ''
        if source in ('gpu/product_'+stem+'battle_entry.slang','gpu/product_fixed_'+stem+'battle_entry.slang') and (iw,ow)==wire:
            kind=candidate;break
    if kind is None:
        raise UnsupportedPortable('Cover DEF composition requires a connected BODY/PART modifier or shot-group product battle')
    indices=[i for i,r in enumerate(prepared['effects']) if r['effect'].get('stat')=='cover_def_pct']
    for index in indices:
        row=meta['binding_source_indices'].index(index);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
        if words[at+F['KIND']]!=4 or words[at+F['STAT']]!=0:raise ValueError('Original cover placeholder changed')
        words[at+F['KIND']]=0;words[at+F['STAT']]=cover_stat
        # Revival's automatic lazy-marker bit belongs only to kind4. The
        # numeric cover carrier now uses kind0's existing revival lifecycle;
        # retain every other flag, including explicit persist_on_revive.
        words[at+F['FLAGS']] &= ~2048
    meta['product_cover_defense']=dict(declarations=cover_declarations,definition_indices=indices,unspecified_quantities=unspecified,
        cpu_state_or_schedule_supplied=False)
    if fixed_values is not None:
        # Use the already checked combined header for both explicit cover and
        # automatic controls. No posture, readiness clock or native state is
        # supplied: these are literal controls and fixed-delay parameters.
        base=L['WORLD_CONTROL_INPUT_BASE'];version=words[base+1]
        if version in (1,2):
            tap_mask=words[base+5] if version==2 else 0
            if version==2 and not 0<tap_mask<32 or any(words[base+(6 if version==2 else 5):base+16]):
                raise UnsupportedPortable('Cover fixed burst requires a canonical control header')
            words[base+1]=3
            words[base+5:base+8]=[tap_mask,0xffffffff,0x4d435631]
        attach_fixed(words,meta,prepared,fixed_values)
    if typed_lock:
        meta['product_typed_cover']=True
        if len(words)!=TL_INPUT:raise ValueError('Complete typed lock prefix required before cover bank')
        return ('gpu/product_typed_lock_'+('fixed_' if fixed_values is not None else '')+'battle_entry.slang',TL_COVER_INPUT,TL_COVER_OUTPUT,list(words)+bank,meta)
    if typed:
        meta['product_typed_cover']=True
        if len(words)!=TYPED_INPUT:raise ValueError('Complete typed prefix required before cover bank')
        return ('gpu/product_typed_'+('fixed_' if fixed_values is not None else '')+'battle_entry.slang',TYPED_COVER_INPUT,TYPED_COVER_OUTPUT,list(words)+bank,meta)
    if coordinate:
        meta['product_coordinate_cover']=True
        if len(words)!=C['BASE']:raise ValueError('Complete coordinate prefix required before cover bank')
        return ('gpu/product_coordinate_cover_'+('fixed_' if fixed_values is not None else '')+'battle_entry.slang',INPUT,OUTPUT,list(words)+bank,meta)
    if movement_range:
        meta['product_movement_range_cover']=dict(output_base=COVER_OUT,end=COVER_END)
        if len(words)!=MR_INPUT:raise ValueError('Complete movement/range prefix required before cover bank')
        return ('gpu/product_movement_range_cover_'+('fixed_' if fixed_values is not None else '')+'battle_entry.slang',MR_INPUT+C['WORDS'],MR_OUTPUT,list(words)+bank,meta)
    if healing:
        meta['product_healing_cover']=True
        if len(words)!=HEAL_INPUT:raise ValueError('Complete healing prefix required before cover bank')
        return ('gpu/product_healing_cover_'+('fixed_' if fixed_values is not None else '')+('group_' if 'group_' in source else '')+'battle_entry.slang',HEAL_INPUT+C['WORDS'],OUTPUT,list(words)+bank,meta)
    if ammo:
        meta['product_ammo_cover']=True
        if len(words)!=AMMO['INPUT_WORDS']:raise ValueError('Complete ammo prefix required before cover bank')
        return ('gpu/product_ammo_cover_'+('fixed_' if fixed_values is not None else '')+('group_' if 'group_' in source else 'target_' if 'target_' in source else '')+'battle_entry.slang',AMMO['INPUT_WORDS']+C['WORDS'],OUTPUT,list(words)+bank,meta)
    if movement:
        meta['product_movement_cover']=True
        if len(words)!=MOVE_INPUT:raise ValueError('Complete movement prefix required before cover bank')
        return ('gpu/product_movement_cover_'+('fixed_' if fixed_values is not None else '')+'battle_entry.slang',MOVE_INPUT+C['WORDS'],OUTPUT,list(words)+bank,meta)
    if named_range:
        meta['product_named_range_cover']=True
        if len(words)!=RANGE_INPUT:raise ValueError('Complete named range prefix required before cover bank')
        return ('gpu/product_named_range_cover_'+('fixed_' if fixed_values is not None else '')+'battle_entry.slang',RANGE_INPUT+C['WORDS'],OUTPUT,list(words)+bank,meta)
    if locks:
        meta['product_lock_cover']=True
        if len(words)!=LOCK_INPUT:raise ValueError('Complete Lock On prefix required before cover bank')
        return ('gpu/product_lock_cover_'+('fixed_' if fixed_values is not None else '')+'battle_entry.slang',LOCK_INPUT+C['WORDS'],OUTPUT,list(words)+bank,meta)
    stem=('fixed_' if fixed_values is not None else '')+(kind.replace('-','_')+'_' if kind else '')
    return ('gpu/product_cover_'+stem+'battle_entry.slang',INPUT,OUTPUT,
        list(words)+[0]*(C['BASE']-len(words))+bank,meta)

def read_result(block,metadata,names,duration,*,out=C['OUTPUT_BASE'],output=OUTPUT):
    """Complete GPU cover receipts; all landing quantities come from readback."""
    info=metadata['product_cover_defense'];head=out
    end=head+OUTPUT-C['OUTPUT_BASE']
    def fail():raise UnsupportedPortable('Invalid or incomplete product cover DEF readback')
    if type(head) is not int or head<C['OUTPUT_BASE'] or end>output or len(block)!=output or block[head]!=MAGIC:fail()
    count=block[head+1]
    if count>C['RECEIPTS'] or any(block[head+2:head+C['RECEIPT_BASE']]):fail()
    if info.get('unspecified_quantities'):
        if info['declarations'] or count or any(block[head+C['RECEIPT_BASE']:end]):fail()
        return None
    from cover_defense_battle_model import normalize
    bases=normalize(info['declarations']['cover_defense'],names)
    def number(at,negative=False):
        x=struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
        if not math.isfinite(x) or not negative and x<0:fail()
        return x
    receipts=[];previous=0.
    for i in range(count):
        at=head+C['RECEIPT_BASE']+i*C['RECEIPT_WORDS'];who,divisor=block[at:at+2]
        if who>=5 or not 1<=divisor<=5 or any(block[at+24:at+32]):fail()
        row=dict(name=names[who],divisor=divisor)
        for off,key in [(2,'time'),(4,'attack'),(6,'coefficient'),(8,'received_snapshot'),(10,'base_defense'),(12,'effective_defense'),(14,'quantity'),(16,'shared_quantity'),(18,'hp_before'),(20,'applied'),(22,'hp_after')]:
            row[key]=number(at+off,key in ('received_snapshot','effective_defense'))
        if (not previous<=row['time']<=duration or row['base_defense']!=bases[row['name']] or row['hp_before']<=0
            or row['applied']!=min(row['hp_before'],row['shared_quantity']) or row['hp_after']!=row['hp_before']-row['applied']):fail()
        previous=row['time'];receipts.append(row)
    if any(block[head+C['RECEIPT_BASE']+count*32:end]):fail()
    return dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(info['declarations']),
        cover_defense=dict(policy='declared-independent-cover-defense-v1',base_defenses=[bases[n] for n in names],receipts=receipts))
