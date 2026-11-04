// combat-prefilter-metal-f32-v1: literal port of app/combat.cu's approximate model.
// Float32 inputs, arithmetic, clock and accumulators; never a final score.
#define CS 44
#define ES 12
#define NS 24
#define ME 160
float hi(float a,float b){return a>b?a:b;}
float lo(float a,float b){return a<b?a:b;}
// Metal round() uses ties away from zero. Preserve CUDA RN ties-to-even.
float roundDamage(float x){
 float lower=floor(x),fraction=x-lower;
 return fraction<0.5f?lower:fraction>0.5f?lower+1.0f:fmod(lower,2.0f)==0.0f?lower:lower+1.0f;
}
struct CombatModel {
 float c[220]; float e[1920]; float env[5]; int ne;
 float stacks[160],expires[160],totals[5],next[5],ready[5],ammo[5],shots[5],warm[5],period[160];
 int shotsOut,cyclesOut;
void buffs(float t,int who,out float b[24]){
 for(int k=0;k<NS;k++)b[k]=c[who*CS+20+k];
 for(int i=0;i<ne;i++)if((int)e[i*ES+3]==0 && stacks[i]>0 && expires[i]>t-1e-8f && ((int)e[i*ES+1]&(1<<who)))b[(int)e[i*ES+2]]+=e[i*ES+6]*stacks[i];
}
float hit(int base,float b[24],float coeff,int normal,int full,int charged,int flags){
 float attack=hi(c[base+0]*(1+b[0]/100)+b[1]-hi(env[1]*(1+b[2]/100)+b[3],0)*(1-b[4]/100),0);
 float crit=lo(.15f+(b[5]+(normal?b[22]:0))/100,1)*hi(.5f+(b[6]+(normal?b[23]:0))/100,0);
 float core=normal && env[2]>0?lo(1,pow(env[2]/hi(c[base+13]*(1-.00908f*b[21]),1),2.55f)):0;
 float bonus=1+crit+(full?.5f:0)+(normal&&c[base+14]>.5f?.3f:0)+core*((c[base+12]-100+b[7])/100);
 float charge=charged?c[base+9]/100*(1+b[9]/100)+b[8]/100:1;
 float extra=b[10]+((flags&1)?b[13]:0)+((flags&2)?b[14]:0)+((flags&4)?b[15]:0)+((flags&8)?b[16]:0);
 float damage=coeff*(normal?1+b[11]/100:1)/100*attack*bonus*charge*(1+extra/100)*(1+b[12]/100)*(c[base+15]>.5f?1.1f+b[17]/100:1);
 return hi(roundDamage(damage),1);
}
[mutating] void event(float t,int ev,int who,int count,int full,int castmask){
 for(int j=0;j<ne;j++){
  float q[12];for(int k=0;k<ES;k++)q[k]=e[j*ES+k];int owner=(int)q[0],kind=(int)q[3],timing=(int)q[4];
  if(timing!=ev || (ev!=0&&ev!=1&&ev!=2&&ev!=3&&ev!=10&&owner!=who))continue;
  if(ev==3 && !(castmask&(1<<owner)))continue;
  if((ev==5||ev==6||ev==10) && (count<=0 || count%(int)q[5]))continue;
  if((int)q[9]==1&&!full || (int)q[9]==2&&full)continue;
  if(kind==0){stacks[j]=lo(stacks[j]+1,q[8]);expires[j]=q[7]<0?1e30f:t+q[7];}
  else if(kind==1){float b[NS];buffs(t,owner,b);totals[owner]+=hit(owner*CS,b,q[6],0,full,0,(int)q[10])*q[11];}
 }
}
[mutating] void run(){
 int totalshots=0,cycles=0;float fbend=-1,burstnext=3;int castmask=0;
 for(int j=0;j<ME;j++){stacks[j]=0;expires[j]=-1;period[j]=j<ne?e[j*ES+5]:0;}
 for(int i=0;i<5;i++){totals[i]=0;next[i]=c[i*CS+7];ready[i]=0;ammo[i]=c[i*CS+2];shots[i]=0;warm[i]=0;}
 event(0,0,0,0,0,0);
 for(int i=0;i<5;i++){float b[NS];buffs(0,i,b);ammo[i]=(int)hi(1,c[i*CS+2]*(1+b[18]/100));}
 int frames=(int)(env[0]*60+.00001f);
 for(int frame=0;frame<frames;frame++){
  float t=frame/60.0f;int full=int(t<fbend);
  if(!full && fbend>=0){event(t,2,0,0,0,castmask);fbend=-1;}
  if(!full && t+1e-8f>=burstnext){
   int chosen[3]={-1,-1,-1};
   for(int stage=1;stage<=3;stage++)for(int i=0;i<5;i++)if((int)c[i*CS+16]==stage&&ready[i]<=t+1e-8f){if(env[4]==i+1&&(cycles+1)%3!=0)continue;chosen[stage-1]=i;break;}
   if(chosen[0]>=0&&chosen[1]>=0&&chosen[2]>=0){
    cycles++;castmask=0;for(int s=0;s<3;s++){int i=chosen[s];castmask|=1<<i;ready[i]=t+c[i*CS+17];}
    // CDR is applied to the selected cooldowns, once per matching effect.
    event(t,3,0,0,0,castmask);
    for(int j=0;j<ne;j++)if((int)e[j*ES+3]==2&&((int)e[j*ES+4]==1||((int)e[j*ES+4]==3&&(castmask&(1<<(int)e[j*ES]))))){for(int i=0;i<5;i++)if((int)e[j*ES+1]&(1<<i))ready[i]-=e[j*ES+6];}
    fbend=t+10;full=1;burstnext=fbend+2;
    event(t,1,0,0,full,castmask);
   }
  }
  for(int j=0;j<ne;j++)if((int)e[j*ES+4]==4&&t+1e-8f>=period[j]){
   // Isolate this periodic effect without firing other periods.
   float q[ES];for(int k=0;k<ES;k++)q[k]=e[j*ES+k];q[4]=0;
   if(!((int)q[9]==1&&!full || (int)q[9]==2&&full)){
    if((int)q[3]==0){stacks[j]=lo(stacks[j]+1,q[8]);expires[j]=q[7]<0?1e30f:t+q[7];}
    else if((int)q[3]==1){int owner=(int)q[0];float b[NS];buffs(t,owner,b);totals[owner]+=hit(owner*CS,b,q[6],0,full,0,(int)q[10])*q[11];}
   }
   period[j]+=e[j*ES+5];
  }
  for(int i=0;i<5;i++){
   if(next[i]>t+1e-8f)continue;
   float a[44];for(int k=0;k<CS;k++)a[k]=c[i*CS+k];float b[NS];buffs(t,i,b);
   int cap=(int)hi(1,a[2]*(1+b[18]/100));
   if(ammo[i]<=0){ammo[i]=cap;warm[i]=0;event(t,8,i,0,full,castmask);}
   totals[i]+=hit(i*CS,b,a[1]/a[10],1,full,int(a[7]>0),0)*a[10]*a[11];
   ammo[i]--;shots[i]++;totalshots++;warm[i]++;
   event(t,5,i,(int)shots[i],full,castmask);
   event(t,6,i,(int)(shots[i]*a[10]*a[11]),full,castmask);
   event(t,10,i,totalshots,full,castmask);
   if(a[7]>0)event(t,9,i,0,full,castmask);
   float interval=a[7]>0?hi(a[19],a[7]*hi(1-b[20]/100,.01f)+a[8]):1/hi(a[4]+(a[5]-a[4])*lo(warm[i]/hi(a[6],1),1),.01f);
   if(ammo[i]<=0){event(t,7,i,0,full,castmask);interval+=hi(a[3]*(1-b[19]/100),.05f);}
   next[i]=t+interval;
  }
 }
 shotsOut=totalshots;cyclesOut=cycles;
}
};
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
[shader("compute")]
[numthreads(1,1,1)]
void optimizerCombat(uint3 id:SV_DispatchThreadID){
 if(id.x>=commands[0])return;
 uint at=1+id.x*2146; CombatModel m;
 m.ne=int(commands[at]);
 for(uint i=0;i<220;i++)m.c[i]=asfloat(commands[at+1+i]);
 for(uint i=0;i<1920;i++)m.e[i]=asfloat(commands[at+221+i]);
 for(uint i=0;i<5;i++)m.env[i]=asfloat(commands[at+2141+i]);
 m.run();
 for(uint i=0;i<5;i++)results[id.x*7+i]=asuint(m.totals[i]);
 results[id.x*7+5]=asuint(float(m.shotsOut));results[id.x*7+6]=asuint(float(m.cyclesOut));
}
