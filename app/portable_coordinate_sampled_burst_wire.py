"""Explicit appended storage for every existing pending entry and literal hit."""
from pathlib import Path
from portable_specs import LIMITS
from portable_coordinate_group_wire import INPUT_WORDS,OUTPUT_WORDS as PREFIX,check_schema as check_prefix
HEAD=919736;HEAD_WORDS=8
SOURCE='gpu/world_coordinate_sampling_burst_entry.slang'
ENTRIES=LIMITS['PENDING'];HITS=256;BASE=PREFIX;WORDS=ENTRIES*HITS*2;OUTPUT_WORDS=BASE+WORDS

def schema():
    return '// Generated sampled pending amount arena; full capacity retained.\n'+''.join(f'static const uint CSB_{k}={v}U;\n' for k,v in dict(BASE=BASE,ENTRIES=ENTRIES,HITS=HITS,WORDS=WORDS,HEAD=HEAD).items())

def check_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1]);check_prefix(root)
    from portable_sampled_damage_totals import BASE as TOTAL_BASE,WORDS as TOTAL_WORDS
    from portable_coordinate_sampling_bank import LAYOUT as BANK
    from portable_coordinate_physical_specs import LAYOUT as CF
    assert max(TOTAL_BASE+TOTAL_WORDS,BANK['RNG']+BANK['RNG_WORDS'])<=HEAD and HEAD+HEAD_WORDS<=CF['END']
    assert not BANK['META']<=HEAD<BANK['META']+BANK['META_WORDS']
    assert (ENTRIES,HITS,BASE,WORDS,OUTPUT_WORDS)==(512,256,1507328,262144,1769472)
    assert (root/'gpu/coordinate_sampled_burst_layout.slang').read_text()==schema()
    assert 'static const uint P_OUTPUT_WORDS = 1769472U;' in (root/'gpu/portable_schema.slang').read_text()
    assert 'outputWords == 1769472' in (root/'scripts/run-metal-probe.swift').read_text()
    return dict(input_words=INPUT_WORDS,output_words=OUTPUT_WORDS,retained_prefix_words=PREFIX,pending_entries=ENTRIES,hits_per_entry=HITS,additional_output_words=WORDS,additional_runtime_bytes=0)
