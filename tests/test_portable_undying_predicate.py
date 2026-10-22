"""One common predicate ABI and strict shared source contract for both backends."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_specs import LIMITS as L,shader_schema
from portable_runtime import validate_effect
from portable_definition_view_contract import verify
from portable_undying_predicate_source_contract import ledger


def adapter():
    s=importlib.util.spec_from_file_location('undying_gpu_test',ROOT/'research/verify-world-undying-predicate-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class UndyingPredicateTests(unittest.TestCase):
    def test_shared_wire_retains_all_native_cases_and_raw_rejections(self):
        m=adapter();entries,data=m.prepare();self.assertEqual(len(entries),28);self.assertEqual(sum(e[2] is not None for e in entries),22)
        at=L['CONDITION_BASE']+2*L['CONDITION_WORDS'];self.assertEqual(entries[1][1][at:at+4],[38,0,0,0]);self.assertEqual(len(data),4+sum(len(e[1])*4 for e in entries))
        for name,words,domain in entries[-6:]:
            self.assertIsNone(domain);m.validate_rejection([64],name)
            with self.assertRaises(AssertionError):m.validate_rejection([0],name)
        self.assertEqual((ROOT/'gpu/portable_schema.slang').read_text(),shader_schema())

    def test_host_rejects_nonworld_passive_or_malformed_marker_predicates(self):
        m=adapter();effect=m.fixtures()[1]['effects'][-1];validate_effect(effect,combat={},world_frame=True)
        for changes,world in [({},False),({'trigger':dict(timing=['passive'],condition=['self_undying'])},True),({'trigger':dict(timing=['on_attack'],condition=['self_undying:1'])},True)]:
            e=copy.deepcopy(effect);e.update(changes)
            with self.assertRaises(ValueError):validate_effect(e,combat={},world_frame=world)

    def test_every_source_delta_and_marker_semantics_are_guarded(self):
        data=ledger(ROOT);self.assertEqual(set(verify(ROOT)['reviewed_undying_predicate_sources']),set(data['sources']))
        for name,row in data['sources'].items():
            source=(ROOT/name).read_text()
            for change in row['changes']:
                with self.subTest(name=name),self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(change['current'],change['baseline'],1)})
        name='gpu/event_runtime.slang';source=(ROOT/name).read_text()
        with self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace('liveMarker(s,owner,S_undying,when)','liveMarker(s,owner,S_invincible,when)',1)})


if __name__=='__main__':unittest.main()
