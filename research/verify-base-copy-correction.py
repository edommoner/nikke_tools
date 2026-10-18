"""Show the previous CPU omission separately from current independent witnesses."""
import argparse,importlib.abc,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--before',action='store_true');args=parser.parse_args()
class Loader(importlib.abc.Loader):
 def __init__(self,path):self.path=path
 def create_module(self,spec):return None
 def exec_module(self,module):
  module.__file__=str(ROOT/'app'/self.path.name);exec(compile(self.path.read_bytes(),module.__file__,'exec'),module.__dict__)
class Finder(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  source=ROOT/'research/ports/v46-max-hp-snapshot-verified/app'/(name+'.py')
  if '.' not in name and source.exists():return importlib.util.spec_from_loader(name,Loader(source))
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
if args.before:sys.meta_path.insert(0,Finder())
import engine_worker
from calculator.buff_manager import BuffManager
spec=importlib.util.spec_from_file_location('copy_before_after_helpers',ROOT/'scripts/verify-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
names=['리타','크라운','모더니아','앨리스','N102'];chars=v.characters(names)
effects=[dict(name=stat,source='스킬1',type='buff',stat=stat,target='self',fixed_value=quantity,duration=.5,copy_from=selector,trigger={'timing':['on_attack'],'condition':[]}) for stat,quantity,selector in [('atk_copy',20,'allies_top_atk:1'),('hp_copy',50,'allies_top_hp:1')]]
class Manager(BuffManager):
 def _register_all(self):self._effects=[(effect,names[0]) for effect in effects];self._build_notify_index()
bs={name:dict(atk=value,**{'def':0},hp=value) for name,value in zip(names,(1000,2000,1500,900,800))}
manager=Manager(chars,state=dict(base_stats=bs,hp={n:v['hp'] for n,v in bs.items()},hp_pct={n:100 for n in names},enemy={'def':0,'core_px':0},full_burst=False,rng_acc={},rng_expected=True,camera=set()))
manager.notify('on_attack',0,names[0])
report=dict(archived_v46=args.before,atk_flat=manager.get_buffs(names[0],'enemy',0).get('atk_flat',0),maximum_hp=manager.effective_max_hp(names[0]),current_hp=manager.state['hp'][names[0]],expected=dict(atk_flat=400,maximum_hp=2000,current_hp=2000),game_rules_verified=False)
(ROOT/f'research/base-copy-{ "before" if args.before else "after"}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
