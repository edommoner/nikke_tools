"""Emit CUDA and Metal from one source; compilation alone is not GPU validation."""
import argparse,hashlib,json,platform,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--compiler',type=Path);args=ap.parse_args()
    compiler=args.compiler or ROOT/f'.tools/slang-2026.20-{platform.system()}-{platform.machine()}/bin'/('slangc.exe' if platform.system()=='Windows' else 'slangc')
    source=ROOT/'gpu/portable_probe.slang';out=ROOT/'research/portable-build';out.mkdir(parents=True,exist_ok=True)
    outputs={}
    for target,extension in [('cuda','cu'),('metal','metal')]:
        output=out/f'portable_probe.{extension}'
        generated=subprocess.run([str(compiler),str(source),'-entry','portableProbe','-target',target,'-fp-mode','precise'],check=True,capture_output=True)
        output.write_bytes(generated.stdout)
        outputs[target]=dict(path=output.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    version=subprocess.run([str(compiler),'-version'],capture_output=True,text=True,check=True)
    report=dict(passed=True,stage='source-generation-only',gpu_execution_verified=False,production_runtime_connected=False,compiler_version=(version.stdout+version.stderr).strip(),source_sha256={'gpu/portable_probe.slang':hashlib.sha256(source.read_bytes()).hexdigest()},outputs=outputs)
    (ROOT/'research/portable-probe-build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
