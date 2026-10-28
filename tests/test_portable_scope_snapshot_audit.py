"""A pointer retained across the update must never count as a saved scalar."""
import json,re,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_scope_snapshot_audit import audit,audit_resident_scalars,function

GOOD=b'''static __device__ __noinline__ uint actorStateQueryScopeSnapshot_0(uint at) { return *p; }
uint actorStatePushQuery_0(uint target) {
uint previous=actorStateQueryScopeSnapshot_0(at);
*p = target+1;
return previous;
}'''

class ScopeSnapshotAuditTests(unittest.TestCase):
    def test_scalar_value_before_store_is_distinct_from_calculation_proof(self):
        r=audit(GOOD,GOOD);self.assertTrue(r['generated_scope_snapshot_verified']);self.assertFalse(r['calculation_verified'])
    def test_old_cuda_retained_pointer_cannot_pass(self):
        bad=GOOD.replace(b'uint previous=actorStateQueryScopeSnapshot_0(at);',b'uint* previous=p;').replace(b'return previous;',b'return *previous;')
        with self.assertRaises(ValueError):audit(bad,GOOD)
    def test_post_store_snapshot_or_removed_noinline_rejected(self):
        bad=GOOD.replace(b'uint previous=actorStateQueryScopeSnapshot_0(at);\n*p = target+1;',b'*p = target+1;\nuint previous=actorStateQueryScopeSnapshot_0(at);')
        for raw in (bad,GOOD.replace(b'__noinline__',b'')):
            with self.assertRaises(ValueError):audit(raw,GOOD)


class ResidentScalarSnapshotTests(unittest.TestCase):
    def pair(self):
        data=json.loads((ROOT/'tests/fixtures/portable-resident-scalar-generated.json').read_text())
        return [data[t]['functions'].encode() for t in ('cuda','metal')]

    def test_actual_generated_scalar_snapshots_are_not_calculation_proof(self):
        result=audit_resident_scalars(*self.pair())
        self.assertTrue(result['generated_resident_scalars_verified']);self.assertFalse(result['calculation_verified'])

    def test_hp_reload_and_post_increment_slot_fail_before_device_use(self):
        cuda,metal=self.pair();text=cuda.decode()
        name,body,_=function(text,'dispatch')
        snapshot=re.search(r'\b(?:ulonglong|ulong)\s+(\w+)\s*=\s*bodyHPBeforeHeal_\d+\(',body).group(1)
        bad_hp=text.replace(snapshot+' ^','state->hp_0[owner] ^')
        self.assertNotEqual(bad_hp,text)
        _,body,_=function(text,'findCarrier')
        slot=re.search(r'\buint\s+(\w+)\s*=\s*carrierCountBeforeAllocate_\d+\(',body).group(1)
        bad_slot=text.replace('return '+slot+';','return state->carrierCount_0;')
        self.assertNotEqual(bad_slot,text)
        for changed in (bad_hp,bad_slot,text.replace('__noinline__','')):
            with self.subTest(changed=changed[-60:]),self.assertRaises(ValueError):audit_resident_scalars(changed.encode(),metal)

    def test_snapshot_reader_mutation_or_wrong_field_is_rejected(self):
        cuda,metal=self.pair();text=cuda.decode()
        _,reader,_=function(text,'bodyHPBeforeHeal')
        for changed in (text.replace(reader,reader+'\nstate->healing_0[0]=0;\n'),text.replace(reader,reader.replace('hp_0','healing_0'))):
            with self.assertRaises(ValueError):audit_resident_scalars(changed.encode(),metal)

    def test_exact_inverse_does_not_depend_on_omitted_unrelated_gpu_entries(self):
        from portable_enemy_ammo_combined_source_contract import project_resident_scalars
        data=json.loads((ROOT/'tests/fixtures/portable-healing-hp-snapshot-delta.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            names=['tests/fixtures/portable-healing-hp-snapshot-delta.json',*data['files']]
            for name in names:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
            projected=project_resident_scalars(root)
            import hashlib
            for name,row in data['files'].items():self.assertEqual(hashlib.sha256(projected[name].encode()).hexdigest(),row['baseline_sha256'])
            self.assertEqual(project_resident_scalars(root,projected),projected)
            for name in data['files']:
                bad={name:(root/name).read_text()+'\n// unreviewed change\n'}
                with self.assertRaises(ValueError):project_resident_scalars(root,bad)
    def test_wrong_return_value_or_writing_snapshot_helper_rejected(self):
        for raw in (GOOD.replace(b'return previous;',b'return *p;'),GOOD.replace(b'{ return *p; }',b'{\n*p = 1;\nreturn *p; }')):
            with self.assertRaises(ValueError):audit(raw,GOOD)

if __name__=='__main__':unittest.main()
