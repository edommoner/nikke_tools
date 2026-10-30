#ifdef PORTABLE_FULL_BURST_LANDING
#define FULL_BURST_PENDING_INVALID(s,d) fullBurstPendingInvalid(s,d)
#else
#define FULL_BURST_PENDING_INVALID(s,d) (d.damagePending > 1 || d.damagePending == 0 && d.pendingHits != 0 || d.damagePending != 0 && (s.combat == 0 || d.damageHits != 1 || d.damageFlags != 0 || d.damageNormal != 0 || d.pendingHits == 0 || d.pendingHits > 256))
#endif
// The same GPU admission checks and observer masks, isolated from execution.
// No checks are moved to the CPU or omitted for either backend.
#ifdef PORTABLE_PRODUCT_OUTLINED_HELPERS
[noinline]
bool admitDefinitionTypes(inout Runtime s,uint input,uint j,inout Definition d,inout uint elementDefinitions)
{
    uint world=input+P_WORLD_META_BASE,codeNames=commands[world+1],refs=input+P_BURST_REFERENCE_BASE;
    bool completed=false;
    do
    {
#include "admission_definition_types.slang"
        completed=true;
    } while(false);
    return completed;
}
[noinline]
bool admitDefinitionTriggers(inout Runtime s,uint input,uint j,inout Definition d,inout uint elementDefinitions)
{
    uint world=input+P_WORLD_META_BASE,codeNames=commands[world+1],refs=input+P_BURST_REFERENCE_BASE;
    bool completed=false;
    do
    {
#include "admission_definition_triggers.slang"
        completed=true;
    } while(false);
    return completed;
}
[noinline]
bool admitDefinitionRoutes(inout Runtime s,uint input,uint j,inout Definition d,inout uint elementDefinitions)
{
    uint world=input+P_WORLD_META_BASE,codeNames=commands[world+1],refs=input+P_BURST_REFERENCE_BASE;
    bool completed=false;
    do
    {
#include "admission_definition_routes.slang"
        completed=true;
    } while(false);
    return completed;
}
[noinline]
bool admitDefinitionMasks(inout Runtime s,uint input,uint j,inout Definition d,inout uint elementDefinitions)
{
    uint world=input+P_WORLD_META_BASE,codeNames=commands[world+1],refs=input+P_BURST_REFERENCE_BASE;
    bool completed=false;
    do
    {
#include "admission_definition_masks.slang"
        completed=true;
    } while(false);
    return completed;
}
#endif

[noinline]
void admitDefinitions(inout Runtime s,uint input)
{
    uint world=input+P_WORLD_META_BASE,codeNames=commands[world+1];
    if(codeNames>P_DEFINITIONS || commands[world]>codeNames) { s.error=64;return; }
    if(commands[world+2]>s.count) { s.error=64;return; }
    uint elementDefinitions=0;
    if(commands[world+3]>1) { s.error=64;return; }
#ifndef PORTABLE_WORLD_ROSTER
    if(commands[world+3]!=0) { s.error=64;return; }
#endif
    if(!validFocusMetadata(input)) { s.error=64;return; }
    for(uint word=5;word<P_WORLD_META_WORDS;word++) if(commands[world+word]!=0) { s.error=64;return; }
    if(commands[input+P_RECIPIENT_META_BASE]>P_RECIPIENT_NODES) { s.error=64;return; }
    if(commands[input+P_RECIPIENT_META_BASE+1]>1) { s.error=64;return; }
    if(!validAlliedRandomMetadata(input)) { s.error=64;return; }
    uint refs=input+P_BURST_REFERENCE_BASE;
    if(commands[refs]>1 || commands[refs+1]>31 || commands[refs]!=0 && s.combat==0) { s.error=64;return; }
    for(uint word=2;word<8;word++) if(commands[refs+word]!=0) { s.error=64;return; }
    for(uint word=28;word<P_BURST_REFERENCE_WORDS;word++) if(commands[refs+word]!=0) { s.error=64;return; }
    if(commands[refs]==0)
    { for(uint word=1;word<P_BURST_REFERENCE_WORDS;word++) if(commands[refs+word]!=0) { s.error=64;return; } }
    else for(uint who=0;who<5;who++)
    {
        uint64_t energy=loadNumber(refs+8+who*4),raw=loadNumber(refs+10+who*4);
        if(!f64Finite(energy) || !f64Finite(raw) || f64Less(energy,0) || f64Less(raw,0) || f64Less(f64FromI64(1000000),energy) || f64Less(f64FromI64(1000000),raw) ||
           (commands[refs+1] & (1U<<who))==0 && !f64Zero(raw)) { s.error=64;return; }
    }
    for (uint j = 0; j < s.count; j++)
    {
        Definition d;loadDefinition(input,j,d); PROJECTILE_ADMIT_ROW(s,j,d)
#ifdef PORTABLE_PRODUCT_OUTLINED_HELPERS
        if(!admitDefinitionTypes(s,input,j,d,elementDefinitions)) break;
        if(!admitDefinitionTriggers(s,input,j,d,elementDefinitions)) break;
        if(!admitDefinitionRoutes(s,input,j,d,elementDefinitions)) break;
        if(!admitDefinitionMasks(s,input,j,d,elementDefinitions)) break;
#else
#include "admission_definition_types.slang"
#include "admission_definition_triggers.slang"
#include "admission_definition_routes.slang"
#include "admission_definition_masks.slang"
#endif
    }
    if(s.error==0 && (elementDefinitions!=commands[world+2] || uint((s.incomingMask&32)!=0)!=commands[world+3])) s.error=64;
}
