"""Data-only original Rei cases, shared source and reusable protection observers."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu,engine_worker
from portable_coordinate_kind_admission import KindAdmission
class OriginalDecoyTests(unittest.TestCase):
    def test_data_cases_use_the_exact_shared_entry(self):
        from calculator import timeline
        from portable_parent_oracles import provider
        a=nikke_gpu.open_suite(dict(suite='coordinate-original-decoy'))
        self.assertEqual(a.SOURCE,nikke_gpu.SUITES['coordinate-original-shared']['source'])
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule in GPU input')):rows,_=a.prepare()
        self.assertEqual(len(rows),3)
        for _,words,domain in rows:
            c,m,_,_=domain;self.assertEqual(len(c['effects']),72);self.assertEqual(c['duration'],8);self.assertEqual(set(m['binding_source_indices']),set(range(72)));self.assertIs(provider(a,domain)[2],a.native_reference)
            self.assertEqual({r['kind'] for r in KindAdmission(ROOT,'gpu/world_coordinate_original_cover_entry.slang').inspect(words)['unsupported']},{31});self.assertFalse(KindAdmission(ROOT,a.SOURCE).inspect(words)['unsupported'])
    def test_shared_scope_still_rejects_an_unknown_kind(self):
        from portable_specs import LIMITS as L,FIELDS as F
        a=nikke_gpu.open_suite(dict(suite='coordinate-original-decoy'));_,words,_=a.prepare()[0][0];words=list(words);words[L['DEFINITION_BASE']+F['KIND']]=38
        self.assertIn(dict(row=0,kind=38),KindAdmission(ROOT,a.SOURCE).inspect(words)['unsupported'])
    def test_decoy_capture_restores_original_methods_on_failure(self):
        from calculator.buff_manager import BuffManager
        from world_original_shield_native import capture
        a=nikke_gpu.open_suite(dict(suite='coordinate-original-decoy'));case,_=a.prepare_case(a.fixtures()[0]);before=[BuffManager._register_all,BuffManager._dispatch_instant,BuffManager.heal_decoy,BuffManager.heal_shield]
        with self.assertRaises(RuntimeError):
            with capture(case,kind='decoy'):raise RuntimeError('native failed')
        self.assertEqual(before,[BuffManager._register_all,BuffManager._dispatch_instant,BuffManager.heal_decoy,BuffManager.heal_shield])
        with self.assertRaises(ValueError):
            with capture(case,kind='unknown'):pass
    def test_expiry_uses_serialized_record_order_not_runtime_slot(self):
        import array,struct,portable_runtime
        from portable_specs import LIMITS as L
        a=nikke_gpu.open_suite(dict(suite='coordinate-original-decoy'))
        block=array.array('I',[0])*159744
        for record,value in ((0,240.),(7,float('inf'))):
            at=L['CARRIER_STATE_BASE']+record*L['CARRIER_WORDS']+5;block[at:at+2]=array.array('I',struct.unpack('<II',struct.pack('<d',value)))
        carrier=dict(slot=7,definition=0,active=True,recipients=1,lazy_pending=False,stacks=1,activated=0.,protection=dict(kind=2,current={'0':4.},capacity={'0':10.}))
        case=dict(names=['Rei'],owners=[0],effects=[dict(stat='decoy')]);meta=dict(binding_source_indices=[0]);expected=dict(original_decoy=dict(final=[dict(row=0,owner=0,members=['Rei'],stack=1,activated=0.,end=240.,current={'Rei':4.},capacity={'Rei':10.})],requests=[],clocks=[]))
        with patch.object(portable_runtime,'decode',return_value=dict(carriers=[carrier],timers=[])):
            self.assertIs(a.shield.compare_protections(block,(case,meta,None,None),expected,kind=2,stat='decoy_heal_pct',field='original_decoy'),expected)
if __name__=='__main__':unittest.main()
