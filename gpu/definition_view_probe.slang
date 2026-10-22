#define portableEvents portableBattleUnused
#include "world_entry_reload_resident_entry.slang"
#undef portableEvents

[noinline]
void probeDefinitionView(inout Runtime s,uint input,uint output)
{
    initializeRuntime(s);
    Definition first=readDefinition(input,0);
    Definition before=first;
    first.damageRoute=commands[input];first.damageHits=commands[input+1];
    Definition after=first;
    first.damageRoute=commands[input+2];first.damageHits=commands[input+3];
    Definition original=readDefinition(input,0),second=readDefinition(input,1);
    s.inputBase=input;s.carrierDefinition[0]=0;
    Definition snapshot=residentDefinition(s,0);
    s.carrierDefinition[0]=1;s.inputBase=input+P_DEFINITION_WORDS;
    results[output]=0;
    results[output+1]=before.owner;results[output+2]=uint(before.budget);storeNumber(output+3,before.value);
    results[output+5]=before.damageRoute;results[output+6]=before.damageHits;
    results[output+7]=first.damageRoute;results[output+8]=first.damageHits;
    results[output+9]=after.damageRoute;results[output+10]=after.damageHits;
    results[output+11]=original.damageRoute;results[output+12]=original.damageHits;
    results[output+13]=snapshot.owner;
    s.inputBase=input;Definition next=residentDefinition(s,0);
    results[output+14]=next.owner;results[output+15]=second.owner;results[output+16]=uint(second.budget);storeNumber(output+17,second.value);
}

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    probeDefinitionView(runtimeStates[id.x],1+id.x*P_INPUT_WORDS,id.x*P_OUTPUT_WORDS);
}
