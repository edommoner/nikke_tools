// Reuse the existing numeric Sum directly; no duplicate compensation formula.
#define portableEvents legacyArcScalarRuntimeEvents
#include "event_runtime.slang"
#undef portableEvents
#include "coordinate_arc_scalar.slang"
uint64_t arcScalarRead(uint at){return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*2056,output=id.x*4104;for(uint i=0;i<4104;i++)results[output+i]=0;
    uint op=commands[input+2],count=commands[input+3];uint64_t x=arcScalarRead(input+4),y=arcScalarRead(input+6);
    bool valid=commands[input]==0x43415331U&&commands[input+1]==1&&(op>=1&&op<=4||op==8||op==9)&&count<=512&&f64Finite(x)&&f64Finite(y);
    if(op<=2&&count!=0||op==1&&!f64Zero(y)||op==3&&(!f64Zero(x)||!f64Zero(y))||op==4&&!f64Zero(y))valid=false;
    CoordinateArcSet a,value;coordinateArcClear(a);
    for(uint i=0;i<512&&valid;i++)
    {
        uint at=input+8+i*4;uint64_t s=arcScalarRead(at),e=arcScalarRead(at+2);
        if(i>=count){if(s!=0||e!=0)valid=false;continue;}
        if(!f64Finite(s)||!f64Finite(e)||f64Less(s,0)||f64Less(e,s)||f64Less(coordinateTau(),e)||i>0&&f64Less(s,a.end[i-1])){valid=false;break;}
        coordinateArcAppend(a,s,e);
    }
    if(!valid){results[output]=64;return;}
    coordinateArcClear(value);uint64_t scalar=0;
    if(op==1)scalar=coordinatePositiveModulo(x,coordinateTau());
    else
    {
        if(op==2)coordinateArcCreate(x,y,value);
        else if(op==3)value=a;
        else if(op==4)coordinateArcShift(a,x,value);
        else
        {
            CoordinateArcSet cover;coordinateArcCreate(x,y,cover);
            if(op==8)coordinateArcSubtract(a,cover,value);
            else coordinateArcIntersect(a,cover,value);
        }
        scalar=coordinateArcMeasure(value);
    }
    if(value.overflow){results[output]=64;return;}
    results[output+1]=0x43415331U;results[output+2]=value.count;results[output+4]=uint(scalar);results[output+5]=uint(scalar>>32);
    for(uint i=0;i<value.count;i++)
    {results[output+8+i*4]=uint(value.start[i]);results[output+9+i*4]=uint(value.start[i]>>32);results[output+10+i*4]=uint(value.end[i]);results[output+11+i*4]=uint(value.end[i]>>32);}
}
