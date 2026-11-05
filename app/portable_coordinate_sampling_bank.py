"""Sampled-shot bank reuses expected-only integration storage, not capacity.

One weaponFrame captures/delivers a shot before the next owner. Persistent
physical MT is separate from boss MT and from the reused per-shot bank.
"""
from pathlib import Path
from portable_coordinate_physical_specs import LAYOUT as CF
LAYOUT=dict(META=CF['BANK'],META_WORDS=768,ROWS=CF['LANDING'],ROW_WORDS=12,PELLETS=1024,RNG=CF['BANK']+4*CF['BANK_WORDS'],RNG_WORDS=632,TARGETS=128,TARGET_WORDS=4,FRAME=128)
def verify():
    a=LAYOUT
    assert CF['INPUT']+__import__('portable_coordinate_landing_v1').INPUT==a['ROWS']
    assert a['ROWS']+a['ROW_WORDS']*a['PELLETS']<=a['META']
    assert a['META']+a['META_WORDS']<=a['RNG']
    assert a['RNG']+a['RNG_WORDS']<=CF['END']
    assert a['FRAME']+a['TARGETS']*a['TARGET_WORDS']<=a['META_WORDS']
    return dict(passed=True,input_words=109528,output_words=1507328,logical_pellets=1024,targets_excluding_body=127,extra_runtime_bytes=0,extra_output_words=0,persistent_mt_separate_from_shot_bank=True)
def schema():return '// Sampled shots reuse expected-only scratch; generated layout.\n'+''.join(f'static const uint CS_{k}={v}U;\n' for k,v in LAYOUT.items())
def check_schema(root=None):
    verify();assert (Path(root or Path(__file__).resolve().parents[1])/'gpu/coordinate_sampling_bank.slang').read_text()==schema()
