// Ordered expected landing on the deterministic common numeric contract.
#include "coordinate_landing_layout.slang"
#include "coordinate_landing_arc_refs.slang"
uint64_t clRead(uint at){return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);}
void clWrite(uint at,uint64_t value){results[at]=uint(value);results[at+1]=uint(value>>32);}
uint64_t clCutRead(uint output,uint index){uint at=output+CL_CUT_OFFSET+index*2;return uint64_t(results[at])|(uint64_t(results[at+1])<<32);}
void clCutWrite(uint output,uint index,uint64_t value){clWrite(output+CL_CUT_OFFSET+index*2,value);}
uint clShapeAt(uint input,uint index){return input+CL_HEADER+index*CL_SHAPE_WORDS;}
bool clShapeValid(uint at)
{
    uint kind=commands[at];if((kind!=1&&kind!=2)||commands[at+1]!=0||commands[at+14]!=0||commands[at+15]!=0)return false;
    for(uint i=2;i<14;i+=2)if(!f64Finite(clRead(at+i)))return false;
    uint64_t r=clRead(at+6),w=clRead(at+8),h=clRead(at+10);
    return kind==1?f64Less(0,r)&&f64Zero(w)&&f64Zero(h):f64Zero(r)&&f64Less(0,w)&&f64Less(0,h);
}
#include "coordinate_prepared_arcs_v1.slang"
uint64_t clPreparedRead(uint output,uint index,uint lane){return clCutRead(output,(CL_PREP_OFFSET-CL_CUT_OFFSET)/2+index*CL_PREP_WORDS/2+lane);}
void clPreparedWrite(uint output,uint index,uint lane,uint64_t value){clWrite(output+CL_PREP_OFFSET+index*CL_PREP_WORDS+lane*2,value);}
[noinline]
void clPrepare(uint input,uint output,uint index)
{
    uint at=clShapeAt(input,index),kind=commands[at];uint64_t x=clRead(at+2),y=clRead(at+4),rotation=clRead(at+12);
    uint64_t dx=cgSub(clRead(input+4),x),dy=cgSub(clRead(input+6),y),cx=cgSub(x,clRead(input+4)),cy=cgSub(y,clRead(input+6));
    uint64_t co=ONE,si=0;if(kind==2)coordinateSinCosDegrees(rotation,si,co);
    uint64_t lx=f64Add(f64Mul(dx,co),f64Mul(dy,si)),ly=f64Add(f64Mul(dx^F64_SIGN,si),f64Mul(dy,co));
    uint64_t two=uint64_t(0x40000000U)<<32,hw=f64Div(clRead(at+8),two),hh=f64Div(clRead(at+10),two);
    uint64_t by=f64Mul(coordinatePositiveModulo(f64Abs(rotation),uint64_t(0x40768000U)<<32),(uint64_t(0x3f91df46U)<<32)|uint64_t(0xa2529d39U))^(rotation&F64_SIGN);
    clPreparedWrite(output,index,0,cx);clPreparedWrite(output,index,1,cy);clPreparedWrite(output,index,2,lx);clPreparedWrite(output,index,3,ly);
    clPreparedWrite(output,index,4,hw);clPreparedWrite(output,index,5,hh);clPreparedWrite(output,index,6,by);clPreparedWrite(output,index,7,coordinateHypot(cx,cy));
    for(uint corner=0;corner<4;corner++)clPreparedWrite(output,index,8+corner,coordinateHypot(cgSub((corner&1)!=0?hw^F64_SIGN:hw,lx),cgSub((corner&2)!=0?hh^F64_SIGN:hh,ly)));
}
[noinline]
void clArcs(uint input,uint output,uint index,uint64_t rho,uint64_t grow,out CoordinateArcSet arcs,out bool valid)
{
    uint at=clShapeAt(input,index);uint64_t corners[4];for(uint i=0;i<4;i++)corners[i]=clPreparedRead(output,index,8+i);
    coordinatePreparedShapeArcs(commands[at],clPreparedRead(output,index,0),clPreparedRead(output,index,1),clPreparedRead(output,index,2),clPreparedRead(output,index,3),clPreparedRead(output,index,4),clPreparedRead(output,index,5),clPreparedRead(output,index,6),clPreparedRead(output,index,7),corners,clRead(at+12),clRead(at+6),rho,grow,arcs,valid);
}
[noinline]
void clGeometry(uint input,uint shape,uint64_t rho,uint64_t grow,out uint64_t distance,out CoordinateArcSet arcs,out uint count,out uint64_t breaks[24],out bool valid)
{
    uint at=clShapeAt(input,shape);uint64_t co,si;
    coordinateGeometryV1(commands[at],clRead(at+2),clRead(at+4),clRead(at+6),clRead(at+8),clRead(at+10),clRead(at+12),clRead(input+4),clRead(input+6),rho,grow,distance,co,si,arcs,count,breaks,valid);
}
[noinline]
void clCutAdd(uint output,inout uint count,uint64_t value,inout bool valid)
{
    uint at=0;while(at<count&&f64Less(clCutRead(output,at),value))at++;
    if(at<count&&f64Equal(clCutRead(output,at),value))return;
    if(count>=CL_CUTS){valid=false;return;}
    for(uint j=count;j>at;j--)clCutWrite(output,j,clCutRead(output,j-1));clCutWrite(output,at,value);count++;
}
[noinline]
void clShapeCuts(uint input,uint index,uint64_t grow,uint64_t radius,uint64_t k,uint output,inout uint cutCount,inout bool valid)
{
    uint64_t distance,breaks[24];uint count;CoordinateArcSet arcs;bool ok;
    clGeometry(input,index,0,grow,distance,arcs,count,breaks,ok);if(!ok){valid=false;return;}
    for(uint i=0;i<count&&valid;i++)if(f64Less(0,breaks[i])&&f64Less(breaks[i],radius))
    {
        uint status;uint64_t cut=coordinateUnitPower(f64Div(breaks[i],radius),k,status);
        if(status!=0){valid=false;return;}clCutAdd(output,cutCount,cut,valid);
    }
}
[noinline]
bool coordinateLandingV1(uint input,uint output)
{
    uint n=commands[input+2],corePresent=commands[input+3];uint64_t radius=larger(clRead(input+8),CL_MIN_RADIUS),grow=clRead(input+10),k=clRead(input+12);
    bool near[CL_TARGETS];uint nearCount=0;bool useCore=false,valid=true;uint64_t front[CL_TARGETS],reach[CL_TARGETS];
    for(uint i=0;i<CL_TARGETS;i++){near[i]=false;front[i]=0;reach[i]=0;}
    uint64_t distance,breaks[24];uint count;CoordinateArcSet arcs;bool ok;
    for(uint i=0;i<n;i++)
    {
        clGeometry(input,i,0,0,distance,arcs,count,breaks,ok);if(!ok)return false;
        near[i]=!f64Less(f64Add(radius,grow),distance);if(near[i])nearCount++;
    }
    if(corePresent!=0){clGeometry(input,CL_TARGETS,0,0,distance,arcs,count,breaks,ok);if(!ok)return false;useCore=!f64Less(radius,distance);}
    results[output+1]=CL_MAGIC;results[output+2]=1;results[output+3]=n;results[output+10]=nearCount;results[output+11]=uint(useCore);
    if(nearCount==0&&!useCore){results[output+12]=1;return true;}
    uint coreAt=clShapeAt(input,CL_TARGETS);
    if(nearCount==0&&commands[coreAt]==1&&f64Equal(clRead(coreAt+2),clRead(input+4))&&f64Equal(clRead(coreAt+4),clRead(input+6)))
    {
        uint status;uint64_t value=coordinateUnitPower(smaller(ONE,f64Div(clRead(coreAt+6),radius)),k,status);
        if(status!=0)return false;clWrite(output+4,value);clWrite(output+6,value);results[output+12]=2;return true;
    }
    uint cutCount=2;clCutWrite(output,0,0);clCutWrite(output,1,ONE);
    for(uint i=0;i<n&&valid;i++)if(near[i])
    {
        clShapeCuts(input,i,0,radius,k,output,cutCount,valid);
        if(f64Less(0,grow))clShapeCuts(input,i,grow,radius,k,output,cutCount,valid);
    }
    if(useCore&&valid)clShapeCuts(input,CL_TARGETS,0,radius,k,output,cutCount,valid);
    if(!valid)return false;
    for(uint i=0;i<n;i++)if(near[i])clPrepare(input,output,i);
    if(useCore)clPrepare(input,output,CL_TARGETS);
    uint nodeCount=0;uint64_t inverse=f64Div(ONE,k),coreOpen=0,coreUnder=0,two=uint64_t(0x40000000U)<<32;
    for(uint u=0;u+1<cutCount;u++)
    {
        uint64_t span=cgSub(clCutRead(output,u+1),clCutRead(output,u));if(!f64Less(CL_MIN_SPAN,span))continue;
        uint64_t mid=f64Div(f64Add(clCutRead(output,u),clCutRead(output,u+1)),two),half=f64Div(span,two);
        for(uint g=0;g<10;g++)
        {
            uint status;uint64_t weight=f64Div(f64Mul(coordinateGaussWeight(g),half),coordinateTau());
            uint64_t rho=f64Mul(radius,coordinateUnitPower(f64Add(mid,f64Mul(half,coordinateGaussX(g))),inverse,status));
            if(status!=0)return false;nodeCount++;CoordinateArcSet covered;coordinateArcClear(covered);
            for(uint i=0;i<n;i++)if(near[i])
            {
                clArcs(input,output,i,rho,0,arcs,ok);if(!ok)return false;
                if(arcs.count!=0)
                {
                    CoordinateArcSet visible;coordinateLandingSubtract(arcs,covered,visible);
                    front[i]=f64Add(front[i],f64Mul(weight,coordinateLandingMeasure(visible)));
                    for(uint j=0;j<arcs.count;j++)coordinateArcInsert(covered,arcs.start[j],arcs.end[j]);
                    if(visible.overflow||covered.overflow)return false;
                }
                if(f64Less(0,grow))
                {
                    clArcs(input,output,i,rho,grow,arcs,ok);if(!ok)return false;
                    reach[i]=f64Add(reach[i],f64Mul(weight,coordinateLandingMeasure(arcs)));
                }
            }
            if(useCore)
            {
                clArcs(input,output,CL_TARGETS,rho,0,arcs,ok);if(!ok)return false;
                if(arcs.count!=0)
                {
                    coreUnder=f64Add(coreUnder,f64Mul(weight,coordinateLandingMeasure(arcs)));
                    CoordinateArcSet visible;coordinateLandingSubtract(arcs,covered,visible);if(visible.overflow)return false;
                    coreOpen=f64Add(coreOpen,f64Mul(weight,coordinateLandingMeasure(visible)));
                }
            }
        }
    }
    if(!f64Finite(coreOpen)||!f64Finite(coreUnder))return false;
    clWrite(output+4,smaller(ONE,larger(0,coreOpen)));clWrite(output+6,smaller(ONE,larger(0,coreUnder)));
    for(uint i=0;i<n;i++)
    {if(!f64Finite(front[i])||!f64Finite(reach[i]))return false;clWrite(output+16+i*2,smaller(ONE,larger(0,front[i])));clWrite(output+16+CL_TARGETS*2+i*2,smaller(ONE,larger(0,reach[i])));}
    results[output+8]=cutCount;results[output+9]=nodeCount;
    return true;
}
