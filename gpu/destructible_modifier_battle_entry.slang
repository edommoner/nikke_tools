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
#define DF_VALID(s,d,descriptor) (commands[descriptor+3]==0x44425431U&&(d.damageFlags&~(H_NAMED_SKILL|524288U))==0)
#define DF_HAS_SAMPLE(s,row) destructibleActivationHasTargets(s,row)
#define DF_COEFF(s,scratch,output,value) dtStore(scratch+532,value);
#define DF_AMOUNT(s,scratch,output,value) dtStore(scratch+534,value);
#define DF_SELECTION(s,scratch,output,selected,f,d) destructibleBattleCapture(s,scratch,selected,f,d);
#define DF_RECEIPT(s,scratch,output,cursor) (results[scratch+530]+16+(cursor)*8)
#define DF_ATTACK_ID(s,scratch,descriptor) results[scratch+531]
#define DF_COMPLETE(s,scratch) if(results[scratch+531]!=0) results[results[scratch+530]+10]=1;
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
    if(normal||optimal||physical||!f64Equal(coreBonus,s.coreBonus)||!f64Equal(charge,ONE)||row!=commands[DF_DESCRIPTOR(s)]||skillHPBasisMode(s,row)!=0||(flags&~(H_NAMED_SKILL|524288U))!=0) { s.error=64;return 0; }
    uint64_t factor5,projectile,shield;
    return destructibleModifierDamage(s,s.inputBase+109568,who,2,coefficient,when,factor5,projectile,shield);
}
#define damageValue modifierFrameDamage
#include "destructible_frame_runtime.slang"
#undef damageValue
bool validBattleModifierAxes(inout Runtime s)
{
    uint descriptor=s.inputBase+109536;
    if(commands[descriptor]!=0x444d4231U||skillHPBasisMode(s,commands[DF_DESCRIPTOR(s)])!=0) return false;
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

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*109824,output=id.x*1048576; WORLD_TEAM_INPUT(input,output)
    for(uint i=786432;i<1048576;i++) results[output+i]=0;
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready) return;
    if(!initializeDestructibleBattle(runtimeStates[id.x])||!validBattleModifierAxes(runtimeStates[id.x])) { results[output]=64;return; }
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    writePortableProgram(runtimeStates[id.x],input,output,queries);
}
