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
    if unspecified and has_incoming_attacks(prepared):
        raise UnsupportedPortable('Independent cover DEF requires explicit reference_models.cover_defense bases; no body DEF or level curve is inferred')
    if set(declarations)-{'cover_defense'}:
        raise UnsupportedPortable('Cover DEF product composition requires a matching combined consumer wire')
    check_schema();names=[c['name'] for c in prepared['chars']]
    # Product-only unavailable flag; zero payload is reserved padding, not a
    # guessed DEF. The device rejects any attempt to consume an absent base.
    bank=[MAGIC,1,5,1]+[0]*20 if unspecified else pack(declarations['cover_defense'],names)
    inner=dict(prepared,_product_cover_compiled=True);inner.pop('reference_models',None)
    from portable_product_fixed import lower as lower_fixed,attach as attach_fixed
    inner,fixed_values=lower_fixed(inner)
    with compiler_policy():source,iw,ow,words,meta=producer(inner)
    if source not in ('gpu/product_battle_entry.slang','gpu/product_fixed_battle_entry.slang') or (iw,ow)!=(104400,786432):
        raise UnsupportedPortable('Cover DEF composition requires the plain shared product battle')
    indices=[i for i,r in enumerate(prepared['effects']) if r['effect'].get('stat')=='cover_def_pct']
    for index in indices:
        row=meta['binding_source_indices'].index(index);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
        if words[at+F['KIND']]!=4 or words[at+F['STAT']]!=0:raise ValueError('Original cover placeholder changed')
        words[at+F['KIND']]=0;words[at+F['STAT']]=STAT
    meta['product_cover_defense']=dict(declarations=declarations,definition_indices=indices,unspecified_quantities=unspecified,
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
    return ('gpu/product_cover_fixed_battle_entry.slang' if fixed_values is not None else 'gpu/product_cover_battle_entry.slang',INPUT,OUTPUT,
        list(words)+[0]*(C['BASE']-len(words))+bank,meta)

def read_result(block,metadata,names,duration):
    """Complete GPU cover receipts; all landing quantities come from readback."""
    info=metadata['product_cover_defense'];head=C['OUTPUT_BASE']
    def fail():raise UnsupportedPortable('Invalid or incomplete product cover DEF readback')
    if len(block)!=OUTPUT or block[head]!=MAGIC:fail()
    count=block[head+1]
    if count>C['RECEIPTS'] or any(block[head+2:head+C['RECEIPT_BASE']]):fail()
    if info.get('unspecified_quantities'):
        if info['declarations'] or count or any(block[head+C['RECEIPT_BASE']:]):fail()
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
    if any(block[head+C['RECEIPT_BASE']+count*32:]):fail()
    return dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(info['declarations']),
        cover_defense=dict(policy='declared-independent-cover-defense-v1',base_defenses=[bases[n] for n in names],receipts=receipts))
