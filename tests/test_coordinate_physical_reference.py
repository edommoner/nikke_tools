"""Canonical expanded physical packets, not GPU coverage."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research')]


class NativePhysicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import engine_worker
        from portable_coordinate_physical_cases import fixtures
        from world_coordinate_physical_native import observe
        cls.cases=fixtures();cls.answers={c['name'].split('/')[-1]:observe(c) for c in cls.cases}

    def test_occlusion_is_not_area_contains_and_body_rounding_is_preserved(self):
        row=self.answers['occlusion-and-body']['physical_pellets'][0]
        self.assertEqual([e['target'] for e in row['packets']],['','front'])
        self.assertGreater(row['part_fraction'],0)
        self.assertLess(row['part_fraction'],1)
        self.assertEqual(row['landing']['front'][1],0)
        self.assertEqual([e['damage'] for e in row['packets']],[1957,65])

    def test_tiny_body_packet_is_retained_even_when_rounded_damage_is_zero(self):
        row=self.answers['full-front']['physical_pellets'][0]
        self.assertGreater(row['body_fraction'],0)
        self.assertLess(row['body_fraction'],1e-12)
        self.assertEqual([(e['target'],e['damage']) for e in row['packets']],[('',0),('front',3000)])
        row=self.answers['interrupt-front']['physical_pellets'][0]
        self.assertEqual(row['part_fraction'],0)
        self.assertEqual(row['packets'][-1]['target'],'stop')

    def test_muzzles_pellets_and_expanded_packet_count_are_distinct(self):
        rows=self.answers['two-muzzles-three-pellets']['physical_pellets']
        self.assertEqual(len(rows),6)
        self.assertEqual(sum(len(r['packets']) for r in rows),12)
        self.assertTrue(all([p['damage'] for p in r['packets']]==[653,22] for r in rows))

    def test_next_frame_retirement_changes_front_geometry(self):
        rows=self.answers['retirement']['physical_pellets']
        self.assertEqual([p['target'] for p in rows[0]['packets']],['','front'])
        self.assertEqual([p['target'] for p in rows[1]['packets']],['','behind'])
        self.assertGreater(rows[1]['time'],rows[0]['time'])

    def test_reach_and_charge_use_the_real_native_packet_producer(self):
        for key in ['pierce-reach','charge-pierce']:
            rows=self.answers[key]['physical_pellets'];self.assertTrue(rows)
            for row in rows:
                self.assertGreater(row['grow'],0)
                self.assertEqual([p['target'] for p in row['packets']],['','front','behind'])
                self.assertEqual([p['extra'] for p in row['packets']],[False,True,True])


if __name__=='__main__':unittest.main()
