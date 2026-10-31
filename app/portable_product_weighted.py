"""Product lowering/readback for the existing shared weighted landing consumer.

Only literal weights and original marker identities enter the GPU. No native
allocation, live recipient mask, damage, clock or protection state is supplied.
"""
import copy,math,struct
from portable_weighted_battle_wire import LAYOUT as W,INPUT,OUTPUT,MAGIC,pack,check_schema,compiler_policy
from portable_runtime import UnsupportedPortable

def required(prepared):
    return ('weighted_incoming' in prepared.get('reference_models',{}) or
        any(r['effect'].get('stat')=='received_dmg_split' for r in prepared['effects']))

def compile_product(prepared,producer):
    from portable_specs import LIMITS as L,FIELDS as F
    declarations=copy.deepcopy(prepared.get('reference_models',{}))
    if 'weighted_incoming' not in declarations:
        raise UnsupportedPortable('Weighted incoming requires explicit reference_models.weighted_incoming weights; game ratios are unverified')
    if set(declarations)!={'weighted_incoming'}:
        raise UnsupportedPortable('Weighted product consumer composition requires a matching combined wire')
    check_schema();names=[c['name'] for c in prepared['chars']]
    pack(declarations['weighted_incoming'],names)
    inner=dict(prepared,_product_weighted_compiled=True);inner.pop('reference_models',None)
    with compiler_policy():source,iw,ow,words,meta=producer(inner)
    if source not in ('gpu/product_battle_entry.slang','gpu/product_fixed_battle_entry.slang') or (iw,ow)!=(104400,786432):
        raise UnsupportedPortable('Weighted product composition requires the plain shared battle entry')
    indices=[i for i,r in enumerate(prepared['effects']) if r['effect'].get('stat')=='received_dmg_split']
    if len(indices)!=2 or {prepared['effects'][i]['effect']['target'] for i in indices}!={'all_allies','self_cover'}:
        raise UnsupportedPortable('Weighted product requires exactly one original body and cover marker')
    rows=[]
    for target in ('all_allies','self_cover'):
        index=next(i for i in indices if prepared['effects'][i]['effect']['target']==target)
        row=meta['binding_source_indices'].index(index);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
        if words[at+F['KIND']]!=4 or words[at+F['STAT']]!=0:raise ValueError('Weighted product placeholder changed')
        rows.append(row)
    bank=pack(declarations['weighted_incoming'],names,rows)
    meta['product_weighted_incoming']=dict(declarations=declarations,source_rows=rows,
        source_name=next(prepared['effects'][i]['effect']['name'] for i in indices if prepared['effects'][i]['effect']['target']=='all_allies'),
        cover_name=next(prepared['effects'][i]['effect']['name'] for i in indices if prepared['effects'][i]['effect']['target']=='self_cover'),
        cpu_state_or_schedule_supplied=False)
    return ('gpu/product_weighted_fixed_battle_entry.slang' if 'fixed_' in source else 'gpu/product_weighted_battle_entry.slang',INPUT,OUTPUT,
        list(words)+[0]*(W['BASE']-len(words))+bank,meta)

def read_result(block,metadata,names,duration):
    """Decode complete ordered GPU allocation receipts, never native replay."""
    info=metadata['product_weighted_incoming'];head=W['OUTPUT_BASE']
    def fail():raise UnsupportedPortable('Invalid or incomplete product weighted incoming readback')
    if len(block)!=OUTPUT or block[head]!=MAGIC:fail()
    ns,nr=block[head+1:head+3]
    if ns>W['CAPACITY'] or nr>W['CAPACITY'] or any(block[head+3:head+W['SNAPSHOTS']]):fail()
    def number(at):
        value=struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
        if not math.isfinite(value) or value<0:fail()
        return value
    snapshots=[];previous=0.;body,cover=info['source_rows']
    for i in range(ns):
        at=head+W['SNAPSHOTS']+i*W['SNAPSHOT_WORDS'];mask,caster,struck,active=block[at:at+4]
        when=number(at+4);amount=number(at+6);total=number(at+8);shares=[number(at+10+j*2) for j in range(6)];epoch=number(at+24)
        if (not 0<mask<32 or caster>=5 or struck>=5 or active not in (mask,mask|32)
            or not previous<=when<=duration or epoch>when or total<=0
            or block[at+22]!=body or block[at+23]!=(cover+1 if active&32 else 0)
            or any(block[at+26:at+48]) or any(shares[j] for j in range(6) if not active&(1<<j))):fail()
        previous=when
        snapshots.append(dict(index=i,time=when,struck=names[struck],caster=names[caster],body_mask=mask,
            body_source_name=info['source_name'],body_source_activated_at=epoch,
            cover_source_name=info['cover_name'] if active&32 else None,amount=amount,status=0,
            active_mask=active,total=total,shares=shares))
    if any(block[head+W['SNAPSHOTS']+ns*48:head+W['RECEIPTS']]):fail()
    receipts=[];expected=[s['index'] for s in snapshots if s['active_mask']&32]
    if nr!=len(expected):fail()
    for i in range(nr):
        at=head+W['RECEIPTS']+i*W['RECEIPT_WORDS'];index,delivered=block[at:at+2]
        when,before,applied,after=[number(at+off) for off in (2,4,6,8)]
        if (index!=expected[i] or delivered>1 or when!=snapshots[index]['time'] or applied>before or after!=before-applied
            or not delivered and applied!=0 or any(block[at+10:at+32])):fail()
        receipts.append(dict(snapshot=index,time=when,hp_before=before,applied=applied,hp_after=after,delivered=bool(delivered)))
    if any(block[head+W['RECEIPTS']+nr*32:]):fail()
    spec=info['declarations']['weighted_incoming']
    return dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(info['declarations']),
        weighted_incoming=dict(policy=spec['policy'],weights=[spec[k] for k in ('caster_weight','other_weight','cover_weight')],
            snapshots=snapshots,cover_receipts=receipts,in_game_rules_verified=False))
