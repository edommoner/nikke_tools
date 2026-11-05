"""Disjoint coordinate and typed-target banks in one resident invocation."""
from pathlib import Path
SOURCE='gpu/world_coordinate_typed_entry.slang'
COORDINATE_INPUT_WORDS=109968
COORDINATE_OUTPUT_WORDS=1769856
TARGET_INPUT_WORDS=5712
TARGET_OUTPUT_WORDS=262144
INPUT_WORDS=COORDINATE_INPUT_WORDS+TARGET_INPUT_WORDS
OUTPUT_WORDS=COORDINATE_OUTPUT_WORDS+TARGET_OUTPUT_WORDS

def layout():
    return dict(input_words=INPUT_WORDS,output_words=OUTPUT_WORDS,input=[dict(name='coordinate',base=0,words=COORDINATE_INPUT_WORDS),dict(name='typed-targets',base=COORDINATE_INPUT_WORDS,words=TARGET_INPUT_WORDS)],output=[dict(name='coordinate',base=0,words=COORDINATE_OUTPUT_WORDS),dict(name='typed-targets',base=COORDINATE_OUTPUT_WORDS,words=TARGET_OUTPUT_WORDS)])

def check_layout(root):
    from portable_specs import check_schema
    check_schema()
    plan=layout()
    for domain in ('input','output'):
        a,b=plan[domain]
        if a['base']+a['words']!=b['base'] or b['base']+b['words']!=plan[domain+'_words']:raise ValueError('Coordinate typed arenas overlap or exceed the declared wire')
    text=(Path(root)/SOURCE).read_text()
    for literal in ('DT_INPUT(s,offset) ((s).inputBase+109968+(offset))','DT_OUTPUT(output,offset) ((output)+1769856+(offset))'):
        if literal not in text:raise ValueError('Coordinate typed consumer layout changed')
    return plan


def regions():
    """Detailed active and clear/reserved owners for the existing arena auditor."""
    from portable_arena_specs import Region
    rows=[Region('input','coordinate-complete-input',0,COORDINATE_INPUT_WORDS),Region('output','coordinate-complete-output',0,COORDINATE_OUTPUT_WORDS)]
    for domain,base,table in [
        ('input',COORDINATE_INPUT_WORDS,[('typed-geometry-or-zero',0,2320),('binding-count',2320,8),('bindings',2328,1536),('reserved-bindings-tail',3864,1256),('descriptor',5120,16),('axes-header',5136,32),('axes',5168,256),('routes',5424,256),('owner-policy',5680,32)]),
        ('output',COORDINATE_OUTPUT_WORDS,[('header',0,16),('reserved-prefix',16,1008),('targets',1024,1792),('clock',2816,16),('reserved-clock-tail',2832,736),('attack-receipts',3568,128*1040),('reserved-receipt-tail',136688,16880),('dfs-scratch',153568,32*544),('clear-tail',170976,91168)])]:
        rows.extend(Region(domain,'typed-'+domain+'-'+name,base+offset,words) for name,offset,words in table)
    return rows,INPUT_WORDS,OUTPUT_WORDS


def audit_reserved(block):
    """Check output owners, clear-only banks and restored common counter context."""
    if len(block)!=OUTPUT_WORDS or block[0]!=0:raise AssertionError('Complete successful coordinate typed output required')
    for region in regions()[0]:
        if region.domain=='output' and ('reserved' in region.name or region.name.endswith('clear-tail')):
            if any(block[region.base:region.end]):raise AssertionError('Coordinate typed clear bank overwritten: '+region.name)
    from portable_specs import LIMITS
    at=LIMITS['COUNTER_CONTEXT_BASE']
    if any(block[at:at+1096]):raise AssertionError('Coordinate typed counter context leaked')
    return True
