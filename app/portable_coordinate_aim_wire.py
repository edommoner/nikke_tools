"""Fixed authored aim wire and private state arena; no runtime decisions packed."""
from pathlib import Path
from portable_coordinate_aim_specs import compile_aim
from portable_coordinate_scene_specs import bits
LAYOUT=dict(BASE_INPUT=108792,HEADER=32,ROWS=40,ROW_WORDS=16,SEQUENCE=672,SEQUENCES=16,INPUT=736,STATE=919840,STATE_WORDS=160,MAGIC=0x43414931)
INPUT_WORDS=LAYOUT['BASE_INPUT']+LAYOUT['INPUT']
OUTPUT_WORDS=1310720

def schema():
    return '// Generated authored coordinate aim layout.\n'+''.join(f'static const uint CI_{k}={v}U;\n' for k,v in LAYOUT.items())

def check_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1])
    assert (root/'gpu/coordinate_aim_layout.slang').read_text()==schema()
    from portable_coordinate_physical_specs import audit_arena,check_schema as check_physical
    from portable_coordinate_cache_specs import LAYOUT as cache,check_schema as check_cache
    from portable_coordinate_core_specs import INPUT_WORDS as core_words
    check_physical(root);check_cache(root);physical=audit_arena(root)
    assert physical['scratch_end']<=LAYOUT['STATE']
    assert LAYOUT['STATE']+LAYOUT['STATE_WORDS']<=cache['BASE']
    assert LAYOUT['BASE_INPUT']==core_words and LAYOUT['HEADER']+LAYOUT['ROWS']*LAYOUT['ROW_WORDS']==LAYOUT['SEQUENCE']
    assert LAYOUT['SEQUENCE']+LAYOUT['SEQUENCES']*4==LAYOUT['INPUT']

def pack(case,descriptors,meta,*,typed_targets=None):
    ir=compile_aim(case,descriptors,names=meta['names'],typed_targets=typed_targets);w=[0]*LAYOUT['INPUT']
    w[:3]=[LAYOUT['MAGIC'],1,ir['mode']]
    for who,owner in enumerate(ir['owners']):
        w[8+who]=len(owner['entries'])
        for i,row in enumerate(owner['entries']):
            when=row['when'];at=LAYOUT['HEADER']+(who*8+i)*16
            w[at:at+8]=[128 if row['target_kind']==0 else row['target_slot'],row['priority']+1,when['kind'],when['code'],when['gate_stage'],when['gate_mask'],meta['states'].get(when.get('buff_name',''),0xffffffff),when.get('minus',0)]
            if when['kind']==0:w[at+6]=0
            else:
                if when['code']!=4:w[at+6]=0xffffffff
                w[at+8:at+12]=when['offset_words']+when['len_words']
    sequence=case.get('sequence',[])
    if len(sequence)>LAYOUT['SEQUENCES']:raise ValueError('Coordinate focus sequence capacity exceeded')
    previous=0.
    for i,e in enumerate(sequence):
        if set(e)-{'t','action','target'} or e.get('action')!='focus' or e.get('target','') not in ['',*meta['names']]:raise ValueError('Coordinate aim requires authored focus-only squad sequence')
        t=float(e.get('t',0));words=bits(t)
        if t<previous or not 0<=t<=180:raise ValueError('Ordered bounded coordinate focus sequence required')
        at=LAYOUT['SEQUENCE']+i*4;w[at:at+4]=[*words,meta['names'].index(e['target'])+1 if e.get('target') else 0,0];previous=t
    w[3]=len(sequence)
    return w
