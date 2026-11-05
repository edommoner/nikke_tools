"""Literal public coordinate scene to the existing shared sampler and actors."""
import copy,math
from portable_runtime import UnsupportedPortable
from portable_logical_geometry_wire import LAYOUT,SCRATCH,compile_logical_geometry
INPUT=LAYOUT['BASE']+LAYOUT['WORDS'];OUTPUT=SCRATCH['OUTPUT_WORDS']

def compile_product(prepared):
    from portable_product_fixed import lower,attach
    from product_reference_models import normalize
    from calculator.boss_pattern import validate
    from calculator.timeline import CharState,_when_label
    declarations=normalize(prepared.get('reference_models'))
    if set(declarations)!={'coordinate'}:raise UnsupportedPortable('Explicit standalone coordinate model required')
    spec=declarations['coordinate'];original=prepared
    if not prepared.get('_product_cover_compiled') and any(a.get('action')=='cover' for c in prepared['chars'] for a in c.get('control',{}).get('sequence',[])):
        raise UnsupportedPortable('Coordinate plus manual cover requires its independent checked cover consumer')
    inner,fixed=lower(prepared);inner=copy.deepcopy(inner);inner.pop('reference_models',None)
    inner['enemy']['coord']=copy.deepcopy(spec['coord']);inner['_product_native_equipment_carriers']=True
    from portable_product_add_attack import lower as lower_add,attach as attach_add
    inner,add_patterns=lower_add(inner)
    words,meta,bindings,scene=compile_logical_geometry(inner,spec['logical_geometry'],allow_empty=True)
    configured={b.label for b in bindings if int(b.kind)==5}
    if configured!={r['label'] for r in spec['logical_geometry']}:raise UnsupportedPortable('Every configured ADD must have one explicit coordinate collider')
    meta['product_coordinate']=dict(declarations=declarations,cpu_state_or_schedule_supplied=False)
    meta['product_manual_cover_owners']=[i for i,c in enumerate(inner['chars']) if any(a.get('action')=='cover' for a in c.get('control',{}).get('sequence',[]))]
    meta['product_control_labels']=[[dict(mode=e['mode'],producer=_when_label(e)) for e in CharState(c,atk,inner['enemy'].get('code'))._click_sched] for c,atk in zip(inner['chars'],inner['base_atk'])]
    nodes=validate(copy.deepcopy(inner['enemy'].get('patterns') or [dict(id='portable-empty-world',kind='idle')]),coord=True)
    meta['product_world']=dict(nodes=[dict(id=p.id,kind=p.kind) for p in nodes],literal_pattern_identity_only=True,cpu_schedule_or_state_supplied=False)
    meta['product_parts']=[dict(name=b.label,slot=i,node=b.run) for i,b in enumerate(bindings) if int(b.kind)==1 and nodes[b.run].id=='authored-live-parts']
    attach(words,meta,original,fixed)
    source='gpu/product_coordinate_'+('fixed_' if fixed is not None else '')+'battle_entry.slang'
    if add_patterns is not None:
        meta['product_coordinate_add']=True
        return attach_add(source,words,meta,inner,add_patterns,prepared['enemy']['patterns'])
    return source,INPUT,OUTPUT,words,meta

def read_result(block,metadata,*,names=None,duration=None):
    from product_coordinate_model import public
    if len(block)!=OUTPUT:raise UnsupportedPortable('Complete coordinate product readback required')
    from portable_logical_geometry_wire import output_regions
    from portable_skill_history import decode_pages,BASE
    from portable_specs import LIMITS as L
    healing_model=None
    try:
        from portable_product_add_attack import coordinate_output_ownership
        owned=coordinate_output_ownership(block,metadata)
        if metadata.get('product_typed_nearby'):
            if owned:raise ValueError('Typed nearby and ADD receipt banks cannot overlap')
            from portable_product_typed import read_nearby_history,NEARBY_OUT,NEARBY_END
            read_nearby_history(block,metadata,duration)
            owned=(NEARBY_OUT,NEARBY_END)

        if metadata.get('product_coordinate_healing'):
            if owned or not isinstance(names,list) or len(names)!=5 or len(set(names))!=5 or type(duration) not in (int,float) or not math.isfinite(duration) or duration<=0:
                raise ValueError('Complete coordinate healing projection context required')
            from portable_product_healing import read_result as read_healing
            from portable_enemy_healing_wire import OUTPUT as H
            healing_model=read_healing(block,metadata,names,duration)
            owned=(H['OUTPUT_BASE'],H['OUTPUT_BASE']+H['RECEIPT_BASE']+H['RECEIPTS']*H['RECEIPT_WORDS'])
        for region in output_regions():
            if region.name.startswith('logical-reserved') or region.name in ('logical-pellet-amounts','logical-shot-header'):
                spans=[(region.base,region.end)]
                if owned and region.name=='logical-reserved-suffix':
                    if not region.base==owned[0]<owned[1]<=region.end:raise ValueError('Coordinate ADD output overlap')
                    spans=[(owned[1],region.end)]
                if any(any(block[a:b]) for a,b in spans):
                    raise ValueError('Nonzero unowned coordinate output or unfinished packet scratch')
        rows=decode_pages(block,block[L['WORLD_SKILL_HEAD_BASE']+1],BASE)
        for row in rows:
            if not 0<=row['row']<len(metadata['binding_source_indices']) or any(not math.isfinite(row[k]) or row[k]<0 for k in ('created','landed','amount','share')):
                raise ValueError('Invalid coordinate skill receipt')
    except (AssertionError,ValueError,IndexError) as error:
        raise UnsupportedPortable('Invalid or incomplete coordinate product history') from error
    info=metadata['product_coordinate']
    model=dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(info['declarations']),coordinate=public(info['declarations']['coordinate']))
    if healing_model is not None:
        from product_reference_models import combine_public
        return combine_public([model,healing_model])
    return model
