// Raw capacity is unchanged. Every packet word, including clocks, is hashed.
#include "coordinate_packet_history_layout.slang"
#include "sha256_runtime.slang"
void cphCompress(uint h)
{
    uint hash[8],block[16];for(uint i=0;i<8;i++)hash[i]=results[h+8+i];for(uint i=0;i<16;i++)block[i]=results[h+16+i];
    sha256Block(hash,block);for(uint i=0;i<8;i++)results[h+8+i]=hash[i];
}
void cphInitialize(uint h)
{
    for(uint i=0;i<CPH_WORDS;i++)results[h+i]=0;
    results[h]=CPH_MAGIC;results[h+1]=1;results[h+3]=CP_TRACE_COUNT;results[h+4]=CP_TRACE_WORDS;results[h+5]=CPH_MAX;
    results[h+8]=0x6a09e667U;results[h+9]=0xbb67ae85U;results[h+10]=0x3c6ef372U;results[h+11]=0xa54ff53aU;
    results[h+12]=0x510e527fU;results[h+13]=0x9b05688cU;results[h+14]=0x1f83d9abU;results[h+15]=0x5be0cd19U;
}
uint coordinateHistoryRecordAt(inout Runtime s,uint retained)
{
    uint h=s.resourceOutput+CPH_BASE;if(results[h]==0&&retained==0)cphInitialize(h);
    uint count=results[h+2];
    if(results[h]!=CPH_MAGIC||results[h+6]!=0||count>=CPH_MAX||retained!=min(count,CP_TRACE_COUNT)){s.error=64;return 0;}
    return count<CP_TRACE_COUNT?s.resourceOutput+CP_TRACE+count*CP_TRACE_WORDS:h+40;
}
void coordinateHistoryRecordDone(inout Runtime s,uint at)
{
    uint h=s.resourceOutput+CPH_BASE,pending=results[h+7];
    for(uint i=0;i<CP_TRACE_WORDS;i++)
    {
        results[h+16+pending++]=sha256Swap(results[at+i]);
        if(pending==16){cphCompress(h);pending=0;}
    }
    results[h+7]=pending;results[h+2]++;
}
bool finishCoordinatePacketHistory(inout Runtime s)
{
    uint h=s.resourceOutput+CPH_BASE;if(results[h]==0)cphInitialize(h);
    uint total=results[h+2],pending=results[h+7];
    if(results[h]!=CPH_MAGIC||results[h+6]!=0||total>CPH_MAX||pending>=16||pending!=(total*12)%16||results[s.resourceOutput+CP_BASE+2]!=min(total,CP_TRACE_COUNT))return false;
    results[h+16+pending++]=0x80000000U;while(pending<14)results[h+16+pending++]=0;
    results[h+30]=0;results[h+31]=total*384;cphCompress(h);
    for(uint i=0;i<8;i++)results[h+32+i]=results[h+8+i];results[h+6]=1;return true;
}
