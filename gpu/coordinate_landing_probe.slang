#define portableEvents legacyLandingV1Events
#include "event_runtime.slang"
#undef portableEvents
#include "coordinate_math.slang"
#include "coordinate_shape_math.slang"
#include "coordinate_arc_scalar.slang"
#include "coordinate_numeric_v1.slang"
#include "coordinate_geometry_v1.slang"
#include "coordinate_power_v1.slang"
#include "coordinate_quadrature_v1.slang"
#include "coordinate_landing_v1.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*CL_INPUT,output=id.x*CL_OUTPUT;for(uint i=0;i<CL_OUTPUT;i++)results[output+i]=0;
    uint n=commands[input+2],core=commands[input+3];bool valid=commands[input]==CL_MAGIC&&commands[input+1]==1&&n<=CL_TARGETS&&core<=1&&commands[input+14]==0&&commands[input+15]==0;
    for(uint i=4;i<14;i+=2)if(!f64Finite(clRead(input+i)))valid=false;
    uint64_t grow=clRead(input+10),k=clRead(input+12);
    valid=valid&&!f64Less(grow,0)&&!f64Less(k,CL_MIN_K)&&!f64Less(CL_MAX_K,k);
    for(uint i=0;i<CL_SHAPES;i++)
    {
        uint at=clShapeAt(input,i);bool used=i<n||(i==CL_TARGETS&&core!=0);
        if(used)valid=valid&&clShapeValid(at);
        else for(uint j=0;j<CL_SHAPE_WORDS;j++)if(commands[at+j]!=0)valid=false;
    }
    if(valid)valid=coordinateLandingV1(input,output);
    if(!valid){for(uint i=0;i<CL_OUTPUT;i++)results[output+i]=0;results[output]=64;}
}
