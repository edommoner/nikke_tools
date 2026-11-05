// Probe snapshots exercise the same policy functions intended for burstFrame.
#include "burst_control_policy.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
uint64_t burstProbeRead(uint at){return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;uint input=1+id.x*224,output=id.x*32;
    for(uint i=0;i<32;i++)results[output+i]=0;
    BurstControlPolicy p;for(uint i=0;i<176;i++)p.words[i]=commands[input+i];
    uint a=input+176;BurstControlState s;
    s.stage=commands[a+1];s.cycle=commands[a+2];s.reentry=commands[a+3];s.unavailable=commands[a+4];s.explicitStage=commands[a+5];
    bool valid=burstControlValid(p)&&commands[a]==0x42535031U&&s.stage>=1&&s.stage<=3&&s.cycle<0xffffffff&&s.reentry<=1&&s.unavailable<32&&s.explicitStage<32&&commands[a+11]==0;
    for(uint i=0;i<5;i++){s.stages[i]=commands[a+6+i];s.ready[i]=burstProbeRead(a+18+i*2);if(s.stages[i]>4||!burstControlBound(s.ready[i],180))valid=false;}
    s.when=burstProbeRead(a+12);s.opened=burstProbeRead(a+14);s.action=burstProbeRead(a+16);
    if(!burstControlBound(s.when,180)||!burstControlBound(s.opened,180)&&s.opened!=((uint64_t(0x3ff00000)<<32)|F64_SIGN)||!burstControlBound(s.action,180)&&s.action!=BC_INF)valid=false;
    for(uint i=28;i<48;i++)if(commands[a+i]!=0)valid=false;
    if(!valid){results[output]=64;return;}
    BurstControlCandidates c=burstControlCandidates(p,s,s.stage,true);BurstControlDecision d=burstControlChoose(p,s,c);uint64_t pred=burstControlPredict(p,s);
    results[output+1]=0x42435631U;results[output+2]=d.owner;results[output+3]=d.waitMask;results[output+4]=uint(d.action);results[output+5]=uint(d.action>>32);results[output+6]=c.count;
    for(uint i=0;i<c.count;i++)results[output+7+i]=c.owners[i]+1;
    results[output+12]=uint(pred);results[output+13]=uint(pred>>32);
}
