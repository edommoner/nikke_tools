// Generated canonical arcs with invariant prepared frame values.
void coordinatePreparedAssign(inout CoordinateArcSet destination,inout CoordinateArcSet source){destination.count=source.count;destination.overflow=source.overflow;for(uint i=0;i<source.count;i++){destination.start[i]=source.start[i];destination.end[i]=source.end[i];}}
[noinline]
void coordinatePreparedIntersect(inout CoordinateArcSet a,inout CoordinateArcSet b,out CoordinateArcSet value)
{
    coordinateArcClear(value);uint i=0,j=0;
    while(i<a.count&&j<b.count)
    {
        uint64_t s=f64Less(a.start[i],b.start[j])?b.start[j]:a.start[i];
        uint64_t e=f64Less(b.end[j],a.end[i])?b.end[j]:a.end[i];
        if(f64Less(s,e))coordinateArcAppend(value,s,e);
        if(f64Less(a.end[i],b.end[j]))i++;else j++;
    }
    value.overflow=value.overflow||a.overflow||b.overflow;
}
[noinline]
void coordinatePreparedShift(inout CoordinateArcSet a,uint64_t by,out CoordinateArcSet value)
{
    coordinateArcClear(value);
    for(uint i=0;i<a.count;i++)
    {
        CoordinateArcSet fragment;
        coordinateArcCreate(f64Add(a.start[i],by),f64Add(a.end[i],a.start[i]^F64_SIGN),fragment);
        for(uint j=0;j<fragment.count&&!value.overflow;j++)coordinateArcInsert(value,fragment.start[j],fragment.end[j]);
        value.overflow=value.overflow||fragment.overflow;
        if(value.overflow)return;
    }
    value.overflow=value.overflow||a.overflow;
}
[noinline]
void coordinatePreparedRectangleArcs(uint64_t lx,uint64_t ly,uint64_t hw,uint64_t hh,uint64_t rho,out CoordinateArcSet value,inout bool valid)
{
    coordinateHalfplaneArcs(0,cgSub(hw,lx),rho,value,valid);
    uint64_t pi=cgConstant(0x400921fbU)|uint64_t(0x54442d18U),half=cgConstant(0x3ff921fbU)|uint64_t(0x54442d18U);
    for(uint i=0;i<3&&value.count!=0&&valid;i++)
    {
        uint64_t beta=i==0?pi:i==1?half:half^F64_SIGN,c=i==0?f64Add(hw,lx):i==1?cgSub(hh,ly):f64Add(hh,ly);
        CoordinateArcSet plane,next;coordinateHalfplaneArcs(beta,c,rho,plane,valid);coordinatePreparedIntersect(value,plane,next);coordinatePreparedAssign(value,next);
    }
}
[noinline]
void coordinatePreparedCircleArcs(uint64_t cx,uint64_t cy,uint64_t d,uint64_t r,uint64_t rho,out CoordinateArcSet value,inout bool valid)
{
    coordinateArcClear(value);uint64_t plus=f64Add(d,rho),outer=f64Add(d,r),inner=cgSub(d,r);
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
void coordinatePreparedShapeArcs(uint kind,uint64_t cx,uint64_t cy,uint64_t lx,uint64_t ly,uint64_t hw,uint64_t hh,uint64_t by,uint64_t d,uint64_t cornerDistance[4],uint64_t rotation,uint64_t radius,uint64_t rho,uint64_t grow,out CoordinateArcSet arcs,out bool valid)
{
    valid=true;coordinateArcClear(arcs);
    if(kind==1){coordinatePreparedCircleArcs(cx,cy,d,f64Add(radius,grow),rho,arcs,valid);return;}
    uint64_t ew=f64Add(hw,grow),eh=f64Add(hh,grow);
        coordinatePreparedRectangleArcs(lx,ly,ew,hh,rho,arcs,valid);
        if(f64Less(0,grow)&&valid)
        {
            CoordinateArcSet extra;coordinatePreparedRectangleArcs(lx,ly,hw,eh,rho,extra,valid);
            for(uint j=0;j<extra.count;j++)coordinateArcInsert(arcs,extra.start[j],extra.end[j]);arcs.overflow=arcs.overflow||extra.overflow;
            for(uint corner=0;corner<4&&valid;corner++)
            {
                uint64_t cx=(corner&1)!=0?hw^F64_SIGN:hw,cy=(corner&2)!=0?hh^F64_SIGN:hh;
                coordinatePreparedCircleArcs(cgSub(cx,lx),cgSub(cy,ly),cornerDistance[corner],grow,rho,extra,valid);
                for(uint j=0;j<extra.count;j++)coordinateArcInsert(arcs,extra.start[j],extra.end[j]);arcs.overflow=arcs.overflow||extra.overflow;
            }
        }
        if(!f64Zero(rotation)&&valid)
        {
            CoordinateArcSet shifted;coordinatePreparedShift(arcs,by,shifted);coordinatePreparedAssign(arcs,shifted);
        }

    valid=valid&&!arcs.overflow;
}
