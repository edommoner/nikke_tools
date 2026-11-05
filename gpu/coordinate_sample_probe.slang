#define portableEvents legacyCoordinateSampleEvents
#include "event_runtime.slang"
#undef portableEvents
#include "coordinate_math.slang"
#include "coordinate_arc_scalar.slang"
#include "coordinate_numeric_v1.slang"
#include "coordinate_power_v1.slang"
#include "coordinate_sample_v1.slang"
uint64_t csRead(uint at){return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);}
void csWrite(uint at,uint64_t v){results[at]=uint(v);results[at+1]=uint(v>>32);}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*24,output=id.x*1024;
    for(uint i=0;i<1024;i++)results[output+i]=0;
    uint mode=commands[input+2],count=commands[input+3],skip=commands[input+6],bound=commands[input+7],critical=commands[input+16];
    uint64_t ax=csRead(input+8),ay=csRead(input+10),radius=csRead(input+12),k=csRead(input+14);
    bool valid=commands[input]==0x43535631U&&commands[input+1]==1&&mode<=2&&count>=1&&count<=16&&skip<=1300&&bound<=128&&critical<=1&&validCoordinateSample(ax,ay,radius,k);
    for(uint i=17;i<24;i++)if(commands[input+i]!=0)valid=false;
    if(!valid){results[output]=64;return;}
    uint rng=output+16;mtSeed(rng,csRead(input+4));
    for(uint i=0;i<skip;i++)mtNext(rng);
    for(uint i=0;i<count;i++)
    {
        bool angle=mode==1||mode==2&&(i%2)!=0;
        uint64_t px,py,u,v;uint status;coordinateSamplePoint(rng,ax,ay,radius,k,angle,px,py,u,v,status);
        if(status!=0){for(uint j=0;j<1024;j++)results[output+j]=0;results[output]=64;return;}
        uint at=output+656+i*16;csWrite(at,px);csWrite(at+2,py);csWrite(at+4,u);csWrite(at+6,v);
        if(critical!=0)csWrite(at+8,coordinateRandom53(rng));
        if(bound!=0)results[at+10]=mtBelow(rng,bound);
        results[at+11]=results[rng];results[at+12]=results[rng+1];results[at+13]=uint(angle);
    }
    results[output+1]=0x43535631U;results[output+2]=1;results[output+3]=count;
}
