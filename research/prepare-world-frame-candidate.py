"""Create one common-source frame-coupling candidate; canonical files untouched."""
import datetime,hashlib,json,shutil,subprocess,tarfile,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def prepare():
 source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 folder=ROOT/'research/portable-build'/('world-frame-candidate-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 archive=subprocess.check_output(['git','archive',source,'gpu'],cwd=ROOT)
 with tarfile.open(fileobj=io.BytesIO(archive)) as t:t.extractall(folder,filter='data')
 for name in ['world_frame_addresses.slang','world_frame_runtime.slang']:shutil.copyfile(ROOT/'gpu'/name,folder/'gpu'/name)
 patches=[]
 def replace(file,old,new,count=1):
  p=folder/'gpu'/file;s=p.read_text();assert s.count(old)==count,(file,old,s.count(old),count);p.write_text(s.replace(old,new));patches.append(dict(file=file,old=old,new=new,count=count))
 replace('portable_schema.slang','PORTABLE_ABI = 1346721395U','PORTABLE_ABI = 1346721396U')
 replace('portable_schema.slang','P_INPUT_WORDS = 86016U','P_INPUT_WORDS = 88848U')
 replace('portable_schema.slang','P_OUTPUT_WORDS = 159744U','P_OUTPUT_WORDS = 225280U')
 replace('event_runtime.slang','#include "protection_runtime.slang"','#include "world_frame_addresses.slang"\n#include "protection_runtime.slang"')
 replace('event_runtime.slang','#include "combat_runtime.slang"','#include "world_frame_runtime.slang"\n#include "combat_runtime.slang"')
 replace('event_runtime.slang','uint at = s.inputBase+P_COMMAND_BASE+uint(f.argument)*8;','uint at = incomingCommandAddress(s,uint(f.argument));')
 replace('event_runtime.slang','uint input = s.inputBase+P_INCOMING_BASE+uint(f.argument)*P_INCOMING_WORDS;','uint input = incomingDamageAddress(s,uint(f.argument));')
 replace('event_runtime.slang','results[s.resourceOutput+P_ENEMY_TARGET_QUERY_BASE+uint(f.argument)*8+1]','results[enemyQueryAddress(s,uint(f.argument))+1]')
 replace('event_runtime.slang','frames[depth].repeatRow=f.cursor==0 ? P_PROTECTION_HIT_BASE+(uint(f.argument)*5+f.owner)*16 : P_SPLIT_HIT_BASE+(uint(f.argument)*20+f.owner*4+f.cursor-1)*16;','uint legacy=f.cursor==0 ? P_PROTECTION_HIT_BASE+(uint(f.argument)*5+f.owner)*16 : P_SPLIT_HIT_BASE+(uint(f.argument)*20+f.owner*4+f.cursor-1)*16;\n                frames[depth].repeatRow=incomingRecordAddress(s,uint(f.argument),f.owner,member,member==f.owner,legacy);')
 replace('event_runtime.slang','uint record=P_PROTECTION_HIT_BASE+(uint(f.argument)*5+who)*16;frames[depth].repeatRow=record;','uint record=incomingRecordAddress(s,uint(f.argument),who,who,true,P_PROTECTION_HIT_BASE+(uint(f.argument)*5+who)*16);frames[depth].repeatRow=record;')
 replace('event_runtime.slang','if(!validEnemyTargeting(s))','if(!initializeWorldFrame(s)) { results[output]=64;return; }\n    if(!validEnemyTargeting(s))')
 replace('event_runtime.slang','    writeDamageAccounting(s,output+P_DAMAGE_ACCOUNTING_STATE_BASE,true);','    worldFrameFinish(s);\n    writeDamageAccounting(s,output+P_DAMAGE_ACCOUNTING_STATE_BASE,true);')
 replace('protection_runtime.slang','uint command=s.inputBase+P_COMMAND_BASE+uint(f.argument)*8;','uint command=incomingCommandAddress(s,uint(f.argument));')
 replace('protection_runtime.slang','results[hit+2]=1;','results[hit+2]=scheduledArgument(uint(f.argument))?results[hit+2]|1U:1U;')
 replace('enemy_target_runtime.slang','uint spec=s.inputBase+P_ENEMY_TARGET_COMMAND_BASE+step*4,rule=','uint spec=enemyRuleAddress(s,step),rule=')
 replace('enemy_target_runtime.slang','uint output=s.resourceOutput+P_ENEMY_TARGET_QUERY_BASE+step*8;','uint output=enemyQueryAddress(s,step);')
 replace('enemy_target_runtime.slang','return (enabled!=0)==(features!=0);','return (enabled!=0)==(features!=0 || worldFrameEnabled(s));')
 replace('combat_runtime.slang','{ s.combatStarted = 1; teamNotify(s,0,0,output); initializeMagazines(s,0); }','{ worldFrameBegin(s,0);if(s.error!=0) return;s.combatStarted = 1; teamNotify(s,0,0,output); initializeMagazines(s,0); }')
 replace('combat_runtime.slang','        tick(s,when,output);','        worldFrameBegin(s,when);if(s.error!=0) return;\n        tick(s,when,output);\n        if(s.error==0) worldFrameDeliver(s,when,output);')
 wrapper=folder/'world_frame_candidate_runtime.slang';wrapper.write_text('#include "gpu/event_runtime.slang"\n')
 record=dict(base_source_commit=source,created=str(folder),source=wrapper.relative_to(ROOT).as_posix(),patches=patches,canonical_changed=False,input_words=88848,output_words=225280,abi='0x50455674',added_common_modules={n:hashlib.sha256((ROOT/'gpu'/n).read_bytes()).hexdigest() for n in ['world_frame_addresses.slang','world_frame_runtime.slang']})
 (folder/'candidate-preparation.json').write_text(json.dumps(record,indent=2)+'\n')
 return record
if __name__=='__main__':print(json.dumps(prepare(),indent=2))
