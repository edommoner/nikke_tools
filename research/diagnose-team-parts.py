import copy,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('team_diagnostic',ROOT/'scripts/verify-team-hits-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
names=['루마니','리타','크라운','앨리스','모더니아'];chars=v.oracle.characters(names)
for i,c in enumerate(chars):c['skill_levels']={'1':3+i,'2':9-i,'3':3+i}
data=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text(encoding='utf-8'))
eff=next(e for e in data[names[0]] if e.get('stat')=='part_dmg_pct')
effects=[(eff,names[0])];program=v.oracle.program(chars,effects)
stats={n:{'atk':100000+i*1000,'hp':1000000,'def':1000} for i,n in enumerate(names)}
class BM(v.BuffManager):
 def _register_all(self):self._effects=copy.deepcopy(effects);self._build_notify_index()
bm=BM(chars,state=dict(base_stats=stats,enemy={},full_burst=False,rng_expected=True,rng_acc={}))
script=[[0,0,0,i,0,-1,0,0] for i in range(5)]
for k,i in enumerate([0,1,2,3,4,3]*5,1):
 t=k/100;bm.tick(t);bm.notify_team_hit('squad_part_hit',t,names[i]);script.append([t,0,44,i,0,-1,0,0])
for i in range(5):script.append([.31,2,103,i,54,i,0,0])
cpu=[bm.get_buffs(n,'__enemy__',.31)['part_dmg_pct'] for n in names]
d=v.Cuda()
try:gpu=v.run(d,[program],script,[[31784,5]],[stats],module_backend='native')['queries'][0]
finally:d.close()
print(json.dumps(dict(cpu=cpu,gpu=[q[0] for q in gpu],active=[dict(caster=ab.caster,value=bm._get_value(ab.effect,ab)) for ab in bm._active]),ensure_ascii=True))
