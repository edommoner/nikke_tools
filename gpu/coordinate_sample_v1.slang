// Generated coordinate-sample-v1; contract ef4aa497a9e99cb2c1e02fe99121b2da6f83a52308ef1d9cdff8534cd4825040.
#ifndef PORTABLE_COORDINATE_SAMPLE_V1
#define PORTABLE_COORDINATE_SAMPLE_V1
uint64_t coordinateRandom53(uint rng)
{
    uint a=mtNext(rng)>>5,b=mtNext(rng)>>6;
    return f64Mul(f64FromI64((uint64_t(a)<<26)+b),(uint64_t(0x3ca00000U)<<32|uint64_t(0x00000000U)));
}
bool validCoordinateSample(uint64_t ax,uint64_t ay,uint64_t radius,uint64_t k)
{return f64Finite(ax)&&f64Finite(ay)&&f64Finite(radius)&&f64Finite(k)&&k>=(uint64_t(0x3ef00000U)<<32|uint64_t(0x00000000U))&&k<=(uint64_t(0x40f00000U)<<32|uint64_t(0x00000000U));}
[noinline]
void coordinateSamplePoint(uint rng,uint64_t ax,uint64_t ay,uint64_t radius,uint64_t k,bool angle,out uint64_t px,out uint64_t py,out uint64_t u,out uint64_t v,out uint status)
{
    status=0;px=0;py=0;u=0;v=0;
    if(!validCoordinateSample(ax,ay,radius,k)){status=64;return;}
    radius=f64Less(radius,(uint64_t(0x3e112e0bU)<<32|uint64_t(0xe826d695U)))?(uint64_t(0x3e112e0bU)<<32|uint64_t(0xe826d695U)):radius;
    u=coordinateRandom53(rng);uint64_t one=ONE,tau=coordinateTau();
    uint64_t inverse=f64Div(one,k);
    uint64_t radial=coordinateUnitPower(u,inverse,status);
    uint64_t rho=f64Mul(radius,radial);
    if(status!=0){status=64;return;}
    if(!angle){px=f64Add(ax,rho);py=ay;}
    else
    {
        v=coordinateRandom53(rng);uint64_t sine,cosine;
            uint64_t theta=f64Mul(tau,v);
        coordinateSinCosRadians(theta,sine,cosine);
    uint64_t dx=f64Mul(rho,cosine);
    uint64_t dy=f64Mul(rho,sine);
    px=f64Add(ax,dx);
    py=f64Add(ay,dy);
    }
    if(!f64Finite(px)||!f64Finite(py))status=64;
}
#endif
