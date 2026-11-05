// Shared SHA-256 compression, used by selection history and healing history.
#ifndef PORTABLE_SHARED_SHA256
#define PORTABLE_SHARED_SHA256
static const uint SHA256_K[64]={
    0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
    0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
    0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
    0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
    0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
    0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
    0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
    0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U};
uint sha256Rotate(uint value,uint n) { return (value>>n)|(value<<(32-n)); }
uint sha256Swap(uint value)
{ return (value>>24)|((value>>8)&0xff00U)|((value<<8)&0xff0000U)|(value<<24); }
[noinline]
void sha256Block(inout uint hash[8],uint block[16])
{
    uint w[64];for(uint i=0;i<16;i++) w[i]=block[i];
    for(uint i=16;i<64;i++)
    {
        uint a=w[i-15],b=w[i-2];
        w[i]=w[i-16]+(sha256Rotate(a,7)^sha256Rotate(a,18)^(a>>3))+w[i-7]+(sha256Rotate(b,17)^sha256Rotate(b,19)^(b>>10));
    }
    uint a=hash[0],b=hash[1],c=hash[2],d=hash[3],e=hash[4],f=hash[5],g=hash[6],h=hash[7];
    for(uint i=0;i<64;i++)
    {
        uint t1=h+(sha256Rotate(e,6)^sha256Rotate(e,11)^sha256Rotate(e,25))+((e&f)^(~e&g))+SHA256_K[i]+w[i];
        uint t2=(sha256Rotate(a,2)^sha256Rotate(a,13)^sha256Rotate(a,22))+((a&b)^(a&c)^(b&c));
        h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
    }
    hash[0]+=a;hash[1]+=b;hash[2]+=c;hash[3]+=d;hash[4]+=e;hash[5]+=f;hash[6]+=g;hash[7]+=h;
}
#endif
