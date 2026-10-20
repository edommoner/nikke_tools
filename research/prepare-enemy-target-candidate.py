"""Isolated target-selection/ordered damage connection; root production files unchanged."""
import datetime,hashlib,io,json,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'app'))
from portable_enemy_target_specs import ABI,META_BASE,COMMAND_BASE,RNG_BASE,RNG_WORDS,QUERY_BASE
BASE='89c19e3'
def patch(p,a,b):
 s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));p.write_text(s.replace(a,b))
def main():
 source=subprocess.check_output(['git','rev-parse',BASE],cwd=R,text=True).strip()
 subprocess.run(['git','diff','--exit-code',source,'--','app','gpu','scripts','tests'],cwd=R,check=True)
 folder=R/'research/portable-build'/('enemy-target-candidate-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',source,'gpu'],cwd=R))) as a:a.extractall(folder,filter='data')
 for name in ('portable_mt19937.slang','enemy_target_runtime.slang'):(folder/'gpu'/name).write_bytes((R/'gpu'/name).read_bytes())
 schema=folder/'gpu/portable_schema.slang';patch(schema,'static const uint PORTABLE_ABI = 1346721394U;',f'static const uint PORTABLE_ABI = {ABI}U;')
 with schema.open('a') as f:
  for name,value in dict(P_ENEMY_TARGET_META_BASE=META_BASE,P_ENEMY_TARGET_COMMAND_BASE=COMMAND_BASE,P_ENEMY_RNG_BASE=RNG_BASE,P_ENEMY_TARGET_QUERY_BASE=QUERY_BASE,S_taunt=66,S_stealth=65).items():f.write(f'static const uint {name} = {value}U;\n')
 event=folder/'gpu/event_runtime.slang'
 patch(event,'#include "admission_runtime.slang"','#include "admission_runtime.slang"\n#include "portable_mt19937.slang"\n#include "enemy_target_runtime.slang"')
 patch(event,'    if(!validProtection(s))','    if(!validEnemyTargeting(s)) { results[output]=64;return; }\n    if(!validProtection(s))')
 patch(event,'    initializeHPWatches(s);','    if(commands[input+P_ENEMY_TARGET_META_BASE]!=0) mtSeed(output+P_ENEMY_RNG_BASE,uint64_t(commands[input+P_ENEMY_TARGET_META_BASE+1])|(uint64_t(commands[input+P_ENEMY_TARGET_META_BASE+2])<<32));\n    initializeHPWatches(s);')
 # Existing layered landing/split/notification engine is reused after victim selection.
 patch(event,'        else if(op==31)','''        else if(op==32)
        {
            uint raw=s.inputBase+P_INCOMING_BASE+step*P_INCOMING_WORDS;
            if(commands[at+3]>1 || commands[at+4]!=0 || commands[at+5]!=0 || commands[at+6]!=0 || commands[at+7]!=0 || !f64Finite(loadNumber(raw)) || !f64Finite(loadNumber(raw+2)) || f64Less(loadNumber(raw),0) || f64Less(loadNumber(raw+2),0) || f64Less((uint64_t(0x46293e59)<<32)|uint64_t(0x39a08cea),loadNumber(raw)) || f64Less(f64FromI64(1000000),loadNumber(raw+2))) { s.error=64;break; }
            chooseEnemyVictims(s,step,when);
            if(s.error==0) dispatch(s,8,0,0,int(step),when,output);
        }
        else if(op==31)''')
 old='''                uint who = frames[depth].cursor, mask = commands[at+5] & ~s.downMask;
                while (who < 5 && (mask & (1U << who)) == 0) who++;
                if (who == 5) { depth--; continue; }
                frames[depth].cursor = who+1; frames[depth].owner = who;'''
 new='''                uint who;
                if(commands[at]==32)
                {
                    uint order=results[s.resourceOutput+P_ENEMY_TARGET_QUERY_BASE+uint(f.argument)*8+1],cursor=frames[depth].cursor,encoded=0;
                    while(cursor<5)
                    {
                        encoded=(order>>(3*cursor++))&7;
                        if(encoded==0 || (s.downMask&(1U<<(encoded-1)))==0) break;
                    }
                    if(encoded==0 || (s.downMask&(1U<<(encoded-1)))!=0) { depth--;continue; }
                    who=encoded-1;frames[depth].cursor=cursor;
                }
                else
                {
                    uint mask=commands[at+5] & ~s.downMask;who=frames[depth].cursor;
                    while(who<5 && (mask&(1U<<who))==0) who++;
                    if(who==5) { depth--;continue; }
                    frames[depth].cursor=who+1;
                }
                frames[depth].owner=who;'''
 patch(event,old,new)
 text=event.read_text();assert text.count('commands[at]==31')==3;text=text.replace('commands[at]==31','(commands[at]==31 || commands[at]==32)');event.write_text(text)
 admission=folder/'gpu/admission_runtime.slang'
 patch(admission,'d.stat == S_received_dmg_pct || d.kind==4','d.stat == S_received_dmg_pct || d.stat == S_taunt || d.kind==4')
 protection=folder/'gpu/protection_runtime.slang'
 patch(protection,'bool covered=(commands[command+4]&(1U<<f.owner))!=0 &&', 'bool automaticCover=commands[command]==32 ? f64Less(0,s.reloadUntil[f.owner]) : (commands[command+4]&(1U<<f.owner))!=0;\n        bool covered=automaticCover &&')
 enemy=folder/'gpu/enemy_buff_runtime.slang'
 patch(enemy,'        uint64_t value = scalarValue(s,row,who);','        if(d.stat==S_taunt) continue;\n        uint64_t value = scalarValue(s,row,who);')
 wrapper=folder/'enemy_target_candidate_runtime.slang';wrapper.write_text('#include "gpu/event_runtime.slang"\n')
 files={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*.slang')}
 result=dict(base_source_commit=source,candidate_directory=str(folder),shader=wrapper.relative_to(R).as_posix(),abi=hex(ABI),input_words=86016,output_words=159744,source_sha256=files,production_adopted=False,gpu_execution_performed=False,scope='Candidate source only;ordered enemy victims feed existing layered incoming engine. Marker admission remains disabled in root production.')
 (R/'research/portable-enemy-target-candidate-preparation.json').write_text(json.dumps(result,indent=2)+'\n');print(result['shader'])
if __name__=='__main__':main()
