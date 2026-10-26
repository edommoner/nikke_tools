// Generated canonical bodies with resource views; arithmetic and iteration order retained.
[noinline]
void arena_coordinateArcCreate(uint64_t start,uint64_t length,inout ArcArenaView value)
{
    arena_coordinateArcClear(value);uint64_t tau=coordinateTau();
    if(!f64Less(0,length))return;
    uint64_t epsilon=uint64_t(0x3d719799U)<<32|uint64_t(0x812dea11U); // 1e-12
    if(!f64Less(length,f64Add(tau,epsilon^F64_SIGN))){arena_coordinateArcAppend(value,0,tau);return;}
    uint64_t a=coordinatePositiveModulo(start,tau),b=f64Add(a,length);
    if(!f64Less(tau,b))arena_coordinateArcAppend(value,a,b);
    else{arena_coordinateArcAppend(value,0,f64Add(b,tau^F64_SIGN));arena_coordinateArcAppend(value,a,tau);}
}
[noinline]
uint64_t arena_coordinateArcMeasure(inout ArcArenaView value)
{
    Sum sum={};
    for(uint i=0;i<value.count;i++)addSum(sum,f64Add(value.end[i],value.start[i]^F64_SIGN));
    // Same finite Neumaier finalization already used by periodicSkillInterval.
    return f64Finite(sum.correction)&&!f64Zero(sum.correction)?f64Add(sum.total,sum.correction):sum.total;
}
[noinline]
void arena_coordinateArcInsert(inout ArcArenaView value,uint64_t start,uint64_t end)
{
    // Stable lexicographic insertion followed by the same touching merge as
    // sorted(value+[interval]). Only active entries move; no 1024-row copies.
    uint position=0;
    while(position<value.count&&(f64Less(value.start[position],start)||
        f64Equal(value.start[position],start)&&!f64Less(end,value.end[position])))position++;
    uint destination=position;
    if(position>0&&!f64Less(value.end[position-1],start))
    {
        destination=position-1;start=value.start[destination];
        if(f64Less(end,value.end[destination]))end=value.end[destination];
    }
    uint after=position;
    while(after<value.count&&!f64Less(end,value.start[after]))
    {if(f64Less(end,value.end[after]))end=value.end[after];after++;}
    uint removed=after-destination,nextCount=value.count+1-removed;
    if(nextCount>COORDINATE_ARC_CAPACITY){value.overflow=true;return;}
    if(removed==0)
    {for(uint at=value.count;at>destination;at--){value.start[at]=value.start[at-1];value.end[at]=value.end[at-1];}}
    else if(removed>1)
    {for(uint at=after;at<value.count;at++){value.start[at-removed+1]=value.start[at];value.end[at-removed+1]=value.end[at];}}
    value.start[destination]=start;value.end[destination]=end;value.count=nextCount;
}
[noinline]
void arena_coordinateArcShift(inout ArcArenaView a,uint64_t by,inout ArcArenaView value)
{
    if(!arcArenaDistinctOne(a,value))return;
    arena_coordinateArcClear(value);
    for(uint i=0;i<a.count;i++)
    {
        ArcArenaView fragment=arcArenaSibling(value,7U);
        arena_coordinateArcCreate(f64Add(a.start[i],by),f64Add(a.end[i],a.start[i]^F64_SIGN),fragment);
        for(uint j=0;j<fragment.count&&!value.overflow;j++)arena_coordinateArcInsert(value,fragment.start[j],fragment.end[j]);
        value.overflow=value.overflow||fragment.overflow;
        if(value.overflow)return;
    }
    value.overflow=value.overflow||a.overflow;
}
void arena_cgFull(inout ArcArenaView value){arena_coordinateArcClear(value);arena_coordinateArcAppend(value,0,coordinateTau());}
[noinline]
void arena_coordinateCircleArcs(uint64_t cx,uint64_t cy,uint64_t r,uint64_t rho,inout ArcArenaView value,inout bool valid)
{
    arena_coordinateArcClear(value);uint64_t d=coordinateHypot(cx,cy),plus=f64Add(d,rho),outer=f64Add(d,r),inner=cgSub(d,r);
    if(!f64Finite(d)||!f64Finite(plus)||!f64Finite(outer)||!f64Finite(inner)){valid=false;return;}
    if(!f64Less(0,rho)){if(!f64Less(r,d))arena_cgFull(value);return;}
    if(!f64Less(r,plus)){arena_cgFull(value);return;}
    if(!f64Less(rho,outer)||!f64Less(inner,rho))return;
    uint64_t numerator=cgSub(f64Add(f64Mul(rho,rho),f64Mul(d,d)),f64Mul(r,r));
    uint64_t denominator=f64Mul(f64Mul(cgConstant(0x40000000U),rho),d);
    if(!f64Finite(numerator)||!f64Finite(denominator)||f64Zero(denominator)){valid=false;return;}
    uint64_t c=f64Div(numerator,denominator),one=cgConstant(0x3ff00000U);
    if(!f64Finite(c)){valid=false;return;}
    c=f64Less(c,one^F64_SIGN)?one^F64_SIGN:f64Less(one,c)?one:c;
    uint64_t half=coordinateAcos(c);
    arena_coordinateArcCreate(cgSub(coordinateAtan2(cy,cx),half),f64Mul(cgConstant(0x40000000U),half),value);
}
[noinline]
void arena_coordinateHalfplaneArcs(uint64_t beta,uint64_t c,uint64_t rho,inout ArcArenaView value,inout bool valid)
{
    arena_coordinateArcClear(value);if(!f64Finite(c)){valid=false;return;}
    if(!f64Less(0,rho)){if(!f64Less(c,0))arena_cgFull(value);return;}
    uint64_t s=f64Div(c,rho),one=cgConstant(0x3ff00000U);
    if(!f64Finite(s)){valid=false;return;}
    if(!f64Less(s,one)){arena_cgFull(value);return;}if(!f64Less(one^F64_SIGN,s))return;
    uint64_t a=coordinateAcos(s);arena_coordinateArcCreate(f64Add(beta,a),cgSub(coordinateTau(),f64Mul(cgConstant(0x40000000U),a)),value);
}
[noinline]
void arena_coordinateRectangleArcs(uint64_t lx,uint64_t ly,uint64_t hw,uint64_t hh,uint64_t rho,inout ArcArenaView value,inout bool valid)
{
    arena_coordinateHalfplaneArcs(0,cgSub(hw,lx),rho,value,valid);
    uint64_t pi=cgConstant(0x400921fbU)|uint64_t(0x54442d18U),half=cgConstant(0x3ff921fbU)|uint64_t(0x54442d18U);
    for(uint i=0;i<3&&value.count!=0&&valid;i++)
    {
        uint64_t beta=i==0?pi:i==1?half:half^F64_SIGN,c=i==0?f64Add(hw,lx):i==1?cgSub(hh,ly):f64Add(hh,ly);
        ArcArenaView plane=arcArenaSibling(value,5U),next=arcArenaSibling(value,6U);arena_coordinateHalfplaneArcs(beta,c,rho,plane,valid);arena_coordinateArcIntersect(value,plane,next);arena_coordinatePreparedAssign(value,next);
    }
}
[noinline]
void arena_coordinateGeometryV1(uint kind,uint64_t x,uint64_t y,uint64_t r,uint64_t w,uint64_t h,uint64_t rotation,uint64_t ax,uint64_t ay,uint64_t rho,uint64_t grow,
    out uint64_t distance,out uint64_t co,out uint64_t si,inout ArcArenaView arcs,out uint breakCount,out uint64_t breaks[24],out bool valid)
{
    valid=true;arena_coordinateArcClear(arcs);breakCount=0;distance=0;co=cgConstant(0x3ff00000U);si=0;
    for(uint i=0;i<24;i++)breaks[i]=0;
    if(kind==2)coordinateSinCosDegrees(rotation,si,co);
    uint64_t dx=cgSub(ax,x),dy=cgSub(ay,y),two=cgConstant(0x40000000U);
    if(!f64Finite(dx)||!f64Finite(dy)){valid=false;return;}
    if(kind==1)
    {
        uint64_t d=coordinateHypot(dx,dy),radius=f64Add(r,grow);
        distance=coordinateShapeMax(0,cgSub(d,r));
        if(!f64Finite(d)||!f64Finite(distance)||!f64Finite(radius)){valid=false;return;}
        arena_coordinateCircleArcs(cgSub(x,ax),cgSub(y,ay),radius,rho,arcs,valid);
        breaks[0]=f64Abs(cgSub(d,radius));breaks[1]=f64Add(d,radius);breakCount=2;
    }
    else
    {
        uint64_t lx=f64Add(f64Mul(dx,co),f64Mul(dy,si)),ly=f64Add(f64Mul(dx^F64_SIGN,si),f64Mul(dy,co));
        uint64_t hw=f64Div(w,two),hh=f64Div(h,two),ew=f64Add(hw,grow),eh=f64Add(hh,grow);
        if(!f64Finite(lx)||!f64Finite(ly)||!f64Finite(ew)||!f64Finite(eh)){valid=false;return;}
        distance=coordinateHypot(coordinateShapeMax(cgSub(f64Abs(lx),hw),0),coordinateShapeMax(cgSub(f64Abs(ly),hh),0));
        if(!f64Finite(distance)){valid=false;return;}
        arena_coordinateRectangleArcs(lx,ly,ew,hh,rho,arcs,valid);
        if(f64Less(0,grow)&&valid)
        {
            ArcArenaView extra=arcArenaSibling(arcs,3U);arena_coordinateRectangleArcs(lx,ly,hw,eh,rho,extra,valid);
            for(uint j=0;j<extra.count;j++)arena_coordinateArcInsert(arcs,extra.start[j],extra.end[j]);arcs.overflow=arcs.overflow||extra.overflow;
            for(uint corner=0;corner<4&&valid;corner++)
            {
                uint64_t cx=(corner&1)!=0?hw^F64_SIGN:hw,cy=(corner&2)!=0?hh^F64_SIGN:hh;
                arena_coordinateCircleArcs(cgSub(cx,lx),cgSub(cy,ly),grow,rho,extra,valid);
                for(uint j=0;j<extra.count;j++)arena_coordinateArcInsert(arcs,extra.start[j],extra.end[j]);arcs.overflow=arcs.overflow||extra.overflow;
            }
        }
        if(!f64Zero(rotation)&&valid)
        {
            uint64_t deg=cgConstant(0x40768000U),scale=cgConstant(0x3f91df46U)|uint64_t(0xa2529d39U);
            uint64_t by=f64Mul(coordinatePositiveModulo(f64Abs(rotation),deg),scale)^(rotation&F64_SIGN);
            ArcArenaView shifted=arcArenaSibling(arcs,4U);arena_coordinateArcShift(arcs,by,shifted);arena_coordinatePreparedAssign(arcs,shifted);
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
void arena_coordinatePreparedAssign(inout ArcArenaView destination,inout ArcArenaView source){destination.count=source.count;destination.overflow=source.overflow;for(uint i=0;i<source.count;i++){destination.start[i]=source.start[i];destination.end[i]=source.end[i];}}
[noinline]
void arena_coordinatePreparedIntersect(inout ArcArenaView a,inout ArcArenaView b,inout ArcArenaView value)
{
    if(!arcArenaDistinct(a,b,value))return;
    arena_coordinateArcClear(value);uint i=0,j=0;
    while(i<a.count&&j<b.count)
    {
        uint64_t s=f64Less(a.start[i],b.start[j])?b.start[j]:a.start[i];
        uint64_t e=f64Less(b.end[j],a.end[i])?b.end[j]:a.end[i];
        if(f64Less(s,e))arena_coordinateArcAppend(value,s,e);
        if(f64Less(a.end[i],b.end[j]))i++;else j++;
    }
    value.overflow=value.overflow||a.overflow||b.overflow;
}
[noinline]
void arena_coordinatePreparedShift(inout ArcArenaView a,uint64_t by,inout ArcArenaView value)
{
    if(!arcArenaDistinctOne(a,value))return;
    arena_coordinateArcClear(value);
    for(uint i=0;i<a.count;i++)
    {
        ArcArenaView fragment=arcArenaSibling(value,7U);
        arena_coordinateArcCreate(f64Add(a.start[i],by),f64Add(a.end[i],a.start[i]^F64_SIGN),fragment);
        for(uint j=0;j<fragment.count&&!value.overflow;j++)arena_coordinateArcInsert(value,fragment.start[j],fragment.end[j]);
        value.overflow=value.overflow||fragment.overflow;
        if(value.overflow)return;
    }
    value.overflow=value.overflow||a.overflow;
}
[noinline]
void arena_coordinatePreparedRectangleArcs(uint64_t lx,uint64_t ly,uint64_t hw,uint64_t hh,uint64_t rho,inout ArcArenaView value,inout bool valid)
{
    arena_coordinateHalfplaneArcs(0,cgSub(hw,lx),rho,value,valid);
    uint64_t pi=cgConstant(0x400921fbU)|uint64_t(0x54442d18U),half=cgConstant(0x3ff921fbU)|uint64_t(0x54442d18U);
    for(uint i=0;i<3&&value.count!=0&&valid;i++)
    {
        uint64_t beta=i==0?pi:i==1?half:half^F64_SIGN,c=i==0?f64Add(hw,lx):i==1?cgSub(hh,ly):f64Add(hh,ly);
        ArcArenaView plane=arcArenaSibling(value,5U),next=arcArenaSibling(value,6U);arena_coordinateHalfplaneArcs(beta,c,rho,plane,valid);arena_coordinatePreparedIntersect(value,plane,next);arena_coordinatePreparedAssign(value,next);
    }
}
[noinline]
void arena_coordinatePreparedCircleArcs(uint64_t cx,uint64_t cy,uint64_t d,uint64_t r,uint64_t rho,inout ArcArenaView value,inout bool valid)
{
    arena_coordinateArcClear(value);uint64_t plus=f64Add(d,rho),outer=f64Add(d,r),inner=cgSub(d,r);
    if(!f64Finite(d)||!f64Finite(plus)||!f64Finite(outer)||!f64Finite(inner)){valid=false;return;}
    if(!f64Less(0,rho)){if(!f64Less(r,d))arena_cgFull(value);return;}
    if(!f64Less(r,plus)){arena_cgFull(value);return;}
    if(!f64Less(rho,outer)||!f64Less(inner,rho))return;
    uint64_t numerator=cgSub(f64Add(f64Mul(rho,rho),f64Mul(d,d)),f64Mul(r,r));
    uint64_t denominator=f64Mul(f64Mul(cgConstant(0x40000000U),rho),d);
    if(!f64Finite(numerator)||!f64Finite(denominator)||f64Zero(denominator)){valid=false;return;}
    uint64_t c=f64Div(numerator,denominator),one=cgConstant(0x3ff00000U);
    if(!f64Finite(c)){valid=false;return;}
    c=f64Less(c,one^F64_SIGN)?one^F64_SIGN:f64Less(one,c)?one:c;
    uint64_t half=coordinateAcos(c);
    arena_coordinateArcCreate(cgSub(coordinateAtan2(cy,cx),half),f64Mul(cgConstant(0x40000000U),half),value);
}
[noinline]
void arena_coordinatePreparedShapeArcs(uint kind,uint64_t cx,uint64_t cy,uint64_t lx,uint64_t ly,uint64_t hw,uint64_t hh,uint64_t by,uint64_t d,uint64_t cornerDistance[4],uint64_t rotation,uint64_t radius,uint64_t rho,uint64_t grow,inout ArcArenaView arcs,out bool valid)
{
    valid=true;arena_coordinateArcClear(arcs);
    if(kind==1){arena_coordinatePreparedCircleArcs(cx,cy,d,f64Add(radius,grow),rho,arcs,valid);return;}
    uint64_t ew=f64Add(hw,grow),eh=f64Add(hh,grow);
        arena_coordinatePreparedRectangleArcs(lx,ly,ew,hh,rho,arcs,valid);
        if(f64Less(0,grow)&&valid)
        {
            ArcArenaView extra=arcArenaSibling(arcs,3U);arena_coordinatePreparedRectangleArcs(lx,ly,hw,eh,rho,extra,valid);
            for(uint j=0;j<extra.count;j++)arena_coordinateArcInsert(arcs,extra.start[j],extra.end[j]);arcs.overflow=arcs.overflow||extra.overflow;
            for(uint corner=0;corner<4&&valid;corner++)
            {
                uint64_t cx=(corner&1)!=0?hw^F64_SIGN:hw,cy=(corner&2)!=0?hh^F64_SIGN:hh;
                arena_coordinatePreparedCircleArcs(cgSub(cx,lx),cgSub(cy,ly),cornerDistance[corner],grow,rho,extra,valid);
                for(uint j=0;j<extra.count;j++)arena_coordinateArcInsert(arcs,extra.start[j],extra.end[j]);arcs.overflow=arcs.overflow||extra.overflow;
            }
        }
        if(!f64Zero(rotation)&&valid)
        {
            ArcArenaView shifted=arcArenaSibling(arcs,4U);arena_coordinatePreparedShift(arcs,by,shifted);arena_coordinatePreparedAssign(arcs,shifted);
        }

    valid=valid&&!arcs.overflow;
}
[noinline]
void arena_coordinateLandingSubtract(inout ArcArenaView a,inout ArcArenaView b,inout ArcArenaView value)
{
    if(!arcArenaDistinct(a,b,value))return;
    arena_coordinateArcClear(value);uint first=0;
    for(uint i=0;i<a.count;i++)
    {
        uint64_t cur=a.start[i],e=a.end[i];
        while(first<b.count&&!f64Less(cur,b.end[first]))first++;
        for(uint j=first;j<b.count;j++)
        {
            uint64_t c=b.start[j],d=b.end[j];
            if(!f64Less(c,e))break;
            if(!f64Less(cur,d))continue;
            if(f64Less(cur,c))arena_coordinateArcAppend(value,cur,c);
            if(f64Less(cur,d))cur=d;
            if(!f64Less(cur,e))break;
        }
        if(f64Less(cur,e))arena_coordinateArcAppend(value,cur,e);
    }
    value.overflow=value.overflow||a.overflow||b.overflow;
}
[noinline]
uint64_t arena_coordinateLandingMeasure(inout ArcArenaView value)
{
    Sum sum={};
    for(uint i=0;i<value.count;i++)addSum(sum,f64Add(value.end[i],value.start[i]^F64_SIGN));
    // Same finite Neumaier finalization already used by periodicSkillInterval.
    return f64Finite(sum.correction)&&!f64Zero(sum.correction)?f64Add(sum.total,sum.correction):sum.total;
}
[noinline]
void arena_clArcs(uint input,uint output,uint index,uint64_t rho,uint64_t grow,inout ArcArenaView arcs,out bool valid)
{
    uint at=clShapeAt(input,index);uint64_t corners[4];for(uint i=0;i<4;i++)corners[i]=clPreparedRead(output,index,8+i);
    arena_coordinatePreparedShapeArcs(commands[at],clPreparedRead(output,index,0),clPreparedRead(output,index,1),clPreparedRead(output,index,2),clPreparedRead(output,index,3),clPreparedRead(output,index,4),clPreparedRead(output,index,5),clPreparedRead(output,index,6),clPreparedRead(output,index,7),corners,clRead(at+12),clRead(at+6),rho,grow,arcs,valid);
}
[noinline]
void arena_clGeometry(uint input,uint shape,uint64_t rho,uint64_t grow,out uint64_t distance,inout ArcArenaView arcs,out uint count,out uint64_t breaks[24],out bool valid)
{
    uint at=clShapeAt(input,shape);uint64_t co,si;
    arena_coordinateGeometryV1(commands[at],clRead(at+2),clRead(at+4),clRead(at+6),clRead(at+8),clRead(at+10),clRead(at+12),clRead(input+4),clRead(input+6),rho,grow,distance,co,si,arcs,count,breaks,valid);
}
[noinline]
void arena_clShapeCuts(uint input,uint index,uint64_t grow,uint64_t radius,uint64_t k,uint output,inout uint cutCount,inout bool valid)
{
    uint64_t distance,breaks[24];uint count;ArcArenaView arcs=arcArenaView(output,CL_OUTPUT,0U);bool ok;
    arena_clGeometry(input,index,0,grow,distance,arcs,count,breaks,ok);if(!ok){valid=false;return;}
    for(uint i=0;i<count&&valid;i++)if(f64Less(0,breaks[i])&&f64Less(breaks[i],radius))
    {
        uint status;uint64_t cut=coordinateUnitPower(f64Div(breaks[i],radius),k,status);
        if(status!=0){valid=false;return;}clCutAdd(output,cutCount,cut,valid);
    }
}
[noinline]
bool arena_coordinateLandingV1(uint input,uint output)
{
    uint n=commands[input+2],corePresent=commands[input+3];uint64_t radius=larger(clRead(input+8),CL_MIN_RADIUS),grow=clRead(input+10),k=clRead(input+12);
    bool near[CL_TARGETS];uint nearCount=0;bool useCore=false,valid=true;uint64_t front[CL_TARGETS],reach[CL_TARGETS];
    for(uint i=0;i<CL_TARGETS;i++){near[i]=false;front[i]=0;reach[i]=0;}
    uint64_t distance,breaks[24];uint count;ArcArenaView arcs=arcArenaView(output,CL_OUTPUT,0U);bool ok;
    for(uint i=0;i<n;i++)
    {
        arena_clGeometry(input,i,0,0,distance,arcs,count,breaks,ok);if(!ok)return false;
        near[i]=!f64Less(f64Add(radius,grow),distance);if(near[i])nearCount++;
    }
    if(corePresent!=0){arena_clGeometry(input,CL_TARGETS,0,0,distance,arcs,count,breaks,ok);if(!ok)return false;useCore=!f64Less(radius,distance);}
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
        arena_clShapeCuts(input,i,0,radius,k,output,cutCount,valid);
        if(f64Less(0,grow))arena_clShapeCuts(input,i,grow,radius,k,output,cutCount,valid);
    }
    if(useCore&&valid)arena_clShapeCuts(input,CL_TARGETS,0,radius,k,output,cutCount,valid);
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
            if(status!=0)return false;nodeCount++;ArcArenaView covered=arcArenaView(output,CL_OUTPUT,1U);arena_coordinateArcClear(covered);
            for(uint i=0;i<n;i++)if(near[i])
            {
                arena_clArcs(input,output,i,rho,0,arcs,ok);if(!ok)return false;
                if(arcs.count!=0)
                {
                    ArcArenaView visible=arcArenaView(output,CL_OUTPUT,2U);arena_coordinateLandingSubtract(arcs,covered,visible);
                    front[i]=f64Add(front[i],f64Mul(weight,arena_coordinateLandingMeasure(visible)));
                    for(uint j=0;j<arcs.count;j++)arena_coordinateArcInsert(covered,arcs.start[j],arcs.end[j]);
                    if(visible.overflow||covered.overflow)return false;
                }
                if(f64Less(0,grow))
                {
                    arena_clArcs(input,output,i,rho,grow,arcs,ok);if(!ok)return false;
                    reach[i]=f64Add(reach[i],f64Mul(weight,arena_coordinateLandingMeasure(arcs)));
                }
            }
            if(useCore)
            {
                arena_clArcs(input,output,CL_TARGETS,rho,0,arcs,ok);if(!ok)return false;
                if(arcs.count!=0)
                {
                    coreUnder=f64Add(coreUnder,f64Mul(weight,arena_coordinateLandingMeasure(arcs)));
                    ArcArenaView visible=arcArenaView(output,CL_OUTPUT,2U);arena_coordinateLandingSubtract(arcs,covered,visible);if(visible.overflow)return false;
                    coreOpen=f64Add(coreOpen,f64Mul(weight,arena_coordinateLandingMeasure(visible)));
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
