import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('coordinate_quantity_adapter',ROOT/'research/verify-coordinate-quantity-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class QuantityTests(unittest.TestCase):
    def test_packing_never_calls_cpu_landing_or_damage_oracle(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No CPU oracle during packing')),patch('coordinate_landing_reference.landing',side_effect=AssertionError('No computed probabilities')):
            rows,raw=a.prepare()
        self.assertEqual(len(rows),31);self.assertEqual(sum(d is not None for _,_,d in rows),25)
        self.assertEqual(len(raw),4+len(rows)*a.INPUT_WORDS*4)

    def test_real_parent_includes_target_packets_and_preserves_landing_order(self):
        rows,_=a.prepare();answers={name.split('/')[-1]:a.native_reference(d) for name,_,d in rows if d is not None and name.startswith('coordinate-quantity/')}
        first=answers['pierce-parent']
        self.assertEqual(first['full_charge_quantities'][0]['dealt'],8000.)
        self.assertEqual([(p['target'],p['damage']) for p in first['landed_packets']],[('',2000),('front',3000),('behind',3000),('',2000)])
        self.assertEqual([p['time'] for p in first['landed_packets']],[.05,.05,.05,1/15])
        self.assertEqual(first['skill_trace'][0]['created'],.05)
        self.assertEqual(first['skill_trace'][0]['landed'],1/15)
        self.assertEqual(answers['including-interrupt']['full_charge_quantities'][0]['dealt'],10000.)
        self.assertEqual(len(answers['two-muzzles-seven-pellets']['full_charge_quantities']),2)
        self.assertEqual(answers['fraction-to-zero']['landed_packets'][-1]['damage'],0)
        self.assertEqual(len(answers['zero-child']['landed_packets']),3)
        self.assertEqual(answers['last-owner']['full_charge_quantities'][0]['owner'],4)
        self.assertEqual([n['owner'] for n in answers['two-shooters']['full_charge_quantities']],[0,3])

    def test_passive_packet_observer_restores_profile_and_notification_on_failure(self):
        import engine_worker
        from calculator.buff_manager import BuffManager
        from world_coordinate_packet_quantity_native import observe
        from portable_coordinate_quantity_cases import fixtures
        previous=sys.getprofile();notify=BuffManager.notify
        with patch('world_coordinate_physical_common.observe',side_effect=ValueError('injected')):
            with self.assertRaises(ValueError):observe(fixtures()[0])
        self.assertIs(sys.getprofile(),previous);self.assertIs(BuffManager.notify,notify)

    def test_comparator_rejects_parent_bits_and_child_time_without_weakening_world_decoder(self):
        import struct
        from portable_coordinate_physical_specs import LAYOUT
        rows,_=a.prepare();_,_,domain=next(r for r in rows if r[0]=='coordinate-quantity/pierce-parent')
        expected=a.native_reference(domain);by_name={r['label']:r for r in domain[3]['rows']};cp=a.parent.CP
        block=[0]*a.OUTPUT_WORDS;block[cp['BASE']]=0x43534b31;block[cp['BASE']+1]=1;block[cp['BASE']+2]=len(expected['landed_packets'])
        for i,p in enumerate(expected['landed_packets']):
            row=by_name.get(p['target']);at=cp['TRACE']+12*i
            block[at:at+12]=[p['owner'],row['slot'] if row else 0,row['kind'] if row else 0,p['generation'],*struct.unpack('<II',struct.pack('<d',p['time'])),*struct.unpack('<II',struct.pack('<d',float(p['damage']))),int(p['extra']),0,0,0]
        bank=LAYOUT['BANK']+14;block[bank:bank+2]=struct.unpack('<II',struct.pack('<d',8000.))
        with patch.object(a.parent.codec,'compare_expected',return_value=None):
            a.compare(block,domain)
            for at in [bank,cp['TRACE']+3*12+4,cp['TRACE']+4*12]:
                changed=list(block);changed[at]^=1
                with self.subTest(at=at),self.assertRaises(AssertionError):a.compare(changed,domain)

if __name__=='__main__':unittest.main()
