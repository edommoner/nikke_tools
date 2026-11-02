"""Ordinary requests into the existing typed coordinate/owner executable."""
import copy,math,struct,array,hashlib
from portable_runtime import UnsupportedPortable
from portable_coordinate_typed_specs import INPUT_WORDS as TYPED_INPUT,COORDINATE_OUTPUT_WORDS as BASE
from portable_product_typed_movement import INPUT,OUTPUT

from portable_logical_geometry_wire import LAYOUT as LOGICAL
NEARBY_BASE=TYPED_INPUT+LOGICAL['WORDS']
from portable_named_range_battle_wire import WORDS as NEARBY_WORDS,OUT as NEARBY_OUT,END as NEARBY_END


def check_schema(root):
    from pathlib import Path
    from portable_coordinate_typed_specs import check_layout
    from portable_skill_history import check_layout as history_layout
    from portable_logical_geometry_wire import check_schema as logical_layout
    check_layout(root);history_layout(root);logical_layout(root)
    from portable_product_typed_movement import check_schema as motion_schema
    motion_schema(root)
    from portable_named_range_battle_wire import shader_schema
    if (Path(root)/'gpu/product_typed_nearby_layout.slang').read_text()!=shader_schema(base=NEARBY_BASE):raise ValueError('Typed nearby bank schema drift')
    source=(Path(root)/'gpu/product_typed_battle_entry.slang').read_text()
    entry=(Path(root)/'gpu/world_coordinate_area_entry.slang').read_text()
    if ('#define PORTABLE_PRODUCT_TYPED_LOGICAL' not in source
            or '#define PORTABLE_LOGICAL_INPUT_BASE 115680U' not in source
            or '#define PORTABLE_COORDINATE_TYPED_MIXED' not in source
            or not 153568+1024*10+128+16<=170976
            or TYPED_INPUT!=115680 or NEARBY_BASE!=121392 or INPUT!=123732
            or '#if defined(PORTABLE_PRODUCT_TYPED_MOTION)\n    uint input=1+id.x*EMB_INPUT' not in entry):
        raise ValueError('Typed product requires adjacent complete typed/logical input banks')


