// Deterministic profile geometry. Historical native-matrix consumers unchanged.
#ifndef PORTABLE_COORDINATE_GEOMETRY_V1
#define PORTABLE_COORDINATE_GEOMETRY_V1
uint64_t cgSub(uint64_t a,uint64_t b){return f64Add(a,b^F64_SIGN);}
uint64_t cgConstant(uint high){return uint64_t(high)<<32;}
void cgFull(out CoordinateArcSet value){coordinateArcClear(value);coordinateArcAppend(value,0,coordinateTau());}
[noinline]
void coordinateCircleArcs(uint64_t cx,uint64_t cy,uint64_t r,uint64_t rho,out CoordinateArcSet value,inout bool valid)
{
    coordinateArcClear(value);uint64_t d=coordinateHypot(cx,cy),plus=f64Add(d,rho),outer=f64Add(d,r),inner=cgSub(d,r);
    if(!f64Finite(d)||!f64Finite(plus)||!f64Finite(outer)||!f64Finite(inner)){valid=false;return;}
    if(!f64Less(0,rho)){if(!f64Less(r,d))cgFull(value);return;}
    if(!f64Less(r,plus)){cgFull(value);return;}
    if(!f64Less(rho,outer)||!f64Less(inner,rho))return;
    uint64_t numerator=cgSub(f64Add(f64Mul(rho,rho),f64Mul(d,d)),f64Mul(r,r));
    uint64_t denominator=f64Mul(f64Mul(cgConstant(0x40000000U),rho),d);
    if(!f64Finite(numerator)||!f64Finite(denominator)||f64Zero(denominator)){valid=false;return;}
    uint64_t c=f64Div(numerator,denominator),one=cgConstant(0x3ff00000U);
    if(!f64Finite(c)){valid=false;return;}
    c=f64Less(c,one^F64_SIGN)?one^F64_SIGN:f64Less(one,c)?one:c;
    uint64_t half=coordinateAcos(c);
    coordinateArcCreate(cgSub(coordinateAtan2(cy,cx),half),f64Mul(cgConstant(0x40000000U),half),value);
}
[noinline]
void coordinateHalfplaneArcs(uint64_t beta,uint64_t c,uint64_t rho,out CoordinateArcSet value,inout bool valid)
{
    coordinateArcClear(value);if(!f64Finite(c)){valid=false;return;}
    if(!f64Less(0,rho)){if(!f64Less(c,0))cgFull(value);return;}
    uint64_t s=f64Div(c,rho),one=cgConstant(0x3ff00000U);
    if(!f64Finite(s)){valid=false;return;}
    if(!f64Less(s,one)){cgFull(value);return;}if(!f64Less(one^F64_SIGN,s))return;
    uint64_t a=coordinateAcos(s);coordinateArcCreate(f64Add(beta,a),cgSub(coordinateTau(),f64Mul(cgConstant(0x40000000U),a)),value);
}
[noinline]
void coordinateRectangleArcs(uint64_t lx,uint64_t ly,uint64_t hw,uint64_t hh,uint64_t rho,out CoordinateArcSet value,inout bool valid)
{
    coordinateHalfplaneArcs(0,cgSub(hw,lx),rho,value,valid);
    uint64_t pi=cgConstant(0x400921fbU)|uint64_t(0x54442d18U),half=cgConstant(0x3ff921fbU)|uint64_t(0x54442d18U);
    for(uint i=0;i<3&&value.count!=0&&valid;i++)
    {
        uint64_t beta=i==0?pi:i==1?half:half^F64_SIGN,c=i==0?f64Add(hw,lx):i==1?cgSub(hh,ly):f64Add(hh,ly);
        CoordinateArcSet plane,next;coordinateHalfplaneArcs(beta,c,rho,plane,valid);coordinateArcIntersect(value,plane,next);value=next;
    }
}
// All literal fields checked by caller. Nonfinite intermediates fail explicitly.
[noinline]
void coordinateGeometryV1(uint kind,uint64_t x,uint64_t y,uint64_t r,uint64_t w,uint64_t h,uint64_t rotation,uint64_t ax,uint64_t ay,uint64_t rho,uint64_t grow,
    out uint64_t distance,out uint64_t co,out uint64_t si,out CoordinateArcSet arcs,out uint breakCount,out uint64_t breaks[24],out bool valid)
{
    valid=true;coordinateArcClear(arcs);breakCount=0;distance=0;co=cgConstant(0x3ff00000U);si=0;
    for(uint i=0;i<24;i++)breaks[i]=0;
    if(kind==2)coordinateSinCosDegrees(rotation,si,co);
    uint64_t dx=cgSub(ax,x),dy=cgSub(ay,y),two=cgConstant(0x40000000U);
    if(!f64Finite(dx)||!f64Finite(dy)){valid=false;return;}
    if(kind==1)
    {
        uint64_t d=coordinateHypot(dx,dy),radius=f64Add(r,grow);
        distance=coordinateShapeMax(0,cgSub(d,r));
        if(!f64Finite(d)||!f64Finite(distance)||!f64Finite(radius)){valid=false;return;}
        coordinateCircleArcs(cgSub(x,ax),cgSub(y,ay),radius,rho,arcs,valid);
        breaks[0]=f64Abs(cgSub(d,radius));breaks[1]=f64Add(d,radius);breakCount=2;
    }
    else
    {
        uint64_t lx=f64Add(f64Mul(dx,co),f64Mul(dy,si)),ly=f64Add(f64Mul(dx^F64_SIGN,si),f64Mul(dy,co));
        uint64_t hw=f64Div(w,two),hh=f64Div(h,two),ew=f64Add(hw,grow),eh=f64Add(hh,grow);
        if(!f64Finite(lx)||!f64Finite(ly)||!f64Finite(ew)||!f64Finite(eh)){valid=false;return;}
        distance=coordinateHypot(coordinateShapeMax(cgSub(f64Abs(lx),hw),0),coordinateShapeMax(cgSub(f64Abs(ly),hh),0));
        if(!f64Finite(distance)){valid=false;return;}
        coordinateRectangleArcs(lx,ly,ew,hh,rho,arcs,valid);
        if(f64Less(0,grow)&&valid)
        {
            CoordinateArcSet extra;coordinateRectangleArcs(lx,ly,hw,eh,rho,extra,valid);
            for(uint j=0;j<extra.count;j++)coordinateArcInsert(arcs,extra.start[j],extra.end[j]);arcs.overflow=arcs.overflow||extra.overflow;
            for(uint corner=0;corner<4&&valid;corner++)
            {
                uint64_t cx=(corner&1)!=0?hw^F64_SIGN:hw,cy=(corner&2)!=0?hh^F64_SIGN:hh;
                coordinateCircleArcs(cgSub(cx,lx),cgSub(cy,ly),grow,rho,extra,valid);
                for(uint j=0;j<extra.count;j++)coordinateArcInsert(arcs,extra.start[j],extra.end[j]);arcs.overflow=arcs.overflow||extra.overflow;
            }
        }
        if(!f64Zero(rotation)&&valid)
        {
            uint64_t deg=cgConstant(0x40768000U),scale=cgConstant(0x3f91df46U)|uint64_t(0xa2529d39U);
            uint64_t by=f64Mul(coordinatePositiveModulo(f64Abs(rotation),deg),scale)^(rotation&F64_SIGN);
            CoordinateArcSet shifted;coordinateArcShift(arcs,by,shifted);arcs=shifted;
        }
        for(uint shape=0;shape<2;shape++)
        {
            uint64_t a=shape==0?ew:hw,b=shape==0?hh:eh;
            breaks[breakCount++]=f64Abs(cgSub(a,lx));breaks[breakCount++]=f64Abs(f64Add(a,lx));
            breaks[breakCount++]=f64Abs(cgSub(b,ly));breaks[breakCount++]=f64Abs(f64Add(b,ly));
            for(uint sx=0;sx<2;sx++)for(uint sy=0;sy<2;sy++)breaks[breakCount++]=coordinateHypot(cgSub(sx!=0?a^F64_SIGN:a,lx),cgSub(sy!=0?b^F64_SIGN:b,ly));
        }
        if(f64Less(0,grow))for(uint sx=0;sx<2;sx++)for(uint sy=0;sy<2;sy++)
        {uint64_t d=coordinateHypot(cgSub(sx!=0?hw^F64_SIGN:hw,lx),cgSub(sy!=0?hh^F64_SIGN:hh,ly));breaks[breakCount++]=f64Abs(cgSub(d,grow));breaks[breakCount++]=f64Add(d,grow);}
    }
    for(uint i=0;i<breakCount;i++)if(!f64Finite(breaks[i]))valid=false;
    for(uint i=0;i<arcs.count;i++)if(!f64Finite(arcs.start[i])||!f64Finite(arcs.end[i]))valid=false;
    valid=valid&&!arcs.overflow;
}
#endif
