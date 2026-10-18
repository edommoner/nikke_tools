"""Reproduce the intentional fresh-lifetime correction against archived v44 CPU."""
import argparse,importlib.abc,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--before',action='store_true');a=parser.parse_args()
class Loader(importlib.abc.Loader):
 def __init__(self,path):self.path=path
 def create_module(self,spec):return None
 def exec_module(self,module):
  module.__file__=str(ROOT/'app'/self.path.name);exec(compile(self.path.read_bytes(),module.__file__,'exec'),module.__dict__)
class Finder(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  source=ROOT/'research/ports/v44-named-hits-verified/app'/(name+'.py')
  if '.' not in name and source.exists():return importlib.util.spec_from_loader(name,Loader(source))
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
if a.before:sys.meta_path.insert(0,Finder())
import engine_worker
from calculator.buff_manager import BuffManager
spec=importlib.util.spec_from_file_location('refresh_helpers',ROOT/'scripts/verify-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
names=['리타','크라운','모더니아','앨리스','N102'];chars=v.characters(names)
effect={'name':'pool','source':'스킬1','type':'buff','stat':'dmg_accum_received_atk_pct','target':'target','fixed_value':100,'duration':.3,'trigger':{'timing':['on_attack'],'condition':[]}}
class Manager(BuffManager):
 def _register_all(self):self._effects=[(effect,names[0])];self._build_notify_index()
bm=Manager(chars,state={'base_stats':{n:{'atk':1000,'def':0,'hp':100000} for n in names},'enemy':{'def':0,'core_px':0},'full_burst':False,'rng_acc':{},'rng_expected':True,'camera':set()})
bm.notify('on_attack',0,names[0]);bm.accumulate_damage(names[1],700,.1);deposited=bm._accum_last['pool'];bm.notify('on_attack',.2,names[0]);after_refresh=bm._accum_last['pool'];bm.tick(.6);released=bm.accum_discharge('pool',.6)
report=dict(archived_v44=a.before,deposited=deposited,archived_after_refresh=after_refresh,released_without_new_hits=released,expected_for_fresh_lifetime=0)
(ROOT/('research/damage-refresh-before.json' if a.before else 'research/damage-refresh-after.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
