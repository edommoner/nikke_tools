"""A passive source-aware observer preserves native calls and restoration."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator.buff_manager import BuffManager
from world_original_periodic_lifecycle import capture

class LifecycleTests(unittest.TestCase):
    def test_complete_rosters_pack_without_cpu_battle_and_oracle_is_local(self):
        spec=importlib.util.spec_from_file_location('lifecycle_test',ROOT/'research/verify-coordinate-original-lifecycle-short.py')
        adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        from calculator import timeline
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU battle in input')):
            entries,_=adapter.prepare()
        self.assertEqual(len(entries),3)
        for _,words,domain in entries:
            self.assertEqual(len(words),adapter.INPUT_WORDS)
            case,meta,_,_=domain
            self.assertEqual(set(meta['binding_source_indices']),set(range(len(case['effects']))))
            self.assertTrue(meta['coordinate_original_input']['original_weapon_metadata_preserved'])
            self.assertIs(provider(adapter,domain)[2],adapter.native_reference)

    def test_alias_refresh_records_incoming_source_and_retained_carrier(self):
        effects=[dict(name='same',type='damage',tick_interval=1,_portable_observer_row=i) for i in range(2)]
        case=dict(names=['A'],owners=[0,0],effects=copy.deepcopy(effects),source_effect_identity=True)
        manager=BuffManager.__new__(BuffManager);manager._active=[];manager._dot_timers={}
        def activate(self,effect,caster,t,*args,**kwargs):
            if not self._active:
                self._active.append(SimpleNamespace(effect=effect,caster=caster,target_chars=['BODY'],activated_at=t,expires_at=t+10,stack=1))
                self._dot_timers[id(effect)]=(caster,t+1,t+10)
            else:
                carrier=self._active[0];carrier.expires_at=t+10
                self._dot_timers[id(carrier.effect)]=(caster,self._dot_timers[id(carrier.effect)][1],t+10)
            return 'native-return'
        before=copy.deepcopy(effects)
        with patch.object(BuffManager,'_activate',activate):
            with capture(case) as rows:
                self.assertEqual(manager._activate(effects[0],'A',1),'native-return')
                manager._activate(effects[1],'A',1.5)
            self.assertIs(BuffManager._activate,activate)
        self.assertEqual(effects,before)
        self.assertEqual([r['row'] for r in rows],[0,1])
        self.assertEqual(rows[1]['before'][0]['row'],0)
        self.assertEqual(rows[1]['after'][0]['row'],0)
        self.assertEqual(rows[1]['before'][0]['timer'],[2,11])
        self.assertEqual(rows[1]['after'][0]['timer'],[2,11.5])
        manager._active[0].target_chars.append('ADD')
        self.assertEqual(rows[1]['after'][0]['targets'],['BODY'])

    def test_exception_restores_original_and_nonperiodic_is_forwarded(self):
        manager=BuffManager.__new__(BuffManager)
        calls=[]
        def activate(self,*args,**kwargs):
            calls.append((args,kwargs));raise RuntimeError('native failure')
        with patch.object(BuffManager,'_activate',activate):
            with self.assertRaisesRegex(RuntimeError,'native failure'):
                with capture({}) as rows:
                    manager._activate(dict(type='buff'),'A',2,suppress_event=True)
            self.assertIs(BuffManager._activate,activate)
        self.assertEqual(rows,[])
        self.assertEqual(calls[0][1],dict(suppress_event=True))

if __name__=='__main__':unittest.main()
