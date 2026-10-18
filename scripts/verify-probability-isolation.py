"""Non-aligned phases distinguish effect identity, parallel squads and lifetimes."""
import sys,json,hashlib,importlib.util,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from gpu_selector import Cuda
from detail_gpu import run
spec=importlib.util.spec_from_file_location('isolation_probability_oracle',ROOT/'scripts/verify-probability-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def verify(device):
 cases=[];bs={n:{'atk':100000+i*10000,'hp':1000000,'def':1000} for i,n in enumerate(v.NAMES)}
 programs=[]
 for values in ((25,50),(50,25)):
  es=[(v.E('shared name','buff','atk_pct',1,event='on_attack',condition=['prob:'+str(p)],max_stack=100),v.NAMES[0]) for p in values]
  programs.append(v.oracle.program(v.oracle.characters(v.NAMES),es))
 script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+[[t,0,7,0,0,-1,0,0] for t in (.1,.2,.3)]+[[.301,2,0,0,-1,0,0,0],[.301,2,106,0,0,1,0,0],[.301,2,106,0,1,2,0,0]]
 gpu=run(device,programs,script,[[31784,50]]*2,[bs]*2,module_backend='native')
 for i,p in enumerate(programs):
  cpu,totals=v.oracle.oracle(p,script,[31784,50],bs);actual=gpu['queries'][i]
  expected=(.75,.5) if i==0 else (.5,.75)
  assert cpu[0][0]==actual[0][0]==1
  assert tuple(cpu[k][0] for k in (1,2))==tuple(actual[k][0] for k in (1,2))==expected
  cases.append({'name':'parallel-alias-source-identity-'+str(i),'passed':True,'expected_atk':1,'cpu_accumulators':list(expected),'gpu_accumulators':[actual[k][0] for k in (1,2)]})
 e=v.E('short state','buff','atk_pct',1,event='on_attack',condition=['prob:30'],duration=.01,max_stack=100)
 p=v.oracle.program(v.oracle.characters(v.NAMES),[(e,v.NAMES[0])]);script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+[[.1*i,0,7,0,0,-1,0,0] for i in range(1,8)]+[[.701,2,0,0,-1,0,0,0],[.701,2,106,0,0,1,0,0]]
 cpu,totals=v.oracle.oracle(p,script,[31784,50],bs);gpu=run(device,[p],script,[[31784,50]],[bs],module_backend='native')['queries'][0]
 assert cpu[0][0]==gpu[0][0]==1 and math.isclose(cpu[1][0],.1,abs_tol=1e-12) and cpu[1][0]==gpu[1][0]
 cases.append({'name':'nonbinary-remainder-survives-active-instance-expiry','passed':True,'cpu_accumulator':cpu[1][0],'gpu_accumulator':gpu[1][0]})
 return cases

if __name__=='__main__':
 d=Cuda()
 try:cases=verify(d)
 finally:d.close()
 files=['scripts/verify-probability-isolation.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','scripts/verify-detail.py']
 report={'passed':True,'backend':'native','cases':cases,'cpu_trace_used_as_gpu_input':False,'scope':'three authored native isolation checks, not catalog or all combinations','source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 (ROOT/'research/detail-probability-isolation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases)}))
