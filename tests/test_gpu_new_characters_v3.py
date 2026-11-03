"""CPU regressions for the Metal admission marker and periodic stack defects."""
import copy,json,re,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]

def function(path,name):
    """Compile the actual scalar Slang helper as C++, replacing only inout syntax."""
    text=(ROOT/path).read_text();start=text.index('bool '+name+'(');end=text.index('{',start);depth=1;end+=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end].replace('inout Runtime s','Runtime& s')

class NewCharacterMetalRegressionTests(unittest.TestCase):
    def test_engaged_marker_cannot_alias_other_tagged_mode_payloads(self):
        from portable_new_character_cases import fixtures
        from test_gpu_new_characters import adapter
        from portable_specs import LIMITS as L
        words=adapter().compile_case(fixtures()[0])[0]
        marker=words[L['DEFINITION_EXTRA_BASE']+3]
        schema=(ROOT/'gpu/portable_schema.slang').read_text()
        tags=[int(value) for value in re.findall(r'P_\w+_FLAG = (\d+)U;',schema)]
        self.assertEqual(marker,2048)
        for flag in (1,2,4,8,16,32,64,128,*tags):self.assertEqual(marker&flag,0)
        self.assertIn('statusMarker(s,who,2048U)',(ROOT/'gpu/status_runtime.slang').read_text())
        self.assertIn('d.quantityFlags&2049U',(ROOT/'gpu/admission_definition_types.slang').read_text())

    def test_actual_product_stack_selector_includes_periodic_membership_and_generations(self):
        # CPU-only execution of the unchanged scalar source, with storage accessors
        # supplied by a small deterministic fixture. No generated GPU execution.
        helpers='\n'.join(function(path,name) for path,name in (
            ('gpu/world_periodic_runtime.slang','periodicSnapshotGeneration'),
            ('gpu/world_periodic_runtime.slang','periodicSnapshotMember'),
            ('gpu/world_periodic_runtime.slang','worldPeriodicNamedMember'),
            ('gpu/world_actor_stacks.slang','actorStackAffected')))
        source=r'''
#include <cassert>
using uint=unsigned int;
const uint ACTOR_REF=128;
uint results[4096]={};
struct Runtime {uint carrierDefinition[4]={2,0,0,0};bool blocked=false,recipient=false;};
struct ActorBits {uint words[4];};
struct Definition {uint kind;};
uint actorPoolCount(Runtime&) {return 2;}
uint actorPoolAt(Runtime&,uint slot) {return 64+slot*16;}
uint periodicDefinitionSnapshot(Runtime&,uint row) {return 128+row*38;}
bool worldPeriodicClock(Runtime&,Definition d) {return d.kind==3;}
Definition readDefinition(uint,uint row) {return {row==2?3U:0U};}
// worldPeriodicNamedMember uses the production Runtime input address too.
bool actorBitsHas(ActorBits b,uint target) {return (b.words[target/32]&(1U<<(target%32)))!=0;}
bool actorRecipientMember(Runtime& s,uint,uint) {return s.recipient;}
bool actorStackBlocked(Runtime& s,uint) {return s.blocked;}
'''.replace('bool blocked=false,recipient=false;','bool blocked=false,recipient=false;uint inputBase=0;')+helpers+r'''
int main() {
 Runtime s;ActorBits boss={{1,0,0,0}},add={{2,0,0,0}},empty={{0,0,0,0}};
 uint at=periodicDefinitionSnapshot(s,2);results[at+2]=3;results[at+1]=5;
 results[actorPoolAt(s,1)+10]=5;
 assert(actorStackAffected(s,0,boss));assert(actorStackAffected(s,0,add));
 assert(!actorStackAffected(s,0,empty));
 results[actorPoolAt(s,1)+10]=6;assert(!actorStackAffected(s,0,add));
 s.blocked=true;assert(!actorStackAffected(s,0,boss));s.blocked=false;
 results[at+2]=0;assert(!actorStackAffected(s,0,boss));
 s.recipient=true;assert(actorStackAffected(s,0,boss));
 s.carrierDefinition[0]=1;s.recipient=false;assert(!actorStackAffected(s,0,boss));
}
'''
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'stack.cpp';path.write_text(source)
            # Both shared callers must include periodic recipients; the former
            # product branch failed the very first boss assertion here.
            for macro in ('PORTABLE_COORDINATE_ORIGINAL_SOURCE_OPS','PORTABLE_COORDINATE_EXISTING_HANDLERS'):
                binary=Path(folder)/macro
                subprocess.run(['/usr/bin/c++','-std=c++17','-D'+macro,str(path),'-o',str(binary)],check=True,capture_output=True,text=True)
                subprocess.run([str(binary)],check=True,capture_output=True,text=True)

    def test_mihara_product_cpu_stack_ablation_matches_reported_gpu_defect(self):
        import engine_worker
        from calculator import buff_manager as bm
        body=json.loads((ROOT/'tests/fixtures/gpu-mihara-stack-product-v3.json').read_text());seen=[]
        original=bm.BuffManager._dispatch_instant
        def capture(manager,e,c,t,*args,**kwargs):
            before=[(a.stack,list(a.target_chars or [])) for a in manager._active if a.effect.get('name')=='사슬 감기']
            result=original(manager,e,c,t,*args,**kwargs)
            if e.get('stat')=='debuff_stack_add':
                seen.append((before,[(a.stack,list(a.target_chars or [])) for a in manager._active if a.effect.get('name')=='사슬 감기']))
            return result
        with patch.object(bm.BuffManager,'_dispatch_instant',capture):canonical=engine_worker.evaluate(dict(copy.deepcopy(body),compute_backend='cpu'))
        replacement={n:[e for e in effects if not (e.get('type')=='instant' and e.get('stat')=='debuff_stack_add')] for n,effects in bm._PARSED_SKILLS.items()}
        with patch.dict(bm._PARSED_SKILLS,replacement,clear=True):ablated=engine_worker.evaluate(dict(copy.deepcopy(body),compute_backend='cpu'))
        self.assertEqual(canonical['total_damage'],391579429);self.assertEqual(ablated['total_damage'],339980705)
        self.assertEqual(seen[0],([(10,['__enemy__'])],[(11,['__enemy__'])]))
        self.assertTrue(any(after==[(20,['__enemy__'])] for _,after in seen))
        self.assertEqual(next(m['damage'] for m in canonical['members'] if m['name']=='미하라 : 본딩 체인'),173495288)
        self.assertEqual(next(m['damage'] for m in ablated['members'] if m['name']=='미하라 : 본딩 체인'),121896564)

    def test_mihara_ordinary_product_packs_dot_and_stack_rows_before_dispatch(self):
        import portable_detail,engine_worker,portable_backend
        from portable_specs import LIMITS as L,FIELDS as F
        body=json.loads((ROOT/'tests/fixtures/gpu-mihara-stack-product-v3.json').read_text())
        with patch.object(engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle during pack')),patch.object(portable_backend,'execute',side_effect=AssertionError('No GPU')):
            prepared,_=portable_detail.prepare(body);source,iw,ow,words,meta=portable_detail.compile_product(prepared)
        self.assertEqual(source,'gpu/product_fixed_battle_entry.slang')
        self.assertEqual(words[L['WORLD_ACTOR_POOL_INPUT_BASE']+4],0x57543031)
        self.assertTrue(any(item['effect'].get('stat')=='debuff_stack_add' for item in prepared['effects']))
        rows={item['effect'].get('name'):i for i,item in enumerate(prepared['effects'])}
        dot,op=rows['사슬 감기'],rows['타이트']
        self.assertEqual(words[L['DEFINITION_BASE']+dot*L['DEFINITION_WORDS']+F['KIND']],3)
        self.assertEqual(words[L['DEFINITION_BASE']+op*L['DEFINITION_WORDS']+F['KIND']],20)
        self.assertEqual(words[L['DEFINITION_BASE']+op*L['DEFINITION_WORDS']+F['TARGET_NAME']],words[L['DEFINITION_BASE']+dot*L['DEFINITION_WORDS']+F['NAME']])

if __name__=='__main__':unittest.main()
