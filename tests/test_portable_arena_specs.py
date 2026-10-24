"""Input/output arena composition must preserve capacities and real declarations."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app')]
from portable_arena_specs import (Region, audit_live_sources, audit_profile,
    audit_regions, attack_group_layout, coordinate_layout, composed_shader_schema)


class ArenaSpecsTests(unittest.TestCase):
    def test_real_legacy_readers_and_both_profiles_are_verified(self):
        self.assertTrue(audit_live_sources(ROOT)['legacy_shader_declarations_verified'])
        for name in ('coordinate','attack-group'):
            row=audit_profile(name)
            self.assertTrue(row['address_plan_verified'])
            self.assertTrue(row['runtime_connected'])
        import portable_battle_attack_group_input as host
        layout=attack_group_layout()
        for symbol,key in [('HEADER','HEADER'),('SLOTS','SLOTS'),('SLOT_WORDS','WORDS'),
                           ('LOG','LOG'),('LOG_CAPACITY','LOG_CAP'),('PACKETS','PACKETS'),
                           ('COMPACT','COMPACT'),('COMPACT_WORDS','COMPACT_WORDS')]:
            self.assertEqual(getattr(host,symbol),layout[key])

    def test_legacy_combination_rejects_input_live_output_and_clear_tail_collisions(self):
        row=audit_profile('combined-legacy')
        self.assertFalse(row['address_plan_verified'])
        self.assertFalse(row['runtime_connected'])
        inputs=[r for r in row['overlaps'] if r['domain']=='input']
        self.assertEqual([(r['start'],r['end']) for r in inputs],[(107584,107592)])
        self.assertEqual([(r['first'],r['second']) for r in inputs],[('coordinate-scene','coordinate-area')])
        outputs=[r for r in row['overlaps'] if r['domain']=='output']
        self.assertEqual(sum(r['words'] for r in outputs if 'coordinate-clear-tail' not in (r['first'],r['second'])),235096)
        self.assertTrue(any('coordinate-clear-tail' in (r['first'],r['second']) for r in outputs))

    def test_composed_plan_retains_every_capacity_and_marks_battle_unconnected(self):
        row=audit_profile('combined-v1')
        self.assertTrue(row['address_plan_verified'])
        self.assertFalse(row['runtime_connected'])
        self.assertFalse(row['gpu_execution_verified'])
        self.assertEqual((row['input_words'],row['output_words']),(108648,1310720))
        before,after=coordinate_layout(),coordinate_layout(1048576)
        addresses={'BASE','FRAME','CAST','PACKETS','TRACE','SELECTION','END'}
        for key in before:
            self.assertEqual(after[key]-before[key],262144 if key in addresses else 0)
        self.assertEqual((ROOT/'gpu/composed_arena_layout.slang').read_text(),composed_shader_schema())
        self.assertEqual(attack_group_layout()['COMPACT_WORDS'],186528)

    def test_all_overlaps_are_reported_including_containment_and_adjacency(self):
        rows=[Region('output','large',0,100),Region('output','small-a',10,5),
              Region('output','small-b',20,5),Region('output','adjacent',100,10),
              Region('input','other-domain',0,100)]
        result=audit_regions(rows,100,110)
        self.assertEqual(len(result['overlaps']),2)
        self.assertEqual([r['words'] for r in result['overlaps']],[5,5])
        self.assertTrue(audit_regions([rows[0],rows[3],rows[4]],100,110)['address_plan_verified'])

    def test_invalid_dimensions_domains_and_capacity_shrink_are_rejected(self):
        for row in [Region('output','bad',-1,4),Region('output','bad',0,0),
                    Region('output','bad',100,1),Region('output','bad',False,1),
                    Region('unknown','bad',0,1)]:
            with self.subTest(row=row),self.assertRaises(ValueError):audit_regions([row],100,100)
        with self.assertRaises(ValueError):audit_regions([Region('input','same',0,1),Region('output','same',0,1)],100,100)
        with self.assertRaises(ValueError):attack_group_layout(1024)
        with self.assertRaises(ValueError):coordinate_layout(1)

    def test_real_shader_declaration_mutations_are_rejected(self):
        original=Path.read_bytes
        for name,old,new in [('coordinate_packet_layout.slang',b'CP_CASTS=32',b'CP_CASTS=16'),
                             ('attack_group_runtime.slang',b'AG_HEADER=800000',b'AG_HEADER=790000'),
                             ('attack_group_runtime.slang',b'inputBase+104400',b'inputBase+104408'),
                             ('world_coordinate_area_entry.slang',b'i=CP_BASE',b'i=800000'),
                             ('composed_arena_layout.slang',b'COMPOSED_INPUT_WORDS=108648',b'COMPOSED_INPUT_WORDS=108640')]:
            def changed(path):
                raw=original(path)
                return raw.replace(old,new,1) if path.name==name else raw
            with self.subTest(name=name),patch.object(Path,'read_bytes',changed),self.assertRaises(ValueError):audit_live_sources(ROOT)

    def test_cli_exit_status_preserves_unsafe_result_and_never_runs_gpu(self):
        with tempfile.TemporaryDirectory() as folder:
            for profile,status in [('combined-legacy',1),('combined-v1',0)]:
                out=Path(folder)/(profile+'.json')
                process=subprocess.run([sys.executable,str(ROOT/'scripts/nikke_gpu.py'),'arena-check',
                    '--profile',profile,'--out',str(out)],cwd=ROOT,capture_output=True,text=True)
                self.assertEqual(process.returncode,status,process.stderr)
                result=json.loads(out.read_bytes())
                self.assertEqual(result['gpu_calls'],0)
                self.assertFalse(result['calculation_verified'])
                self.assertEqual(result['address_plan_verified'],status==0)


if __name__=='__main__':unittest.main()
