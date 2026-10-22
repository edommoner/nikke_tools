"""Friendly RNG admission, static packing and strict source correspondence."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend
from calculator import timeline
from portable_runtime import validate_effect
from portable_ally_random_specs import MAGIC,pack
from portable_specs import LIMITS as L
from portable_definition_view_contract import verify
from portable_ally_random_source_contract import ledger


def adapter():
    spec=importlib.util.spec_from_file_location('ally_random_gpu_test',ROOT/'research/verify-world-ally-random-short.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class AlliedRandomTests(unittest.TestCase):
    def test_static_compiler_and_seed_zero_do_not_run_battles(self):
        def forbidden(*args,**kwargs):raise AssertionError('Packing must not simulate or execute GPU')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'execute',forbidden):
            entries,data=adapter().prepare()
        self.assertEqual((len(entries),sum(d is not None for _,_,d in entries)),(30,20))
        self.assertEqual(len(data),4+sum(len(words)*4 for _,words,_ in entries))
        for _,words,domain in entries[:20]:
            self.assertEqual(words[L['RECIPIENT_META_BASE']+1:L['RECIPIENT_META_BASE']+5],
                             [0,MAGIC,domain[0]['seed'],0])
            for row,effect in enumerate(domain[0]['effects']):
                if effect.get('type')=='buff' and effect['target'].startswith(('allies_random:','allies_broken_cover_random:')):
                    self.assertGreater(words[L['RECIPIENT_BASE']+row*8+7]>>4,0)

    def test_private_world_gate_lists_and_seed_shape(self):
        effect=adapter().fixtures()[0]['effects'][-1]
        validate_effect(effect,combat={},world_frame=True)
        for combat,world in [(None,True),({},False)]:
            with self.assertRaises(ValueError):validate_effect(effect,combat=combat,world_frame=world)
        with self.assertRaisesRegex(ValueError,'lazy-list'):
            validate_effect(dict(effect,target=['self',effect['target']]),combat={},world_frame=True)
        for seed in (-1,2**64,True,1.0,None):
            with self.assertRaises(ValueError):pack([0]*8,dict(RECIPIENT_META_BASE=0),[(effect,0)],seed)
        words=[0]*8;pack(words,dict(RECIPIENT_META_BASE=0),[(effect,0)],2**64-1)
        self.assertEqual(words[2:5],[MAGIC,0xffffffff,0xffffffff])

    def test_every_reviewed_shader_delta_rejects_mutation(self):
        data=ledger(ROOT)
        self.assertEqual(set(verify(ROOT)['reviewed_ally_random_sources']),set(data['sources']))
        for name,row in data['sources'].items():
            source=(ROOT/name).read_text()
            for change in row['changes']:
                with self.subTest(name=name),self.assertRaises(AssertionError):
                    verify(ROOT,sources={name:source.replace(change['current'],change['baseline'],1)})


if __name__=='__main__':unittest.main()
