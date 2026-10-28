StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "binary64.slang"
#include "world_schedule.slang"
#include "world_add_attack_cursor.slang"
#include "world_add_attack_layout.slang"

void adsEmit(inout WorldSchedule w,uint node,uint slot,uint generation,uint index,uint64_t when)
{
    uint h=w.output+ADS_HEAD,count=results[h+1];if(count>=1024){w.error=2;return;}
    uint at=w.output+ADS_QUEUE+count*8;
    results[at]=node;results[at+1]=slot;results[at+2]=generation;results[at+3]=index;
    wsStore(at+4,when);results[h+1]=count+1;
}

void adsFrame(inout WorldSchedule w,uint input,uint64_t when,uint mask)
{
    uint first=results[w.output+2],offset=0;
    // Component-only authored clear stimuli. The battle caller will supply
    // actual actor-pool liveness, using the same nextWorldAddAttack function.
    for(uint n=0;n<w.count;n++)
    {
        uint row=input+ADS_ROW_BASE+n*8,s=wsState(w,n);
        for(uint slot=0;slot<commands[row];slot++)
        {
            uint p=w.output+ADS_STATE+(offset+slot)*4;
            if(results[s]!=0 && (mask&(1U<<n))!=0)results[p+2]=results[s+1];
        }
        offset+=commands[row];
    }
    wsBegin(w,when,mask);if(w.error!=0)return;
    uint end=results[w.output+2];offset=0;
    for(uint n=0;n<w.count && w.error==0;n++)
    {
        uint s=wsState(w,n),row=input+ADS_ROW_BASE+n*8,generation=results[s+1];
        // Preserve declaration order across BODY and ADD nodes, not a second
        // pass that would put every ADD after every BODY attack.
        for(uint i=first;i<end && w.error==0;i++)
        {
            uint at=w.output+WS_LOG+i*6;
            if(results[at]==3 && results[at+1]==n)adsEmit(w,n,0,generation,results[at+2],when);
        }
        for(uint slot=0;slot<commands[row] && w.error==0;slot++)
        {
            uint p=w.output+ADS_STATE+(offset+slot)*4,index;
            bool alive=results[s]!=0 && results[p+2]!=generation;
            while(nextWorldAddAttack(p,generation,alive,wsRead(s+2),commands[row+1],wsLoad(row+2),when,index) && w.error==0)
            {adsEmit(w,n,slot+1,generation,index,when);results[s+4]++;}
        }
        offset+=commands[row];
    }
    results[w.output+ADS_HEAD+2]++;
}

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*ADS_INPUT,output=id.x*ADS_OUTPUT;
    for(uint i=0;i<ADS_OUTPUT;i++)results[output+i]=0;
    WorldSchedule w;w.input=input;w.output=output;w.count=commands[input+1];w.error=0;
    uint steps=commands[input+2],mode=commands[input+3],finish=commands[input+4],decl=input+ADS_BASE;
    uint64_t through=wsLoad(input+6);
    bool valid=commands[input]==0x57533031U && steps<=64 && mode<=2 && finish<=1 && commands[input+5]==0
        && f64Finite(through) && !f64Less(through,0) && !f64Less(f64FromI64(180),through)
        && (mode==0 || steps==0) && commands[decl]==0x41445331U && commands[decl+1]==1 && commands[decl+2]==w.count;
    for(uint j=8;j<16;j++)valid=valid && commands[input+j]==0;
    for(uint j=4;j<16;j++)valid=valid && commands[decl+j]==0;
    if(!valid || !wsValidate(w)){results[output]=64;return;}
    uint total=0;
    for(uint n=0;n<32;n++)
    {
        uint row=decl+16+n*8,count=commands[row];uint64_t interval=wsLoad(row+2);
        if(n>=w.count || count==0){for(uint j=0;j<8;j++)valid=valid && commands[row+j]==0;continue;}
        valid=valid && count<=127 && commands[row+1]<=0x7fffffffU && commands[wsNode(w,n)+6]==0
            && f64Finite(interval) && !f64Less(interval,0) && (commands[row+1]!=0 || f64Zero(interval));
        for(uint j=4;j<8;j++)valid=valid && commands[row+j]==0;
        total+=count;
    }
    valid=valid && total<=127 && total==commands[decl+3];
    uint64_t previous=0;
    for(uint step=0;step<64;step++)
    {
        uint at=input+2064+step*4,mask=commands[at+2];uint64_t t=wsLoad(at);
        if(step>=steps){for(uint j=0;j<4;j++)valid=valid && commands[at+j]==0;continue;}
        valid=valid && f64Finite(t) && !f64Less(t,previous) && !f64Less(through,t) && commands[at+3]==0 && (w.count==32 || (mask>>w.count)==0);
        for(uint n=0;n<w.count;n++)if((mask&(1U<<n))!=0)valid=valid && (commands[wsNode(w,n)+1]&2)!=0;
        previous=t;
    }
    if(!valid){results[output]=64;return;}
    results[output+ADS_HEAD]=0x41445331U;
    if(mode==0)
        for(uint step=0;step<steps && w.error==0;step++){uint at=input+2064+step*4;adsFrame(w,input,wsLoad(at),commands[at+2]);}
    else
    {
        adsFrame(w,input,0,0);uint64_t accumulated=0;
        for(uint frame=0;frame<=10800 && w.error==0;frame++)
        {
            uint64_t t=mode==1?accumulated:f64Div(f64FromI64(frame),uint64_t(0x404e0000)<<32);
            if(f64Less(through,t))break;
            adsFrame(w,input,t,0);accumulated=f64Add(t,uint64_t(0x3f911111)<<32|0x11111111);
        }
    }
    if(finish!=0 && w.error==0)wsFinish(w,through);
    results[output]=w.error;
}
