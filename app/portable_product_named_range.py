"""Product binding of existing named radial/count runtime and typed records."""
import copy,math,struct
from portable_runtime import UnsupportedPortable
from portable_named_range_battle_wire import INPUT,OUTPUT,OUT,OUT_HEADER,CASTS,CAST_WORDS,END,MAGIC


def required(prepared):
    return 'named_range' in prepared.get('reference_models',{}) or any(r['effect'].get('stat')=='effect_range_pct' for r in prepared['effects'])


def compile_product(prepared):
    from portable_named_range_battle_wire import compile_battle,check_schema
    from calculator.boss_pattern import validate
    from calculator.timeline import CharState,_when_label
    declarations=copy.deepcopy(prepared.get('reference_models',{}))
    if set(declarations)!={'named_range'}:
        error=UnsupportedPortable('Named range requires explicit reference_models.named_range geometry and rules; composition is not connected')
        for row in prepared['effects']:
            e=row['effect']
            if e.get('stat') in ('effect_range_pct','effect_target_count_add'):
                error.effect_context=dict(character=row['owner'],effect=e.get('name',''),stat=e['stat'],target=e.get('target',''));break
        raise error
    from portable_product_fixed import lower as lower_fixed,attach as attach_fixed
    original=prepared
    prepared,fixed_values=lower_fixed(prepared)
    if any(a.get('action')=='cover' for c in prepared['chars'] for a in c.get('control',{}).get('sequence',[])):
        raise UnsupportedPortable('Named range with manual cover requires its combined coordinate consumer')
    spec=declarations['named_range'];check_schema()
    words,meta,bindings,scene=compile_battle(dict(prepared,_product_native_equipment_carriers=True),spec['logical_geometry'],spec['rules'])
    meta['product_named_range']=dict(declarations=declarations,names=[c['name'] for c in prepared['chars']],cpu_state_or_schedule_supplied=False)
    meta['product_control_labels']=[
        [dict(mode=e['mode'],producer=_when_label(e)) for e in CharState(c,atk,prepared['enemy'].get('code'))._click_sched]
        for c,atk in zip(prepared['chars'],prepared['base_atk'])]
    nodes=validate(copy.deepcopy(prepared['enemy'].get('patterns') or []),coord=True)
    meta['product_world']=dict(nodes=[dict(id=p.id,kind=p.kind) for p in nodes],literal_pattern_identity_only=True,cpu_schedule_or_state_supplied=False)
    attach_fixed(words,meta,original,fixed_values)
    source='gpu/product_named_range_fixed_battle_entry.slang' if fixed_values is not None else 'gpu/product_named_range_battle_entry.slang'
    return source,INPUT,OUTPUT,words,meta


def read_result(block,meta,duration):
    def fail():raise UnsupportedPortable('Invalid or incomplete product named range cast history')
    if len(block)!=OUTPUT or block[0]!=0:fail()
    h=list(block[OUT:OUT+OUT_HEADER]);count=h[2]
    if count>CASTS or h!=[MAGIC,1,count]+[0]*(OUT_HEADER-3):fail()
    info=meta['product_named_range'];bound={r['row']:r for r in meta['named_range_battle']['bindings']}
    rules={(r['owner'],r['effect']):r for r in info['declarations']['named_range']['rules']}
    names=info['names'];casts=[];previous=0.
    for i in range(count):
        at=OUT+OUT_HEADER+i*CAST_WORDS;raw=list(block[at:at+CAST_WORDS]);row,who=raw[:2]
        if row not in bound or who>=len(names) or bound[row]['owner']!=names[who] or any(raw[22:]):fail()
        def num(offset):
            value=struct.unpack('<d',struct.pack('<II',*raw[offset:offset+2]))[0]
            if not math.isfinite(value):fail()
            return value
        r=dict(owner=names[who],effect=bound[row]['effect'],time=num(2),base_radius=num(4),percent=num(6),factor=num(8),radius=num(10),base_count=raw[12],capacity=raw[13],additional_targets=num(14),body_position=raw[16],add_count=raw[17],aim=[num(18),num(20)])
        rule=rules[(r['owner'],r['effect'])]
        if (not previous<=r['time']<=duration or r['base_radius']!=rule['base_radius'] or r['base_count']!=rule['base_count']
            or not 0<=r['capacity']<=128 or not 0<=r['add_count']<=127 or not 0<=r['body_position']<=r['add_count']+1
            or r['add_count']+bool(r['body_position'])>r['capacity'] or r['factor']<0 or r['radius']<0
            or r['additional_targets']<0 or r['additional_targets']!=int(r['additional_targets']) or r['capacity']!=r['base_count']+r['additional_targets']):fail()
        previous=r['time'];casts.append(r)
    if any(block[OUT+OUT_HEADER+count*CAST_WORDS:END]):fail()
    return dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(info['declarations']),named_range=dict(casts=casts))
