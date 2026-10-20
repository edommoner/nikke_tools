"""80 actual-firing inputs for either GPU;independent native study runs after readback."""
import argparse,array,datetime,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import dispatch_programs,pack_programs,decode
from portable_specs import LIMITS as L

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=['metal','cuda'],default='metal');args=parser.parse_args()
 spec=importlib.util.spec_from_file_location('physical_hp_core',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 cases=[]
 for owner in range(5):
  for target in ('self','all_allies'):
   shooter=owner if target=='self' else (owner+1)%5
   for weapon_type in ('AR','SG','SR','RL'):
    for duration in (-1,1):
     charge=weapon_type in ('SR','RL');w=dict(enabled=True,mode='charge' if charge else 'auto',base_weapon_type=weapon_type,coefficient=100,capacity=1000,interval=1,charge=.5,full_charge_mult=300 if charge else 100,pellets=10 if weapon_type=='SG' else 1,gauge=0)
     weapons=[dict(enabled=False) for _ in range(5)];weapons[shooter]=w
     effect=dict(name='hp-attack',source='스킬1',type='buff',stat='atk_from_hp_pct',fixed_value=10,target=target,duration=duration,trigger=dict(timing=['battle_start'],condition=[]))
     cases.append(dict(name=f'hp-attack-physical-{owner}-{target}-{weapon_type}-{duration}',effects=[effect],owners=[owner],environment=dict(allies=[dict(base_hp=10000+2000*i,hp=10000+2000*i,base_defense=0) for i in range(5)]),combat=dict(weapons=weapons,targets=[dict(hp=1e12,defense=0)]),script=[[2,24,0,0,0,-1,0,0],[2,2,0,0,0,0,0,0]],expected_queries=[{}]))
 programs=[v.compile_case(c) for c in cases]
 folder=ROOT/'research/portable-build'/('hp-attack-physical-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 (folder/'input.bin').write_bytes(pack_programs(programs));raw,evidence=dispatch_programs(programs,backend=args.backend)
 (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 # Inputs above contain only authored constants and grid horizon,never native hit times.
 subprocess.run([sys.executable,'research/characterize-hp-attack-physical.py'],cwd=ROOT,check=True)
 native_path=ROOT/'research/portable-hp-attack-physical-native.json';native=json.loads(native_path.read_text());assert native['passed'] and len(native['cases'])==len(cases)
 words=array.array('I');words.frombytes(raw)
 if sys.byteorder!='little':words.byteswap()
 rows=[]
 for i,(c,n) in enumerate(zip(cases,native['cases'])):
  actual=decode(words[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1]);expected=[0]*5;expected[n['shooter']]=sum(h['damage'] for h in n['hits']);got=actual['queries'][0]['damage'];passed=actual['status']==0 and got==expected
  rows.append(dict(name=c['name'],passed=passed,actual=actual,expected_damage=expected,native=n))
 paths=['research/verify-hp-attack-physical.py','research/characterize-hp-attack-physical.py','scripts/verify-portable-combat.py','scripts/portable_weapon_oracle.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
 result=dict(passed=all(r['passed'] for r in rows),cases=rows,captured=str(folder),**evidence,cpu_trace_used_as_gpu_input=False,native_report_sha256=hashlib.sha256(native_path.read_bytes()).hexdigest(),validation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},scope='80 AR/SG/SR/RL actual-firing damage totals,5 owners,self/other recipient,finite/infinite. Separate from fixed3539 core;no all-character or full-state certification.')
 (ROOT/f'research/portable-hp-attack-physical-{args.backend}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 assert result['passed'],[(r['name'],r['actual']['status'],r['actual']['queries'][0]['damage'],r['expected_damage']) for r in rows if not r['passed']]
 print('80 HP-derived actual-firing damage cases passed',args.backend)
if __name__=='__main__':main()
