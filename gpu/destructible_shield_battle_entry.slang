// The ordinary battle loop owns the single WorldSchedule. Only typed storage
// and bounded receipt/scratch banks are added after its unchanged output prefix.
#define PORTABLE_RESIDENT_RUNTIME
#define PORTABLE_DESTRUCTIBLE_FRAME
#define PORTABLE_DESTRUCTIBLE_BATTLE
#define DF_DESCRIPTOR(s) ((s).inputBase+109520)
#define DF_EXTRA(s) ((s).inputBase+104400)
#define DF_BASE(output) ((output)+787456)
#define DF_HEADER(output) ((output)+789248)
#define DF_SCHEDULE(s,w,extra,output) WorldSchedule w=frameSchedule(s);
#define DF_SCRATCH(output,depth) ((output)+940000+uint(depth)*544)
#ifndef DF_VALID
#define DF_VALID(s,d,descriptor) (commands[descriptor+3]==0x44425431U&&(d.damageFlags&~(H_NAMED_SKILL|524288U))==0)
#endif
#define DF_HAS_SAMPLE(s,row) destructibleActivationHasTargets(s,row)
#define DF_COEFF(s,scratch,output,value) dtStore(scratch+532,value);
#define DF_AMOUNT(s,scratch,output,value) dtStore(scratch+534,value);
#define DF_SELECTION(s,scratch,output,selected,f,d) destructibleBattleCapture(s,scratch,selected,f,d);
#define DF_RECEIPT(s,scratch,output,cursor) (results[scratch+530]+16+(cursor)*8)
#define DF_ATTACK_ID(s,scratch,descriptor) results[scratch+531]
#define DF_COMPLETE(s,scratch) if(results[scratch+531]!=0) results[results[scratch+530]+10]=1;
#define DF_ROW_ENABLED(s,row) ((row)<(s).count&&commands[(s).inputBase+109824+(row)]!=0)
#define DF_BODY_FALLBACK(s,row) (commands[(s).inputBase+109824+(row)]>=3)
#define DF_MATCH(s,row,at,selected) (results[at+3]!=0&&(DF_BODY_FALLBACK(s,row)?((selected)==0&&(results[at]==3||(commands[(s).inputBase+109824+(row)]==4&&results[at]==4))&&results[at+10]==commands[(s).inputBase+110081]&&results[at+11]==commands[(s).inputBase+110082]&&results[at+12]==commands[(s).inputBase+110083]):results[at]==2))
#define portableEvents unusedNormalBattleEntry
#include "world_projectile_chain_entry.slang"
#undef portableEvents
#include "destructible_target_core.slang"
#include "destructible_world_runtime.slang"
#include "destructible_battle_runtime.slang"
#include "destructible_modifier_runtime.slang"
// The plain DBT1 skill already excludes physical/category/HP-basis variants.
// Named coefficient/completion bits do not add a scalar factor of their own.
uint64_t modifierFrameDamage(inout Runtime s,uint who,uint64_t coefficient,uint64_t when,bool normal,uint64_t coreBonus,uint flags,uint64_t charge,bool optimal,bool physical,uint row)
{
#ifdef PORTABLE_DESTRUCTIBLE_ROSTER_SKILL
    if(rosterShieldSkillsEnabled(s)) return rosterShieldSkillDamage(s,who,coefficient,when,normal,coreBonus,flags,charge,optimal,physical,row);
#endif
    if(normal||optimal||physical||!f64Equal(coreBonus,s.coreBonus)||!f64Equal(charge,ONE)||!DF_ROW_ENABLED(s,row)||skillHPBasisMode(s,row)!=0||(flags&~(H_NAMED_SKILL|524288U))!=0) { s.error=64;return 0; }
    uint64_t factor5,projectile,shield;
    uint kind=commands[s.inputBase+109824+row];
    if(kind==4)
    {
        uint count=commands[DF_EXTRA(s)+2320],base=DF_BASE(s.resourceOutput);bool found=false;
        for(uint slot=0;slot<count;slot++)
        {
            uint at=dtAt(base,slot);
            if(DF_MATCH(s,row,at,0)) { kind=results[at]==4?0:3;found=true;break; }
        }
        if(!found) { s.error=64;return 0; }
    }
    return destructibleModifierDamage(s,s.inputBase+109568,who,kind,coefficient,when,factor5,projectile,shield);
}
#define damageValue modifierFrameDamage
#include "destructible_frame_runtime.slang"
#undef damageValue
bool validBattleModifierAxes(inout Runtime s)
{
    uint descriptor=s.inputBase+109536;
    uint source=commands[DF_DESCRIPTOR(s)];
    if(commands[descriptor]!=0x444d4231U||(source<s.count&&skillHPBasisMode(s,source)!=0)) return false;
    for(uint i=1;i<32;i++) if(commands[descriptor+i]!=0) return false;
    for(uint row=0;row<256;row++)
    {
        uint axis=commands[descriptor+32+row];if(axis!=0&&axis!=2&&axis!=3) return false;
        if(row>=s.count) { if(axis!=0) return false;continue; }
        if(axis!=0)
        {
            Definition d=readDefinition(s.inputBase,row);
            if(d.kind!=4||d.stat!=0||d.enemyBuff!=0||d.healthScaling!=0||d.quantityFlags!=0||d.alliedFlags!=0||d.damageFlags!=0||!f64Finite(d.value)) return false;
        }
    }
    return true;
}

