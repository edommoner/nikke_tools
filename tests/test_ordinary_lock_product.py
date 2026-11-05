"""Canonical ordinary markers on BODY/ADD, separate from declared locks."""
import copy,json,struct,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker,portable_detail as product,portable_backend
from portable_specs import LIMITS as L,FIELDS as F
from portable_product_ordinary_lock import PROJECTILE_RETURN
from calculator.boss_pattern import BossScript

class OrdinaryLockProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.requests=json.loads((ROOT/'tests/fixtures/ordinary-lock-product-v2.json').read_text())

    def test_body_and_add_keep_complete_definitions_and_generic_enemy_marker(self):
        for request in self.requests:
            for mode in ('fixed','accumulate'):
                body=copy.deepcopy(request['body']);body['burst_gauge_mode']=mode
                with self.subTest(name=request['name'],mode=mode),patch.object(engine_worker.sim,'execute',side_effect=AssertionError('No CPU state in input')):
                    p,run=product.prepare(body);before=copy.deepcopy(p);s,iw,ow,w,m=product.compile_product(p)
                    self.assertEqual(p,before);self.assertTrue(run.expected);self.assertEqual((iw,ow),(104400,786432))
                    self.assertEqual(s,'gpu/product_ordinary_lock_'+('fixed_' if mode=='fixed' else '')+'battle_entry.slang')
                    portable_backend.validate_composed_stride(s,iw,ow)
                    self.assertNotIn('product_lock_on',m);self.assertFalse(m['product_ordinary_lock']['declared_lock_model_inferred'])
                    self.assertEqual(set(m['binding_source_indices']),set(range(len(p['effects']))))
                    for i in m['product_ordinary_lock']['marker_indices']:
                        row=m['binding_source_indices'].index(i);a=L['DEFINITION_BASE']+row*32;d=L['DAMAGE_DEFINITION_BASE']+row*8
                        self.assertEqual((w[a+F['KIND']],w[a+F['STAT']]),(4,0))
                        self.assertTrue(m['enemy_buff_definitions'][row]);self.assertEqual(w[d:d+3],[6,1,0])
                        e=p['effects'][i]['effect'];self.assertEqual(e['target'],'enemies_nearest:1')
                        self.assertEqual(struct.pack('<II',*w[a+F['DURATION']:a+F['DURATION']+2]),struct.pack('<d',e['duration']))
                        self.assertEqual(m['product_ordinary_lock']['original_definitions'][i],p['effects'][i])
                    for i in m['product_ordinary_lock']['projectile_return_indices']:
                        row=m['binding_source_indices'].index(i);a=L['DEFINITION_BASE']+row*32;d=L['DAMAGE_DEFINITION_BASE']+row*8
                        self.assertEqual(w[a+F['DAMAGE_FLAGS']],PROJECTILE_RETURN)
                        self.assertEqual(w[d:d+4],[1,1,1,0]);self.assertEqual(w[a+F['KIND']],3)
                        self.assertEqual(m['product_ordinary_lock']['original_definitions'][i],p['effects'][i])

    def test_upstream_nearest_is_aim_then_spawn_order_without_geometry(self):
        boss=BossScript.__new__(BossScript)
        boss._alive_adds=lambda:[NS(id='late-id',spec=NS(hp=10,hit_hp=0),dealt=0,hits=0),NS(id='early-id',spec=NS(hp=10,hit_hp=0),dealt=0,hits=0)]
        boss._aim_enemy=lambda caster:'early-id'
        self.assertEqual(boss.resolve_enemies('enemies_nearest:1',caster='owner'),['early-id'])
        self.assertEqual(boss.resolve_enemies('enemies_nearest:3',caster='owner'),['early-id','late-id','__enemy__'])
        self.assertEqual(boss.resolve_enemies('enemies_with_buff:록 온',lambda who,name:who=='late-id'),['late-id'])
        self.assertEqual(boss.resolve_enemies('enemies_with_buff:록 온',lambda who,name:False),['__enemy__'])
        source=(ROOT/'gpu/world_actor_fields.slang').read_text()
        self.assertIn('if(route==6)',source);self.assertIn('output[n++]=first',source)
        self.assertIn('actorSortSpawnOrder',source)

    def test_declared_model_still_requires_exact_original_marker(self):
        from portable_product_programs import body_for_program
        from portable_product_locks import compile_product
        b=body_for_program(ROOT,'lock-fixed');p,_=product.prepare(b)
        # This path must retain the declared frozen-lock implementation.
        s,iw,ow,w,m=compile_product(p);self.assertIn('product_lock_on',m);self.assertNotIn('product_ordinary_lock',m)
        bad=copy.deepcopy(p);bad['effects']=[r for r in bad['effects'] if r['effect'].get('stat')!='lock_on']
        with patch.object(engine_worker.sim,'execute',side_effect=AssertionError('Guard before CPU')):
            with self.assertRaisesRegex(ValueError,'original Lock On owner/marker'):compile_product(bad)

    def test_standard_body_cpu_still_equals_saved_metal_total(self):
        body=dict(copy.deepcopy(self.requests[1]['body']),compute_backend='cpu')
        with patch.object(portable_backend,'execute',side_effect=AssertionError('CPU only')):
            result=engine_worker.evaluate(body)
        self.assertEqual(result['total_damage'],804324380)
        self.assertNotIn('reference_models',result)

    def test_projectile_return_is_scoped_and_does_not_zero_damage_or_emit_hits(self):
        from portable_product_ordinary_lock import compile_product
        p,_=product.prepare(self.requests[0]['body'])
        bad=copy.deepcopy(p);row=next(r for r in bad['effects'] if r['effect'].get('target')=='all_projectiles');row['effect']['tick_interval']=1.
        with self.assertRaisesRegex(ValueError,'Plain all_projectiles'):compile_product(bad)
        source=(ROOT/'gpu/dispatch_phases.slang').read_text()
        self.assertIn('else if(d.kind==3 && (d.damageFlags&1048576U)!=0) {}',source)
        guard=(ROOT/'gpu/admission_definition_types.slang').read_text()
        self.assertIn('#ifdef PORTABLE_PRODUCT_UPSTREAM_PROJECTILE_RETURN',guard)
        self.assertIn('d.kind!=3 || !worldSkillsEnabled(s) || !validWorldSkillDefinition',guard)

if __name__=='__main__':unittest.main()
