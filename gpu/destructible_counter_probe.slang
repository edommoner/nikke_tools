#define PORTABLE_RESIDENT_RUNTIME
#define portableEvents unusedLiteralCounterEntry
#include "counter_landing_entry.slang"
#undef portableEvents
#include "destructible_target_core.slang"
#include "destructible_world_runtime.slang"
#include "destructible_impact_runtime.slang"
// Existing literal executor owns [0,524288); declared world uses [600000,704480).
// This driver supplies resolved receipts, not automatic battle/weapon admission.
static const uint DC_BASE_INPUT=97464U,DC_INPUT=102584U,DC_SIDE=600000U;
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*DC_INPUT,output=id.x*786432,extra=input+DC_BASE_INPUT,dout=output+DC_SIDE,base=dout+16384,header=dout+18200;
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready) return;
    for(uint i=0;i<104480;i++) results[dout+i]=0;
    WorldSchedule w;w.input=extra;w.output=dout+16;w.count=commands[extra+1];w.error=0;
    uint bindings=extra+2328,count=commands[extra+2320],steps=commands[extra+3864];uint64_t through=wsLoad(extra+6);
    if(commands[extra]!=0x57533031U||commands[extra+2]!=0||commands[extra+3]!=0||commands[extra+4]!=0||commands[extra+5]!=0||!f64Finite(through)||f64Less(through,0)||f64Less(f64FromI64(180),through)||steps>32||!wsValidate(w)) w.error=64;
    for(uint i=8;i<16;i++) if(commands[extra+i]!=0) w.error=64;
    for(uint i=2064;i<2320;i++) if(commands[extra+i]!=0) w.error=64;
    for(uint i=2321;i<2328;i++) if(commands[extra+i]!=0) w.error=64;
    for(uint i=3865;i<3872;i++) if(commands[extra+i]!=0) w.error=64;
    if(w.error==0&&!dwValidate(w,bindings,count,base)) w.error=64;
    if(steps<=32) for(uint i=3872+steps*32;i<5120;i++) if(commands[extra+i]!=0) w.error=64;
    if(w.error==0) targetCounterCommand(runtimeStates[id.x],input+P_COMMAND_BASE,0,0,output);
    for(uint step=0;step<steps&&w.error==0&&runtimeStates[id.x].error==0;step++)
    {
        uint at=extra+3872+step*32,op=commands[at],answer=dout+20000+step*2640;uint64_t when=wsLoad(at+5);
        results[answer]=op;
        for(uint i=15;i<32;i++) if(commands[at+i]!=0) w.error=64;
        if(!f64Finite(when)||f64Less(through,when)||op>4) w.error=64;
        if(op==1) { if(commands[at+12]>=5||commands[at+13]>=4||commands[at+14]>=0x1000000U) w.error=64; }
        else { for(uint i=1;i<5;i++) if(commands[at+i]!=0) w.error=64;for(uint i=7;i<11;i++) if(commands[at+i]!=0) w.error=64;for(uint i=12;i<15;i++) if(commands[at+i]!=0) w.error=64; }
        if(op!=1&&op!=2&&commands[at+11]!=0) w.error=64;
        if(w.error!=0) break;
        if(op==3) dwFinish(w,bindings,count,base,header,when);
        else results[answer+2]=uint(dwBegin(w,bindings,count,base,header,when));
        if(w.error!=0) break;
        beginLazyRoot(runtimeStates[id.x],when);tick(runtimeStates[id.x],when,output);
        if(op==4) dispatch(runtimeStates[id.x],0,7,0,0,when,output);
        if(op==1)
        {
            DWReceipt r=dwLand(w,base,count,header,commands[at+1],commands[at+2],commands[at+3],commands[at+4],commands[at+11],wsLoad(at+7),wsLoad(at+9),when);
            results[answer+3]=r.delivered;results[answer+4]=r.broken;dtStore(answer+5,r.took);results[answer+7]=r.ownerKind;results[answer+8]=r.ownerId;results[answer+9]=r.ownerGeneration;
            results[answer+10]=r.kind;results[answer+11]=r.identity;results[answer+12]=r.generation;dtStore(answer+13,r.when);
            if(w.error==0) dwPublishImpact(runtimeStates[id.x],r,output+599980,commands[at+12],commands[at+13],commands[at+11],commands[at+14],commands[at+2],commands[at+3],commands[at+4],wsLoad(at+7),wsLoad(at+9),when,output);
        }
        if(op==2) { uint status;dtSelect(base,count,commands[at+11],answer+16,status);w.error=status; }
        results[answer+1]=w.error;results[answer+20]=results[header+3];results[answer+21]=results[w.output+1];results[answer+22]=results[w.output+2];
        dtStore(answer+24,plainQuantity(runtimeStates[id.x],0,S_atk_pct,when));
        snapshotTargetCounters(runtimeStates[id.x],step);
        for(uint i=0;i<128*DT_WORDS;i++) results[answer+32+i]=results[base+i];
        for(uint i=0;i<32*24;i++) results[answer+1824+i]=results[w.output+16+i];
    }
    uint status=w.error!=0?w.error:runtimeStates[id.x].error;
    results[dout]=status==0?0:64;results[dout+1]=steps;results[dout+2]=status;results[dout+3]=count;
    results[output]=status==0?0:64;
}
