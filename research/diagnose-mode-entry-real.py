"""New short-horizon inputs and post-battle stat probes for the retained real mismatch."""
import array,copy,datetime,hashlib,importlib.util,json,shutil,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import portable_runtime as runtime,portable_combat
from portable_specs import LIMITS as L

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 prep=json.loads((ROOT/'research/portable-mode-entry-candidate-preparation.json').read_text());base=Path(prep['candidate_directory']);folder=ROOT/'research/portable-build'/('mode-entry-diagnosis-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();shutil.copytree(base/'gpu',folder/'gpu')
 keys=['atk_pct','atk_flat','crit_rate','crit_dmg','charge_dmg_pct','charge_dmg_mag_pct','pierce_enabled','normal_atk_dmg_pct','atk_dmg_pct','received_dmg_pct','element_bonus','enemy_def_down_pct']
 shader=folder/'gpu/event_runtime.slang';s=shader.read_text();pos=s.rfind('\n}');code='\n    uint64_t diagnostic[64]; collectStats(s,0,loadNumber(input+P_COMMAND_BASE+(commands[input+2]-1)*8+1),diagnostic);\n'
 for i,key in enumerate(keys):code+=f'    storeNumber(output+P_MODE_ENTRY_STATE_BASE+10+{i*2},diagnostic[S_{key}]);\n'
 s=s[:pos]+code+s[pos:];shader.write_text(s);wrapper=folder/'mode_entry_diagnostic_runtime.slang';wrapper.write_text('#include "gpu/event_runtime.slang"\n')
 adapter=module('diagnostic_entry_adapter',base/'app/portable_runtime.py');combat=module('diagnostic_entry_combat',base/'app/portable_combat.py');roster=module('diagnostic_real_roster',ROOT/'scripts/verify-portable-roster-battles.py');reference=roster.reference
 from portable_roster_input import compile_static_battle
 from detail_coverage import body_for
 old_compile=runtime.compile_program;old_pack=portable_combat.pack_mode;programs=[];plans=[]
 def compile(*a,**kw):w,m=adapter.compile_program(*a,**kw);w[0]=0x50455672;return w,m
 runtime.compile_program=compile;portable_combat.pack_mode=combat.pack_mode
 try:
  for t in (1,3,5,7,10,20):
   body={**body_for(roster.roster_for('라플라스 : 얼티밋 히어로'),duration=t),'burst_gauge_mode':'accumulate'};p=roster.adapter.evaluate({**body,'_portable_static_inputs':True});programs.append(compile_static_battle(p,trace='burst'));plans.append((body,p,t))
 finally:runtime.compile_program=old_compile;portable_combat.pack_mode=old_pack
 (folder/'input.bin').write_bytes(runtime.pack_programs(programs));one,many=runtime.execute,runtime.execute_batches
 def single(source,*a,**kw):return one(wrapper.relative_to(ROOT).as_posix(),*a,**kw)
 def batch(source,*a,**kw):return many(wrapper.relative_to(ROOT).as_posix(),*a,**kw)
 runtime.execute=single;runtime.execute_batches=batch
 try:raw,evidence=runtime.dispatch_programs(programs,backend='metal')
 finally:runtime.execute=one;runtime.execute_batches=many
 (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 out=array.array('I');out.frombytes(raw)
 if sys.byteorder!='little':out.byteswap()
 rows=[]
 from calculator import timeline
 for i,(body,p,t) in enumerate(plans):
  managers=[];Original=timeline.BurstController
  class Recording(Original):
   def tick(self,now,bm,state):events=super().tick(now,bm,state);managers.append((bm,now));return events
  with patch.object(timeline,'BurstController',Recording):cpu=reference.native_reference(copy.deepcopy(body))
  bm,now=managers[-1];buffs=bm.get_buffs(body['squad'][0],'__enemy__',now)
  gpu=runtime.decode(out[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1]);diff=reference.compare_native_result(gpu,p,cpu,program=programs[i]);values=struct.unpack_from('<'+str(len(keys))+'d',raw,(i*L['OUTPUT_WORDS']+159232+10)*4)
  aliases={'received_dmg_pct':'received_dmg','element_bonus':'element_bonus'}
  native={k:buffs.get(aliases.get(k,k),0) for k in keys};actual=dict(zip(keys,values));rows.append(dict(duration=t,differences=diff,gpu_stats=actual,native_stats=native,gpu=gpu,native=cpu))
 result=dict(diagnostic_complete=True,production_adopted=False,scope='New short real inputs;post-battle diagnostic stats only. Not a passing certification.',captured=str(folder),cases=rows,**evidence,cpu_trace_used_as_gpu_input=False)
 (ROOT/'research/portable-mode-entry-real-diagnosis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print([(r['duration'],len(r['differences'])) for r in rows])
if __name__=='__main__':main()
