"""Original support branches need real damage, recovery and source receipts."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu as cli
from portable_original_support_profiles import profiles
from portable_original_support_contracts import verify
from world_original_support_native import selected

class OriginalSupportConditions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        m=dict(suite='original-support-conditions',purpose='development',selected_cases=[]);cls.adapter=cli.open_suite(m)
        with patch('calculator.timeline.simulate',side_effect=AssertionError('Packing cannot simulate')):
            cls.rows,_=cli.prepare_entries(cls.adapter,m)

    def fixture(self,case):
        scene=case['catalogue_profile']['scene_witness']['scenario'];pair=scene.startswith('Naga-Tia');injured=scene!='Naga-Tia-shield'
        cover=1 if pair else 0
        hits=[] if not injured else [dict(pattern='hp-first',owner=0,hp=10,cover=0,down=False),dict(pattern='cover-first',owner=cover,hp=0,cover=10,down=False),dict(pattern='hp-second',owner=2,hp=10,cover=0,down=False)]
        if scene=='Naga-Tia-injured-shield':hits.append(dict(pattern='shield-hit',owner=0,hp=0,shield=10,down=False))
        events=[dict(row=i,owner=case['owners'][i],time=4) for i in selected(case) if pair or case['names'][case['owners'][i]]=='티아']
        heals=[]
        for i,(e,o) in enumerate(zip(case['effects'],case['owners'])):
            if case['names'][o] in ('나가','티아') and e.get('stat') in ('heal_hp_pct','cover_heal_pct'):
                before=dict(hp=[100.]*5,cover_hp=[100.]*5);after=copy.deepcopy(before)
                if injured:after['hp' if e['stat']=='heal_hp_pct' else 'cover_hp']=[200.]*5
                heals.append(dict(row=i,owner=o,time=4,stat=e['stat'],name=e['name'],before=before,after=after))
        return dict(burst_controls=dict(ticks=[dict(cycles=1)]),battle=dict(hits=hits),manual_actions=dict(events=[dict(kind='_enter_cover',owner=cover,time=.9)] if injured else []),support_conditions=dict(activations=events,heals=heals),sampled_health_returns=[dict(kind='_apply_lifesteal',hp=[100.]*5),dict(kind='_apply_lifesteal',hp=[200.]*5)])

    def test_all_original_definitions_and_explicit_controls_reach_common_wire(self):
        self.assertEqual(len(self.rows),4);self.assertEqual([len(r[2][0]['effects']) for r in self.rows],[70,75,74,74])
        self.assertEqual(set(r[0] for r in self.rows),set(profiles()))
        for _,words,(case,meta,*_) in self.rows:
            self.assertEqual(len(words),115680);self.assertEqual(case['duration'],30)
            original=case['original_run']['prepared'];self.assertEqual(case['effects'],[r['effect'] for r in original['effects']])
            self.assertFalse(case['declared_owner_counter']);self.assertTrue(meta['ordered_recipients'])
            self.assertEqual(sorted(meta['binding_source_indices']),list(range(len(case['effects']))))
            if case.get('declared_manual_sequences'):
                self.assertTrue(meta['coordinate_original_input']['declared_manual_sequences_applied_after_identity_check'])
                self.assertFalse(meta['coordinate_original_input']['original_controls_preserved'])
                self.assertFalse(any(c.get('control',{}).get('sequence') for c in original['chars']))

    def test_positive_contracts_reject_missing_damage_recovery_cover_or_source(self):
        for _,_,(case,*_) in self.rows:
            n=self.fixture(case);verify(case,n);scene=case['catalogue_profile']['scene_witness']['scenario']
            faults=['source','cycle']
            if scene!='Naga-Tia-shield':faults+=['hp','cover','manual','healing']
            if scene=='Tia-injured':faults+=['lifesteal']
            if scene=='Naga-Tia-injured-shield':faults+=['shield']
            for fault in faults:
                bad=copy.deepcopy(n)
                if fault=='source':bad['support_conditions']['heals'][0]['owner']=4
                elif fault=='cycle':bad['burst_controls']['ticks'][0]['cycles']=0
                elif fault=='hp':bad['battle']['hits'][0]['hp']=0
                elif fault=='cover':bad['battle']['hits'][1]['cover']=0
                elif fault=='manual':bad['manual_actions']['events']=[]
                elif fault=='healing':
                    for h in bad['support_conditions']['heals']:h['after']=copy.deepcopy(h['before'])
                elif fault=='lifesteal':bad['sampled_health_returns'][1]['hp']=[100.]*5
                else:bad['battle']['hits'][-1]['hp']=10
                with self.subTest(scene=scene,fault=fault),self.assertRaises(AssertionError):verify(case,bad)

    def test_no_injury_control_and_solo_shield_conditions_cannot_be_promoted(self):
        for _,_,(case,*_) in self.rows:
            scene=case['catalogue_profile']['scene_witness']['scenario'];n=self.fixture(case)
            if scene=='Naga-Tia-shield':
                heal=next(h for h in n['support_conditions']['heals'] if h['stat']=='heal_hp_pct');heal['after']['hp'][0]+=1
            elif scene=='Naga-injured':
                row=selected(case)[0];n['support_conditions']['activations'].append(dict(row=row,owner=case['owners'][row],time=4))
            else:continue
            with self.subTest(scene=scene),self.assertRaises(AssertionError):verify(case,n)

    def test_unknown_scene_and_negative_source_row_are_rejected(self):
        case=copy.deepcopy(self.rows[0][2][0]);native=self.fixture(case)
        case['catalogue_profile']['scene_witness']['scenario']='unknown'
        with self.assertRaises(AssertionError):verify(case,native)
        case=self.rows[0][2][0];native['support_conditions']['heals'][0]['row']=-1
        with self.assertRaises(AssertionError):verify(case,native)

    def test_sealed_source_inputs_and_cache_only_profile_keep_one_shared_executor(self):
        from portable_backend import source_hashes
        config=cli.SUITES['original-support-conditions'];cached=cli.SUITES['original-support-conditions-cache-only']
        self.assertFalse(config['development_only']);self.assertTrue(cached['require_paired_generation'])
        self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        for key in ('script','source','golden','inputs','native','frozen_cases','input_words','output_words'):
            self.assertEqual(config[key],cached[key])
        _,data=cli.prepare_entries(self.adapter,dict(suite='original-support-conditions',purpose='sealed',selected_cases=[]))
        raw=(ROOT/config['golden']).read_bytes();golden=json.loads(raw)
        self.assertEqual(hashlib.sha256(data).hexdigest(),golden['input_sha256'])
        self.assertEqual(golden['source_sha256'],source_hashes(config['source']))
        prior=json.loads((ROOT/'research/portable-original-catalogue-support-v1-expected.json').read_text())
        self.assertEqual(golden['source_sha256'],prior['source_sha256'])
        self.assertEqual(golden['generated_normalized'],prior['generated_normalized'])
        certificate=json.loads((ROOT/cli.SUITES[cli.compiler_alias('original-support-conditions')]['golden']).read_text())
        self.assertEqual(certificate['baseline_golden_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(certificate['source_sha256'],golden['source_sha256'])
        self.assertFalse(certificate['calculation_verified'])
        receipt=json.loads((ROOT/'tests/fixtures/original-support-conditions-independent-v1.json').read_text())
        self.assertEqual((receipt['input_count'],receipt['native_cases'],receipt['gpu_calls']),(4,4,0))
        self.assertFalse(receipt['live_parent_receipt_present'])
        for key in ('input_sha256','output_sha256'):self.assertEqual(receipt[key],golden[key])

if __name__=='__main__':unittest.main()
