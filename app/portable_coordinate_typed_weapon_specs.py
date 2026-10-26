"""Weapon-only ownership of the existing typed arena; no wire/Runtime growth."""
from pathlib import Path
from portable_coordinate_typed_specs import INPUT_WORDS,OUTPUT_WORDS,COORDINATE_OUTPUT_WORDS
SOURCE='gpu/world_coordinate_typed_weapon_entry.slang'
HEAD=170976;HEADER_WORDS=64;RETAINED=2048;RECORD_WORDS=24

def regions():
    from portable_arena_specs import Region
    from portable_coordinate_typed_specs import regions as prior
    rows,iw,ow=prior();rows=[r for r in rows if r.name not in ('typed-output-dfs-scratch','typed-output-clear-tail')]
    for name,offset,count in (
        ('pellet-snapshot',153568,8192),('generation-snapshot',161760,128),('counter-packet',161888,16),
        ('reserved-weapon-scratch-tail',161904,9072),('history-header',HEAD,64),
        ('history-retained',171040,49152),('history-overflow-temporary',220192,24),('reserved-history-tail',220216,41928),
    ):rows.append(Region('output','typed-weapon-'+name,COORDINATE_OUTPUT_WORDS+offset,count))
    return rows,iw,ow

def check_layout(root):
    from portable_coordinate_typed_specs import check_layout as prior
    from portable_arena_specs import audit_regions
    from portable_coordinate_sampling_bank import LAYOUT
    root=Path(root);plan=prior(root);rows,iw,ow=regions();audit=audit_regions(rows,iw,ow)
    if not audit['address_plan_verified']:raise ValueError('Typed weapon arena overlaps')
    if LAYOUT['FRAME']+LAYOUT['TARGETS']*LAYOUT['TARGET_WORDS']!=640 or 640+128!=LAYOUT['META_WORDS']:raise ValueError('Typed ordering must fit the unused sampling metadata tail')
    text=(root/'gpu/coordinate_typed_weapon_runtime.slang').read_text()
    for literal in ('CTW_KEEP=2048U,CTW_WORDS=24U','DT_OUTPUT(s.resourceOutput,170976)','hit*8','+8192','h+64+min(count,CTW_KEEP)*CTW_WORDS'):
        if literal not in text:raise ValueError('Typed weapon consumer arena changed')
    return dict(plan,weapon_only_requires_zero_skill_routes=True,typed_order_words=128,retained_records=RETAINED,all_records_hashed=True,extra_runtime_bytes=0,extra_output_words=0)
