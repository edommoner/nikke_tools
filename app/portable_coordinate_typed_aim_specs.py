"""Frame-candidate owner within the retained typed weapon arena."""
from portable_coordinate_typed_weapon_specs import COORDINATE_OUTPUT_WORDS
SOURCE='gpu/world_coordinate_typed_aim_entry.slang'
HEAD=220224;WORDS=544

def regions():
    from portable_arena_specs import Region
    from portable_coordinate_typed_weapon_specs import regions as prior
    rows,iw,ow=prior();rows=[r for r in rows if r.name!='typed-weapon-reserved-history-tail']
    rows += [Region('output','typed-aim-reserved-before',COORDINATE_OUTPUT_WORDS+220216,8),Region('output','typed-aim-frame',COORDINATE_OUTPUT_WORDS+HEAD,WORDS),Region('output','typed-aim-reserved-after',COORDINATE_OUTPUT_WORDS+HEAD+WORDS,262144-HEAD-WORDS)]
    return rows,iw,ow

def check_layout(root):
    from pathlib import Path
    from portable_arena_specs import audit_regions
    from portable_coordinate_typed_weapon_specs import check_layout as prior
    plan=prior(root);rows,iw,ow=regions();assert audit_regions(rows,iw,ow)['address_plan_verified']
    text=(Path(root)/'gpu/coordinate_typed_aim_runtime.slang').read_text()
    for literal in ('DT_OUTPUT(s.resourceOutput,220224)','h+32+i*4','i<512'):
        assert literal in text,literal
    return dict(plan,typed_aim_frame_words=WORDS,typed_slots=128,focus_id_bits=9,extra_runtime_bytes=0,extra_output_words=0)
