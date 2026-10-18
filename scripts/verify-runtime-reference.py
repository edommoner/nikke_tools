"""Compare real squads against the independently loaded pre-migration CPU code.

The archived implementation is regression evidence, not gameplay authority.
Normal module filenames preserve the pinned engine/data root during loading.
"""
import argparse,hashlib,importlib.abc,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class ArchivedLoader(importlib.abc.Loader):
    def __init__(self,path,name):self.path=path;self.name=name
    def create_module(self,spec):return None
    def exec_module(self,module):
        filename=str(ROOT/'app'/self.path.name)
        module.__file__=filename
        exec(compile(self.path.read_bytes(),filename,'exec'),module.__dict__)

class ArchivedFinder(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if '.' in fullname:return None
        source=ROOT/'research/ports/runtime-before/app'/(fullname+'.py')
        if source.exists():return importlib.util.spec_from_loader(fullname,ArchivedLoader(source,fullname))

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--side',choices=['before','after']);args=parser.parse_args()
    sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
    if args.side:
        if args.side=='before':sys.meta_path.insert(0,ArchivedFinder())
        import engine_worker as adapter
        cases=json.loads((ROOT/'research/runtime-reference-inputs.json').read_text(encoding='utf-8'))
        result={name:adapter.evaluate(body) for name,body in cases}
        (ROOT/f'research/runtime-reference-{args.side}.json').write_text(json.dumps(result,ensure_ascii=False)+'\n',encoding='utf-8')
    else:
        charge=load('runtime_charge_inputs','scripts/verify-heal-charge.py')
        decoy=load('runtime_decoy_inputs','scripts/verify-decoy-healing.py')
        full=load('runtime_full_inputs','scripts/verify-full-detail.py')
        cases=[(name,body) for _,name,body,_ in charge.fixtures('new') if name.startswith('raw-')]
        cases += [(name,body) for name,body,_ in decoy.real_fixtures()]
        cases += [('owned-burst-auto',full.fixture(60,grown=True)),('owned-burst-mast-position',full.fixture(60,'mast3',True,True))]
        (ROOT/'research/runtime-reference-inputs.json').write_text(json.dumps(cases,ensure_ascii=False)+'\n',encoding='utf-8')
        for side in ('before','after'):
            subprocess.run([sys.executable,__file__,'--side',side],cwd=ROOT,check=True)
        before=json.loads((ROOT/'research/runtime-reference-before.json').read_text(encoding='utf-8'))
        after=json.loads((ROOT/'research/runtime-reference-after.json').read_text(encoding='utf-8'))
        fields=('total_damage','members','burst_timeline','base_stats','boss_timeline','burst_policy','shooting_policy','burst_gauge_mode')
        rows=[dict(name=name,checks={key:old.get(key)==after[name].get(key) for key in fields}) for name,old in before.items()]
        passed=all(all(row['checks'].values()) for row in rows)
        report=dict(passed=passed,cases=rows,old_reference_is_game_authority=False,
                    scope='Independent pre-migration CPU implementation, real complete squads; no CPU trace used as GPU input.')
        (ROOT/'research/runtime-reference-migration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(passed=passed,cases=len(rows))))
        raise SystemExit(0 if passed else 1)
