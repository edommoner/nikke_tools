// Execute the existing complete world program; read its caller-owned pools.
#define PORTABLE_COORDINATE_POOL
#define portableEvents legacyCoordinatePoolEvents
#include "world_projectile_entry.slang"
#undef portableEvents
#include "coordinate_scene.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*(P_INPUT_WORDS+C_INPUT),output=id.x*P_OUTPUT_WORDS,dst=output+786432U;
    WORLD_TEAM_INPUT(input,output)
    Runtime s;initializeRuntime(s);bool ready;initializePortableProgram(s,input,output,ready);if(!ready)return;
    CoordinateScene c;c.input=input+P_INPUT_WORDS;c.output=dst;c.count=commands[c.input+2];c.state=actorPoolAt(s,0);c.error=0;c.poolStride=16;c.poolBySlot=1;c.poolStart=8;
    // Validate binding/HP agreement before running the battle, with no pool copy.
    if(commands[c.input]!=0x434f4f31U||commands[c.input+1]!=1||commands[c.input+3]!=commands[input+P_WORLD_FRAME_INPUT_BASE+1]||c.count+1!=actorPoolCount(s)||!cValidate(c,commands[c.input+3])){results[output]=64;return;}
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
    uint queries;executePortableCommands(s,input,output,queries);if(s.error!=0){writePortableProgram(s,input,output,queries);return;}
    for(uint i=0;i<P_OUTPUT_WORDS-786432U;i++)results[dst+i]=0;
    uint64_t when=commands[input+2]>0?loadNumber(input+P_COMMAND_BASE+(commands[input+2]-1)*8+1):0;
    cCapture(c,dst,when);
    writePortableProgram(s,input,output,queries);
}