def compile_product(prepared):
    from product_typed_model import normalize_product,validate_logical_owners,LOGICAL_FIELD_MODE
    from portable_product_fixed import lower,attach
    from portable_coordinate_typed_input import compile_coordinate_typed
    from calculator.timeline import CharState,_when_label
    from calculator.boss_pattern import validate
    declarations=copy.deepcopy(prepared.get('reference_models',{}))
    if {'typed_targets','lock_on'}<=set(declarations):
        from portable_product_locks import compile_product as locks
        return locks(prepared,typed_model=normalize_product(declarations['typed_targets']))
    if set(declarations)-{'typed_targets','enemy_movement'}:raise UnsupportedPortable('Typed product composition requires its matching checked shared GPU consumer')
    spec=normalize_product(declarations['typed_targets'])
    if any(r['effect'].get('target') in ('all_projectiles','typed_point') for r in prepared['effects']):
        raise UnsupportedPortable('Original typed skill damage requires its checked common skill route; weapon typed admission cannot omit it')
    if any(p.get('kind') not in ('idle','summon','attack') or p.get('kind')=='summon' and (p.get('spec',{}).get('attack') or p.get('spec',{}).get('self_destruct')) for p in prepared['enemy'].get('patterns',[])):
        raise UnsupportedPortable('Typed product attack world requires its combined checked incoming consumer')
    from portable_product_world_contract import has_incoming_attacks
    from portable_product_cover import required as cover_required
    if has_incoming_attacks(prepared) and cover_required(prepared):
        raise UnsupportedPortable('Typed incoming attacks with independent/manual cover require the combined checked cover consumer')
    manual=[i for i,c in enumerate(prepared['chars']) if any(a.get('action')=='cover' for a in c.get('control',{}).get('sequence',[]))]
    controlled=dict(prepared,_product_manual_cover=True) if manual else prepared
    inner,fixed=lower(controlled,manual_posture=True);inner=copy.deepcopy(inner);inner.pop('reference_models',None)
    inner['enemy']['coord']=copy.deepcopy(spec['coord']);inner['_product_native_equipment_carriers']=True
    if any(p.get('kind')=='attack' and p.get('spec',{}).get('debuffs') for p in inner['enemy'].get('patterns',[])):
        inner['_product_boss_debuffs']=True
    inner['typed_aim_policy']=copy.deepcopy(spec['aim_policy']);inner['typed_actor_policy']=copy.deepcopy(spec['actor_policy'])
    nearby_source=copy.deepcopy(inner)
    if 'enemy_movement' in prepared.get('reference_models',{}):
        from portable_enemy_movement_wire import lower_effects
        inner,_=lower_effects(inner)
    for rule in spec.get('nearby_rules',[]):
        found=[i for i,item in enumerate(inner['effects']) if item['owner']==rule['owner'] and item['effect'].get('name')==rule['effect']]
        if len(found)!=1:raise UnsupportedPortable('Exact original nearby owner/effect binding required')
        effect=inner['effects'][found[0]]['effect']
        if effect.get('target')!='target_and_nearby:'+str(rule['base_count']-1):raise UnsupportedPortable('Nearby count must preserve original primary plus neighbours')
        effect['target']='enemies_nearest:'+str(rule['base_count'])
    words,meta,bindings,scene=compile_coordinate_typed(inner,spec['bindings'],probe_kind=spec['bindings'][0]['kind'],geometry=spec['geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True,coordinate_logical_owners=spec['actor_policy']=={'mode':LOGICAL_FIELD_MODE},mixed_weapon_kinds=len({b['kind'] for b in spec['bindings']})>1)
    validate_logical_owners(spec,bindings)
    from portable_logical_geometry_wire import pack as logical_pack,validate as logical_validate
    shapes=spec.get('logical_geometry',[])
    if {b.label for b in bindings if int(b.kind)==5}!={row['label'] for row in shapes}:
        raise UnsupportedPortable('Every configured typed-world ADD must have one explicit collider')
    logical=logical_pack(shapes,bindings,allow_empty=True)
    logical_validate(logical,words[:109968],bindings,allow_empty=True)
    if len(words)!=TYPED_INPUT:raise UnsupportedPortable('Incomplete original typed input bank')
    words+=logical
    from portable_named_range_battle_wire import pack_rules,MAGIC as NEARBY_MAGIC,WORDS as NRB_WORDS
    rules=spec.get('nearby_rules',[])
    bank,bound=pack_rules(nearby_source,meta,bindings,rules)
    if len(words)!=NEARBY_BASE:raise UnsupportedPortable('Complete logical bank required before nearby rules')
    words+=bank
    from portable_product_typed_movement import append_bank
    append_bank(words,meta,prepared,bindings)
    meta['named_range_battle']=dict(bindings=bound)
    meta['product_typed_nearby']=dict(declarations={'named_range':dict(coord=spec['coord'],logical_geometry=shapes,rules=rules)},names=[c['name'] for c in inner['chars']])
    meta['product_typed_targets']=dict(declarations={'typed_targets':spec},cpu_state_or_schedule_supplied=False)
    meta['product_manual_cover_owners']=manual
    meta['product_control_labels']=[[dict(mode=e['mode'],producer=_when_label(e)) for e in CharState(c,atk,inner['enemy'].get('code'))._click_sched] for c,atk in zip(inner['chars'],inner['base_atk'])]
    nodes=validate(copy.deepcopy(inner['enemy'].get('patterns') or [dict(id='portable-empty-world',kind='idle')]),coord=True)
    meta['product_world']=dict(nodes=[dict(id=p.id,kind=p.kind) for p in nodes],literal_pattern_identity_only=True,cpu_schedule_or_state_supplied=False)
    meta['product_parts']=[]
    attach(words,meta,prepared,fixed)
    return 'gpu/product_typed_'+('fixed_' if fixed is not None else '')+'battle_entry.slang',INPUT,OUTPUT,words,meta


class TypedStateView:
    """Readonly address translation for the unchanged common typed decoder.

    The complete skill-history bank is validated before projecting it out of
    the legacy weapon-only decoder's formerly unused skill receipt area.
    """
    def __init__(self,block):self.block=block
    def __len__(self):return 1048576
    def __getitem__(self,key):
        if isinstance(key,slice):
            a,b,step=key.indices(len(self));return [self[i] for i in range(a,b,step)]
        if not 0<=key<len(self):raise IndexError(key)
        if 790000<=key<923120:return 0
        return self.block[key if key<786432 else key-786432+BASE]


def read_result(block,metadata,names,duration):
    from portable_skill_history import decode_pages,BASE as SKILLS,END
    from portable_specs import LIMITS as L
    from portable_world_result import read_typed_battle
    from portable_coordinate_typed_specs import regions
    from product_typed_model import public_from_words
    def fail(message):raise UnsupportedPortable('Invalid or incomplete typed product readback: '+message)
    if len(block)!=OUTPUT or block[0]!=0:fail('wire/status')
    spec=metadata['product_typed_targets']['declarations']['typed_targets']
    try:
        skill_rows=decode_pages(block,block[L['WORLD_SKILL_HEAD_BASE']+1],SKILLS)
        for row in skill_rows:
            if not 0<=row['row']<len(metadata['binding_source_indices']) or any(not math.isfinite(row[k]) or row[k]<0 for k in ('created','landed','amount','share')):fail('skill history')
        if block[BASE+1]!=0:fail('undeclared typed skill route')
        for region in regions()[0]:
            if region.domain=='output' and 'reserved' in region.name and any(block[region.base:region.end]):fail(region.name)
        nearby=read_nearby_history(memoryview(block)[:2032000],metadata,duration)
        if any(block[END:NEARBY_OUT]) or any(block[NEARBY_END:BASE+136688]) or any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]):fail('unused skill tail or counter context')
        c=dict(typed_bindings=spec['bindings'],max_attacks=128,effects=[],names=names)
        state=read_typed_battle(TypedStateView(block),(c,metadata,()))
        if state['attacks'] or not state['finished'] or state['time']!=duration:fail('typed clock')
        model=read_weapon_history(block,metadata,names,duration,state,base=BASE,tail_start=262144)
        if spec.get('nearby_rules'):model['nearby_casts']=nearby
    except (AssertionError,IndexError,KeyError,ValueError,struct.error) as error:
        raise UnsupportedPortable('Invalid or incomplete typed product history') from error
    result=dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(metadata['product_typed_targets']['declarations']),typed_targets=model)
    from portable_product_typed_movement import read_result as movement
    moving=movement(block,metadata,duration)
    if moving is not None:
        from product_reference_models import combine_public
        result=combine_public([result,moving])
    return result


