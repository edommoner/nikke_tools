#include "lock_delivery_policy.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
static const uint LD_INPUT=1032U,LD_OUTPUT=16U,LD_CAPACITY=128U,LD_MAGIC=0x4c443031U;
bool lockDeliveryHandleValid(uint at)
{return commands[at]<6&&commands[at+1]<0x10000000U&&commands[at+2]>0&&commands[at+2]<0x80000000U;}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 tid:SV_DispatchThreadID)
{
    if(tid.x>=commands[0])return;
    uint input=1+tid.x*LD_INPUT,output=tid.x*LD_OUTPUT;
    for(uint i=0;i<LD_OUTPUT;i++)results[output+i]=0;
    uint revision=commands[input],count=commands[input+1],hit=commands[input+2],hits=commands[input+3],current=commands[input+4];
    bool valid=revision<0x80000000U&&count<=128&&hit>=1&&hit<=hits&&hits<=256&&current<=128&&commands[input+5]==LD_MAGIC&&commands[input+6]==0&&commands[input+7]==0;
    if(!valid){results[output]=64;return;}
    for(uint table=0;table<2;table++)for(uint i=0;i<128;i++)
    {
        uint at=input+8+table*512+i*4,n=table==0?count:current;
        if(i>=n){for(uint j=0;j<4;j++)if(commands[at+j]!=0)valid=false;continue;}
        if(!lockDeliveryHandleValid(at)||commands[at+3]>(table==0?0U:1U))valid=false;
        for(uint j=0;j<i;j++){uint other=input+8+table*512+j*4;if(commands[other]==commands[at]&&commands[other+1]==commands[at+1])valid=false;}
    }
    if(!valid){results[output]=64;return;}
    uint index=lockDeliveryIndex(hit,count),status=LD_EMPTY,kind=0xffffffffU,identity=0,generation=0,now=0;
    if(index!=0xffffffffU)
    {
        uint at=input+8+index*4;kind=commands[at];identity=commands[at+1];generation=commands[at+2];bool present=false,alive=false;
        for(uint i=0;i<current;i++){uint row=input+520+i*4;if(commands[row]==kind&&commands[row+1]==identity){present=true;now=commands[row+2];alive=commands[row+3]!=0;}}
        status=lockDeliveryStatus(generation,present,now,alive);
    }
    results[output+1]=status;results[output+2]=index;results[output+3]=kind;results[output+4]=identity;results[output+5]=generation;results[output+6]=now;
    results[output+7]=revision;results[output+8]=hit;results[output+9]=hits;results[output+10]=count;results[output+11]=current;results[output+12]=LD_MAGIC;
}
