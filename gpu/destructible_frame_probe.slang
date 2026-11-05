#define PORTABLE_RESIDENT_RUNTIME
#define PORTABLE_DESTRUCTIBLE_FRAME
#define PORTABLE_WORLD_PROJECTILE_DIAGNOSTIC
#define portableEvents unusedLiteralCounterEntry
#include "world_skill_entry.slang"
#undef portableEvents
#include "destructible_target_core.slang"
#include "destructible_world_runtime.slang"
#include "destructible_impact_runtime.slang"
#include "destructible_attack_runtime.slang"
#include "destructible_frame_runtime.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*102600,output=id.x*786432,extra=input+97464,batch=input+102584,dout=output+600000,base=dout+16384,header=dout+18200;
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready) return;
    for(uint i=0;i<112000;i++) results[dout+i]=0;
    WorldSchedule w;w.input=extra;w.output=dout+16;w.count=commands[extra+1];w.error=0;
    uint bindings=extra+2328,count=commands[extra+2320];uint64_t through=wsLoad(extra+6);
    if(commands[extra]!=0x57533031U||!f64Finite(through)||f64Less(through,0)||f64Less(f64FromI64(180),through)||!wsValidate(w)||commands[extra+3864]!=2) w.error=64;
    for(uint i=2;i<6;i++) if(commands[extra+i]!=0) w.error=64;
    for(uint i=8;i<16;i++) if(commands[extra+i]!=0) w.error=64;
    for(uint i=2064;i<2320;i++) if(commands[extra+i]!=0) w.error=64;
    for(uint i=2321;i<2328;i++) if(commands[extra+i]!=0) w.error=64;
    for(uint i=3865;i<3872;i++) if(commands[extra+i]!=0) w.error=64;
    for(uint i=3936;i<5120;i++) if(commands[extra+i]!=0) w.error=64;

    if(w.error==0&&!dwFrameDescriptorValid(runtimeStates[id.x],batch)) w.error=64;
    if(w.error==0&&!dwValidate(w,bindings,count,base)) w.error=64;
    if(w.error==0) { beginLazyRoot(runtimeStates[id.x],0);tick(runtimeStates[id.x],0,output);dispatch(runtimeStates[id.x],0,0,0,0,0,output); }
    uint64_t when=0;
    for(uint step=0;step<2&&w.error==0&&runtimeStates[id.x].error==0;step++)
    {
        uint at=extra+3872+step*32;when=wsLoad(at+5);
        for(uint i=0;i<32;i++) if(i!=5&&i!=6&&commands[at+i]!=0) w.error=64;
        if(!f64Finite(when)||f64Less(through,when)) w.error=64;
        if(w.error!=0) break;
        dwBegin(w,bindings,count,base,header,when);
        if(w.error==0) { beginLazyRoot(runtimeStates[id.x],when);tick(runtimeStates[id.x],when,output); }
    }
    if(w.error==0&&runtimeStates[id.x].error==0)
    {
        runtimeStates[id.x].phase=commands[batch+2]!=0?5U:0U;
        for(uint root=0;root<commands[batch+4]&&runtimeStates[id.x].error==0;root++) dispatch(runtimeStates[id.x],0,commands[batch+5],0,0,when,output);
        results[output+705008]=runtimeStates[id.x].activations[commands[batch]];
        snapshotTargetCounters(runtimeStates[id.x],0);dtStore(output+705000,plainQuantity(runtimeStates[id.x],0,S_atk_pct,when));
    }
    uint status=w.error!=0?w.error:runtimeStates[id.x].error;results[output]=status==0?0:64;
}
