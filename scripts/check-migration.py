"""Lightweight host readiness and optional CPU startup; never launches a GPU."""
import argparse,json,platform,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def command(args):
    result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=30)
    return dict(passed=result.returncode==0,output=(result.stdout+result.stderr).strip()[:200])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cpu-smoke',action='store_true');args=ap.parse_args()
    engine=ROOT/'research/upstream/nikke-calc-master'
    required=['runner/sim.py','data/parsed_nikke.json']
    report=dict(platform=platform.system(),architecture=platform.machine(),python=platform.python_version(),engine_present=all((engine/p).is_file() for p in required),gpu_executed=False,warnings=[])
    if sys.version_info[:2]!=(3,12):report['warnings'].append('The Windows numerical baseline uses Python 3.12; use the same minor version for comparison.')
    report['node']=command(['node','--version']) if shutil.which('node') else dict(passed=False,output='node not found')
    report['slang_installed']=any((ROOT/'.tools').glob('slang-*/bin/slangc*'))
    if sys.platform=='darwin':
        report['metal_compiler']=command(['xcrun','--find','metal']) if shutil.which('xcrun') else dict(passed=False,output='xcrun not found')
        report['swift']=command(['swift','--version']) if shutil.which('swift') else dict(passed=False,output='swift not found')
    if args.cpu_smoke:
        process=subprocess.run([sys.executable,str(ROOT/'app/engine_worker.py')],input=json.dumps(dict(action='catalog')),cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
        result=json.loads(process.stdout) if process.stdout.strip() else {}
        count=len(result.get('characters',[]));report['cpu_catalog']=dict(passed=process.returncode==0 and count>0,characters=count)
        if not report['cpu_catalog']['passed']:report['cpu_catalog']['error']=result.get('error') or process.stderr[:200]
    report['passed']=report['node']['passed'] and report['engine_present'] and report.get('cpu_catalog',dict(passed=True))['passed']
    report['scope']='Host/CPU startup only. This does not validate Metal execution, CUDA equivalence, numerical portability, or performance.'
    (ROOT/'research/migration-readiness.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__':main()
