"""Original probability source, nonzero received scalar and source coefficient guards."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_cover_defense_modifier_contracts import verify
from portable_backend import source_hashes

class CoverModifiers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=importlib.util.spec_from_file_location('modifier_unit_adapter',ROOT/'research/verify-cover-defense-modifiers.py');cls.adapter=importlib.util.module_from_spec(s);s.loader.exec_module(cls.adapter)
        cls.rows,cls.data=cls.adapter.prepare();cls.saved=json.loads((ROOT/'tests/fixtures/cover-defense-modifiers-cpu-v1.json').read_text())
    def test_original_noah_probability_and_all_effects_remain_authored(self):
        self.assertEqual(len(self.rows),13);self.assertEqual(sum(d is not None for _,_,d in self.rows),6)
        for _,_,domain in self.rows[4:6]:
            c=domain[0];contract=c['cover_defense_case']['contract'];row=contract['noah_source_row'];effect=c['effects'][row]
            self.assertEqual(len(c['effects']),69);self.assertEqual(c['names'],['솔져 O.W.','노아','드레이크','자칼','메어리'])
            self.assertEqual(c['owners'][row],1);self.assertEqual(effect['trigger'],dict(timing=['received_hit_count:1'],condition=['prob:10']))
            self.assertEqual(effect['values']['10'],-8.);self.assertEqual(effect['duration'],10.)
            self.assertEqual(hashlib.sha256(json.dumps(effect,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),contract['noah_source_sha256'])
            self.assertEqual(len(c['cover_defense_case']['patterns']),17)
            self.assertEqual(c['cover_defense_case']['patterns'][1]['spec']['hits'],64)
    def test_saved_real_sources_and_passive_observation_equivalence(self):
        self.assertFalse(self.saved['gpu_verified'])
        for row in self.saved['cases']:
            self.assertEqual(verify(row['case'],row['native']),row['contract'])
            self.assertEqual(row['observer_clean_sha256'],row['observer_off_sha256'])
            self.assertEqual(row['contract']['original_probability_activations'],3)
            self.assertEqual(row['contract']['nonzero_received_receipts'],11)
            self.assertEqual(row['contract']['coefficients'],[33.33,137.5,250.])
    def test_corrupt_source_scalar_divisor_and_missing_priming_are_rejected(self):
        row=self.saved['cases'][0]
        for field in ('received_snapshot','coefficient','divisor'):
            bad=copy.deepcopy(row['native']);bad['cover_defense']['receipts'][0][field]+=1
            with self.subTest(field=field),self.assertRaises(AssertionError):verify(row['case'],bad)
        bad=copy.deepcopy(row['native']);bad['received_conditions']['activations'][0]['owner']=0
        with self.assertRaises(AssertionError):verify(row['case'],bad)
        bad=copy.deepcopy(row['native']);bad['received_conditions']['activations'].append(dict(bad['received_conditions']['activations'][0]))
        with self.assertRaises(AssertionError):verify(row['case'],bad)
        bad=copy.deepcopy(row['native']);at=next(i for i,h in enumerate(bad['battle']['hits']) if h['pattern']=='noah-prime' and h['owner']==1);bad['battle']['hits'].pop(at)
        with self.assertRaises(AssertionError):verify(row['case'],bad)
    def test_actual_failure_terms_need_compensation_and_aggregate_is_not_tolerant(self):
        import functools,operator,math
        row=self.saved['cases'][0];terms=[h['hp'] for h in row['native']['battle']['hits'] if h['owner']==3]
        naive=functools.reduce(operator.add,terms,0.);correct=sum(terms)
        self.assertNotEqual(naive,correct);self.assertEqual(math.nextafter(naive,math.inf),correct)
        bad=copy.deepcopy(row['native']);bad['battle']['allies'][3]['received_damage']=naive
        with self.assertRaisesRegex(AssertionError,'compensated received'):verify(row['case'],bad)
        for r in self.saved['cases']:
            verify(r['case'],r['native'])

    def test_same_shader_and_previous_full_cohort_are_retained(self):
        golden=json.loads((ROOT/'research/portable-cover-defense-battle-v1-expected.json').read_text())
        self.assertEqual(self.adapter.SOURCE,'gpu/world_cover_defense_entry.slang')
        from portable_received_sum_source_contract import historical_hashes
        self.assertEqual(historical_hashes(ROOT,self.adapter.SOURCE),golden['source_sha256'])
        previous,_=self.adapter.base.prepare()
        import array
        raw=array.array('I',[len(previous)])
        for _,words,_ in previous:raw.extend(words)
        if sys.byteorder!='little':raw.byteswap()
        self.assertEqual(hashlib.sha256(raw.tobytes()).hexdigest(),golden['input_sha256'])
        import nikke_gpu
        self.assertTrue(nikke_gpu.SUITES['cover-defense-modifiers']['development_only'])
        self.assertEqual(nikke_gpu.SUITES['cover-defense-modifiers']['inputs'],13)

if __name__=='__main__':unittest.main()
