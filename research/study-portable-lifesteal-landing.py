import sys,copy,json,importlib.util,argparse
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('metal','cuda'),default='metal');args=parser.parse_args()
sys.path[:0]=['app','scripts']
import engine_worker
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_weapon_oracle import authored_weapon,authored_weapon_state
from timer_registry_cases import NAMES
from portable_runtime import run_programs
from portable_specs import LIMITS as L,FIELDS as F
sp=importlib.util.spec_from_file_location('v','scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
c=copy.deepcopy(json.load(open('tests/fixtures/portable-lifesteal-prototype.json'))['cases'][0]);c['name']='life-native-normal-then-next-frame-skill-landings';c['combat']['clock']='accumulated';c['combat']['weapons'][0]=dict(enabled=True,mode='auto',stage=0,capacity=20,coefficient=100,interval=1,reload=1,gauge=0)
c['effects'].append(dict(name='on attack skill',type='damage',source='스킬2',stat='damage:2',fixed_value=100,target='enemy',trigger=dict(timing=['on_attack'],condition=[])));c['owners'].append(0);c['script']=[[.05,24,0,0,0,-1,0,0],[.05,2,0,0,-1,0,0,0]];c['environment']['native_landing']=True;c['script'].insert(1,[.05,30,0,0,0,-1,0,0]);c['expected_queries']=[dict(damage=[3000,0,0,0,0],allies=[dict(hp=250)])]
raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(c['effects'],c['owners'])];history=[];capture={}
original_bm,original_char=timeline.BuffManager,timeline.CharState
class Manager(BuffManager):
 def _register_all(self):self._effects=raw;self._build_notify_index()
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);capture['bm']=self
  for n,h in zip(NAMES,c['environment']['allies']):self.state['base_stats'][n].update(atk=1000,hp=h['base_hp']);self.state['hp'][n]=h['hp'];self.state['hp_pct'][n]=h['hp']/h['base_hp']*100
 def notify(self,event,t,owner,*args,**kwargs):
  if owner==NAMES[0] and event in ('on_attack','hit_count','hit_count:on attack skill','event:heal_received'):history.append(dict(event=event,time=t,hp=self.state['hp'][owner]))
  return super().notify(event,t,owner,*args,**kwargs)
 def apply_shared_body_heal(self,name,amount,t):
  history.append(dict(event='native-body-heal',owner=NAMES.index(name),time=t,hp=self.state['hp'][name],amount=amount));return super().apply_shared_body_heal(name,amount,t)
def actor(char,*args):
 index=NAMES.index(char['name']);w=c['combat']['weapons'][index];authored_weapon(char,w);st=authored_weapon_state(char,w,1000)
 if not w.get('enabled',False):st.tick=lambda *a,**k:[]
 return st
try:
 timeline.BuffManager=Manager;timeline.CharState=actor
 chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES]
 result=timeline.simulate(chars,dict(duration=.05,rng_mode='expected',burst_gauge_mode='accumulate'),dict(**{'def':0},core_px=0,code=None,optimal_range_weapons=[]))
 native=dict(hp=capture['bm'].state['hp'][NAMES[0]],damage=sum(h.damage for h in result.hits),hits=[dict(time=h.t,damage=h.damage,tag=h.hit_tag) for h in result.hits],history=history)
finally:timeline.BuffManager=original_bm;timeline.CharState=original_char
assert native['hp']==250 and native['damage']==3000,native
words,meta=v.compile_case(c)
r=run_programs([(words,meta)],backend=args.backend);r.update(passed=r['results'][0]['queries'][0]['allies'][0]['hp']==native['hp'] and sum(r['results'][0]['queries'][0]['damage'])==native['damage'],stage='shared-landing-queue-study',case=c,native=native,scope='Working normal lifesteal path is verified separately. Actual native timeline exposes missing deferred skill landing recovery; production admission stays closed.')
Path('research/portable-lifesteal-landing-queue-study'+('' if args.backend=='metal' else '-cuda')+'.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('Native',native['hp'],native['damage'],'GPU',r['results'][0]['queries'][0]['allies'][0]['hp'],sum(r['results'][0]['queries'][0]['damage']))
