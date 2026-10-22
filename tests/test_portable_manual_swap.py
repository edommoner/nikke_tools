"""Finite owner flags, backward raw rejection, and exact shared source guards."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_reload_specs import pack
from portable_manual_swap_cases import fixtures
from portable_definition_view_contract import verify
from portable_manual_swap_source_contract import ledger
from portable_specs import LIMITS as L


class ManualSwapTests(unittest.TestCase):
    def test_default_header_bytes_and_explicit_boolean_owner_mask(self):
        effects=fixtures()[0]['effects'];old=pack(effects)
        self.assertEqual(old[:8],[0x57524c31,1,2,0,0,0,0,0])
        self.assertEqual(pack(effects,manual_swap=[False]*5),old)
        for who in range(5):
            flags=[i==who for i in range(5)];words=pack(effects,manual_swap=flags)
            self.assertEqual(words[3:5],[1<<who,0x574d5331]);self.assertEqual(words[:3]+words[5:],old[:3]+old[5:])
        for flags in ([True]*4,[True]*6,[1,False,False,False,False],(False,)*5,'false'):
            with self.subTest(flags=flags),self.assertRaises(ValueError):pack(effects,manual_swap=flags)

    def test_all_covered_contracts_pack_and_cover_is_explicitly_rejected(self):
        spec=importlib.util.spec_from_file_location('manual_swap_tests',ROOT/'research/verify-world-manual-swap-short.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        entries,data=adapter.prepare();self.assertEqual(len(entries),30);self.assertEqual(sum(v[2] is not None for v in entries),23)
        for _,words,domain in entries:
            if domain is None:continue
            flags=domain[0].get('manual_swap',[False]*5)
            self.assertEqual(words[L['WORLD_RELOAD_INPUT_BASE']+3],sum(1<<i for i,v in enumerate(flags) if v))
            from portable_specs import FIELDS as F
            for row,effect in enumerate(domain[0]['effects']):
                if effect['type']=='weapon_change':self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['KIND']],2)
        cover=next(c for c in fixtures() if c['name'].endswith('cover-pump-order'))
        with self.assertRaisesRegex(ValueError,'Non-hold sequence'):adapter.suite.compile_case(cover)

    def test_exact_source_delta_rejects_lost_hooks_or_changed_order_and_budget(self):
        data=ledger(ROOT);self.assertEqual(set(verify(ROOT)['reviewed_manual_swap_sources']),set(data['sources']))
        for name,row in data['sources'].items():
            for change in row['changes']:
                source=(ROOT/name).read_text();modified=source.replace(change['current'],change['baseline'],1)
                with self.subTest(name=name),self.assertRaises(AssertionError):verify(ROOT,sources={name:modified})
        name='gpu/world_reload_runtime.slang';source=(ROOT/name).read_text()
        for old,new in [('commands[p+3]>=32','commands[p+3]>=64'),('d.conditionCount==0','d.conditionCount>0'),('activationConditions(s,row,when)','basicConditions(s,row,when,true)'),('if(d.kind!=2||d.owner!=who||d.conditionCount==0)','if(d.kind!=2||d.owner!=who||d.conditionCount==0||d.maxTriggers==0)')]:
            self.assertIn(old,source)
            with self.assertRaises(AssertionError):verify(ROOT,sources={name:source.replace(old,new,1)})


if __name__=='__main__':unittest.main()
