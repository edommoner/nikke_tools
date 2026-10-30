// Existing carrier lifetime, DFS frames, HP and cover; output-only snapshots.
#include "incoming_weighted_allocation.slang"
uint weightedHead(inout Runtime s){return s.resourceOutput+WGT_OUTPUT_BASE;}
uint weightedScratch(inout Runtime s,uint depth){return weightedHead(s)+WGT_SCRATCH+depth*WGT_SCRATCH_WORDS;}
uint weightedSnapshot(inout Runtime s,uint index){return weightedHead(s)+WGT_SNAPSHOTS+index*WGT_SNAPSHOT_WORDS;}
bool initializeWeightedIncoming(inout Runtime s)
{
    uint at=s.inputBase+WGT_BASE;
    if(commands[at]!=WGT_MAGIC||commands[at+1]!=1||commands[at+2]!=5||commands[at+3]!=0)return false;
    for(uint i=10;i<16;i++)if(commands[at+i]!=0)return false;
    for(uint i=4;i<10;i+=2){uint64_t w=loadNumber(at+i);if(!f64Finite(w)||!f64Less(0,w))return false;}
    for(uint i=WGT_OUTPUT_BASE;i<WGT_OUTPUT;i++)results[s.resourceOutput+i]=0;
    results[weightedHead(s)]=WGT_MAGIC;return true;
}
uint captureWeightedIncoming(inout Runtime s,uint who,uint64_t amount,uint64_t when)
{
    uint source=0xffffffff,caster=0,coverSource=0xffffffff,mask=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);
        if(d.stat==WGT_BODY_STAT && queryRecipient(s,row,who,when))
        {if(source!=0xffffffff){s.error=64;return 0;}source=row;caster=d.owner;}
    }
    if(source==0xffffffff)return 0;
    if(incomingSplitGroup(s,who,when)!=0){s.error=64;return 0;}
    for(uint member=0;member<5;member++)if((s.downMask&(1U<<member))==0&&queryRecipient(s,source,member,when))mask|=1U<<member;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);
        if(d.stat==WGT_COVER_STAT&&d.owner==caster&&s.alive[row]!=0&&s.stacks[row]>0&&f64Less(when,s.end[row]))
        {if(coverSource!=0xffffffff){s.error=64;return 0;}coverSource=row;}
    }
    bool cover=coverSource!=0xffffffff&&(s.downMask&(1U<<caster))==0&&f64Less(0,s.coverHP[caster]);
    uint active;uint64_t total,shares[6];uint at=s.inputBase+WGT_BASE;
    uint status=incomingWeightedAllocation(mask,caster,cover,amount,loadNumber(at+4),loadNumber(at+6),loadNumber(at+8),active,total,shares);
    if(status!=0){s.error=status;return 0;}
    uint head=weightedHead(s),index=results[head+1];if(index>=WGT_CAPACITY){s.error=2;return 0;}results[head+1]=index+1;
    uint outAt=weightedSnapshot(s,index);results[outAt]=mask;results[outAt+1]=caster;results[outAt+2]=who;results[outAt+3]=active;
    storeNumber(outAt+4,when);storeNumber(outAt+6,amount);storeNumber(outAt+8,total);
    for(uint i=0;i<6;i++)storeNumber(outAt+10+i*2,shares[i]);
    results[outAt+22]=s.carrierDefinition[source];results[outAt+23]=cover? s.carrierDefinition[coverSource]+1:0;
    storeNumber(outAt+24,s.activated[source]);return index+1;
}
[noinline]
void advanceWeightedIncoming(inout Runtime s,inout DISPATCH_FRAMES(frames),inout int depth,Frame f)
{
    uint scratch=weightedScratch(s,uint(depth)),encoded=results[scratch],snapshot=weightedSnapshot(s,encoded-1);
    if(encoded==0||encoded>results[weightedHead(s)+1]){s.error=64;return;}
    uint mask=results[snapshot],member=f.cursor;
    while(member<5&&((mask&(1U<<member))==0||(s.downMask&(1U<<member))!=0))member++;
    if(member<5)
    {
        frames[depth].cursor=member+1;pushFrame(s,frames,depth,23,0,member,f.argument,f.time);
        if(s.error==0)
        {
            frames[depth].healthValue=protectionNumber(snapshot+10+member*2);frames[depth].repeatPassive=uint(member==f.owner);
            uint legacy=P_PROTECTION_HIT_BASE+(uint(f.argument)*5+f.owner)*16;
            frames[depth].repeatRow=incomingRecordAddress(s,uint(f.argument),f.owner,member,member==f.owner,legacy);
        }
        return;
    }
    if(f.cursor<=5&&(results[snapshot+3]&32)!=0)
    {
        frames[depth].cursor=6;uint owner=results[snapshot+1],head=weightedHead(s),index=results[head+2];
        if(index>=WGT_CAPACITY){s.error=2;return;}
        uint outAt=head+WGT_RECEIPTS+index*WGT_RECEIPT_WORDS;results[head+2]=index+1;
        uint64_t before=s.coverHP[owner],applied=0;bool delivered=(s.downMask&(1U<<owner))==0&&f64Less(0,before);
        if(delivered){applied=smaller(before,protectionNumber(snapshot+20));consumeIncomingCover(s,owner,applied,uint(f.argument),f.time);}
        results[outAt]=encoded-1;results[outAt+1]=uint(delivered);storeNumber(outAt+2,f.time);storeNumber(outAt+4,before);storeNumber(outAt+6,applied);storeNumber(outAt+8,s.coverHP[owner]);
        if(f64Less(0,applied))pushFrame(s,frames,depth,0,36,owner,0,f.time);
        return;
    }
    for(uint i=0;i<WGT_SCRATCH_WORDS;i++)results[scratch+i]=0;
    depth--;
}
