import copy,importlib.util,json,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('portable_probe_verifier',ROOT/'scripts/verify-portable-probe.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


class PortableProbeTests(unittest.TestCase):
    def test_fixture_wire_dimensions_and_invalid_commands(self):
        cases=json.loads(probe.FIXTURE.read_text(encoding='utf-8'))['cases']
        data=probe.pack_cases(cases);self.assertEqual(len(data),(1+len(cases)*97)*4)
        self.assertEqual(struct.unpack_from('<I',data)[0],len(cases))
        for bad in (-1,2**32,True):
            changed=copy.deepcopy(cases);changed[0]['steps'][0][2]=bad
            with self.assertRaises(ValueError):probe.pack_cases(changed)
        changed=copy.deepcopy(cases);changed[0]['steps'][0][0]=99
        with self.assertRaises(ValueError):probe.pack_cases(changed)


if __name__=='__main__':unittest.main()
