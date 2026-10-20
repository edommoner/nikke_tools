"""Explicit isolated shared-source patch;root compute stays at0ae6a14 bytes."""
import datetime,hashlib,importlib.util,io,json,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def patch(path,old,new):
 s=path.read_text();assert s.count(old)==1,(path,old);path.write_text(s.replace(old,new))
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 base=subprocess.check_output(['git','rev-parse','d181fcd'],cwd=ROOT,text=True).strip();subprocess.run(['git','diff','--exit-code',base,'--','app','scripts','gpu','tests'],cwd=ROOT,check=True)
 folder=ROOT/'research/portable-build'/('mode-entry-candidate-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',base,'gpu','app/portable_combat.py','app/portable_runtime.py','app/portable_runtime_layout.py','app/portable_specs.py'],cwd=ROOT))) as a:a.extractall(folder,filter='data')
 patch(folder/'app/portable_runtime.py',"            if row[7]<0 and row[14]>0:raise UnsupportedPortable('Infinite conditional weapon mode is not ported')\n",'')
 patch(folder/'app/portable_combat.py',"    if row[42]!=0:\n        raise ValueError('Authored mode entry delays require explicit sampling design')", "    if not 0<=row[42]<=180:raise ValueError('Invalid mode entry delay')")
 patch(folder/'app/portable_combat.py',"    words[at+24:at+26]=double_words(row[226]);words[at+26]=int(bool(row[30]));words[at+27]=int(bool(row[231]))", "    words[at+24:at+26]=double_words(row[226]);words[at+26]=int(bool(row[30]));words[at+27]=int(bool(row[231]))\n    # Measured entry delay has an explicit presence flag,including zero.\n    if row[240]:words[at+28:at+32]=[*double_words(row[42]),1,0]")
 patch(folder/'app/portable_specs.py','ABI = 0x50455671','ABI = 0x50455672')
 patch(folder/'app/portable_specs.py',"FIELDS = dict(OWNER=0", "LIMITS['MODE_ENTRY_STATE_BASE']=LIMITS['PROBABILITY_STATE_BASE']+LIMITS['PROBABILITY_STATE_WORDS']\nLIMITS['MODE_ENTRY_STATE_WORDS']=10\nassert LIMITS['MODE_ENTRY_STATE_BASE']+LIMITS['MODE_ENTRY_STATE_WORDS']<=LIMITS['OUTPUT_WORDS']\n\nFIELDS = dict(OWNER=0")
 patch(folder/'gpu/event_runtime.slang','uint64_t modeEnd[5], reentryDelay;', 'uint64_t modeEnd[5], reentryDelay, modeEntryUntil[5];')
 patch(folder/'gpu/event_runtime.slang','    s.modeIndex[who] = -1; s.modeEpoch[who]++; s.appliedEpoch[who] = s.modeEpoch[who]; s.modeShots[who] = 0;', '    s.modeIndex[who] = -1; s.modeEpoch[who]++; s.appliedEpoch[who] = s.modeEpoch[who]; s.modeShots[who] = 0; s.modeEntryUntil[who] = F64_SIGN | ONE;')
 patch(folder/'gpu/event_runtime.slang','    results[output] = s.error; results[output+1] = queries;', '    if((s.quantityMask & 512)!=0) for(uint who=0;who<5;who++) storeNumber(output+P_MODE_ENTRY_STATE_BASE+who*2,s.modeEntryUntil[who]);\n    results[output] = s.error; results[output+1] = queries;')
 patch(folder/'gpu/incoming_runtime.slang','    s.modeIndex[who] = -1; s.modeEpoch[who]++; s.appliedEpoch[who] = s.modeEpoch[who];', '    s.modeIndex[who] = -1; s.modeEpoch[who]++; s.appliedEpoch[who] = s.modeEpoch[who]; s.modeEntryUntil[who] = F64_SIGN | ONE;')
 patch(folder/'gpu/combat_runtime.slang','s.lastFire[who] = f64FromI64(uint64_t(-999)); s.postReloadUntil[who] = F64_SIGN | ONE;', 's.lastFire[who] = f64FromI64(uint64_t(-999)); s.postReloadUntil[who] = F64_SIGN | ONE; s.modeEntryUntil[who] = F64_SIGN | ONE;')
 old='''        w.capacity = w.sentinelMode != 0 ? 999999 : ammoInstantCapacity(s,who,when); s.modeMagazine[who] = w.capacity;
        s.ammo[who] = w.capacity; s.nextShot[who] = when; s.charging[who] = 0; s.reloadUntil[who] = F64_SIGN | ONE; s.postReloadUntil[who] = F64_SIGN | ONE;
    }
    if (index >= 0) w.capacity = s.modeMagazine[who];'''
 new='''        uint64_t entryDelay=index>=0 ? loadNumber(s.inputBase+P_MODE_BASE+uint(index)*P_MODE_WORDS+28) : 0;
        bool hasEntry=index>=0 && commands[s.inputBase+P_MODE_BASE+uint(index)*P_MODE_WORDS+30]!=0;
        s.modeEntryUntil[who]=hasEntry ? f64Add(when,entryDelay) : F64_SIGN | ONE;
        if(!hasEntry)
        {
            w.capacity = w.sentinelMode != 0 ? 999999 : ammoInstantCapacity(s,who,when); s.modeMagazine[who] = w.capacity;
            s.ammo[who] = w.capacity;
        }
        s.nextShot[who] = when; s.charging[who] = 0; s.reloadUntil[who] = F64_SIGN | ONE; s.postReloadUntil[who] = F64_SIGN | ONE;
    }
    if(index>=0 && !f64Less(s.modeEntryUntil[who],0) && !f64Less(when,s.modeEntryUntil[who]))
    {
        s.modeEntryUntil[who]=F64_SIGN | ONE;
        // Native samples the magazine after entry wait. A prior instant may
        // already have captured its capacity;do not invalidate that capture.
        w.capacity=w.sentinelMode!=0 ? 999999 : ammoInstantCapacity(s,who,when);s.modeMagazine[who]=w.capacity;
        s.ammo[who]=w.capacity;if(w.mode!=1) s.nextShot[who]=when;s.charging[who]=0;s.chargeStartedAt[who]=when;
    }
    if (index >= 0) w.capacity = s.modeMagazine[who];'''
 patch(folder/'gpu/combat_runtime.slang',old,new)
 patch(folder/'gpu/combat_runtime.slang','    if (s.error != 0) return;\n    if (s.modeIndex[who] < 0 && f64Less(0,s.reloadUntil[who])', '    if (s.error != 0) return;\n    if(s.modeIndex[who]>=0 && !f64Less(s.modeEntryUntil[who],0)) return;\n    if (s.modeIndex[who] < 0 && f64Less(0,s.reloadUntil[who])')
 patch(folder/'gpu/admission_runtime.slang','        if (d.owner >= 5 || d.triggerCount == 0', '''        uint entry=s.inputBase+P_MODE_BASE+j*P_MODE_WORDS+28;
        uint64_t entryDelay=loadNumber(entry);
        if(d.kind==2)
        {
            if(s.combat==0 || !f64Finite(entryDelay) || f64Less(entryDelay,0) || f64Less(f64FromI64(180),entryDelay) || (commands[entry+2]>1 || commands[entry+2]==0 && !f64Zero(entryDelay)) || commands[entry+3]!=0) { s.error=64;break; }
            if(commands[entry+2]!=0) s.quantityMask|=512;
        }
        else if(commands[entry]!=0 || commands[entry+1]!=0 || commands[entry+2]!=0 || commands[entry+3]!=0) { s.error=64;break; }
        if (d.owner >= 5 || d.triggerCount == 0''')
 patch(folder/'gpu/pending_burst_runtime.slang',"        uint target = s.target; s.target = 0; s.damageExclusion = row+1;", """        uint64_t coefficient=s.pendingCoefficient[index];
        uint reference=s.inputBase+P_REFERENCE_DEFINITION_BASE+row*4;
        if((commands[reference]&3)==1)
        {
            bool present;uint64_t scale=referenceCount(s,d.owner,(commands[reference+1]&511)-1,commands[reference+2]&255,false,present);
            coefficient=f64Mul(coefficient,present ? scale : 0);
            if(!f64Finite(coefficient)) { s.error=16;return; }
            if(f64Zero(coefficient)) { s.pendingAmount[index]=0;continue; }
        }
        uint target = s.target; s.target = 0; s.damageExclusion = row+1;""")
 patch(folder/'gpu/pending_burst_runtime.slang','s.pendingAmount[index] = damageValue(s,d.owner,s.pendingCoefficient[index],when,false,s.coreBonus);','s.pendingAmount[index] = damageValue(s,d.owner,coefficient,when,false,s.coreBonus);')
 patch(folder/'gpu/pending_burst_runtime.slang','for (uint hit = 0; hit < d.damageHits && s.error == 0; hit++)','for (uint hit = 0; hit < d.damageHits && s.error == 0 && !f64Zero(s.pendingAmount[index]); hit++)')
 schema=module('mode_entry_candidate_specs',folder/'app/portable_specs.py');(folder/'gpu/portable_schema.slang').write_text(schema.shader_schema())
 init=module('mode_entry_candidate_init',folder/'app/portable_runtime_layout.py');(folder/'gpu/runtime_init.slang').write_text(init.runtime_initializer())
 wrapper=folder/'mode_entry_candidate_runtime.slang';wrapper.write_text('#include "gpu/event_runtime.slang"\n')
 files={str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for top in ('app','gpu') for p in (folder/top).rglob('*') if p.is_file() and p.suffix in ('.py','.slang')}
 record=dict(base_source_commit=base,candidate_directory=str(folder),shader=wrapper.relative_to(ROOT).as_posix(),source_sha256=files,production_sources_changed=False)
 (ROOT/'research/portable-mode-entry-candidate-preparation.json').write_text(json.dumps(record,indent=2)+'\n');print(str(folder))
if __name__=='__main__':main()
