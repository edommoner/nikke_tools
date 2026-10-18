"""One fixture packer and comparison for portable GPU backends; no CPU replay."""
import argparse,hashlib,json,platform,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/portable-probe.json'


def pack_cases(cases):
    if not 1<=len(cases)<=64:raise ValueError('Probe requires 1..64 cases')
    words=[len(cases)]
    for case in cases:
        steps=case['steps'];expected=case['expected']
        if not 1<=len(steps)<=16 or len(expected)!=7:raise ValueError('Invalid probe dimensions')
        for row in steps:
            if len(row)!=6 or any(type(v) is not int or not 0<=v<2**32 for v in row) or not 1<=row[0]<=6:raise ValueError('Invalid probe command')
            if row[0]==4 and (row[5]==0 or row[3]<=row[2]):raise ValueError('Invalid clock interval/lifetime')
        if any(type(v) is not int or not 0<=v<2**32 for v in expected):raise ValueError('Invalid expected output')
        words += [len(steps)]+[v for row in steps for v in row]+[0]*((16-len(steps))*6)
    return struct.pack('<'+'I'*len(words),*words)


def main():
    ap=argparse.ArgumentParser();mode=ap.add_mutually_exclusive_group(required=True);mode.add_argument('--validate-only',action='store_true');mode.add_argument('--backend',choices=('metal',));args=ap.parse_args()
    cases=json.loads(FIXTURE.read_text(encoding='utf-8'))['cases'];packed=pack_cases(cases)
    files=[FIXTURE,Path(__file__).resolve(),ROOT/'gpu/portable_probe.slang',ROOT/'scripts/run-metal-probe.swift']
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    report=dict(passed=True,stage='fixture-validation',gpu_execution_verified=False,production_runtime_connected=False,cases=[c['name'] for c in cases],source_sha256=before)
    if not args.validate_only:
        if sys.platform!='darwin':raise SystemExit('Metal execution requires macOS; no CPU fallback counts as GPU verification')
        directory=ROOT/'research/portable-build';source=directory/'portable_probe.metal'
        build=json.loads((ROOT/'research/portable-probe-build.json').read_text(encoding='utf-8'))
        if build['source_sha256']['gpu/portable_probe.slang']!=before['gpu/portable_probe.slang'] or hashlib.sha256(source.read_bytes()).hexdigest()!=build['outputs']['metal']['sha256']:raise ValueError('Rebuild the changed portable probe first')
        input_path=directory/'input.bin';output_path=directory/'output.bin';input_path.write_bytes(packed)
        if output_path.exists():output_path.unlink()
        process=subprocess.run(['swift',str(ROOT/'scripts/run-metal-probe.swift'),str(source),str(input_path),str(output_path)],check=True,capture_output=True,text=True,encoding='utf-8')
        actual=list(struct.unpack('<'+'I'*(len(cases)*7),output_path.read_bytes()))
        for index,case in enumerate(cases):
            if actual[index*7:(index+1)*7]!=case['expected']:raise AssertionError((case['name'],actual[index*7:(index+1)*7],case['expected']))
        report.update(stage='gpu-execution',gpu_execution_verified=True,backend='metal',device=json.loads(process.stdout)['device'],output=actual)
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    suffix='fixtures' if args.validate_only else args.backend
    (ROOT/f'research/portable-probe-{suffix}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
