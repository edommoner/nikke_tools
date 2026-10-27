"""Declared manual input preserves original growth, effects and weapon identity."""
import copy,importlib.util,math,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
s=importlib.util.spec_from_file_location('original_controls_test_suite',ROOT/'research/verify-original-lock-controls.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
from portable_declared_manual_sequences import apply
from portable_heavyarms_original_composition import prepare_case
class OriginalControls(unittest.TestCase):
    def test_literal_overlay_preserves_input_and_refuses_replacement_and_bad_times(self):
        chars=[dict(name='a',control=dict(click=[])),dict(name='b',control={})];old=copy.deepcopy(chars)
        rows=[dict(action='cover',t=.35,duration=.25)]
        out=apply(chars,{'a':rows});self.assertEqual(chars,old);self.assertEqual(out[0]['control']['sequence'],rows);self.assertEqual(out[1],chars[1])
        for declarations in [{},{'unknown':rows},{'a':[]},{'a':rows*9},{'a':[dict(action='hold',t=0.,duration=.1)]},{'a':[dict(action='cover',t=True,duration=.1)]},{'a':[dict(action='cover',t=math.nan,duration=.1)]},{'a':[dict(action='cover',t=0.,duration=-1.)]},{'a':[dict(action='cover',t=1.,duration=.1),dict(action='cover',t=0.,duration=.1)]}]:
            with self.subTest(declarations=declarations),self.assertRaises(ValueError):apply(chars,declarations)
        with self.assertRaisesRegex(ValueError,'cannot be overwritten'):apply(out,{'a':rows})
    def test_static_pack_preserves_all_original_effects_and_original_body(self):
        from calculator import timeline
        from portable_heavyarms_lock_cases import source_definitions,NAME
        with patch.object(timeline,'simulate',side_effect=AssertionError('Packing must not run a battle')):
            plain,_=prepare_case(3,3);covered,prepared=prepare_case(3,3,cover=(0,.35,.25));words,meta,_=suite.compile_case(covered)
        self.assertEqual(covered['original_run'],plain['original_run']);self.assertEqual(covered['effects'],plain['effects']);self.assertEqual(covered['combat'],plain['combat']);self.assertEqual(covered['owners'],plain['owners'])
        self.assertEqual(covered['effects'][:25],source_definitions());self.assertEqual(len(covered['effects']),91)
        self.assertEqual(set(meta['binding_source_indices']),set(range(91)))
        self.assertEqual(covered['controls'][0]['sequence'],covered['declared_manual_sequences'][NAME])
        self.assertNotIn('sequence',prepared['chars'][0].get('control',{}))
        self.assertEqual(words[suite.parent.L['WORLD_CONTROL_INPUT_BASE']+1],3)
    def test_native_cover_removes_real_enemy_marker_and_restarts_acquisition(self):
        from world_named_enemy_removal_native import capture
        c,_=prepare_case(3,3,cover=(0,.35,.25));words,meta,bindings=suite.compile_case(c)
        with capture(c['names']) as removals:n=suite.native_reference((c,meta,bindings))
        rows=[r for r in removals if r['time']==.35 and r['owner']==0]
        self.assertEqual(len(rows),2) # diagnostics on/off must make the same mutation
        self.assertEqual(rows[0],rows[1]);self.assertTrue(rows[0]['before']);self.assertEqual(rows[0]['after'],[])
        self.assertIn(.35,n['lock_clears']);self.assertTrue(any(e['kind']=='_enter_cover' and e['owner']==0 for e in n['manual_actions']['events']))
        before=[p for p in n['lock_pulses'] if p['time']<.35];after=[p for p in n['lock_pulses'] if p['time']>.6]
        self.assertEqual(before[-1]['receipt'][1],1);self.assertEqual(after[0]['receipt'][1],1);self.assertGreater(after[0]['receipt'][2],before[-1]['receipt'][2])
        identity=n['original_input_identity'];self.assertFalse(identity['original_controls_preserved']);self.assertTrue(identity['declared_manual_sequences_applied_after_identity_check'])
    def test_old_four_inputs_preserved_and_new_rejects_stay_raw(self):
        import array,hashlib,json
        entries,raw=suite.parent.prepare();old=json.loads((ROOT/'research/portable-original-lock-composition-v1-expected.json').read_text())
        selected=entries
        data=array.array('I',[len(selected)])
        for _,words,_ in selected:data.extend(words)
        if sys.byteorder!='little':data.byteswap()
        self.assertEqual(hashlib.sha256(data.tobytes()).hexdigest(),old['input_sha256'])
        self.assertEqual(len(entries),8);self.assertEqual(sum(d is not None for _,_,d in entries),4)
        self.assertEqual(len(raw),4+8*109536*4)
        self.assertEqual(len(suite.fixtures()),9)
if __name__=='__main__':unittest.main()
