"""Counter resources stay verified without becoming ordinary enemy fields."""
import array,importlib.util,struct,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_specs import LIMITS as L

def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
recipient=module('counter_field_decode_recipient','research/verify-world-actor-recipients.py')
fields=module('counter_field_decode_fields','research/verify-world-actor-fields.py')

class CounterFieldDecodeTests(unittest.TestCase):
    def test_refresh_distinguishes_decoding_from_native_execution_changes(self):
        from portable_original_history_repackage import changed_functions
        before='def decoded(): pass\ndef native_reference(): pass\n'
        after='def decoded(): return 1\ndef native_reference(): pass\n'
        self.assertEqual(changed_functions(before,after),{'decoded'})
        self.assertEqual(changed_functions(before,after.replace('native_reference(): pass','native_reference(): return 2')),{'decoded','native_reference'})

    def fixture(self,shared):
        block=array.array('I',[0])*524288;block[9]=2
        case=dict(effects=[dict(type='buff',stat='target_hit_counter',target='boss',name='counter'),dict(type='buff',stat='received_dmg_pct',target='boss',name='real-field')],owners=[0,0])
        for slot in range(2):
            p=L['CARRIER_STATE_BASE']+slot*L['CARRIER_WORDS'];block[p:p+5]=array.array('I',[slot,slot,0,1,1]);block[p+5:p+7]=array.array('I',struct.unpack('<II',struct.pack('<d',10.)))
            key=L['WORLD_ACTOR_FIELD_KEY_BASE']+slot*4;block[key:key+4]=array.array('I',[0x80000001 if shared else 1,1,0,0])
            at=L['WORLD_ACTOR_RECIPIENT_BASE']+16+slot*L['WORLD_ACTOR_RECIPIENT_WORDS'];block[at]=1;block[at+1]=1;block[at+2]=1;block[at+8]=1
        return block,case,[SimpleNamespace(kind=0,identity=0)]
    def test_shared_decoder_keeps_real_fields_and_separate_counter_resources(self):
        block,c,bindings=self.fixture(True);before=block.tobytes();resources=dict(epoch=6,resources=[dict(name='counter',credit=0)])
        with patch.object(recipient.state,'decoded',return_value=dict(enemy_fields={},target_counters=resources)):
            actual=recipient.decoded(block,{},c,bindings)
        self.assertEqual([r['name'] for r in actual['enemy_fields']['carriers']],['real-field']);self.assertEqual(actual['enemy_fields']['recipient_memberships'],[[[0,0,1]]]);self.assertIs(actual['target_counters'],resources);self.assertEqual(block.tobytes(),before)
    def test_single_recipient_decoder_uses_the_same_definition_classifier(self):
        block,c,bindings=self.fixture(False);before=block.tobytes()
        with patch.object(fields.pool,'decoded',return_value={}):actual=fields.decoded(block,{},c,bindings)
        self.assertEqual([r['name'] for r in actual['enemy_fields']['carriers']],['real-field']);self.assertEqual(block.tobytes(),before)

if __name__=='__main__':unittest.main()
