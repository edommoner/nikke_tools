"""Removal semantics, transparent observers, static operands and retained inputs."""
import copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,portable_backend,detail_gpu
from calculator.buff_manager import BuffManager
from calculator.boss_pattern import BossScript
from calculator import timeline
from portable_named_enemy_removal_cases import fixtures
from portable_named_enemy_removal_contracts import verify
from world_named_enemy_removal_native import observe,plain
from portable_specs import LIMITS as L
from portable_named_enemy_specs import selection_name

def load(name):
    s=importlib.util.spec_from_file_location('test_named_removal_'+name,ROOT/'research'/('verify-world-'+name+'-short.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NamedEnemyRemovalTests(unittest.TestCase):
    def test_literal_contracts_without_packing_or_gpu(self):
        def no(*a,**kw):raise AssertionError('Packing/GPU forbidden')
        with patch.object(timeline,'simulate',no):cases=fixtures()
        self.assertEqual(len(cases),16);before=copy.deepcopy(cases)
        with patch.object(portable_runtime,'compile_program',no),patch.object(detail_gpu,'compile_effects',no),patch.object(portable_backend,'build',no),patch.object(portable_backend,'execute',no):
            for c in cases:verify(c,observe(c)[0])
        self.assertEqual(cases,before)
    def test_entire_native_trace_rng_and_query_counts_unchanged(self):
        for c in fixtures():
            def measured(fn):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'_by_name',autospec=True,side_effect=BuffManager._by_name) as named,patch.object(BuffManager,'_resolve_enemies',autospec=True,side_effect=BuffManager._resolve_enemies) as resolved,patch.object(BossScript,'_ranked',autospec=True,side_effect=BossScript._ranked) as ranked,patch.object(BuffManager,'notify',autospec=True,side_effect=BuffManager.notify) as notify,patch.object(BuffManager,'_dispatch_instant',autospec=True,side_effect=BuffManager._dispatch_instant) as dispatch:
                    answer=fn(c);return answer,[m.call_count for m in (get,named,resolved,ranked,notify,dispatch)],random.getstate()
            (n,t),counts,state=measured(observe);n.pop('named_enemy_removal');(p,trace),old,prior=measured(plain)
            with self.subTest(case=c['name']):self.assertEqual((n,t,counts,state),(p,trace,old,prior))
    def test_mutation_notification_scope_and_choice_faults_rejected(self):
        for index in (2,6,10,14):
            c=fixtures()[index];n=observe(c)[0]
            for fault in ('after','callback','time','owner','before'):
                bad=copy.deepcopy(n);call=bad['named_enemy_removal']['removals'][0]
                if fault=='after':call['after']=[dict(owner=0,members=['wrong'])]
                elif fault=='callback':call['events']=[]
                elif fault=='time':call['time']=1
                elif fault=='owner':call['owner']=4
                else:call['before']=[]
                with self.subTest(case=c['name'],fault=fault),self.assertRaises(AssertionError):verify(c,bad)
        c=fixtures()[2];n=observe(c)[0];n['named_enemy_removal']['selection']['recipients'][0]['picked']=['__enemy__']
        with self.assertRaises(AssertionError):verify(c,n)
    def test_global_scope_does_not_pack_or_allocate_selector_operand(self):
        m=load('named-enemy-removal');rows,_=m.prepare();self.assertEqual((len(rows),sum(r[2] is not None for r in rows)),(23,16))
        for _,w,domain in rows[:16]:
            c=domain[0];at=L['MODE_BASE']+(len(c['effects'])-1)*L['MODE_WORDS']+24
            if c['contract']['scope']=='global':self.assertEqual(w[at:at+4],[0]*4);self.assertIsNone(selection_name(c['effects'][-1]))
            else:self.assertNotEqual(w[at],0)
        self.assertTrue(all(d is None for _,_,d in rows[16:]))
        from portable_readiness_semantics import reference_readiness
        issue=dict(phase='effect',category='effect',kind='instant',stat='remove_named_buff',target='enemies_with_buff:mark')
        r=reference_readiness(issue);self.assertEqual(r['recorded_cases'],18);self.assertFalse(r['full_character_verified']);self.assertFalse(r['gpu_supported'])
        self.assertEqual(reference_readiness(dict(issue,fields=['unknown']))['lane'],'reference_review')
    def test_retained207_input_bytes_and_source_guard(self):
        a,data=load('named-enemy-retention').prepare();rows,current=load('named-enemy-removal-retention').prepare();self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(230,171));self.assertEqual(current[4:len(data)],data[4:])
        from portable_named_enemy_source_contract import project_sources
        project_sources(ROOT)
        name='gpu/named_enemy_recipient_runtime.slang';text=(ROOT/name).read_text()
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:text.replace('(d.kind==1 || d.kind==15) && d.target==2','true')})
if __name__=='__main__':unittest.main()
