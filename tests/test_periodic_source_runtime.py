import sys,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from periodic_source_runtime import refresh,tick,count
from periodic_source_specs import specification,MAX_SOURCES
from effect_runtime import pool

def effect(name='source',slots=(-1,2,3),base=1,step=10):
    return dict(type='instant',stat='periodic_source_refresh',target='self',periodic_source=dict(name=name,slots=list(slots),base_interval=base,population_reduction_pct=step))

class PeriodicSourceTests(unittest.TestCase):
    def manager(self):
        events=[];manager=SimpleNamespace(notify=lambda *args:events.append(args));return manager,events
    def test_population_expiry_does_not_rewrite_reserved_clock(self):
        manager,events=self.manager();refresh(manager,effect(), 'owner',0)
        record=pool(manager,'periodic_sources')['owner','source']
        self.assertAlmostEqual(record.next_at,.8)
        tick(manager,.8);self.assertAlmostEqual(record.next_at,1.6)
        tick(manager,1.6);self.assertAlmostEqual(record.next_at,2.4)
        self.assertEqual(count(manager,'owner','source',2),2);self.assertAlmostEqual(record.next_at,2.4)
        tick(manager,2.400001);self.assertAlmostEqual(record.next_at,3.3)
        self.assertEqual(count(manager,'owner','source',3),1)
        tick(manager,3.300001);self.assertAlmostEqual(record.next_at,4.3);self.assertEqual(len(events),4)
    def test_refresh_atomically_replaces_slots_and_old_due_time(self):
        manager,events=self.manager();refresh(manager,effect(slots=(1,),base=1),'owner',0)
        tick(manager,1);self.assertEqual(events,[]);self.assertIsNone(pool(manager,'periodic_sources')['owner','source'].next_at)
        refresh(manager,effect(slots=(-1,),base=2),'owner',1.1);tick(manager,2)
        self.assertEqual(events,[]);tick(manager,3.1);self.assertEqual(len(events),1)
        self.assertEqual(pool(manager,'periodic_sources')['owner','source'].epoch,2)
    def test_child_refresh_survives_parent_clock_commit(self):
        manager,events=self.manager();refresh(manager,effect(slots=(-1,),base=1),'owner',0)
        manager.notify=lambda *args:refresh(manager,effect(slots=(-1,),base=3),'owner',args[1])
        tick(manager,1);self.assertEqual(pool(manager,'periodic_sources')['owner','source'].next_at,4)
    def test_owner_then_channel_order_and_child_append_snapshot(self):
        manager,events=self.manager()
        for owner,name in [('a','one'),('b','two'),('a','three')]:refresh(manager,effect(name,(-1,),1,0),owner,0)
        def notify(*args):
            events.append(args)
            if len(events)==1:refresh(manager,effect('new',(-1,),1,0),'a',1)
        manager.notify=notify;tick(manager,1)
        self.assertEqual([(e[0],e[2]) for e in events],[('source_tick:one','a'),('source_tick:three','a'),('source_tick:two','b')])
    def test_zero_is_a_present_resource_and_lag_has_one_emission_per_tick(self):
        manager,events=self.manager();refresh(manager,effect(slots=(0,),base=1),'owner',0)
        self.assertEqual(count(manager,'owner','source',0),0);self.assertIsNone(count(manager,'owner','absent',0))
        refresh(manager,effect(slots=(-1,),base=1),'owner',0);tick(manager,10)
        self.assertEqual(len(events),1);self.assertEqual(pool(manager,'periodic_sources')['owner','source'].next_at,2)
    def test_descriptor_and_capacity_fail_before_overflow(self):
        for changed in (effect(slots=()),effect(slots=(-2,)),effect(base=0),effect(slots=(-1,)*7,step=20),effect(slots=(True,))):
            with self.assertRaises(ValueError):specification(changed)
        manager,_=self.manager()
        for i in range(MAX_SOURCES):refresh(manager,effect(str(i),(-1,)),'owner',0)
        with self.assertRaises(ValueError):refresh(manager,effect('overflow',(-1,)),'owner',0)
        refresh(manager,effect('0',(-1,)),'owner',1)

if __name__=='__main__':unittest.main()
