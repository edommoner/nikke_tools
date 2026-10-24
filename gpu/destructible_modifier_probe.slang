#define PORTABLE_RESIDENT_RUNTIME
#define portableEvents unusedOrdinaryEventEntry
#include "event_runtime.slang"
#undef portableEvents
#include "destructible_modifier_runtime.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*86304,output=id.x*P_OUTPUT_WORDS,descriptor=input+86016;
    for(uint i=0;i<P_OUTPUT_WORDS;i++) results[output+i]=0;
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready) return;
    uint kind=commands[descriptor+1],who=commands[descriptor+2];
    uint64_t when=loadNumber(descriptor+4),coefficient=loadNumber(descriptor+6);
    bool valid=commands[descriptor]==0x444d5131U&&(kind==0||kind==2||kind==3)&&who<5&&commands[descriptor+3]==0&&f64Finite(when)&&!f64Less(when,0)&&f64Finite(coefficient)&&!f64Less(coefficient,0);
    for(uint i=8;i<32;i++) if(commands[descriptor+i]!=0) valid=false;
    for(uint row=0;row<256;row++)
    {
        uint axis=commands[descriptor+32+row];
        if(axis!=0&&axis!=2&&axis!=3) valid=false;
        if(row>=runtimeStates[id.x].count) { if(axis!=0) valid=false;continue; }
        if(axis!=0)
        {
            Definition d=readDefinition(input,row);
            if(d.kind!=4||d.stat!=0||d.enemyBuff!=0||d.healthScaling!=0||d.quantityFlags!=0||d.alliedFlags!=0||d.damageFlags!=0) valid=false;
        }
    }
    if(!valid) { results[output]=64;return; }
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    if(runtimeStates[id.x].error==0) { beginLazyRoot(runtimeStates[id.x],when);tick(runtimeStates[id.x],when,output); }
    uint64_t factor5,projectile,shield;
    uint64_t amount=destructibleModifierDamage(runtimeStates[id.x],descriptor+32,who,kind,coefficient,when,factor5,projectile,shield);
    uint at=output+P_OUTPUT_WORDS-32;results[at]=0x444d5131U;results[at+1]=kind;
    storeNumber(at+2,amount);storeNumber(at+4,factor5);storeNumber(at+6,projectile);storeNumber(at+8,shield);
    results[output]=runtimeStates[id.x].error;
}
