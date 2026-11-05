"""Original squad composition must retain independently admitted MODE owners."""
import copy,math,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker
import portable_detail as product
from portable_specs import LIMITS as L,FIELDS as F
from portable_revival_specs import MAGIC
from portable_stack_specs import META_MAGIC,pack_metadata
from portable_runtime import double_words

def checked_revival_seed(words,L,row,*,stack_enabled=True):
    """CPU mirror of initializeRevival's kind29 descriptor checks (no battle).

    This diagnoses the static union only; GPU execution/CPU parity remain
    separate requirements. Addresses are relative to one unframed program.
    """
    from portable_specs import FIELDS as F
    def number(at):
        import struct
        return struct.unpack('<d',struct.pack('<II',*words[at:at+2]))[0]
    d=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
    mode=L['MODE_BASE']+row*L['MODE_WORDS']
    health=L['HEALTH_DEFINITION_BASE']+row*L['HEALTH_DEFINITION_WORDS']
    extra=L['DEFINITION_EXTRA_BASE']+row*L['DEFINITION_EXTRA_WORDS']
    value=number(d+F['VALUE'])
    if (words[3]==0 or words[L['WORLD_FRAME_INPUT_BASE']]==0 or
        words[d+F['KIND']]!=29 or words[d+F['STAT']]!=0 or
        words[health+3]!=0 or words[d+F['TARGET']]>1 or words[extra+3]!=0 or
        words[health]!=0 or words[health+1]!=0 or words[d+F['DAMAGE_FLAGS']]!=0 or
        not math.isfinite(value) or value<=0 or number(d+F['INTERVAL'])!=0 or
        words[mode]!=MAGIC or words[mode+3]!=0 or any(words[mode+4:mode+28])):
        raise ValueError(f'initializeRevival kind29 descriptor refused at row {row}, MODE word {mode}')
    if stack_enabled and any(words[mode+28:mode+L['MODE_WORDS']]):
        raise ValueError(f'validStackDefinitions revival tail refused at row {row}')
    return words[mode+1]|(words[mode+2]<<32)


SQUAD=['미카 : 스노우 버디','아르카나 : 포츈 메이트','홍련 : 신살','마나','누아르']

class ProductRevivalStackUnionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        demo=engine_worker.demo(True)
        cls.body=dict(profile=demo['profile'],patches={},stat_deltas={},squad=SQUAD,
            compute_backend='native_detail',verify_detail=True,duration=180,level=400,
            burst_policy='rules',shooting_policy='auto',burst_gauge_mode='fixed',seed=0,
            weapon_mode_swap=False,enemy={'def':31784,'code':'풍압','core_px':0,'distance':30,'parts':[],'patterns':[]})
        prepared,_=product.prepare(cls.body)
        cls.source,_,_,cls.words,cls.meta=product.compile_product(prepared)

    def test_original_mana_revive_is_admitted_with_stack_operators(self):
        self.assertTrue(self.meta['stack_operators'])
        self.assertEqual(self.meta['effects'][84],'매터 감마 3')
        self.assertEqual(self.meta['names'][self.meta['binding_owners'][84]],'마나')
        self.assertEqual(checked_revival_seed(self.words,L,84),0)
        at=L['MODE_BASE']+84*L['MODE_WORDS']
        self.assertEqual(self.words[at:at+4],[MAGIC,0,0,0])
        self.assertIn('if(d.kind==29)', (ROOT/'gpu/stack_runtime.slang').read_text())

    def test_original_overwritten_tag_and_malformed_seed_reserved_word_are_rejected(self):
        at=L['MODE_BASE']+84*L['MODE_WORDS']
        for offset,value in ((0,META_MAGIC),(3,1),(4,1),(28,1),(31,1)):
            words=list(self.words);words[at+offset]=value
            with self.subTest(offset=offset),self.assertRaisesRegex(ValueError,'row 84'):
                checked_revival_seed(words,L,84)

    def test_stack_packer_preserves_revival_seed_and_still_packs_carrier(self):
        effects=[(dict(type='instant',stat='revive',name='revive'),0),
                 (dict(type='instant',stat='buff_stack_add',target_effect='carrier'),0),
                 (dict(type='buff',stat='atk_pct',name='carrier'),0)]
        words=[0]*L['INPUT_WORDS'];at=L['MODE_BASE']
        words[at:at+4]=[MAGIC,0x89abcdef,0x12345678,0]
        pack_metadata(words,L,effects,double_words)
        self.assertEqual(words[at:at+4],[MAGIC,0x89abcdef,0x12345678,0])
        self.assertEqual(words[at+2*L['MODE_WORDS']],META_MAGIC)
