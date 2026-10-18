import sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from lifecycle_specs import LifecycleSpec,ordered_specs,gpu_source_matches
from effect_runtime import Catalog,Handler,RuntimeState,state,pool

class RuntimeCatalogTests(unittest.TestCase):
    def test_order_nested_delivery_and_registration_seal(self):
        specs=(LifecycleSpec('first'),LifecycleSpec('second',depends=('first',)))
        catalog=Catalog(specs);calls=[]
        def first(manager,*args):
            calls.append('first-start');catalog.emit('before_notify',manager,'nested',0,'a');calls.append('first-end')
        catalog.register('first',Handler(activate=first,before_notify=lambda *args:calls.append('nested-first')))
        catalog.register('second',Handler(activate=lambda *args:calls.append('second'),before_notify=lambda *args:calls.append('nested-second')))
        catalog.seal();catalog.emit('activate',object(),{},'a',0)
        self.assertEqual(calls,['first-start','nested-first','nested-second','first-end','second'])
        with self.assertRaises(RuntimeError):catalog.register('third',Handler())
        with self.assertRaises(TypeError):catalog.handlers['first']=Handler()
    def test_bad_dependencies_duplicate_stat_and_incomplete_implementation_reject(self):
        generic=LifecycleSpec('generic',cpu_phase='prepare_activation',current_instance=True,any_instance=True)
        self.assertEqual(ordered_specs((generic,)),(generic,))
        for spec in (LifecycleSpec('bad',activation_stat=1,any_instance=True),LifecycleSpec('bad',gpu_prepare='prepare_generic',any_instance=True),LifecycleSpec('bad',any_instance=1)):
            with self.subTest(spec=spec),self.assertRaises(ValueError):ordered_specs((spec,))
        with self.assertRaises(ValueError):ordered_specs((LifecycleSpec('child',depends=('missing',)),))
        with self.assertRaises(ValueError):ordered_specs((LifecycleSpec('one',activation_stat=74),LifecycleSpec('two',activation_stat=74)))
        with self.assertRaises(ValueError):ordered_specs((LifecycleSpec('one',gpu_activate='not;a;function'),))
        c=Catalog((LifecycleSpec('one',cpu_phase='activate'),))
        with self.assertRaises(ValueError):c.register('one',Handler())
        with self.assertRaises(ValueError):c.seal()
    def test_future_operation_can_be_added_without_replacing_executor(self):
        c=Catalog((LifecycleSpec('existing'),LifecycleSpec('new_operation',depends=('existing',))))
        calls=[]
        for name in ('existing','new_operation'):
            c.register(name,Handler(activate=lambda manager,effect,caster,t,key=name:calls.append((key,effect['value']))))
        c.seal();c.emit('activate',None,{'value':7},'new-character',0)
        self.assertEqual(calls,[('existing',7),('new_operation',7)])
    def test_generated_cuda_catalog_matches(self):self.assertTrue(gpu_source_matches())

class RuntimeStateTests(unittest.TestCase):
    def test_activation_carrier_context_restores_after_nested_calls_and_exceptions(self):
        from effect_runtime import activation,CATALOG
        from unittest.mock import patch
        manager=NS(_active=[]);first=object();second=object();seen=[]
        def deliver(phase,owner,effect,caster,t):
            seen.append(state(owner).activation_stack[-1])
            if effect['name']=='outer':
                activation(owner,{'name':'inner'},caster,t,second)
                seen.append(state(owner).activation_stack[-1]);raise ValueError('witness')
        with patch.object(CATALOG,'emit',deliver),self.assertRaises(ValueError):activation(manager,{'name':'outer'},'a',0,first)
        self.assertEqual(seen,[first,second,first]);self.assertEqual(state(manager).activation_stack,[])
    def test_bulk_expiry_preserves_charge_until_its_own_end_notification(self):
        import engine_worker
        from calculator.buff_manager import BuffManager
        manager=BuffManager.__new__(BuffManager)
        manager._active=[];manager._notify_ctx={};manager.is_down=lambda name:False
        record=NS(uid=1,caster='a',effect={'name':'pool'},heal_charge_current=7.0,
                  heal_charge_ended=False,heal_charge_done=False)
        resources=pool(manager,'healing_charge');resources[1]=record
        delivered=[]
        def deliver(event,t,caster):
            if event=='event:state_end:pool':
                self.assertTrue(record.heal_charge_ended)
                delivered.append(manager.take_heal_charge('pool',caster,t))
        manager._notify=deliver
        manager.notify('event:state_end:earlier-sibling',1,'a')
        self.assertIn(1,resources)
        manager.notify('event:state_end:pool',1,'a')
        self.assertEqual(delivered,[7.0]);self.assertEqual(resources,{})
    def test_manager_and_resource_kind_isolation(self):
        a=NS(_active=[]);b=NS(_active=[])
        pool(a,'shield')[1]='shield';pool(a,'healing_charge')[1]='charge'
        self.assertEqual(pool(b,'shield'),{})
        self.assertEqual(pool(a,'shield'),{1:'shield'})
        self.assertEqual(pool(a,'healing_charge'),{1:'charge'})
    def test_retention_and_owner_down_cleanup_are_explicit(self):
        manager=NS(_active=[]);runtime=RuntimeState()
        a=NS(uid=1,caster='a',ended=True);b=NS(uid=2,caster='b',ended=True);c=NS(uid=3,caster='a',ended=False)
        resources=runtime.pool('charge');resources.update({1:a,2:b,3:c})
        runtime.retire(manager,'charge',{1,2,3},lambda ab:ab.ended)
        self.assertEqual(set(resources),{1,2})
        runtime.retire(manager,'charge',set(),lambda ab:ab.ended,owner='a')
        self.assertEqual(set(resources),{2})
    def test_nested_context_and_exception_restore_real_adapter(self):
        import engine_worker
        from calculator.buff_manager import BuffManager
        manager=BuffManager.__new__(BuffManager);manager._active=[];manager._notify_ctx={}
        calls=[]
        def deliver(event,t,caster):
            calls.append((event,len(state(manager).event_stack),manager.notify_ctx('marker')))
            if event=='outer':
                manager.notify('inner',t,caster,marker='child')
                calls.append(('resumed',len(state(manager).event_stack),manager.notify_ctx('marker')))
            if event=='error':raise ValueError('witness')
        manager._notify=deliver
        manager.notify('outer',0,'a',marker='parent')
        self.assertEqual(calls,[('outer',1,'parent'),('inner',2,'child'),('resumed',1,'parent')])
        with self.assertRaises(ValueError):manager.notify('error',0,'a')
        self.assertEqual(state(manager).event_stack,[]);self.assertEqual(manager._notify_ctx,{})

if __name__=='__main__':unittest.main()
