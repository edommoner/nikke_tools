"""GPU input decoder vs frozen v41 decoder expressions, never battle replay."""
import array,hashlib,importlib.util,json,random,re,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_backend import execute
from portable_specs import LIMITS as L
BASE='70f90181245ff1ca5d0930bc2e332762d99ebde1'
old=subprocess.check_output(['git','show',BASE+':gpu/event_runtime.slang'],cwd=ROOT,text=True)
schema=subprocess.check_output(['git','show',BASE+':gpu/portable_schema.slang'],cwd=ROOT,text=True)
constants={name:int(value) for name,value in re.findall(r'static const uint (\w+) = (\d+)U;',schema)}
body=old.split('struct Definition\n{',1)[1].split('};',1)[0];fields=[]
for declaration in body.split(';'):
 if not declaration.strip():continue
 match=re.fullmatch(r'\s*(uint64_t|uint|int)\s+(.+?)\s*',declaration,re.S)
 fields.extend((name.strip(),match[1]) for name in match[2].split(','))
start=old.index('    for (uint j = 0; j < s.count; j++)\n    {\n        uint at = input+P_DEFINITION_BASE')
end=old.index('        s.defs[j] = d;',start)
expressions=dict(re.findall(r'\bd\.(\w+)\s*=(?!=)\s*([^;]+);',old[start:end]))
assert set(expressions)=={f for f,t in fields}
stride=sum(2 if t=='uint64_t' else 1 for f,t in fields);output_words=stride*256
scalar_control='--scalar-accessor-control' in sys.argv
out_control='--out-parameter-control' in sys.argv
source=ROOT/('gpu/definition_scalar_probe.slang' if scalar_control else 'gpu/definition_out_probe.slang' if out_control else 'gpu/definition_input_probe.slang')
entry='definitionScalarProbe' if scalar_control else 'definitionOutProbe' if out_control else 'definitionInputProbe'
lines=['// Decoder-only probe; frozen v41 semantics are checked independently on host.','#include "event_runtime.slang"','[shader("compute")]','[numthreads(1,1,1)]','void '+entry+'(uint3 thread : SV_DispatchThreadID)','{','    uint id=thread.x;if(id>=commands[0]) return;',f'    uint input=1+id*P_INPUT_WORDS,output=id*{output_words}U;','    for(uint row=0;row<P_DEFINITIONS;row++)','    {','        Definition d=readDefinition(input,row);',f'        uint at=output+row*{stride}U;'];offset=0
for name,kind in fields:
 lines.append(f'        storeNumber(at+{offset}U,d.{name});' if kind=='uint64_t' else f'        results[at+{offset}U]=uint(d.{name});');offset+=2 if kind=='uint64_t' else 1
lines+=['    }','}']
if scalar_control:
 lines=[line.replace('Definition d=readDefinition(input,row);','// Each scalar accessor executes independently.') for line in lines]
 lines=[re.sub(r'\bd\.(\w+)',lambda m:'definition_'+m[1]+'(input,row)',line) for line in lines]
if out_control:
 lines[2:2]=['[noinline]','void loadDefinitionOutControl(uint input,uint row,out Definition d)','{ loadDefinition(input,row,d); }']
 lines=[line.replace('Definition d=readDefinition(input,row);','Definition d;loadDefinitionOutControl(input,row,d);') for line in lines]
source.write_text('\n'.join(lines)+'\n')
backend=sys.argv[sys.argv.index('--backend')+1] if '--backend' in sys.argv else 'metal'
rng=random.Random(711);count=4;words=array.array('I',[count]);words.extend([0]*L['INPUT_WORDS']);words.extend([0xffffffff]*L['INPUT_WORDS']);words.extend(rng.getrandbits(32) for _ in range(L['INPUT_WORDS']));patterns=[0,0x80000000,0x7ff00000,1];words.extend(patterns[i%4] for i in range(L['INPUT_WORDS']))
packed=words.tobytes() if sys.byteorder=='little' else None
if packed is None:words.byteswap();packed=words.tobytes();words.byteswap()
expected=[]
for case in range(count):
 input=1+case*L['INPUT_WORDS']
 for j in range(256):
  env=dict(constants,input=input,j=j,commands=words,int=lambda n:n-2**32 if n>=2**31 else n,loadNumber=lambda at:int(words[at])|(int(words[at+1])<<32))
  for name,base,width in [('at','P_DEFINITION_BASE','P_DEFINITION_WORDS'),('packet','P_DAMAGE_DEFINITION_BASE','P_DAMAGE_DEFINITION_WORDS'),('bullet','P_BULLET_DEFINITION_BASE',None),('periodic','P_PERIODIC_DEFINITION_BASE',None),('extra','P_DEFINITION_EXTRA_BASE','P_DEFINITION_EXTRA_WORDS'),('health','P_HEALTH_DEFINITION_BASE','P_HEALTH_DEFINITION_WORDS'),('duration','P_DURATION_DEFINITION_BASE',None)]:env[name]=input+constants[base]+j*(constants[width] if width else 2)
  for name,kind in fields:
   value=eval(expressions[name],{'__builtins__':{}},env)
   expected.append(value&0xffffffff)
   if kind=='uint64_t':expected.append((value>>32)&0xffffffff)
raw,evidence=execute(source.relative_to(ROOT).as_posix(),entry,packed,L['INPUT_WORDS'],output_words,backend)
assert raw==struct.pack('<'+str(len(expected))+'I',*expected)
report=dict(passed=True,abi='production-scalar-accessors' if scalar_control else 'out-parameter-control' if out_control else 'production-forceinline-view',scope='All 55 input decoder fields vs frozen v41 expressions, 4 adversarial programs x 256 definitions, signed IDs, flags and arbitrary binary64 bits; not full event executor verification',frozen_reference=BASE,decoded_fields=len(fields),records=count*256,word_values=len(expected),frozen_decoder_sha256=hashlib.sha256(old.encode()).hexdigest(),**evidence)
(ROOT/f'research/portable-definition-{"scalar" if scalar_control else "out" if out_control else "input"}-{backend}.json').write_text(json.dumps(report,indent=2)+'\n');print('Definition input GPU codec passed',backend,len(fields),count*256,flush=True)
