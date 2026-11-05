#define portableEvents legacyCommonNumericRuntimeEvents
#include "event_runtime.slang"
#undef portableEvents
#include "coordinate_math.slang"
#include "coordinate_arc_scalar.slang"
#include "coordinate_numeric_v1.slang"
uint64_t numericRead(uint at){return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*12,output=id.x*16;for(uint i=0;i<16;i++)results[output+i]=0;
    uint op=commands[input+2];uint64_t a=numericRead(input+4),b=numericRead(input+6);
    bool valid=commands[input]==0x434e5631U&&commands[input+1]==1&&op>=1&&op<=5&&commands[input+3]==0&&f64Finite(a)&&f64Finite(b);
    for(uint i=8;i<12;i++)if(commands[input+i]!=0)valid=false;
    if(op!=3&&!f64Zero(b))valid=false;
    if(op==2&&f64Abs(a)>coordinateTau()||op==4&&f64Abs(a)>ONE||op==5&&(a&F64_SIGN)!=0&&!f64Zero(a))valid=false;
    if(!valid){results[output]=64;return;}
    uint64_t x=0,y=0;
    if(op==1)coordinateSinCosDegrees(a,x,y);
    else if(op==2)coordinateSinCosRadians(a,x,y);
    else if(op==3)x=coordinateAtan2(a,b);
    else if(op==4)x=coordinateAcos(a);
    else x=coordinateSqrt(a);
    results[output+1]=0x434e5631U;results[output+2]=op;results[output+3]=1;
    results[output+4]=uint(x);results[output+5]=uint(x>>32);results[output+6]=uint(y);results[output+7]=uint(y>>32);
}
