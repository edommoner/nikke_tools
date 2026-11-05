#define portableEvents legacyGeometryV1RuntimeEvents
#include "event_runtime.slang"
#undef portableEvents
#include "coordinate_math.slang"
#include "coordinate_shape_math.slang"
#include "coordinate_arc_scalar.slang"
#include "coordinate_numeric_v1.slang"
#include "coordinate_geometry_v1.slang"
uint64_t geometryRead(uint at){return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);}
void geometryWrite(uint at,uint64_t value){results[at]=uint(value);results[at+1]=uint(value>>32);}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*24,output=id.x*4160;for(uint i=0;i<4160;i++)results[output+i]=0;
    uint kind=commands[input+2];uint64_t x=geometryRead(input+4),y=geometryRead(input+6),r=geometryRead(input+8),w=geometryRead(input+10),h=geometryRead(input+12),rotation=geometryRead(input+14),ax=geometryRead(input+16),ay=geometryRead(input+18),rho=geometryRead(input+20),grow=geometryRead(input+22);
    bool valid=commands[input]==0x43475631U&&commands[input+1]==1&&(kind==1||kind==2)&&commands[input+3]==0;
    for(uint i=4;i<24;i+=2)valid=valid&&f64Finite(geometryRead(input+i));
    valid=valid&&!f64Less(grow,0)&&!f64Less(rho,0);
    valid=valid&&(kind==1?f64Less(0,r)&&f64Zero(w)&&f64Zero(h):f64Zero(r)&&f64Less(0,w)&&f64Less(0,h));
    if(!valid){results[output]=64;return;}
    uint64_t distance,co,si,breaks[24];uint count;CoordinateArcSet arcs;
    coordinateGeometryV1(kind,x,y,r,w,h,rotation,ax,ay,rho,grow,distance,co,si,arcs,count,breaks,valid);
    if(!valid){results[output]=64;return;}
    results[output+1]=0x43475631U;results[output+2]=1;results[output+3]=arcs.count;geometryWrite(output+4,distance);
    results[output+6]=uint(coordinateShapeContains(distance,grow));results[output+7]=count;
    geometryWrite(output+8,coordinateArcMeasure(arcs));geometryWrite(output+10,co);geometryWrite(output+12,si);
    for(uint i=0;i<arcs.count;i++){geometryWrite(output+16+i*4,arcs.start[i]);geometryWrite(output+18+i*4,arcs.end[i]);}
    for(uint i=0;i<count;i++)geometryWrite(output+4112+i*2,breaks[i]);
}
