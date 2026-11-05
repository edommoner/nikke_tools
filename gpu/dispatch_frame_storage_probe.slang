// Exercise the real shared frame storage without running a battle.
#define PORTABLE_RESIDENT_RUNTIME
#define PORTABLE_COMPOSED_ARENA
#define PORTABLE_RESIDENT_FRAME_STACK
#define PORTABLE_ATTACK_GROUPS
#define PORTABLE_PARENT_FIXED_DAMAGE
static const uint P_OUTPUT_WORDS=1040;
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "dispatch_frame_type.slang"
struct Runtime { uint64_t guard; uint error; uint dispatchFrameWords[1024]; };
RWStructuredBuffer<Runtime> runtimeStates;
#include "dispatch_frame_storage.slang"

[ForceInline]
void mutateProbeFrame(inout Frame f)
{ f.cursor+=3;f.value^=uint64_t(0x80000001U)<<32; }

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*40,output=id.x*1040,op=commands[input];
    runtimeStates[id.x].guard=uint64_t(0x12345678U)<<32|id.x;
    runtimeStates[id.x].error=0;
    for(uint i=0;i<1024;i++)runtimeStates[id.x].dispatchFrameWords[i]=0xdeadbeefU;
    DispatchFrameStack frames;frames.caseIndex=id.x;
    // Fill the same Runtime storage with raw input, then load/store through the
    // production codec. This checks all optional fields and padding words.
    for(uint slot=0;slot<32;slot++)
    {
        for(uint word=0;word<32;word++)runtimeStates[id.x].dispatchFrameWords[slot*32+word]=commands[input+8+word];
        Frame f=loadDispatchFrame(frames,slot);f.cursor+=slot;storeDispatchFrame(frames,slot,f);
    }
    if(op==1) { frames[31].cursor++;frames[31].value^=uint64_t(1)<<63; }
    if(op==2) { Frame f=loadDispatchFrame(frames,31);mutateProbeFrame(f);storeDispatchFrame(frames,31,f); }
    if(op==3) { Frame f=loadDispatchFrame(frames,32);if(f.value!=0 || f.cursor!=0)runtimeStates[id.x].error=64; }
    if(op==4) { Frame f={};storeDispatchFrame(frames,32,f); }
    if(runtimeStates[id.x].guard!=(uint64_t(0x12345678U)<<32|id.x))runtimeStates[id.x].error=64;
    for(uint i=0;i<16;i++)results[output+i]=0;
    results[output]=0;results[output+1]=0x46524d31U;results[output+2]=runtimeStates[id.x].error;
    results[output+3]=32;results[output+4]=32;results[output+5]=id.x;results[output+6]=0x12345678U;
    for(uint i=0;i<1024;i++)results[output+16+i]=runtimeStates[id.x].dispatchFrameWords[i];
}
