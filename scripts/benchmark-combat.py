"""Repeatable local GPU combat timing; synthetic demo data only, no network.
This is not a speedup comparison with the full CPU engine (different fidelity).
"""
import argparse,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'app'))
import engine_worker as adapter
from gpu_selector import Cuda
from gpu_combat import Combat,prefilter

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidates',type=int,default=800);args=ap.parse_args()
 if not 1<=args.candidates<=2048:ap.error('candidates must be 1..2048')
 demo=adapter.demo();evaluation={'profile':demo['profile'],'duration':180,'level':400,'enemy':{'def':10000,'code':'작열','core_px':50,'distance':30}}
 d=Cuda()
 try:
  combat=Combat(d)
  # Warm up driver JIT and code residency separately from measured combat.
  prefilter({'evaluation':{**evaluation,'duration':1},'squads':[demo['squad']]},d,combat)
  result=prefilter({'evaluation':evaluation,'squads':[demo['squad']]*args.candidates},d,combat)
  result.pop('scores');result['issue_count']=len(result.pop('issues'))
  result['workload']='same synthetic demo squad repeated; 180 seconds at 60 fps'
  print(json.dumps(result,ensure_ascii=True,indent=2))
 finally:d.close()
if __name__=='__main__':main()
