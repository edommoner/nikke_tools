StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "binary64.slang"
#include "world_schedule.slang"
[shader("compute")]
[numthreads(1,1,1)]
void worldScheduleProbe(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*2320,output=id.x*65536;
    for(uint j=0;j<65536;j++) results[output+j]=0;
    WorldSchedule w;w.input=input;w.output=output;w.count=commands[input+1];w.error=0;
    uint steps=commands[input+2],mode=commands[input+3],finish=commands[input+4];uint64_t through=wsLoad(input+6);
    if(commands[input]!=0x57533031 || mode>2 || finish>1 || !f64Finite(through) || f64Less(through,0) || steps>64 || mode!=0 && (steps!=0 || f64Less(uint64_t(0x40668000)<<32,through)) || commands[input+5]!=0)
    { results[output]=64;return; }
    for(uint j=8;j<16;j++) if(commands[input+j]!=0) { results[output]=64;return; }
    if(!wsValidate(w)) { results[output]=64;return; }
    uint64_t previous=0;
    for(uint step=0;step<64;step++)
    {
        uint at=input+2064+step*4;uint64_t time=wsLoad(at);uint mask=commands[at+2];
        if(step>=steps) { for(uint j=0;j<4;j++) if(commands[at+j]!=0) { results[output]=64;return; }continue; }
        if(!f64Finite(time) || f64Less(time,previous) || f64Less(through,time) || commands[at+3]!=0 || w.count<32 && (mask>>w.count)!=0)
        { results[output]=64;return; }
        for(uint n=0;n<w.count;n++) if((mask&(1U<<n))!=0 && (commands[wsNode(w,n)+1]&2)==0) { results[output]=64;return; }
        previous=time;
    }
    if(mode==0)
    {
        for(uint step=0;step<steps && w.error==0;step++)
        {
            uint at=input+2064+step*4;wsBegin(w,wsLoad(at),commands[at+2]);results[output+4]++;
            for(uint j=0;j<32*24;j++) results[output+WS_SNAP+step*32*24+j]=results[output+16+j];
            results[output+3]++;
        }
    }
    else
    {
        wsBegin(w,0,0);results[output+4]++;
        uint64_t accumulated=0;
        for(uint frame=0;frame<=10800 && w.error==0;frame++)
        {
            uint64_t time=mode==1?accumulated:f64Div(f64FromI64(frame),uint64_t(0x404e0000)<<32);
            if(f64Less(through,time)) break;
            wsBegin(w,time,0);results[output+4]++;
            accumulated=f64Add(time,uint64_t(0x3f911111)<<32|0x11111111);
        }
    }
    if(finish!=0 && w.error==0) wsFinish(w,through);
    results[output]=w.error;
}
