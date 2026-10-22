"""Generate diagnostic entries from unchanged shared phases; never launch them."""
import hashlib,json,os,platform,subprocess,time
from pathlib import Path

PHASES={
    'init':'initializeRuntime(runtimeStates[id.x]); bool ready; initializePortableProgram(runtimeStates[id.x],input,output,ready); results[output+1]=uint(ready);',
    'commands':'uint queries; executePortableCommands(runtimeStates[id.x],input,output,queries); results[output+1]=queries;',
    'write':'writePortableProgram(runtimeStates[id.x],input,output,results[output+1]);',
}
ENTRY='portablePhase'


def digest(raw):return hashlib.sha256(raw).hexdigest()


def wrapper(root,source,phase):
    if phase not in PHASES:raise ValueError('Unknown diagnostic phase')
    path=(Path(root)/source).resolve()
    if any(char in str(path) for char in ('"','\n','\r')):raise ValueError('Unsupported shader path')
    return ('// Diagnostic source generation only; not a valid standalone battle.\n'
        '#define portableEvents unusedFullPortableEvents\n#include "'+path.as_posix()+'"\n'
        '#undef portableEvents\n[shader("compute")]\n[numthreads(1,1,1)]\n'
        'void '+ENTRY+'(uint3 id : SV_DispatchThreadID) {\n'
        'if(id.x>=commands[0]) return;\n'
        'uint input=1+id.x*P_INPUT_WORDS,output=id.x*P_OUTPUT_WORDS;\n'
        'WORLD_TEAM_INPUT(input,output)\n'+PHASES[phase]+'\n}\n')


def generate(root,source,output,*,package_id,source_hashes,compiler_root=None,runner=None):
    from portable_compiler_stats import cuda_statistics
    root=Path(root).resolve();output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    compiler_root=Path(compiler_root or os.environ.get('NIKKE_SLANG_ROOT',root/f'.tools/slang-2026.20-{platform.system()}-{platform.machine()}')).resolve()
    compiler=compiler_root/'bin'/('slangc.exe' if os.name=='nt' else 'slangc')
    report=dict(schema=1,package_id=package_id,source=source,entry=ENTRY,passed=False,phases={},
        gpu_calls=dict(build=0,execute=0),slang_codegen_calls=0,nvrtc_calls=0,driver_calls=0,kernel_calls=0,
        calculation_verified=False,executable_battle_verified=False,
        scope='Slang CUDA/Metal diagnostic generation only. No compiler-memory, executable ABI, numerical equivalence or GPU-support proof')
    started=time.perf_counter()
    try:
        if not compiler.is_file():raise ValueError('Slang compiler missing: '+str(compiler))
        before=source_hashes(source);report['source_sha256']=before
        report['compiler']=dict(path=str(compiler),sha256=digest(compiler.read_bytes()))
        # Require the existing common phases and resident caller; do not silently
        # apply these diagnostic bodies to a different suite/implementation.
        for name in ('gpu/program_phases.slang','gpu/event_runtime.slang','gpu/world_projectile_resident_entry.slang'):
            if name not in before:raise ValueError('Diagnostic requires shared resident runtime closure')
        invoke=runner or subprocess.run
        for phase in PHASES:
            path=output/(phase+'.slang');text=wrapper(root,source,phase)
            with path.open('x') as stream:stream.write(text)
            row=dict(wrapper_sha256=digest(path.read_bytes()),targets={});report['phases'][phase]=row
            for target,suffix in (('cuda','cu'),('metal','metal')):
                generated=output/(phase+'.'+suffix);reflection=output/(phase+'.'+target+'.reflection.json')
                argv=[str(compiler),str(path),'-entry',ENTRY,'-target',target,'-fp-mode','precise','-line-directive-mode','none','-o',str(generated),'-reflection-json',str(reflection)]
                record=dict(argv=argv);row['targets'][target]=record
                tick=time.perf_counter();report['slang_codegen_calls']+=1
                try:result=invoke(argv,capture_output=True,timeout=60)
                except subprocess.TimeoutExpired as error:
                    record.update(timed_out=True,elapsed_seconds=time.perf_counter()-tick)
                    for label,raw in (('stdout',error.stdout),('stderr',error.stderr)):
                        with (output/(phase+'.'+target+'.'+label+'.log')).open('xb') as stream:stream.write(raw or b'')
                    raise
                for label,raw in (('stdout',result.stdout),('stderr',result.stderr)):
                    with (output/(phase+'.'+target+'.'+label+'.log')).open('xb') as stream:stream.write(raw)
                record.update(exit_code=result.returncode,elapsed_seconds=time.perf_counter()-tick)
                if result.returncode:raise RuntimeError('Diagnostic Slang generation failed: '+phase+'/'+target)
                for artifact in (generated,reflection):
                    if not artifact.is_file() or not artifact.stat().st_size:raise ValueError('Diagnostic artifact missing/empty: '+artifact.name)
                raw=generated.read_bytes()
                record.update(bytes=len(raw),sha256=digest(raw),reflection_sha256=digest(reflection.read_bytes()))
                if target=='cuda':record['statistics']=cuda_statistics(raw)
            if source_hashes(source)!=before:raise ValueError('Shared source changed during diagnostic generation')
        if digest(compiler.read_bytes())!=report['compiler']['sha256']:raise ValueError('Slang compiler changed during generation')
        report['passed']=True
    except BaseException as error:
        report['error']=type(error).__name__+': '+str(error)
        raise
    finally:
        report['elapsed_seconds']=time.perf_counter()-started
        with (output/'report.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    return report
