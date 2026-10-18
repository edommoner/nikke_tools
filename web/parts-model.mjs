export const reachLabels=['','貫通・爆発・パーツ指定','貫通範囲100%以上・爆発・パーツ指定','爆発・パーツ指定','爆発範囲100%以上・パーツ指定','パーツ指定スキルのみ'];
export function normalizeParts(value){
 if(!Array.isArray(value)||value.length>32)throw Error('パーツは32個まで指定できます。');
 const names=new Set();return value.map(p=>{
  if(!p||Object.keys(p).sort().join(',')!=='hp,name,reach'||typeof p.name!=='string'||!p.name.trim()||p.name.length>80||names.has(p.name))throw Error('パーツ名は重複しない80文字以内の名前にしてください。');
  if(typeof p.hp!=='number'||!Number.isFinite(p.hp)||p.hp<0||p.hp>1e15||!Number.isInteger(p.reach)||p.reach<1||p.reach>5)throw Error('パーツHPは0〜1,000,000,000,000,000、到達段階は1〜5で指定してください。');
  names.add(p.name);return {name:p.name,hp:p.hp,reach:p.reach};
 });
}
export function validParts(value){try{normalizeParts(value);return true;}catch{return false;}}