def read_weapon_history(block,metadata,names,duration,state,*,base=BASE,tail_start=None,locked=False):
    """The same complete physical packet/aim decoder for standalone and locks."""
    from portable_coordinate_typed_aim_specs import WORDS as AIM_WORDS
    from product_typed_model import public_from_words
    spec=metadata['product_typed_targets']['declarations']['typed_targets']
    def fail(message):raise UnsupportedPortable('Invalid or incomplete typed product readback: '+message)
    from portable_product_typed_movement import WEAPON_CAPACITY,weapon_rows,END,LOCK_END
    h=base+170976;keep=WEAPON_CAPACITY;width=24;count=block[h+2]
    if list(block[h:h+2])!=[0x43545731,1] or count>keep or list(block[h+3:h+6])!=[count,keep,width] or block[h+7]!=(count*width)%16 or block[h+40]!=1 or any(block[h+41:h+64]):fail('physical history capacity/header')
    rows=[];last=0.
    for row in weapon_rows(block,base,count,LOCK_END if locked else END):
        slot=row[5]
        if row[1]>=5 or slot>=len(spec['bindings']) or row[2]!=spec['bindings'][slot]['kind'] or row[3]!=spec['bindings'][slot]['identity'] or row[4]==0 or any(row[22:]) or any(row[k]>1 for k in (14,15,17,18,19)):fail('physical identity')
        values=[struct.unpack('<d',struct.pack('<II',*row[at:at+2]))[0] for at in (6,8,10,12)]
        if any(not math.isfinite(x) or x<0 for x in values) or not last<=values[0]<=duration or values[3]>values[2] or not row[14] and (values[3] or row[15]):fail('physical amounts/order')
        last=values[0];rows.append(row)
    raw=array.array('I',(x for row in rows for x in row))
    if __import__('sys').byteorder!='little':raw.byteswap()
    digest=list(struct.unpack('>8I',hashlib.sha256(raw.tobytes()).digest()))
    if list(block[h+8:h+16])!=digest or list(block[h+32:h+40])!=digest:fail('complete physical history digest/tail')
    pending=(count*width)%16;tail=[int.from_bytes(x.to_bytes(4,'little'),'big') for x in list(raw)[-pending:]] if pending else []
    tail.append(0x80000000);tail += [0]*(14-len(tail));bits=count*width*32;tail += [bits>>32,bits&0xffffffff]
    if list(block[h+16:h+32])!=tail:fail('completed SHA block')
    from portable_coordinate_typed_aim_specs import HEAD as AIM_HEAD,WORDS as AIM_WORDS
    aim=base+AIM_HEAD;n=block[aim+6];when=struct.unpack('<d',struct.pack('<II',*block[aim+4:aim+6]))[0]
    if list(block[aim:aim+2])!=[0x43544131,1] or block[aim+2]==0 or n>len(spec['bindings']) or block[aim+7]>1 or not math.isfinite(when) or not 0<=when<=duration or any(block[aim+12:aim+32]):fail('aim frame header')
    candidates=[];seen=set();nodes=[r['id'] for r in metadata['product_world']['nodes']]
    for i in range(n):
        row=list(block[aim+32+i*4:aim+36+i*4]);slot=row[0]-129
        if not 0<=slot<len(spec['bindings']) or row[1]==0 or row[2]!=nodes.index(spec['bindings'][slot]['node']) or row[3]!=spec['bindings'][slot]['identity'] or slot in seen:fail('aim final candidates')
        seen.add(slot);candidates.append(row)
    if block[aim+3]!=(candidates[0][0] if candidates else 0) or any(block[aim+32+n*4:aim+AIM_WORDS]) or any(block[aim+AIM_WORDS:base+tail_start] if tail_start is not None else block[aim+AIM_WORDS:]):fail('aim unused tail/candidate')
    model=public_from_words(spec,state['state'],rows,names,duration);model['shot_count']=block[h+6];model['skill_attacks']=[]
    model['aim_state']=dict(frames=block[aim+2],time=when,candidate=block[aim+3],canonical_has_adds=bool(block[aim+7]),rows=candidates,stream_fingerprints=[format(block[aim+8]|block[aim+9]<<32,'016x'),format(block[aim+10]|block[aim+11]<<32,'016x')])
    return model


def read_nearby_history(block,metadata,duration):
    from portable_product_named_range import read_result as read_nearby
    copied=dict(metadata,product_named_range=metadata['product_typed_nearby'])
    return read_nearby(block,copied,duration)['named_range']['casts']
