// Exact integer expansion and per-parent bitonic sort. Host merges sorted beams.
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
[shader("compute")]
[numthreads(1,1,1)]
void optimizerSelect(uint3 id: SV_DispatchThreadID) {
 if(id.x>=commands[0])return;
 uint at=1+id.x*1612, nc=commands[at], last=commands[at+1];
 uint64_t total=uint64_t(commands[at+10])|(uint64_t(commands[at+11])<<32);
 uint64_t values[256]; uint indices[256];
 for(uint i=0;i<256;i++) {
  uint64_t value=0;
  if(i<nc) {
   uint c=at+12+i*10; bool valid=last==0xffffffffU||i>last;
   for(uint k=0;k<8;k++)if((commands[at+2+k]&commands[c+k])!=0)valid=false;
   if(valid)value=total+(uint64_t(commands[c+8])|(uint64_t(commands[c+9])<<32))+1;
  }
  values[i]=value; indices[i]=i;
 }
 for(uint stage=2;stage<=256;stage*=2)for(uint stride=stage/2;stride>0;stride/=2)
  for(uint i=0;i<256;i++) {
   uint j=i^stride;
   if(j>i) {
    bool better=values[i]>values[j]||(values[i]==values[j]&&indices[i]<indices[j]);
    if(better!=((i&stage)==0)) {
     uint64_t v=values[i];values[i]=values[j];values[j]=v;
     uint x=indices[i];indices[i]=indices[j];indices[j]=x;
    }
   }
  }
 for(uint i=0;i<160;i++) {
  uint outAt=id.x*480+i*3;
  results[outAt]=uint(values[i]);results[outAt+1]=uint(values[i]>>32);results[outAt+2]=indices[i];
 }
}
