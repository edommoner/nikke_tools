// Version1: retain128 raw records and SHA-256 every ordered semantic atom.
// Clock words are excluded explicitly: sample6/7, revival2/3. LE atom bytes.
static const uint OH_PREFIX=128U,OH_MAX=1048576U,OH_MAGIC=0x4f485331U;
#include "sha256_runtime.slang"
uint ohRotate(uint value,uint n) { return sha256Rotate(value,n); }
uint ohSwap(uint value) { return sha256Swap(value); }
void ohCompress(uint head)
{
    uint hash[8],block[16];
    for(uint i=0;i<8;i++) hash[i]=results[head+8+i];
    for(uint i=0;i<16;i++) block[i]=results[head+16+i];
    sha256Block(hash,block);
    for(uint i=0;i<8;i++) results[head+8+i]=hash[i];
}
bool ohAppendAtom(uint head,uint at)
{
    uint kind=results[at];if(kind<1 || kind>3) return false;
    uint count=results[head+7];
    for(uint i=0;i<8;i++)
    {
        bool clock=kind==3 ? i>=6 : i==2 || i==3;
        results[head+16+count++]=clock ? 0 : ohSwap(results[at+i]);
        if(count==16) { ohCompress(head);count=0; }
    }
    results[head+7]=count;return true;
}
bool initializeOrderedHistory(uint prefix,uint head)
{
    for(uint i=0;i<64;i++) results[head+i]=0;
    results[head]=OH_MAGIC;results[head+1]=1;results[head+2]=OH_PREFIX;
    results[head+3]=OH_PREFIX;results[head+5]=8;
    results[head+8]=0x6a09e667U;results[head+9]=0xbb67ae85U;results[head+10]=0x3c6ef372U;results[head+11]=0xa54ff53aU;
    results[head+12]=0x510e527fU;results[head+13]=0x9b05688cU;results[head+14]=0x1f83d9abU;results[head+15]=0x5be0cd19U;
    for(uint i=0;i<OH_PREFIX;i++) if(!ohAppendAtom(head,prefix+i*8)) return false;
    return true;
}
uint orderedHistoryRecordAt(uint prefix,uint head,uint index,bool enabled)
{
    if(index<OH_PREFIX) return prefix+index*8;
    if(!enabled || index>=OH_MAX) return 0xffffffffU;
    if(index==OH_PREFIX && !initializeOrderedHistory(prefix,head)) return 0xffffffffU;
    if(results[head]!=OH_MAGIC || results[head+2]!=index || results[head+6]!=0) return 0xffffffffU;
    return head+48;
}
bool orderedHistoryRecordDone(uint head,uint index,uint at)
{
    if(index<OH_PREFIX) return true;
    if(!ohAppendAtom(head,at)) return false;
    results[head+2]=index+1;results[head+4]=index+1-OH_PREFIX;return true;
}
bool finishOrderedHistory(uint head,uint total)
{
    if(total<=OH_PREFIX) return true;
    if(total>OH_MAX || results[head]!=OH_MAGIC || results[head+2]!=total || results[head+6]!=0) return false;
    uint count=results[head+7];if(count!=0 && count!=8) return false;
    results[head+16+count++]=0x80000000U;
    while(count<14) results[head+16+count++]=0;
    results[head+30]=0;results[head+31]=total*256U;ohCompress(head);
    for(uint i=0;i<8;i++) results[head+32+i]=results[head+8+i];
    results[head+6]=1;return true;
}
