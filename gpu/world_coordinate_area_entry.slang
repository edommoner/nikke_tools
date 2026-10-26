// Execute the existing complete world program; read its caller-owned pools.
#include "coordinate_area_hooks.slang"
#define portableEvents legacyCoordinatePoolEvents
#ifndef PORTABLE_COMPOSED_ARENA
#include "world_projectile_entry.slang"
#endif
#undef portableEvents
#undef sampleCoordinateSkill
#undef captureCoordinateCast
#undef validCoordinateSkillDefinition
#undef deliverCoordinateParts
#include "coordinate_skill_runtime.slang"
#include "coordinate_area_runtime.slang"
#ifdef PORTABLE_COMPOSED_ARENA
[noinline]
void executeComposedCoordinateEvents(inout Runtime s,uint3 id)
#else
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
#endif
{
    if(id.x>=commands[0])return;
#ifdef PORTABLE_COORDINATE_TYPED_TARGETS
    uint input=1+id.x*115680U,output=id.x*P_OUTPUT_WORDS,dst=output+CP_BASE;
#elif defined(PORTABLE_COORDINATE_BURST_CONTROLS)
    uint input=1+id.x*(P_INPUT_WORDS+C_INPUT+CA_INPUT+CC_INPUT+CI_INPUT+440U),output=id.x*P_OUTPUT_WORDS,dst=output+CP_BASE;
#elif defined(PORTABLE_COORDINATE_SQUAD_ACTIONS)
    uint input=1+id.x*(P_INPUT_WORDS+C_INPUT+CA_INPUT+CC_INPUT+CI_INPUT+264U),output=id.x*P_OUTPUT_WORDS,dst=output+CP_BASE;
#elif defined(PORTABLE_COORDINATE_COVER_POLICIES)
    uint input=1+id.x*(P_INPUT_WORDS+C_INPUT+CA_INPUT+CC_INPUT+CI_INPUT+128U),output=id.x*P_OUTPUT_WORDS,dst=output+CP_BASE;
#elif defined(PORTABLE_COORDINATE_AUTHORED_AIM)
    uint input=1+id.x*(P_INPUT_WORDS+C_INPUT+CA_INPUT+CC_INPUT+CI_INPUT),output=id.x*P_OUTPUT_WORDS,dst=output+CP_BASE;
#elif defined(PORTABLE_COORDINATE_LIVE_CORE)
    uint input=1+id.x*(P_INPUT_WORDS+C_INPUT+CA_INPUT+CC_INPUT),output=id.x*P_OUTPUT_WORDS,dst=output+CP_BASE;
#else
    uint input=1+id.x*(P_INPUT_WORDS+C_INPUT+CA_INPUT),output=id.x*P_OUTPUT_WORDS,dst=output+CP_BASE;
#endif
    WORLD_TEAM_INPUT(input,output)
#ifndef PORTABLE_COMPOSED_ARENA
    Runtime s;
#endif
    initializeRuntime(s);bool ready;initializePortableProgram(s,input,output,ready);if(!ready)return;
    CoordinateScene c;c.input=input+P_INPUT_WORDS;c.output=dst;c.count=commands[c.input+2];c.state=actorPoolAt(s,0);c.error=0;c.poolStride=16;c.poolBySlot=1;c.poolStart=8;
    // Validate binding/HP agreement before running the battle, with no pool copy.
    if(commands[c.input]!=0x434f4f31U||commands[c.input+1]!=1||commands[c.input+3]!=commands[input+P_WORLD_FRAME_INPUT_BASE+1]
#ifndef PORTABLE_COORDINATE_GROUPS
       ||c.count+1!=actorPoolCount(s)
#endif
       ||!cValidate(c,commands[c.input+3])){results[output]=64;return;}
    uint64_t end=commands[input+2]>0?loadNumber(input+P_COMMAND_BASE+(commands[input+2]-1)*8+1):0;
    if(commands[c.input+4]!=1||commands[c.input+C_OP_BASE]!=4||commands[c.input+C_OP_BASE+1]!=0||!f64Equal(cNumber(c.input+C_OP_BASE+2),end)){results[output]=64;return;}
    for(uint i=5;i<16;i++)if(commands[c.input+i]!=0){results[output]=64;return;}
    for(uint i=C_OP_BASE+4;i<C_INPUT;i++)if(commands[c.input+i]!=0){results[output]=64;return;}
    for(uint i=0;i<c.count;i++)
    {
        uint row=cRow(c,i),slot=commands[row+5];if(slot>=actorPoolCount(s)){results[output]=64;return;}
        uint bind=actorBinding(s,slot),def=actorPoolDef(s,slot);
        if(commands[bind]!=commands[row]||commands[bind+1]!=commands[row+1]||commands[bind+3]!=commands[row+2]||commands[bind+4]!=commands[row+3]||!f64Equal(loadNumber(def+2),cNumber(row+20))){results[output]=64;return;}
    }
    if(!validCoordinateAreaIR(s)){results[output]=64;return;}
#ifdef PORTABLE_COORDINATE_PHYSICAL
    if(!initializeCoordinatePhysical(s)){results[output]=64;return;}
#endif
    if(!worldSkillsEnabled(s)||!actorPoolsEnabled(s)){results[output]=64;return;}
#ifdef PORTABLE_COORDINATE_GROUPS
    for(uint i=CP_BASE;i<AG_COMPACT;i++)results[output+i]=0;
#else
    for(uint i=CP_BASE;i<P_OUTPUT_WORDS;i++)results[output+i]=0;
#endif
    results[output+CP_BASE]=0x43534b31U;
#ifdef PORTABLE_COORDINATE_TYPED_TARGETS
    if(!initializeCoordinateTypedTargets(s)){results[output]=64;return;}
#endif
    uint queries;executePortableCommands(s,input,output,queries);
    for(uint i=5;i<16;i++)results[output+CP_BASE+i]=0;
    writePortableProgram(s,input,output,queries);
}
#ifdef PORTABLE_COMPOSED_ARENA
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
#ifdef PORTABLE_COORDINATE_ARC_ARENA
    uint arcBase=id.x*P_OUTPUT_WORDS+CRA_BASE;
    for(uint i=0;i<CRA_WORDS;i++)results[arcBase+i]=0;
#endif
    executeComposedCoordinateEvents(runtimeStates[id.x],id);
#ifdef PORTABLE_COORDINATE_ARC_ARENA
    for(uint i=0;i<CRA_WORDS;i++)results[arcBase+i]=0;
#endif
}
#endif
