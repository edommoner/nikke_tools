/** Preserve imported boss definitions; the engine validates the full grammar. */
export function normalizePatterns(value){
 if(!Array.isArray(value)||value.length>128)throw Error('ボス行動は128件以内で指定してください。');
 const valid=v=>{if(typeof v==='number')return Number.isFinite(v);if(v===null||typeof v==='string'||typeof v==='boolean')return true;if(Array.isArray(v))return v.every(valid);return typeof v==='object'&&Object.values(v).every(valid);};
 if(value.some(p=>!p||Array.isArray(p)||typeof p!=='object'||typeof p.kind!=='string'||!valid(p))||JSON.stringify(value).length>262144)throw Error('ボス行動の定義が不正、または大きすぎます。');
 return structuredClone(value);
}
export function validPatterns(value){try{normalizePatterns(value);return true;}catch{return false;}}
export function makePhase({id,kind,wait=0,duration=5,value=6,repeat=false}){
 if(typeof id!=='string'||!id||!['core','move'].includes(kind)||typeof repeat!=='boolean')throw Error('コア出現または移動を指定してください。');
 if(![wait,duration,value].every(v=>typeof v==='number'&&Number.isFinite(v))||wait<0||wait>180||duration<=0||duration>180||value<0||value>1000||kind==='core'&&(!Number.isInteger(value)||value<1))throw Error('待ち時間は0〜180秒、継続時間は0より大きい180秒以内、コアは1〜1000の整数、距離は0〜1000で指定してください。');
 return {id,kind,delay:wait,until:{time:duration},after:repeat?['start',id]:['start'],repeat:repeat?0:1,[kind==='core'?'core_px':'distance']:value,note:kind==='core'?'コア出現':'距離変更'};
}
export function editablePhase(p){
 if(!p||!['core','move'].includes(p.kind)||typeof p.id!=='string')return null;
 const field=p.kind==='core'?'core_px':'distance',allowed=new Set(['id','kind','delay','until','after','repeat',field,'note']);
 if(Object.keys(p).some(k=>!allowed.has(k))||!p.until||Object.keys(p.until).join(',')!=='time')return null;
 const repeat=p.repeat===0;if(![0,1,undefined].includes(p.repeat)||JSON.stringify(p.after||['start'])!==JSON.stringify(repeat?['start',p.id]:['start']))return null;
 const value={id:p.id,kind:p.kind,wait:p.delay??0,duration:p.until.time,value:p[field],repeat};
 try{makePhase(value);return value;}catch{return null;}
}
