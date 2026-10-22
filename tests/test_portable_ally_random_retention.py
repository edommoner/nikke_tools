"""The combined batch keeps each family's original full input bytes and labels."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]

class AlliedRandomRetentionTests(unittest.TestCase):
    def test_all_original_inputs_and_rejection_domains_retained(self):
        s=importlib.util.spec_from_file_location('ally_random_retention_test',ROOT/'research/verify-world-ally-random-retention-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        import nikke_gpu as cli
        with cli.forbid_gpu():entries,data=m.prepare()
        self.assertEqual(len(entries),1234);self.assertEqual(len(set(e[0] for e in entries)),1234)
        self.assertEqual(sum(e[2] is not None for e in entries),980)
        offset=0;stride=m.suite.INPUT*4
        for family in m.FAMILIES:
            golden=json.loads((ROOT/cli.SUITES[family]['golden']).read_text());count=len(golden['entries']);selected=entries[offset:offset+count]
            expected_input=count.to_bytes(4,'little')+data[4+offset*stride:4+(offset+count)*stride]
            self.assertEqual(hashlib.sha256(expected_input).hexdigest(),golden['input_sha256'],family)
            self.assertEqual([e[0] for e in selected],[family+'/'+e['name'] for e in golden['entries']])
            offset+=count
        self.assertEqual(offset,1234)

if __name__=='__main__':unittest.main()
