"""Mac-only source-generation hypothesis; never compile CUDA or launch a GPU.

The original source tree is read-only. All transformations and generated files
live under the fresh --out directory. Not a production implementation.
"""
import pathlib,re,sys,os,json,hashlib,time
from unittest.mock import patch


def main():
    import argparse,platform
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=pathlib.Path,required=True);args=parser.parse_args()
    if platform.system()!='Darwin':raise ValueError('Source exploration runs on Mac only')
    root=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(root/'app')]
    import portable_backend as backend
    from portable_compiler_stats import cuda_statistics
    source='gpu/compiler_commands_entry.slang';original=backend.source_hashes(source)
    lab=args.out.resolve();lab.mkdir(parents=True,exist_ok=False)
    for name in original:
     p=lab/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/name).read_bytes())
    state=lab/'gpu/event_runtime.slang';decoder=lab/'gpu/definition_runtime.slang'
    text=state.read_text();start=text.index('struct Definition\n');end=text.index('\n};',start)+3
    fields=[]
    for group in text[start:end].split('{',1)[1].rsplit('}',1)[0].split(';'):
     if not group.strip():continue
     kind,names=group.strip().split(None,1)
     fields += [(kind,name.strip()) for name in names.split(',')]
    decode=decoder.read_text();begin=decode.index('{',decode.index('void loadDefinition'));finish=decode.index('\n}',begin)+2
    assignments=dict(re.findall(r'd\.(\w+)\s*=\s*(definition_\w+)\(input,row\);',decode[begin:finish]))
    assert set(assignments)=={n for _,n in fields}
    assert len(fields)==55,'Expected the fixed55-member baseline Definition'
    props=['struct Definition { uint _wireInput,_wireRow,_overrideMask,_route,_hits;']
    for kind,name in fields:
     override={'damageRoute':('_route',1),'damageHits':('_hits',2)}.get(name)
     getter=assignments[name]+'(_wireInput,_wireRow)'
     if override:
      slot,bit=override;props.append(f'property {kind} {name} {{ get {{ return (_overrideMask&{bit}U)!=0 ? {slot} : {getter}; }} set {{ {slot}=newValue; _overrideMask|={bit}U; }} }}')
     else:props.append(f'property {kind} {name} {{ get {{ return {getter}; }} }}')
    props.append('};')
    state.write_text(text[:start]+'\n'.join(props)+text[end:])
    decoder.write_text(decode[:begin]+'{ d._wireInput=input;d._wireRow=row;d._overrideMask=0;d._route=0;d._hits=0; }'+decode[finish:])
    started=time.perf_counter();report=dict(schema=1,scope='Temporary Slang source-generation prototype only; no numeric/ABI/compiler-memory proof',modified_shared_files=['gpu/event_runtime.slang','gpu/definition_runtime.slang'],original_source_sha256=original,original_definition_members=len(fields),override_fields=['damageRoute','damageHits'],prototype_storage_members=5,nvrtc_calls=0,driver_calls=0,kernel_calls=0)
    try:
     with patch.object(backend,'ROOT',lab),patch.dict(os.environ,NIKKE_SLANG_ROOT=str(root/'.tools/slang-2026.20-Darwin-arm64')):
      outputs,hashes=backend.build(source,'portableEvents')
      report['generated']={k:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for k,p in outputs.items()}
      report['cuda_stats']=cuda_statistics(outputs['cuda'].read_bytes(),runtime='Definition_0')
      report['source_sha256']=hashes;report['passed']=True
    except BaseException as error:report['passed']=False;report['error']=str(error)
    finally:
     report['seconds']=time.perf_counter()-started
     (lab/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','original_source_sha256','cuda_stats')},indent=2))
    assert backend.source_hashes(source)==original

    if not report['passed']:raise RuntimeError(report['error'])


if __name__=='__main__':main()
