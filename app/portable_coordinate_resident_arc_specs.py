"""A separate tail bank for full-capacity arc views in the resident executor."""
from pathlib import Path
from portable_coordinate_typed_specs import INPUT_WORDS,OUTPUT_WORDS as PREFIX_WORDS
from portable_coordinate_arc_arena import WORDS,CAPACITY,SLOTS,ROW_WORDS,HEADER_WORDS
from portable_coordinate_physical_specs import LAYOUT as PHYSICAL
SOURCE='gpu/world_coordinate_resident_arc_entry.slang'
BASE=PREFIX_WORDS;OUTPUT_WORDS=BASE+WORDS;SCRATCH_OFFSET=BASE-PHYSICAL['LANDING']
PROFILE='coordinate-resident-arc-v1'

def schema():
    return '// Generated resident arc tail; previous banks retain all capacity.\n'+''.join(f'static const uint CRA_{name}={value}U;\n' for name,value in dict(BASE=BASE,WORDS=WORDS,END=OUTPUT_WORDS,SCRATCH_OFFSET=SCRATCH_OFFSET).items())

def regions():
    from portable_arena_specs import Region
    from portable_coordinate_typed_aim_specs import regions as prior
    rows,iw,ow=prior();assert ow==BASE and iw==INPUT_WORDS
    rows.append(Region('output','resident-arc-header',BASE,HEADER_WORDS))
    for slot in range(SLOTS):rows.append(Region('output','resident-arc-slot-'+str(slot),BASE+HEADER_WORDS+slot*ROW_WORDS,ROW_WORDS))
    return rows,iw,OUTPUT_WORDS

def check_layout(root):
    from portable_arena_specs import audit_regions
    from portable_coordinate_typed_aim_specs import check_layout as prior
    from portable_coordinate_arc_arena import check
    root=Path(root);prior(root);check(root)
    assert (root/'gpu/coordinate_resident_arc_layout.slang').read_text()==schema(),'Resident arc tail layout drift'
    rows,iw,ow=regions();plan=audit_regions(rows,iw,ow)
    if not plan['address_plan_verified']:raise ValueError('Resident arc tail overlaps previous banks')
    # All prior regions and dimensions remain intact. Never borrow weapon/cache storage.
    assert PHYSICAL['LANDING']+SCRATCH_OFFSET==BASE
    assert (CAPACITY,SLOTS,WORDS)==(1024,8,32786)
    assert BASE==2032000 and OUTPUT_WORDS==2064786
    text=(root/SOURCE).read_text()
    assert '#define PORTABLE_COORDINATE_ARC_ARENA' in text and '#include "world_coordinate_typed_logical_owner_entry.slang"' in text
    return dict(plan,previous_output_words=BASE,extra_output_words=WORDS,extra_runtime_bytes=0,public_gpu_admitted=False)
