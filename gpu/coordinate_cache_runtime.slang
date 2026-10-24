uint gcHead(inout Runtime s){return s.resourceOutput+GC_BASE;}
uint gcSig(inout Runtime s){return s.resourceOutput+GC_SIG;}
uint gcTable(inout Runtime s){return s.resourceOutput+GC_TABLE;}
uint gcData(inout Runtime s){return s.resourceOutput+GC_DATA;}
void initializeGeometryCache(inout Runtime s)
{
    for(uint i=GC_BASE;i<GC_END;i++)results[s.resourceOutput+i]=0;
    results[gcHead(s)]=GC_MAGIC;results[gcHead(s)+1]=1;
}
void coordinateCachedAim(inout Runtime s,inout uint64_t ax,inout uint64_t ay)
{
    if(results[gcHead(s)+2]!=0){ax=actorNumber(gcSig(s)+10);ay=actorNumber(gcSig(s)+12);}
}
[noinline]
void coordinateCacheRefresh(inout Runtime s)
{
    uint h=gcHead(s),sig=gcSig(s),frame=s.resourceOutput+CP_FRAME,n=results[frame+2];
    if(n>CL_TARGETS){s.error=64;return;}results[h+13]++;
    uint meta=coordinateAreaInput(s);uint64_t ax=cNumber(meta+4),ay=cNumber(meta+6),cx,cy,diameter;
    coordinateCoreGeometry(s,ax,ay,cx,cy,diameter);
    uint64_t radius=f64Div(diameter,uint64_t(0x40000000U)<<32);
    if(!f64Less(0,diameter)){radius=0;cx=0;cy=0;} // Native Geometry.core is None, including base -0.
    else if(!f64Less(0,radius)){s.error=64;return;}
    bool same=results[h+2]!=0&&results[h+3]==n;
    if(same)for(uint i=0;i<n;i++)if(results[sig+16+i]!=results[frame+8+i*4]){same=false;break;}
    same=same&&f64Equal(actorNumber(sig+4),cx)&&f64Equal(actorNumber(sig+6),cy)&&f64Equal(actorNumber(sig+8),radius)&&f64Equal(actorNumber(sig+10),ax)&&f64Equal(actorNumber(sig+12),ay);
    if(same)return;
    uint used=results[h+5]*results[h+4];
    if(used>GC_END-GC_DATA){s.error=64;return;}
    for(uint i=0;i<used;i++)results[gcData(s)+i]=0;
    for(uint i=0;i<GC_SLOTS;i++)results[gcTable(s)+i]=0;
    for(uint i=0;i<GC_SIG_WORDS;i++)results[sig+i]=0;
    results[sig]=n;storeNumber(sig+4,cx);storeNumber(sig+6,cy);storeNumber(sig+8,radius);storeNumber(sig+10,ax);storeNumber(sig+12,ay);
    for(uint i=0;i<n;i++)results[sig+16+i]=results[frame+8+i*4];
    results[h+2]=1;results[h+3]=n;results[h+4]=12+4*n;results[h+5]=0;
    results[h+6]=min(GC_MAX_ENTRIES,(GC_END-GC_DATA)/results[h+4]);results[h+7]++;results[h+10]++;
}
uint coordinateKeyHash(uint64_t key[4])
{
    uint h=2166136261U;
    for(uint i=0;i<4;i++){h=(h^uint(key[i]))*16777619U;h=(h^uint(key[i]>>32))*16777619U;}
    return h&(GC_SLOTS-1);
}
void coordinateCacheRead(uint at,uint output,uint n)
{
    results[output+1]=CL_MAGIC;results[output+2]=1;results[output+3]=n;
    clWrite(output+4,actorNumber(at+8));clWrite(output+6,actorNumber(at+10));
    for(uint i=0;i<n;i++)
    {
        clWrite(output+16+i*2,actorNumber(at+12+i*2));
        clWrite(output+16+CL_TARGETS*2+i*2,actorNumber(at+12+n*2+i*2));
    }
}
[noinline]
bool coordinateCachedLanding(inout Runtime s,uint input,uint output,uint logicalCount)
{
    uint h=gcHead(s),sig=gcSig(s),n=results[input+2],count=results[h+5],stride=results[h+4];
    if(results[h+2]==0||n!=results[h+3]||count>results[h+6]||logicalCount==0){s.error=64;return false;}
    // Native Geometry keeps its first equal geometry, including raw signed
    // zeros. Misses therefore use that representative, not a newer equal one.
#ifndef PORTABLE_COORDINATE_AUTHORED_AIM
    clWrite(input+4,actorNumber(sig+10));clWrite(input+6,actorNumber(sig+12));
#endif
    uint64_t radius=actorNumber(sig+8);results[input+3]=uint(f64Less(0,radius));
    if(results[input+3]!=0)
    {
        uint coreAt=clShapeAt(input,CL_TARGETS);results[coreAt]=1;
        clWrite(coreAt+2,actorNumber(sig+4));clWrite(coreAt+4,actorNumber(sig+6));clWrite(coreAt+6,radius);
    }
    uint64_t key[4];
    for(uint i=0;i<4;i++){uint status;key[i]=coordinateCacheKey(actorNumber(input+4+i*2),status);if(status!=0){s.error=16;return false;}}
    uint bucket=coordinateKeyHash(key),empty=GC_SLOTS;
    for(uint probe=0;probe<GC_SLOTS;probe++)
    {
        uint table=gcTable(s)+bucket,link=results[table];
        if(link==0){empty=table;break;}
        if(link>count){s.error=64;return false;}
        uint at=gcData(s)+(link-1)*stride;bool equal=true;
        for(uint i=0;i<4;i++)if(actorNumber(at+i*2)!=key[i]){equal=false;break;}
        if(equal){coordinateCacheRead(at,output,n);results[h+8]++;results[h+14]+=logicalCount-1;return true;}
        bucket=(bucket+1)&(GC_SLOTS-1);
    }
    if(empty==GC_SLOTS||count==results[h+6]){results[h+11]=1;s.error=64;return false;}
    if(!coordinateLandingV1(input,output))return false;
    uint at=gcData(s)+count*stride;
    for(uint i=0;i<4;i++)storeNumber(at+i*2,key[i]);
    storeNumber(at+8,actorNumber(output+4));storeNumber(at+10,actorNumber(output+6));
    for(uint i=0;i<n;i++)
    {
        storeNumber(at+12+i*2,actorNumber(output+16+i*2));
        storeNumber(at+12+n*2+i*2,actorNumber(output+16+CL_TARGETS*2+i*2));
    }
    results[empty]=count+1;results[h+5]++;results[h+9]++;results[h+12]=max(results[h+12],count+1);results[h+14]+=logicalCount-1;
    return true;
}
