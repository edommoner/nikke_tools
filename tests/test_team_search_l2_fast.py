"""Small native/WASM raw-binary64 regression (no external evidence required)."""
import importlib.util
import copy
import os
import subprocess
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]

class FastL2Tests(unittest.TestCase):
    def test_native_wasm_bit_identity(self):
        if not shutil.which('clang++') or not shutil.which('node'):self.skipTest('clang++/node unavailable')
        sys.path.insert(0,str(ROOT/'app'))
        from portable_wasm import toolchain
        compiler,env=toolchain(ROOT)
        if not os.access(compiler,os.X_OK):self.skipTest('em++ unavailable')
        try:subprocess.check_output([str(compiler),'--version'],env=env,stderr=subprocess.STDOUT,timeout=10)
        except (OSError,subprocess.SubprocessError):self.skipTest('em++ unavailable')
        spec=importlib.util.spec_from_file_location('l2_fast_verify',ROOT/'research/team-search/l2_fast/verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
        import itertools,random
        p=v.synthetic();names=list(p['characters']);rng=random.Random(190019)
        squads=[rng.sample(names,5) for _ in range(256)]+[list(s) for s in itertools.islice(itertools.permutations(names,5),128)]
        out=Path(tempfile.mkdtemp(prefix='s19-fast-test-'))
        r=v.compare(p,squads,out,v.l2_fast.build(),v.l2_fast.build(True),'synthetic')
        self.assertEqual(r['differences'],0)
        self.assertTrue(all(r['opcode_visits'].values()))
        lib=v.l2_fast.build();wasm=v.l2_fast.build(True)
        for i,duration in enumerate((0.,3.,3.1,3.2,3.57,15.57,2000.)):
            q=copy.deepcopy(p);q['settings']['duration']=duration
            if i==6:
                # Exercise the 32-cycle cap and generic A-stage multi-use.
                q['characters']['a']['metadata']['burst_stage']='A'
                for c in q['characters'].values():c['metadata']['burst_cooldown']=0.
            edge=v.compare(q,[names[:5],names[1:6],list(reversed(names[:5]))],out,lib,wasm,'edge'+str(i))
            self.assertEqual(edge['differences'],0)
        score=v.l2_fast.Score(p)
        self.assertEqual(score.score_many(squads[:3]),[score(s) for s in squads[:3]])
        with self.assertRaises(ValueError):score([names[0]]*5)
        score.close()
        with self.assertRaises(RuntimeError):score(squads[0])

if __name__=='__main__':unittest.main()
