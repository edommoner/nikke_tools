"""Exact authored ablation and the shared squad-ammo owner-liveness boundary."""
import array,copy,hashlib,json,sys,unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker,portable_detail,portable_backend
from calculator import buff_manager as bm

FIXTURE=ROOT/'tests/fixtures/mermaid-burst-charge-ablation-v1.json'

@contextmanager
def ablated(job):
    # Same two patches as metal-ablation-v1/harness.py: query rows and the
    # registered event list, retaining collection rows and rebuilding the index.
    original_rows=bm.BuffManager.char_effects
    original_register=bm.BuffManager._register_all
    removed={}
    def selected(e):
        return e.get('type')=='instant' and str(e.get('stat') or '').split(':')[0]=='burst_charge_pct'
    def remember(e,owner):
        row=dict(owner=owner,effect=copy.deepcopy(e))
        removed[json.dumps(row,ensure_ascii=False,sort_keys=True)]=row
    def rows(manager,owner):
        result=original_rows(manager,owner)
        for e in result:
            if selected(e):remember(e,owner)
        return [e for e in result if not selected(e)]
    def register(manager):
        original_register(manager)
        for e,owner in manager._effects:
            if selected(e) and e.get('_source_tag')!='collection':remember(e,owner)
        manager._effects=[(e,n) for e,n in manager._effects if not selected(e) or e.get('_source_tag')=='collection']
        manager._build_notify_index()
    with patch.object(bm.BuffManager,'char_effects',rows),patch.object(bm.BuffManager,'_register_all',register):yield removed

class MermaidAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.job=json.loads(FIXTURE.read_text())

    def test_exact_cpu_reference_and_post_death_counter_boundary(self):
        events=[];executed=[];original=engine_worker.sim.execute;notify=bm.BuffManager._notify
        def observe(run):
            result=original(run);executed.append(result);return result
        def notified(manager,event,t,caster):
            if event=='squad_ammo_consume':
                count=manager._event_counts.get('__squad__',{}).get(event,0)+1
                if count in (500,1000):events.append((count,t,'리틀 머메이드' in manager.state.get('down',())))
            return notify(manager,event,t,caster)
        with ablated(self.job) as removed,patch.object(engine_worker.sim,'execute',observe),patch.object(bm.BuffManager,'_notify',notified),patch.object(portable_backend,'execute',side_effect=AssertionError('Device forbidden')):
            payload=engine_worker.evaluate(dict(copy.deepcopy(self.job['body']),compute_backend='cpu'))
        self.assertEqual(list(removed.values()),self.job['cpu_removal']['removed_rows'])
        self.assertEqual(payload['total_damage'],86669329)
        self.assertEqual({m['name']:m['damage'] for m in payload['members']},self.job['expected_cpu_ablated_members'])
        public={k:payload[k] for k in ('total_damage','members','burst_timeline','incoming_hits','parts_state','boss_timeline','reference_models') if k in payload}
        raw=json.dumps(public,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),self.job['expected_cpu_ablated_public_sha256'])
        self.assertEqual(events,[(500,21.650000000000052,False),(1000,45.23333333333205,True)])
        spray=[h for h in executed[0].hits if h.caster=='리틀 머메이드' and h.skill_name=='거품 난사']
        self.assertEqual([(h.t,h.damage) for h in spray],[(21.650000000000052,104497)]*10)

    def test_ablated_product_input_is_admitted_without_scheduling_from_cpu(self):
        with ablated(self.job) as removed,patch.object(engine_worker.sim,'execute',side_effect=AssertionError('CPU battle forbidden')):
            prepared,_=portable_detail.prepare(copy.deepcopy(self.job['body']))
            source,iw,ow,words,meta=portable_detail.compile_product(prepared)
        self.assertEqual(len(removed),1)
        self.assertEqual((source,iw,ow),('gpu/product_battle_entry.slang',104400,786432))
        wire=array.array('I',[1,*words])
        if sys.byteorder!='little':wire.byteswap()
        # Exact failing capture input: only shared execution changes.
        self.assertEqual(hashlib.sha256(wire.tobytes()).hexdigest(),'19061ed83194e8a1b2f9e28e2b3a0acb912d5f1eda0b517f1b9c6658c4ef7a00')

    def test_shared_dispatch_checks_subscriber_after_count_before_activation(self):
        text=(ROOT/'gpu/dispatch_phases.slang').read_text()
        guard='if (f.mode == 0 && f.event == 26 && (s.downMask & (1U << d.owner)) != 0) continue;'
        self.assertIn(guard,text)
        self.assertLess(text.index('WORLD_TEAM_COUNTER(s,f.event,counter)'),text.index(guard))
        self.assertLess(text.index(guard),text.index('if (f.mode == 0 && !activationConditions'))
        # Preserve broadcast delivery when the emitter is down, independently
        # of the subscriber guard. This is also required for revival counts.
        runtime=(ROOT/'gpu/event_runtime.slang').read_text()
        self.assertIn('f.event != 26 && f.event != 28 && f.event != 38',runtime)

if __name__=='__main__':unittest.main()
