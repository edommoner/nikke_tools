// Version1: retain128 raw records and SHA-256 every ordered semantic atom.
// Clock words are excluded explicitly: sample6/7, revival2/3. LE atom bytes.
static const uint OH_PREFIX=128U,OH_MAX=1048576U,OH_MAGIC=0x4f485331U;
static const uint OH_K[64]={
    0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
    0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
    0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
    0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
    0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
    0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
    0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
    0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U};
uint ohRotate(uint value,uint n) { return (value>>n)|(value<<(32-n)); }
uint ohSwap(uint value)
{ return (value>>24)|((value>>8)&0xff00U)|((value<<8)&0xff0000U)|(value<<24); }
void ohCompress(uint head)
{
    uint w[64];for(uint i=0;i<16;i++) w[i]=results[head+16+i];
    for(uint i=16;i<64;i++)
    {
        uint a=w[i-15],b=w[i-2];
        w[i]=w[i-16]+(ohRotate(a,7)^ohRotate(a,18)^(a>>3))+w[i-7]+(ohRotate(b,17)^ohRotate(b,19)^(b>>10));
    }
    uint a=results[head+8],b=results[head+9],c=results[head+10],d=results[head+11];
    uint e=results[head+12],f=results[head+13],g=results[head+14],h=results[head+15];
    for(uint i=0;i<64;i++)
    {
        uint t1=h+(ohRotate(e,6)^ohRotate(e,11)^ohRotate(e,25))+((e&f)^(~e&g))+OH_K[i]+w[i];
        uint t2=(ohRotate(a,2)^ohRotate(a,13)^ohRotate(a,22))+((a&b)^(a&c)^(b&c));
        h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
    }
    results[head+8]+=a;results[head+9]+=b;results[head+10]+=c;results[head+11]+=d;
    results[head+12]+=e;results[head+13]+=f;results[head+14]+=g;results[head+15]+=h;
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
