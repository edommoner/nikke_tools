"""Admission operands, unchanged retained inputs, independent selection diagnostics."""
import copy,hashlib,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_specs import LIMITS as L
from portable_named_enemy_specs import MAGIC,OFFSET,allocate_names,pack
from portable_named_enemy_source_contract import project_sources

def load(name):
    s=importlib.util.spec_from_file_location('test_named_'+name,ROOT/'research'/('verify-world-'+name+'-short.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NamedEnemyGpuTests(unittest.TestCase):
    def test_live_names_are_static_operands_not_preselected_masks(self):
        m=load('named-enemy');rows,_=m.prepare();self.assertEqual(len(rows),32)
        for label,w,domain in rows[:23]:
            c,meta,_=domain;at=L['MODE_BASE']+(len(c['effects'])-1)*L['MODE_WORDS']+OFFSET
            self.assertEqual(w[at:at+4],[MAGIC,meta['states'][c['contract']['mark_name']]+1,int(c['contract']['mark_name']==''),0])
        self.assertTrue(all(d is None for _,_,d in rows[23:]))
        empty=next(r for r in rows[:23] if r[0].endswith('empty-name'));w=empty[1];self.assertEqual(w[L['MODE_BASE']+OFFSET:L['MODE_BASE']+OFFSET+4],[MAGIC,0,2,0])
    def test_operand_capacity_and_overlap_fail_closed(self):
        with self.assertRaises(ValueError):allocate_names([({'target':'enemies_with_buff:new'},0)],{str(i):i for i in range(256)})
        w=[0]*L['WORLD_ACTOR_STATE_INPUT_WORDS'];at=L['MODE_BASE']+OFFSET;w[at]=1
        with self.assertRaises(ValueError):pack(w,L,[({'type':'buff','target':'enemies_with_buff:x'},0)],{'x':0})
    def test_retention_prefix_is_byte_identical(self):
        old,data=load('random-cleanse-retention').prepare();rows,current=load('named-enemy-retention').prepare()
        self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(207,155));self.assertEqual(current[4:4+len(data)-4],data[4:])
    def test_source_inverse_and_guard_fault_rejected(self):
        sources,changed=project_sources(ROOT);self.assertEqual(len(changed),8)
        for name in changed:
            current=(ROOT/name).read_text()
            with self.subTest(name=name),self.assertRaises((AssertionError,ValueError)):project_sources(ROOT,{name:current+'\n// unreviewed\n'})
        name='gpu/named_enemy_recipient_runtime.slang'
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text().replace('name>P_DEFINITIONS','name>99999')})
    def test_every_dynamic_definition_capture_forwards_its_identity(self):
        import re
        for p in (ROOT/'gpu').glob('*.slang'):
            for line in p.read_text().splitlines():
                if 'actorSetCapture(s,' in line and 'd.damageCount' in line:
                    self.assertIn('NAMED_ENEMY_ARGUMENT(',line,p.name)
    def test_diagnostic_masks_all128_and_wrong_choice_rejected(self):
        m=load('named-enemy-diagnostic');rows,_=m.prepare()
        for label,w,domain in rows:
            c,_,bindings=domain;block=[0]*786432;block[m.BASE+6]=3
            for i,picked in enumerate(c['contract']['picked']):
                mask=[0]*4
                for label in picked:
                    j=next(j for j,b in enumerate(bindings) if b.label==label);mask[j//32]|=1<<(j%32)
                at=m.TRACE+i*8;block[at:at+8]=[0x4e455431,len(c['effects'])-1,*mask,len(picked),0]
            m.compare_trace(block,domain);block[m.TRACE+2]^=1
            with self.assertRaises(AssertionError):m.compare_trace(block,domain)
if __name__=='__main__':unittest.main()