bool validShieldBattleRoutes(inout Runtime s)
{
    uint base=s.inputBase+110080;
    bool weapons=false;
#ifdef PORTABLE_DESTRUCTIBLE_WEAPON
    weapons=destructibleWeaponEnabled(s);
    if(weapons&&!validDestructibleWeapons(s)) return false;
#endif
    bool hitShields=commands[base]==0x48534932U;
    if(weapons) hitShields=commands[base+4]==1;
    if((!weapons&&!hitShields&&commands[base]!=0x48534931U)||commands[base+1]!=0||commands[base+2]!=0||commands[base+3]!=1||commands[base+4]!=uint(hitShields)) return false;
#ifdef PORTABLE_DESTRUCTIBLE_BODY_LIFESTEAL
    bool bodyLifesteal=commands[base]==0x48534935U;
#ifdef PORTABLE_DESTRUCTIBLE_BODY_ACCUM
    bool bodyAccum=commands[base]==0x48534936U;
    bodyLifesteal=bodyLifesteal||bodyAccum;
    if(bodyAccum&&commands[base+7]!=1) return false;
#endif
    if(bodyLifesteal&&(!weapons||commands[base+6]!=1)) return false;
#ifdef PORTABLE_DESTRUCTIBLE_BODY_ACCUM
    for(uint i=bodyAccum?8U:bodyLifesteal?7U:weapons?6U:5U;i<32;i++) if(commands[base+i]!=0) return false;
#else
    for(uint i=bodyLifesteal?7U:weapons?6U:5U;i<32;i++) if(commands[base+i]!=0) return false;
#endif
#else
    for(uint i=weapons?6U:5U;i<32;i++) if(commands[base+i]!=0) return false;
#endif
    if(!DF_ROW_ENABLED(s,commands[DF_DESCRIPTOR(s)])&&!(weapons&&commands[DF_DESCRIPTOR(s)]==0xffffffffU)) return false;
    for(uint row=0;row<256;row++)
    {
        uint route=commands[s.inputBase+109824+row];
        if(route==0) continue;
        if((route!=2&&route!=3&&!(hitShields&&route==4))||row>=s.count||skillHPBasisMode(s,row)!=0) return false;
        Definition d=readDefinition(s.inputBase,row);
#ifdef PORTABLE_DESTRUCTIBLE_ROSTER_SKILL
        if(rosterShieldSkillsEnabled(s))
        { if((route!=3&&route!=4)||!rosterShieldSkillDefinition(s,d)) return false;continue; }
#endif
        if(d.kind!=3||d.stat!=0||d.damageRoute!=1||d.damageCount!=1||d.damageHits!=1||d.damagePending!=0||d.damageNormal!=0||(d.damageFlags&~(H_NAMED_SKILL|524288U))!=0||d.healthScaling!=0||d.quantityFlags!=0||!dtQuantity(d.value)) return false;
    }
    return true;
}

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*110112,output=id.x*1048576; WORLD_TEAM_INPUT(input,output)
    for(uint i=786432;i<1048576;i++) results[output+i]=0;
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready) return;
    if(!initializeDestructibleBattle(runtimeStates[id.x])||!validBattleModifierAxes(runtimeStates[id.x])||!validShieldBattleRoutes(runtimeStates[id.x])) { results[output]=64;return; }
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    writePortableProgram(runtimeStates[id.x],input,output,queries);
}
