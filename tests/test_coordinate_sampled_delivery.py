"""Real sampled ownership, skill-mode exclusions and retained source identity."""
import copy,importlib.util,sys,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_coordinate_sampled_delivery_cases import fixtures
from world_coordinate_sampled_delivery_native import observe
from portable_coordinate_sampled_delivery_contracts import verify
s=importlib.util.spec_from_file_location('delivery_test_adapter',ROOT/'research/verify-coordinate-sampled-delivery-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class DeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures();cls.before=copy.deepcopy(cls.cases);cls.answers={c['name'].rsplit('/',1)[1]:observe(c)[0] for c in cls.cases}
    def test_native_contracts_and_immutable_inputs(self):
        self.assertEqual(len(self.cases),14);self.assertEqual(self.cases,self.before)
        for c in self.cases:self.assertTrue(verify(c,self.answers[c['name'].rsplit('/',1)[1]])['verified'])
    def test_skill_flag_is_live_and_first_coefficient_is_actual(self):
        for label in ['skill-auto','skill-charge-parent','skill-first','skill-life']:self.assertTrue(any(s['skill_damage'] for s in self.answers[label]['sampled_live_shots']))
        mode=[s for s in self.answers['skill-first']['sampled_live_shots'] if s['mode']];self.assertEqual(mode[0]['coefficient'],277);self.assertTrue(all(s['coefficient']==123 for s in mode[1:]))
    def test_skill_modes_do_not_enter_normal_shot_groups(self):
        n=self.answers['group-skill-excluded'];self.assertTrue(n['physical_pellets']);self.assertFalse(n['groups']);self.assertFalse(n['group_notices'])
    def test_parts_do_not_become_logical_enemy_members(self):
        for label in ['group-parts','group-front','group-muzzles']:
            n=self.answers[label];self.assertTrue(n['groups']);self.assertTrue(all(t[0] in (0,5) for g in n['groups'] for t in g['targets']))
    def test_add_retirement_preserves_typed_generation_and_children(self):
        alive=self.answers['group-add-alive'];retired=self.answers['group-add-retirement'];self.assertTrue(any(r['target'][0]==5 for r in alive['group_receipts']));self.assertTrue(any(len(g['targets'])>=2 for g in retired['groups']))
        self.assertTrue(all(p['target']==p['label'] or p['target']=='' and p['label']=='__enemy__' for p in retired['landed_packets']))
        self.assertEqual(retired['group_children'][0]['targets'],retired['groups'][0]['targets'])
        self.assertEqual([r['target'] for r in retired['group_child_landings'] if r['group_identity']==1],[[0,0,1]])
    def test_group_buff_changes_following_shot(self):
        p=self.answers['group-buff-next']['physical_pellets'];self.assertLess(p[0]['packets'][0]['damage'],p[-1]['packets'][0]['damage'])
    def test_old120_and_gpu_source_are_exactly_retained(self):
        rows,_=a.prepare();old,_=a.parent.prepare();self.assertEqual(rows[:120],old);self.assertEqual((len(rows),sum(r[2] is not None for r in rows)),(136,126))
        from portable_backend import source_hashes
        g=json.loads((ROOT/'research/portable-coordinate-sampled-vital-short-expected.json').read_text());self.assertEqual(source_hashes(a.SOURCE),g['source_sha256'])
    def test_packet_policy_is_explicit_for_shared_history_comparator(self):
        with self.assertRaises(ValueError):a.groups.compare_group_receipts([],None,{},compare_packets=0)
    def test_outer_creation_observer_survives_group_scope_setup(self):
        from world_coordinate_sampled_skill_native import creation_indices,trace_view
        c=next(c for c in self.cases if c['name'].endswith('/group-body'))
        with creation_indices(c) as indices:n,t=observe(c)
        self.assertTrue(indices);self.assertEqual(len(trace_view(n['skill_trace'],indices)),len(n['skill_trace']))
if __name__=='__main__':unittest.main()
