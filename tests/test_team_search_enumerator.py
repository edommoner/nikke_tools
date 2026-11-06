"""Tiny brute force, exact coverage, stable ties and worker determinism (<30s)."""
import copy, ctypes as C, importlib.util, itertools, json, os
from pathlib import Path
import shutil, subprocess, sys, tempfile, unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/team-search'))
import l2_fast, l2_score, l2_score_s20

class EnumeratorTests(unittest.TestCase):
    def test_brute_force_and_partitions(self):
        if not shutil.which('clang++') or not shutil.which('node'):self.skipTest('clang++/node unavailable')
        sys.path.insert(0,str(ROOT/'app'))
        from portable_wasm import toolchain
        compiler,env=toolchain(ROOT)
        try:subprocess.check_output([str(compiler),'--version'],env=env,stderr=subprocess.STDOUT,timeout=10)
        except (OSError,subprocess.SubprocessError):self.skipTest('WASM toolchain unavailable')
        spec=importlib.util.spec_from_file_location('verify_enum',ROOT/'research/team-search/l2_fast/verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
        lib=l2_fast.build();wasm=l2_fast.build(True)
        out=Path(tempfile.mkdtemp(prefix='s21-enum-'))
        for mask in (None,2,15):
            p=v.synthetic()
            if mask is not None:
                p['s20']={'version':2,'switches':mask}
                # Conditional stage override: original B1 becomes B2 only with
                # another literal B1; tests the effective-stage filter.
                p['characters']['a']['mechanics_s20']=[[1,0,2,1,2.,0,0]]
            score=l2_fast.Score(p,library=lib);roster=list(reversed(range(7)))
            oracle=(l2_score if mask is None else l2_score_s20).Score(p)
            cycle=l2_score.cycle if mask is None else l2_score_s20.cycle
            expected=[]
            for ids in itertools.combinations(range(7),5):
                squad=[score.names[i] for i in ids]
                if cycle(squad,p['characters'],180.)[2]:expected.append(dict(indices=list(ids),score=oracle(squad)))
            expected.sort(key=lambda r:(-r['score'],r['indices']))
            for stride in (1,3):
                filtered=[]
                for rank,ids in enumerate(itertools.combinations(range(7),5)):
                    if rank%stride==0:filtered += [r for r in expected if r['indices']==list(ids)]
                filtered.sort(key=lambda r:(-r['score'],r['indices']))
                for k in (1,100):
                    native=l2_fast.enumerate_top(score,roster,k,1,stride)
                    threaded=l2_fast.enumerate_top(score,roster,k,10,stride)
                    self.assertEqual(native['entries'],filtered[:k]);self.assertEqual(native['entries'],threaded['entries'])
                    self.assertEqual(native['counts']['visited'],21)
                    self.assertEqual(native['counts']['scored'],len(filtered))
                table=out/f'{mask}.l2ft';table.write_bytes(score.raw);rfile=out/'roster.json';rfile.write_text(json.dumps(roster))
                for workers in (1,10):
                    r=json.loads(subprocess.check_output(['node',str(ROOT/'research/team-search/l2_fast/runner.mjs'),'--enumerate','--wasm',str(wasm),'--table',str(table),'--roster',str(rfile),'--k','100','--workers',str(workers),'--stride',str(stride)]))
                    self.assertEqual(r['entries'],filtered);self.assertEqual(r['counts']['scored'],len(filtered))
            cli=json.loads(subprocess.check_output([str(lib.parent/'l2-cli'),str(table),'--enumerate','100','10','1',*map(str,roster)]))
            self.assertEqual(cli['entries'],expected)
            with self.assertRaises(ValueError):l2_fast.enumerate_top(score,[0,0,1,2,3])
            with self.assertRaises(ValueError):l2_fast.enumerate_top(score,roster,k=0)
            score.close()
        # Every covered score ties: lexicographic ascending indices must win.
        p=v.synthetic()
        for c in p['characters'].values():
            for g in c['groups']:g['unit']=0.
        score=l2_fast.Score(p,library=lib)
        a=l2_fast.enumerate_top(score,list(range(7)),3,10)['entries']
        self.assertEqual([r['indices'] for r in a],sorted(r['indices'] for r in a))
        self.assertTrue(all(r['score']==1. for r in a))

if __name__=='__main__':unittest.main()
