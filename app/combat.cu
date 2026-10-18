// Approximate search model: one independent squad timeline per CUDA thread.
// The pinned CPU engine remains the final scoring authority. See gpu_combat.py.
#define CS 44
#define ES 12
#define NS 24
#define ME 160
__device__ double hi(double a,double b){return a>b?a:b;}
__device__ double lo(double a,double b){return a<b?a:b;}
__device__ void buffs(const double* c,const double* e,int ne,const double* stacks,const double* expires,double t,int who,double* b){
 for(int k=0;k<NS;k++)b[k]=c[who*CS+20+k];
 for(int i=0;i<ne;i++)if((int)e[i*ES+3]==0 && stacks[i]>0 && expires[i]>t-1e-8 && ((int)e[i*ES+1]&(1<<who)))b[(int)e[i*ES+2]]+=e[i*ES+6]*stacks[i];
}
__device__ double hit(const double* c,const double* b,const double* env,double coeff,int normal,int full,int charged,int flags){
 double attack=hi(c[0]*(1+b[0]/100)+b[1]-hi(env[1]*(1+b[2]/100)+b[3],0)*(1-b[4]/100),0);
 double crit=lo(.15+(b[5]+(normal?b[22]:0))/100,1)*hi(.5+(b[6]+(normal?b[23]:0))/100,0);
 double core=normal && env[2]>0?lo(1,pow(env[2]/hi(c[13]*(1-.00908*b[21]),1),2.55)):0;
 double bonus=1+crit+(full?.5:0)+(normal&&c[14]>.5?.3:0)+core*((c[12]-100+b[7])/100);
 double charge=charged?c[9]/100*(1+b[9]/100)+b[8]/100:1;
 double extra=b[10]+((flags&1)?b[13]:0)+((flags&2)?b[14]:0)+((flags&4)?b[15]:0)+((flags&8)?b[16]:0);
 double damage=coeff*(normal?1+b[11]/100:1)/100*attack*bonus*charge*(1+extra/100)*(1+b[12]/100)*(c[15]>.5?1.1+b[17]/100:1);
 return hi((double)__double2ll_rn(damage),1);
}
__device__ void event(const double* c,const double* e,int ne,const double* env,double t,int ev,int who,int count,int full,int castmask,double* stacks,double* expires,double* totals){
 for(int j=0;j<ne;j++){
  const double* q=e+j*ES;int owner=(int)q[0],kind=(int)q[3],timing=(int)q[4];
  if(timing!=ev || (ev!=0&&ev!=1&&ev!=2&&ev!=3&&ev!=10&&owner!=who))continue;
  if(ev==3 && !(castmask&(1<<owner)))continue;
  if((ev==5||ev==6||ev==10) && (count<=0 || count%(int)q[5]))continue;
  if((int)q[9]==1&&!full || (int)q[9]==2&&full)continue;
  if(kind==0){stacks[j]=lo(stacks[j]+1,q[8]);expires[j]=q[7]<0?1e30:t+q[7];}
  else if(kind==1){double b[NS];buffs(c,e,ne,stacks,expires,t,owner,b);totals[owner]+=hit(c+owner*CS,b,env,q[6],0,full,0,(int)q[10])*q[11];}
 }
}
extern "C" __global__ void combat(const double* chars,const double* effects,const int* counts,const double* enemies,double* output,int n){
 int id=blockIdx.x*blockDim.x+threadIdx.x;if(id>=n)return;
 const double* c=chars+id*5*CS;const double* e=effects+id*ME*ES;const double* env=enemies+id*5;int ne=counts[id];
 double stacks[ME],expires[ME],totals[5],next[5],ready[5],ammo[5],shots[5],warm[5],period[ME];
 int totalshots=0,cycles=0;double fbend=-1,burstnext=3;int castmask=0;
 for(int j=0;j<ME;j++){stacks[j]=0;expires[j]=-1;period[j]=j<ne?e[j*ES+5]:0;}
 for(int i=0;i<5;i++){totals[i]=0;next[i]=c[i*CS+7];ready[i]=0;ammo[i]=c[i*CS+2];shots[i]=0;warm[i]=0;}
 event(c,e,ne,env,0,0,0,0,0,0,stacks,expires,totals);
 for(int i=0;i<5;i++){double b[NS];buffs(c,e,ne,stacks,expires,0,i,b);ammo[i]=(int)hi(1,c[i*CS+2]*(1+b[18]/100));}
 int frames=(int)(env[0]*60+.00001);
 for(int frame=0;frame<frames;frame++){
  double t=frame/60.0;int full=t<fbend;
  if(!full && fbend>=0){event(c,e,ne,env,t,2,0,0,0,castmask,stacks,expires,totals);fbend=-1;}
  if(!full && t+1e-8>=burstnext){
   int chosen[3]={-1,-1,-1};
   for(int stage=1;stage<=3;stage++)for(int i=0;i<5;i++)if((int)c[i*CS+16]==stage&&ready[i]<=t+1e-8){if(env[4]==i+1&&(cycles+1)%3!=0)continue;chosen[stage-1]=i;break;}
   if(chosen[0]>=0&&chosen[1]>=0&&chosen[2]>=0){
    cycles++;castmask=0;for(int s=0;s<3;s++){int i=chosen[s];castmask|=1<<i;ready[i]=t+c[i*CS+17];}
    // CDR is applied to the selected cooldowns, once per matching effect.
    event(c,e,ne,env,t,3,0,0,0,castmask,stacks,expires,totals);
    for(int j=0;j<ne;j++)if((int)e[j*ES+3]==2&&((int)e[j*ES+4]==1||((int)e[j*ES+4]==3&&(castmask&(1<<(int)e[j*ES]))))){for(int i=0;i<5;i++)if((int)e[j*ES+1]&(1<<i))ready[i]-=e[j*ES+6];}
    fbend=t+10;full=1;burstnext=fbend+2;
    event(c,e,ne,env,t,1,0,0,full,castmask,stacks,expires,totals);
   }
  }
  for(int j=0;j<ne;j++)if((int)e[j*ES+4]==4&&t+1e-8>=period[j]){
   // Isolate this periodic effect without firing other periods.
   double q[ES];for(int k=0;k<ES;k++)q[k]=e[j*ES+k];q[4]=0;
   if(!((int)q[9]==1&&!full || (int)q[9]==2&&full)){
    if((int)q[3]==0){stacks[j]=lo(stacks[j]+1,q[8]);expires[j]=q[7]<0?1e30:t+q[7];}
    else if((int)q[3]==1){int owner=(int)q[0];double b[NS];buffs(c,e,ne,stacks,expires,t,owner,b);totals[owner]+=hit(c+owner*CS,b,env,q[6],0,full,0,(int)q[10])*q[11];}
   }
   period[j]+=e[j*ES+5];
  }
  for(int i=0;i<5;i++){
   if(next[i]>t+1e-8)continue;
   const double* a=c+i*CS;double b[NS];buffs(c,e,ne,stacks,expires,t,i,b);
   int cap=(int)hi(1,a[2]*(1+b[18]/100));
   if(ammo[i]<=0){ammo[i]=cap;warm[i]=0;event(c,e,ne,env,t,8,i,0,full,castmask,stacks,expires,totals);}
   totals[i]+=hit(a,b,env,a[1]/a[10],1,full,a[7]>0,0)*a[10]*a[11];
   ammo[i]--;shots[i]++;totalshots++;warm[i]++;
   event(c,e,ne,env,t,5,i,(int)shots[i],full,castmask,stacks,expires,totals);
   event(c,e,ne,env,t,6,i,(int)(shots[i]*a[10]*a[11]),full,castmask,stacks,expires,totals);
   event(c,e,ne,env,t,10,i,totalshots,full,castmask,stacks,expires,totals);
   if(a[7]>0)event(c,e,ne,env,t,9,i,0,full,castmask,stacks,expires,totals);
   double interval=a[7]>0?hi(a[19],a[7]*hi(1-b[20]/100,.01)+a[8]):1/hi(a[4]+(a[5]-a[4])*lo(warm[i]/hi(a[6],1),1),.01);
   if(ammo[i]<=0){event(c,e,ne,env,t,7,i,0,full,castmask,stacks,expires,totals);interval+=hi(a[3]*(1-b[19]/100),.05);}
   next[i]=t+interval;
  }
 }
 for(int i=0;i<5;i++)output[id*7+i]=totals[i];output[id*7+5]=totalshots;output[id*7+6]=cycles;
}
