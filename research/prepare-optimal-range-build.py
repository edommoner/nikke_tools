"""One-shot v25 assembly, preserving the last verified source and binaries."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','scripts/build-combat.py','scripts/build-detail-native.py']
texts={f:(ROOT/f).read_text(encoding='utf-8') for f in files}
assert "DETAIL_ABI='detail_charge_immunity_v24'" in texts['app/detail_gpu.py']
archive=ROOT/'research/ports/v24';archive.mkdir(exist_ok=True)
for f in files+['app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json']:
    target=archive/Path(f).name;assert not target.exists(),target;target.write_bytes((ROOT/f).read_bytes())
def replace(t,old,new):
    assert t.count(old)==1,(old[:90],t.count(old));return t.replace(old,new)
host=texts[files[0]].replace('detail_charge_immunity_v24','detail_optimal_range_v25').replace('detail_state_bytes_v24','detail_state_bytes_v25')
host=replace(host,"'burst_charge_speed_pct':60}","'burst_charge_speed_pct':60,'optimal_range_min':61,'optimal_range_max_pct':62}")
host=replace(host,'NE,EW,CW,OW=128,264,168,48','NE,EW,CW,OW=128,268,168,48')
host=replace(host,"    elif condition=='not_core':typ=27","    elif condition=='optimal_range':\n     if '_detail_range' not in c:raise UnsupportedDetail('optimal range metadata is required')\n     typ=33\n    elif condition=='not_core':typ=27")
host=replace(host,"   elif kind=='buff' and stat in EXTRA:q[1]=0;q[2]=EXTRA[stat]","   elif kind=='buff' and stat in EXTRA:\n    if stat in ('optimal_range_min','optimal_range_max_pct') and any('_detail_range' not in ch for ch in chars):raise UnsupportedDetail('optimal range metadata is required')\n    q[1]=0;q[2]=EXTRA[stat]")
host=replace(host,"    q[249]=float(_pick('burst_energy',over,eff,defaults,default=0))","    from calculator.buff_manager import optimal_range_of\n    q[264:266]=optimal_range_of(caster,weapon)\n    q[249]=float(_pick('burst_energy',over,eff,defaults,default=0))")
host=replace(host,"  # Five exact 32-bit words encode explicitly prioritized cycles 1..160.","  if '_detail_range' in c:\n   lo,hi,distance=c['_detail_range']\n   if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (lo,hi)) or lo<0 or hi<lo or distance is not None and (not isinstance(distance,(int,float)) or not math.isfinite(distance)):raise ValueError('Invalid compiled optimal range')\n   r[164:168]=[lo,hi,0 if distance is None else distance,1 if distance is None else 2]\n  # Five exact 32-bit words encode explicitly prioritized cycles 1..160.")
host=replace(host,'not 0<=r[2]<61','not 0<=r[2]<63')
host=replace(host," if any(b[0]<a[0] for a,b in zip(script,script[1:])):"," if any(row[1]==2 and row[2]==113 and row[4] not in (0,1) for row in script):raise ValueError('Invalid optimal range query')\n if any(b[0]<a[0] for a,b in zip(script,script[1:])):")
host=replace(host,"  from calculator.buff_manager import in_optimal_range\n  c['_detail_mode_optimal']", "  from calculator.buff_manager import in_optimal_range,optimal_range_of\n  lo,hi=optimal_range_of(c['name'],st.weapon_type)\n  c['_detail_range']=[lo,hi,distance]\n  c['_optimal']=in_optimal_range(enemy,c['name'],st.weapon_type,{})\n  c['_detail_mode_optimal']")
cu=texts[files[1]].replace('detail_charge_immunity_v24','detail_optimal_range_v25').replace('detail_state_bytes_v24','detail_state_bytes_v25')
cu=replace(cu,'#define EW 264','#define EW 268')
cu=replace(cu,'double cached[5][61]','double cached[5][63]')
helper='''// Authoritative CPU interval semantics, evaluated from live range buffs.
// Predicate uses the innate weapon; outgoing shots use their weapon context.
__device__ int optimal_range(const double* c,const double* e,int ne,State* s,int who,int full,int use_mode){
 const double* a=c+who*CW;
 const double* mode=use_mode&&s->weapon_context[who]&&s->mode[who]>=0?effect(e,s,s->mode[who]):0;
 if(a[167]<2)return (mode?mode[30]:a[14])>.5;
 double lo=mode?mode[264]:a[164],hi=mode?mode[265]:a[165],d=a[166];
 hi*=1+stat(c,e,ne,s,who,62,full)/100;
 lo=mx(0,lo*(1-stat(c,e,ne,s,who,61,full)/100));
 return lo-1e-9<=d&&d<=hi+1e-9;
}
'''
anchor='__device__ int base_condition(const double* c,const double* e,int ne,State* s,const double* q,int full,int runtime,int slot,double core_frac,int hit_crit,int first,int limit){'
cu=replace(cu,anchor,helper+anchor)
cu=replace(cu,'  else if(!base_condition(c,e,ne,s,q,full,0,slot,core_frac,hit_crit,j,1))return 0;', '  else if((int)q[15+j*3]==33){if(!optimal_range(c,e,ne,s,(int)q[0],full,0))return 0;}\n  else if(!base_condition(c,e,ne,s,q,full,0,slot,core_frac,hit_crit,j,1))return 0;')
cu=replace(cu,'(normal&&(mode?mode[30]:a[14])>.5?.3:0)','(normal&&optimal_range(c,e,ne,s,who,full,1)?.3:0)')
cu=replace(cu,'   if(ev==103){dst[0]=stat(c,e,ne,s,who,arg,full);continue;}','   if(ev==113){dst[0]=optimal_range(c,e,ne,s,who,full,arg);continue;}\n   if(ev==103){dst[0]=stat(c,e,ne,s,who,arg,full);continue;}')
for f,t in [(files[0],host),(files[1],cu)]+[(f,texts[f].replace('detail_charge_immunity_v24','detail_optimal_range_v25')) for f in files[2:]]:
    (ROOT/f).write_text(t,encoding='utf-8')
print('Prepared v25 dynamic optimal range source; binaries must be rebuilt')
