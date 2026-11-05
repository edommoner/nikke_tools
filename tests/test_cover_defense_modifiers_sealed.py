"""Current compensated aggregate, original Noah source and old raw retention."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
def read(path):return json.loads((ROOT/path).read_text())
class ModifiersSealed(unittest.TestCase):
    def test_historical_source_and_all_thirteen_inputs_remain_bound_to_fresh_seal(self):
        from portable_weighted_incoming_source_contract import historical_hashes
        s=importlib.util.spec_from_file_location('modifier_sealed_adapter',ROOT/'research/verify-cover-defense-modifiers.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows,data=m.prepare()
        golden=read('research/portable-cover-defense-modifiers-v1-expected.json');proof=read('tests/fixtures/cover-defense-modifiers-metal-v1.json');audit=read('tests/fixtures/cover-defense-modifiers-independent-v1.json')
        self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(13,6))
        self.assertEqual(hashlib.sha256(data).hexdigest(),golden['input_sha256']);self.assertEqual(historical_hashes(ROOT,m.SOURCE),golden['source_sha256'])
        for key in ('input_sha256','output_sha256'):
            self.assertEqual(proof[key],golden[key]);self.assertEqual(audit[key],golden[key])
        self.assertEqual(proof['source_sha256'],golden['source_sha256']);self.assertEqual(proof['generated_normalized'],golden['generated_normalized'])
        self.assertFalse(audit['live_parent_receipt_present']);self.assertEqual(audit['gpu_calls'],0);self.assertEqual((audit['input_count'],audit['native_cases']),(13,6))
        self.assertTrue(proof['compensated_received_aggregate']);self.assertEqual(proof['runtime_extra_bytes'],40)
        self.assertEqual(proof['original_probability_activations'],[3,3]);self.assertEqual(proof['nonzero_received_receipts'],22)

if __name__=='__main__':unittest.main()
