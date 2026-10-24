// Generated from portable_coordinate_numeric_v1; contract 94bed5dc9d555fb2a50ce9912aaa3ebab650e5e795a97311f486c46486065d73
// Requires binary64, coordinate_math and coordinate_arc_scalar helpers.
#ifndef PORTABLE_COORDINATE_NUMERIC_V1
#define PORTABLE_COORDINATE_NUMERIC_V1
[noinline]
uint64_t coordinateKernel_sin(uint64_t z)
{
    uint64_t z2=f64Mul(z,z),one=(uint64_t(0x3ff00000U)<<32|uint64_t(0x00000000U));
    uint64_t sin_k19=(uint64_t(0xbc62f49bU)<<32|uint64_t(0x46814157U));
    uint64_t sin_k17=(uint64_t(0x3ce952c7U)<<32|uint64_t(0x7030ad4aU));
    uint64_t sin_k15=(uint64_t(0xbd6ae7f3U)<<32|uint64_t(0xe733b81fU));
    uint64_t sin_k13=(uint64_t(0x3de61246U)<<32|uint64_t(0x13a86d09U));
    uint64_t sin_k11=(uint64_t(0xbe5ae645U)<<32|uint64_t(0x67f544e4U));
    uint64_t sin_k9=(uint64_t(0x3ec71de3U)<<32|uint64_t(0xa556c734U));
    uint64_t sin_k7=(uint64_t(0xbf2a01a0U)<<32|uint64_t(0x1a01a01aU));
    uint64_t sin_k5=(uint64_t(0x3f811111U)<<32|uint64_t(0x11111111U));
    uint64_t sin_k3=(uint64_t(0xbfc55555U)<<32|uint64_t(0x55555555U));
    uint64_t sin_m17=f64Mul(sin_k19,z2);
    uint64_t sin_a17=f64Add(sin_m17,sin_k17);
    uint64_t sin_m15=f64Mul(sin_a17,z2);
    uint64_t sin_a15=f64Add(sin_m15,sin_k15);
    uint64_t sin_m13=f64Mul(sin_a15,z2);
    uint64_t sin_a13=f64Add(sin_m13,sin_k13);
    uint64_t sin_m11=f64Mul(sin_a13,z2);
    uint64_t sin_a11=f64Add(sin_m11,sin_k11);
    uint64_t sin_m9=f64Mul(sin_a11,z2);
    uint64_t sin_a9=f64Add(sin_m9,sin_k9);
    uint64_t sin_m7=f64Mul(sin_a9,z2);
    uint64_t sin_a7=f64Add(sin_m7,sin_k7);
    uint64_t sin_m5=f64Mul(sin_a7,z2);
    uint64_t sin_a5=f64Add(sin_m5,sin_k5);
    uint64_t sin_m3=f64Mul(sin_a5,z2);
    uint64_t sin_a3=f64Add(sin_m3,sin_k3);
    uint64_t sin_cube=f64Mul(z,z2);
    uint64_t sin_tail=f64Mul(sin_cube,sin_a3);
    uint64_t sin_result=f64Add(z,sin_tail);
    return sin_result;
}
[noinline]
uint64_t coordinateKernel_cos(uint64_t z)
{
    uint64_t z2=f64Mul(z,z),one=(uint64_t(0x3ff00000U)<<32|uint64_t(0x00000000U));
    uint64_t cos_k20=(uint64_t(0x3c1e542bU)<<32|uint64_t(0xa4020225U));
    uint64_t cos_k18=(uint64_t(0xbca68278U)<<32|uint64_t(0x63b97d97U));
    uint64_t cos_k16=(uint64_t(0x3d2ae7f3U)<<32|uint64_t(0xe733b81fU));
    uint64_t cos_k14=(uint64_t(0xbda93974U)<<32|uint64_t(0xa8c07c9dU));
    uint64_t cos_k12=(uint64_t(0x3e21eed8U)<<32|uint64_t(0xeff8d898U));
    uint64_t cos_k10=(uint64_t(0xbe927e4fU)<<32|uint64_t(0xb7789f5cU));
    uint64_t cos_k8=(uint64_t(0x3efa01a0U)<<32|uint64_t(0x1a01a01aU));
    uint64_t cos_k6=(uint64_t(0xbf56c16cU)<<32|uint64_t(0x16c16c17U));
    uint64_t cos_k4=(uint64_t(0x3fa55555U)<<32|uint64_t(0x55555555U));
    uint64_t cos_k2=(uint64_t(0xbfe00000U)<<32|uint64_t(0x00000000U));
    uint64_t cos_m18=f64Mul(cos_k20,z2);
    uint64_t cos_a18=f64Add(cos_m18,cos_k18);
    uint64_t cos_m16=f64Mul(cos_a18,z2);
    uint64_t cos_a16=f64Add(cos_m16,cos_k16);
    uint64_t cos_m14=f64Mul(cos_a16,z2);
    uint64_t cos_a14=f64Add(cos_m14,cos_k14);
    uint64_t cos_m12=f64Mul(cos_a14,z2);
    uint64_t cos_a12=f64Add(cos_m12,cos_k12);
    uint64_t cos_m10=f64Mul(cos_a12,z2);
    uint64_t cos_a10=f64Add(cos_m10,cos_k10);
    uint64_t cos_m8=f64Mul(cos_a10,z2);
    uint64_t cos_a8=f64Add(cos_m8,cos_k8);
    uint64_t cos_m6=f64Mul(cos_a8,z2);
    uint64_t cos_a6=f64Add(cos_m6,cos_k6);
    uint64_t cos_m4=f64Mul(cos_a6,z2);
    uint64_t cos_a4=f64Add(cos_m4,cos_k4);
    uint64_t cos_m2=f64Mul(cos_a4,z2);
    uint64_t cos_a2=f64Add(cos_m2,cos_k2);
    uint64_t cos_tail=f64Mul(z2,cos_a2);
    uint64_t cos_result=f64Add(one,cos_tail);
    return cos_result;
}
[noinline]
uint64_t coordinateKernel_atan(uint64_t z)
{
    uint64_t z2=f64Mul(z,z),one=(uint64_t(0x3ff00000U)<<32|uint64_t(0x00000000U));
    uint64_t atan_k63=(uint64_t(0xbf904104U)<<32|uint64_t(0x10410410U));
    uint64_t atan_k61=(uint64_t(0x3f90c971U)<<32|uint64_t(0x4fbcda3bU));
    uint64_t atan_k59=(uint64_t(0xbf915b1eU)<<32|uint64_t(0x5f75270dU));
    uint64_t atan_k57=(uint64_t(0x3f91f704U)<<32|uint64_t(0x7dc11f70U));
    uint64_t atan_k55=(uint64_t(0xbf929e41U)<<32|uint64_t(0x29e4129eU));
    uint64_t atan_k53=(uint64_t(0x3f93521cU)<<32|uint64_t(0xfb2b78c1U));
    uint64_t atan_k51=(uint64_t(0xbf941414U)<<32|uint64_t(0x14141414U));
    uint64_t atan_k49=(uint64_t(0x3f94e5e0U)<<32|uint64_t(0xa72f0539U));
    uint64_t atan_k47=(uint64_t(0xbf95c988U)<<32|uint64_t(0x2b931057U));
    uint64_t atan_k45=(uint64_t(0x3f96c16cU)<<32|uint64_t(0x16c16c17U));
    uint64_t atan_k43=(uint64_t(0xbf97d05fU)<<32|uint64_t(0x417d05f4U));
    uint64_t atan_k41=(uint64_t(0x3f98f9c1U)<<32|uint64_t(0x8f9c18faU));
    uint64_t atan_k39=(uint64_t(0xbf9a41a4U)<<32|uint64_t(0x1a41a41aU));
    uint64_t atan_k37=(uint64_t(0x3f9bacf9U)<<32|uint64_t(0x14c1bad0U));
    uint64_t atan_k35=(uint64_t(0xbf9d41d4U)<<32|uint64_t(0x1d41d41dU));
    uint64_t atan_k33=(uint64_t(0x3f9f07c1U)<<32|uint64_t(0xf07c1f08U));
    uint64_t atan_k31=(uint64_t(0xbfa08421U)<<32|uint64_t(0x08421084U));
    uint64_t atan_k29=(uint64_t(0x3fa1a7b9U)<<32|uint64_t(0x611a7b96U));
    uint64_t atan_k27=(uint64_t(0xbfa2f684U)<<32|uint64_t(0xbda12f68U));
    uint64_t atan_k25=(uint64_t(0x3fa47ae1U)<<32|uint64_t(0x47ae147bU));
    uint64_t atan_k23=(uint64_t(0xbfa642c8U)<<32|uint64_t(0x590b2164U));
    uint64_t atan_k21=(uint64_t(0x3fa86186U)<<32|uint64_t(0x18618618U));
    uint64_t atan_k19=(uint64_t(0xbfaaf286U)<<32|uint64_t(0xbca1af28U));
    uint64_t atan_k17=(uint64_t(0x3fae1e1eU)<<32|uint64_t(0x1e1e1e1eU));
    uint64_t atan_k15=(uint64_t(0xbfb11111U)<<32|uint64_t(0x11111111U));
    uint64_t atan_k13=(uint64_t(0x3fb3b13bU)<<32|uint64_t(0x13b13b14U));
    uint64_t atan_k11=(uint64_t(0xbfb745d1U)<<32|uint64_t(0x745d1746U));
    uint64_t atan_k9=(uint64_t(0x3fbc71c7U)<<32|uint64_t(0x1c71c71cU));
    uint64_t atan_k7=(uint64_t(0xbfc24924U)<<32|uint64_t(0x92492492U));
    uint64_t atan_k5=(uint64_t(0x3fc99999U)<<32|uint64_t(0x9999999aU));
    uint64_t atan_k3=(uint64_t(0xbfd55555U)<<32|uint64_t(0x55555555U));
    uint64_t atan_m61=f64Mul(atan_k63,z2);
    uint64_t atan_a61=f64Add(atan_m61,atan_k61);
    uint64_t atan_m59=f64Mul(atan_a61,z2);
    uint64_t atan_a59=f64Add(atan_m59,atan_k59);
    uint64_t atan_m57=f64Mul(atan_a59,z2);
    uint64_t atan_a57=f64Add(atan_m57,atan_k57);
    uint64_t atan_m55=f64Mul(atan_a57,z2);
    uint64_t atan_a55=f64Add(atan_m55,atan_k55);
    uint64_t atan_m53=f64Mul(atan_a55,z2);
    uint64_t atan_a53=f64Add(atan_m53,atan_k53);
    uint64_t atan_m51=f64Mul(atan_a53,z2);
    uint64_t atan_a51=f64Add(atan_m51,atan_k51);
    uint64_t atan_m49=f64Mul(atan_a51,z2);
    uint64_t atan_a49=f64Add(atan_m49,atan_k49);
    uint64_t atan_m47=f64Mul(atan_a49,z2);
    uint64_t atan_a47=f64Add(atan_m47,atan_k47);
    uint64_t atan_m45=f64Mul(atan_a47,z2);
    uint64_t atan_a45=f64Add(atan_m45,atan_k45);
    uint64_t atan_m43=f64Mul(atan_a45,z2);
    uint64_t atan_a43=f64Add(atan_m43,atan_k43);
    uint64_t atan_m41=f64Mul(atan_a43,z2);
    uint64_t atan_a41=f64Add(atan_m41,atan_k41);
    uint64_t atan_m39=f64Mul(atan_a41,z2);
    uint64_t atan_a39=f64Add(atan_m39,atan_k39);
    uint64_t atan_m37=f64Mul(atan_a39,z2);
    uint64_t atan_a37=f64Add(atan_m37,atan_k37);
    uint64_t atan_m35=f64Mul(atan_a37,z2);
    uint64_t atan_a35=f64Add(atan_m35,atan_k35);
    uint64_t atan_m33=f64Mul(atan_a35,z2);
    uint64_t atan_a33=f64Add(atan_m33,atan_k33);
    uint64_t atan_m31=f64Mul(atan_a33,z2);
    uint64_t atan_a31=f64Add(atan_m31,atan_k31);
    uint64_t atan_m29=f64Mul(atan_a31,z2);
    uint64_t atan_a29=f64Add(atan_m29,atan_k29);
    uint64_t atan_m27=f64Mul(atan_a29,z2);
    uint64_t atan_a27=f64Add(atan_m27,atan_k27);
    uint64_t atan_m25=f64Mul(atan_a27,z2);
    uint64_t atan_a25=f64Add(atan_m25,atan_k25);
    uint64_t atan_m23=f64Mul(atan_a25,z2);
    uint64_t atan_a23=f64Add(atan_m23,atan_k23);
    uint64_t atan_m21=f64Mul(atan_a23,z2);
    uint64_t atan_a21=f64Add(atan_m21,atan_k21);
    uint64_t atan_m19=f64Mul(atan_a21,z2);
    uint64_t atan_a19=f64Add(atan_m19,atan_k19);
    uint64_t atan_m17=f64Mul(atan_a19,z2);
    uint64_t atan_a17=f64Add(atan_m17,atan_k17);
    uint64_t atan_m15=f64Mul(atan_a17,z2);
    uint64_t atan_a15=f64Add(atan_m15,atan_k15);
    uint64_t atan_m13=f64Mul(atan_a15,z2);
    uint64_t atan_a13=f64Add(atan_m13,atan_k13);
    uint64_t atan_m11=f64Mul(atan_a13,z2);
    uint64_t atan_a11=f64Add(atan_m11,atan_k11);
    uint64_t atan_m9=f64Mul(atan_a11,z2);
    uint64_t atan_a9=f64Add(atan_m9,atan_k9);
    uint64_t atan_m7=f64Mul(atan_a9,z2);
    uint64_t atan_a7=f64Add(atan_m7,atan_k7);
    uint64_t atan_m5=f64Mul(atan_a7,z2);
    uint64_t atan_a5=f64Add(atan_m5,atan_k5);
    uint64_t atan_m3=f64Mul(atan_a5,z2);
    uint64_t atan_a3=f64Add(atan_m3,atan_k3);
    uint64_t atan_cube=f64Mul(z,z2);
    uint64_t atan_tail=f64Mul(atan_cube,atan_a3);
    uint64_t atan_result=f64Add(z,atan_tail);
    return atan_result;
}
void coordinateQuadrantPair(uint q,uint64_t z,bool negative,bool axisZeros,out uint64_t sine,out uint64_t cosine)
{
    uint64_t s=coordinateKernel_sin(z),c=coordinateKernel_cos(z);
    if(q==0){sine=s;cosine=c;}
    else if(q==1){sine=c;cosine=s^F64_SIGN;}
    else if(q==2){sine=s^F64_SIGN;cosine=c^F64_SIGN;}
    else if(q==3){sine=c^F64_SIGN;cosine=s;}
    else if(q==4){sine=s;cosine=c;}
    if(negative)sine^=F64_SIGN;
    if(axisZeros){if(f64Zero(sine))sine=negative?F64_SIGN:0;if(f64Zero(cosine))cosine=0;}
}
[noinline]
void coordinateSinCosDegrees(uint64_t degrees,out uint64_t sine,out uint64_t cosine)
{
    uint64_t r=coordinatePositiveModulo(f64Abs(degrees),(uint64_t(0x40768000U)<<32|uint64_t(0x00000000U)));uint q=4;
    if(r<=(uint64_t(0x40468000U)<<32|uint64_t(0x00000000U)))q=0;
    else if(r<(uint64_t(0x4060e000U)<<32|uint64_t(0x00000000U)))q=1;
    else if(r<=(uint64_t(0x406c2000U)<<32|uint64_t(0x00000000U)))q=2;
    else if(r<(uint64_t(0x4073b000U)<<32|uint64_t(0x00000000U)))q=3;
    uint64_t z=f64Mul(f64Add(r,f64FromI64(q*90)^F64_SIGN),(uint64_t(0x3f91df46U)<<32|uint64_t(0xa2529d39U)));
    coordinateQuadrantPair(q,z,(degrees&F64_SIGN)!=0,true,sine,cosine);
}
[noinline]
void coordinateSinCosRadians(uint64_t radians,out uint64_t sine,out uint64_t cosine)
{
    uint64_t x=f64Abs(radians);uint status;uint q=uint(f64ToI64(f64Integral(f64Div(x,(uint64_t(0x3ff921fbU)<<32|uint64_t(0x54442d18U))),0),1,status));uint64_t z=x;
    z=f64Add(z,f64Mul(f64FromI64(q),(uint64_t(0x3ff921fbU)<<32|uint64_t(0x40000000U)))^F64_SIGN);
    z=f64Add(z,f64Mul(f64FromI64(q),(uint64_t(0x3e74442dU)<<32|uint64_t(0x00000000U)))^F64_SIGN);
    z=f64Add(z,f64Mul(f64FromI64(q),(uint64_t(0x3cf84698U)<<32|uint64_t(0x80000000U)))^F64_SIGN);
    z=f64Add(z,f64Mul(f64FromI64(q),(uint64_t(0x3b78cc51U)<<32|uint64_t(0x60000000U)))^F64_SIGN);
    z=f64Add(z,f64Mul(f64FromI64(q),(uint64_t(0x39f01b83U)<<32|uint64_t(0x80000000U)))^F64_SIGN);
    z=f64Add(z,f64Mul(f64FromI64(q),(uint64_t(0x387a2520U)<<32|uint64_t(0x40000000U)))^F64_SIGN);
    coordinateQuadrantPair(q,z,(radians&F64_SIGN)!=0,false,sine,cosine);
}
[noinline]
uint64_t coordinateSqrt(uint64_t x)
{
    if(f64Zero(x))return x;int exponent;uint64_t s;f64Unpack(x,exponent,s);
    int e=exponent-1023,rootExponent=e/2;if(e<0&&e%2!=0)rootExponent--;
    CoordinateWide radicand=cmShift(cmWide(0,s),uint(52+e-2*rootExponent));uint64_t root=0;
    for(int bit=52;bit>=0;bit--){uint64_t candidate=root|(uint64_t(1)<<uint(bit));if(!cmLess(radicand,cmSquare(candidate,0)))root=candidate;}
    CoordinateWide four=cmShift(radicand,2),mid=cmSquare(2*root+1,0);bool above=cmLess(mid,four),equal=!above&&!cmLess(four,mid);
    if(above||(equal&&(root&1)!=0))root++;return f64Pack(0,rootExponent+1023,root<<3);
}
[noinline]
uint64_t coordinateAtan2(uint64_t y,uint64_t x)
{
    uint64_t ax=f64Abs(x),ay=f64Abs(y),sign=y&F64_SIGN;
    if(ay==0)return sign|((x&F64_SIGN)!=0?(uint64_t(0x400921fbU)<<32|uint64_t(0x54442d18U)):0);
    if(ax==0)return sign|(uint64_t(0x3ff921fbU)<<32|uint64_t(0x54442d18U));
    bool swapped=ay>ax;uint64_t t=swapped?f64Div(ax,ay):f64Div(ay,ax),one=(uint64_t(0x3ff00000U)<<32|uint64_t(0x00000000U));
    uint64_t angle=t>(uint64_t(0x3fda8279U)<<32|uint64_t(0x99fcef32U))?f64Add((uint64_t(0x3fe921fbU)<<32|uint64_t(0x54442d18U)),coordinateKernel_atan(f64Div(f64Add(t,one^F64_SIGN),f64Add(t,one)))):coordinateKernel_atan(t);
    if(swapped)angle=f64Add((uint64_t(0x3ff921fbU)<<32|uint64_t(0x54442d18U)),angle^F64_SIGN);if((x&F64_SIGN)!=0)angle=f64Add((uint64_t(0x400921fbU)<<32|uint64_t(0x54442d18U)),angle^F64_SIGN);return angle|sign;
}
uint64_t coordinateAcos(uint64_t x){uint64_t one=(uint64_t(0x3ff00000U)<<32|uint64_t(0x00000000U));return coordinateAtan2(coordinateSqrt(f64Mul(f64Add(one,x^F64_SIGN),f64Add(one,x))),x);}
#endif
