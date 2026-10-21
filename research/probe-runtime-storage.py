"""Code-generation evidence only: no NVRTC, Metal pipeline or GPU dispatch."""
import argparse,hashlib,json,platform,re,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_backend


def main(output):
    with output.open('x',encoding='utf-8') as stream:stream.write('{}\n')
    source='gpu/runtime_storage_probe.slang';started=time.perf_counter();rows=[]
    def forbidden(*args,**kwargs):raise RuntimeError('GPU execution forbidden in compiler storage probe')
    result=dict(stage='slang-code-generation-only',passed=False,source=source,observer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),host=platform.platform(),gpu_calls=0,nvrtc_calls=0,metal_pipeline_calls=0,compiler_memory_improvement_verified=False,scope='Two tiny address-space examples only; not complete Runtime, physical ABI, compiler peak, performance or battle equivalence')
    try:
        with patch.object(portable_backend,'execute',forbidden),patch.object(portable_backend,'execute_batches',forbidden):
            for entry in ('storageReference','storageIndirect'):
                paths,hashes=portable_backend.build(source,entry)
                for target,path in paths.items():
                    raw=path.read_bytes();text=raw.decode();copied=bool(re.search(r'\bProbeState_0\s+\w+\s*[=;]',text))
                    pointer=('ProbeState_0 device*' in text if target=='metal' else 'RWStructuredBuffer<ProbeState_0>' in text)
                    assert pointer and not copied,(entry,target,'unexpected state lowering')
                    rows.append(dict(entry=entry,target=target,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),source_sha256=hashes,private_state_copy_declaration=copied,device_buffer_pointer_emitted=pointer,excerpt=[line for line in text.splitlines() if 'resident_0' in line or 'ProbeState_0 *' in line or 'ProbeState_0 device*' in line]))
        result.update(passed=True,rows=rows)
    except BaseException as error:
        result['error']=type(error).__name__+': '+str(error);raise
    finally:
        result['elapsed_seconds']=time.perf_counter()-started
        output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('stage','passed','elapsed_seconds','gpu_calls','nvrtc_calls','compiler_memory_improvement_verified')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    main(parser.parse_args().out)
