"""Real CPU release lifetime witnesses plus exact shared-source audit guards."""
import importlib.util,sys,unittest,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('coordinate_accum_adapter',ROOT/'research/verify-coordinate-accum-emission-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class AccumEmissionTests(unittest.TestCase):
    def test_packing_has_no_native_or_computed_quantities(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No oracle packing')),patch('coordinate_landing_reference.landing',side_effect=AssertionError('No probability packing')):
            rows,raw=a.prepare()
        self.assertEqual(len(rows),84);self.assertEqual(sum(d is not None for _,_,d in rows),78)
        self.assertEqual(len(raw),4+84*a.INPUT_WORDS*4)
        old,_=a.parent.prepare();self.assertEqual(rows[:31],old)

    def test_real_native_release_lifetimes_and_exclusions(self):
        from portable_coordinate_accum_emission_cases import fixtures
        values={c['name'].split('/')[-1]:a.native_reference((c,None,None,None)) for c in fixtures()}
        def emissions(label):return [e['amount'] for e in values[label]['damage_accumulation']['events'] if e['kind']=='emission']
        for label,expected in {'dealt-default':[900],'received-default':[4500],'base50-named25':[675],'absent-base-named25':[1125],'zero-base-named25':[225],'split-only-and-int-truncation':[1126],'release-feeds-another-pool':[900,9900],'duplicate-name-last-archive':[4500],'last-owner-cap-snapshot':[2000],'scatter-two-muzzles':[1800],'ordered-baseline-cancellation':[9],'all-pools-full-before-notices':[500,500]}.items():self.assertEqual(emissions(label),expected,label)
        for label in ['fully-occluded','explicit-zero-base','negative-rate','zero-cap','negative-cap','empty-expiry','missing-name','refresh-clears-archive']:self.assertEqual(emissions(label),[],label)
        for name,v in values.items():
            events=v['damage_accumulation']['events'];em=[e for e in events if e['kind']=='emission']
            names={e['name'] for e in em};land=[p for p in v['landed_packets'] if p['skill_name'] in names]
            self.assertEqual(len(land),len(em),name)
            self.assertTrue(all(not p['target'] for p in land),name)
            self.assertEqual(sorted(p['damage'] for p in land),sorted(e['amount'] for e in em),name)
        first=values['dealt-default'];self.assertEqual(first['skill_trace'][0]['created'],.41666666666666663)
        self.assertEqual(first['skill_trace'][0]['landed'],.41666666666666663)
        self.assertTrue(any(p['target'] for p in first['landed_packets']))

    def test_release_comparison_keeps_world_packet_and_pool_comparators(self):
        from portable_coordinate_accum_emission_cases import fixtures
        case=fixtures()[0];domain=(case,{'states':{}},None,None);native={'damage_accumulation':{'final':{}},'sentinel':'full world'}
        with patch.object(a,'native_reference',return_value=native),patch.object(a.parent,'compare_expected') as world,patch.object(a,'compare_final') as pool:
            self.assertEqual(a.compare([0],domain),native)
            world.assert_called_once_with([0],domain,{'sentinel':'full world'},verify_parent_quantity=False)
            pool.assert_called_once_with([0],domain[1],native['damage_accumulation'])
            pool.side_effect=AssertionError('mutated pool')
            with self.assertRaises(AssertionError):a.compare([0],domain)

    def test_passive_accumulation_observer_restores_nested_hooks_on_failure(self):
        from portable_coordinate_accum_emission_cases import fixtures
        from calculator.buff_manager import BuffManager
        from calculator import timeline
        before=(sys.getprofile(),BuffManager.notify,timeline.HitEvent)
        with patch.object(a,'observe',side_effect=ValueError('injected')):
            with self.assertRaises(ValueError):a.native_reference((fixtures()[0],None,None,None))
        self.assertEqual(before,(sys.getprofile(),BuffManager.notify,timeline.HitEvent))

    def test_source_inverse_rejects_unregistered_emission_edits(self):
        from portable_coordinate_accum_emission_source_contract import project_sources
        data=json.loads((ROOT/'tests/fixtures/portable-coordinate-accum-emission-source-delta.json').read_text());projected=project_sources(ROOT)
        for name,row in data['sources'].items():
            self.assertEqual(projected[name],row['baseline'])
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed\n'})

if __name__=='__main__':unittest.main()
