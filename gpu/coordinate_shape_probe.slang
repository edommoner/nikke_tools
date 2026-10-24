StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "binary64.slang"
#include "coordinate_math.slang"
#include "coordinate_shape_math.slang"
uint64_t shapeRead(uint at){return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint at=1+id.x*24,outAt=id.x*8;for(uint i=0;i<8;i++)results[outAt+i]=0;
    uint kind=commands[at+2];bool valid=commands[at]==0x43534831U&&commands[at+1]==1&&(kind==1||kind==2)&&commands[at+3]==0;
    for(uint j=4;j<24;j+=2)valid=valid&&f64Finite(shapeRead(at+j));
    uint64_t radius=shapeRead(at+8),width=shapeRead(at+10),height=shapeRead(at+12),co=shapeRead(at+14),si=shapeRead(at+16),grow=shapeRead(at+22);
    valid=valid&&coordinateShapeMatrixValid(kind,co,si)&&!f64Less(grow,0);
    if(kind==1)valid=valid&&f64Less(0,radius)&&f64Zero(width)&&f64Zero(height);
    else valid=valid&&f64Zero(radius)&&f64Less(0,width)&&f64Less(0,height);
    if(!valid){results[outAt]=64;return;}
    uint64_t d=coordinateShapeDistance(kind,shapeRead(at+4),shapeRead(at+6),radius,width,height,co,si,shapeRead(at+18),shapeRead(at+20));
    results[outAt+1]=0x43534831U;results[outAt+2]=uint(d);results[outAt+3]=uint(d>>32);results[outAt+4]=uint(coordinateShapeContains(d,grow));
}
