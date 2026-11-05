// Preserve the first512 records byte-for-byte. On overflow only, chain every
// complete20-word LE record, including clocks, through SHA256(previous32 || row80).
#include "sha256_runtime.slang"
static const uint HEAL_CHARGE_HISTORY_TAIL=781320U;
[noinline]
void hashHealChargeRecord(uint tail,uint row[20])
{
    uint hash[8]={0x6a09e667U,0xbb67ae85U,0x3c6ef372U,0xa54ff53aU,0x510e527fU,0x9b05688cU,0x1f83d9abU,0x5be0cd19U};
    uint block[16];
    for(uint i=0;i<8;i++) { block[i]=results[tail+i];block[8+i]=sha256Swap(row[i]); }
    sha256Block(hash,block);
    for(uint i=0;i<12;i++) block[i]=sha256Swap(row[8+i]);
    block[12]=0x80000000U;block[13]=0;block[14]=0;block[15]=896U;
    sha256Block(hash,block);for(uint i=0;i<8;i++) results[tail+i]=hash[i];
}
[noinline]
void beginHealChargeHistory(uint head,uint tail)
{
    for(uint i=0;i<8;i++) results[tail+i]=0;
    for(uint index=0;index<512;index++)
    {
        uint row[20];for(uint i=0;i<20;i++) row[i]=results[head+8+index*20+i];
        hashHealChargeRecord(tail,row);
    }
    results[head+3]=0x48434831U;results[head+4]=1;results[head+5]=512;results[head+7]=20;
}
