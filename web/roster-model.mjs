/** Roster ordering uses observed values only; missing values always sort last. */
import {validPatterns} from './phase-model.mjs';
import {validParts} from './parts-model.mjs';
export const elementLabels={'풍압':'風圧','수냉':'水冷','작열':'灼熱','전격':'電撃','철갑':'鉄甲'};
export const manufacturerLabels={'엘리시온':'エリシオン','미실리스':'ミシリス','테트라':'テトラ','필그림':'ピルグリム','어브노말':'アブノーマル'};
const iconBase='https://www.blablalink.com/assets/nikke/version/default/shiftysassets/images/';
const manufacturerIcons={'엘리시온':'elysion','미실리스':'missilis','테트라':'tetra','필그림':'pilgrim','어브노말':'abnormal'};
const elementIcons={'풍압':'wind','수냉':'water','작열':'fire','전격':'electric','철갑':'iron'};
const weapons=['AR','SMG','SG','MG','SR','RL'];
export function manufacturerIconUrl(value){return Object.hasOwn(manufacturerIcons,value)?`${iconBase}icon-manufacturer-${manufacturerIcons[value]}--white.png`:null;}
export function elementIconUrl(value){return Object.hasOwn(elementIcons,value)?`${iconBase}icon-code-${elementIcons[value]}.png`:null;}
export function burstIconUrl(value){return ['1','2','3'].includes(value)?`${iconBase}icon-burst-${value}.png`:null;}
export function matchesRosterFilters(meta,filters){
  return Object.entries(filters).every(([category,selected])=>{
    if(!selected.size)return true;
    const value=meta?.[category];
    if(category==='burst')return value==='A'||(['1','2','3'].includes(value)&&selected.has(value));
    const known=category==='manufacturer'?Object.hasOwn(manufacturerLabels,value):category==='element'?Object.hasOwn(elementLabels,value):category==='weapon'&&weapons.includes(value);
    return known&&selected.has(value);
  });
}
export function skillValues(value){if(typeof value==='number')return [value,value,value];if(typeof value==='string')return value.split('/').map(Number);return Array.isArray(value)?value:['1','2','3'].map(k=>value?.[k]);}
export function rosterValue(entry,field){
  if(field==='power')return numeric(entry._observed_combat_power);
  if(field==='limit'){const b=numeric(entry.breakthrough),c=numeric(entry.core_enhancement);return b===null||c===null?null:b+c;}
  if(field==='skill'){const v=skillValues(entry.skill_levels);return v.length===3&&v.every(n=>numeric(n)!==null)?v.reduce((a,b)=>a+b,0):null;}
  if(field==='burst')return numeric(skillValues(entry.skill_levels)[2]);
  if(field==='affinity')return numeric(entry.affinity);
  if(field==='level')return numeric(entry._observed_level);
  if(field==='favorite')return numeric(entry.favorite_stage);
  return null;
}
function numeric(v){return typeof v==='number'&&Number.isFinite(v)&&v>=0?v:null;}
export function sortRoster(names,{field='default',direction='desc',entry,label}){
  if(field==='default')return [...names];
  return [...names].sort((a,b)=>{
    if(field==='name')return label(a).localeCompare(label(b),'ja')*(direction==='asc'?1:-1);
    const x=rosterValue(entry(a),field),y=rosterValue(entry(b),field);
    if(x===null||y===null)return x===y?label(a).localeCompare(label(b),'ja'):x===null?1:-1;
    return (x-y)*(direction==='asc'?1:-1)||label(a).localeCompare(label(b),'ja');
  });
}
export function visibleTeams(single,active,count){return single?[active]:Array.from({length:count},(_,i)=>i);}
export const presetFields=['enemy-def','enemy-code','level','duration','core','distance'];
export function validPreset(p){const s=p?.settings;return (p?.patterns===undefined||validPatterns(p.patterns))&&(p?.parts===undefined||validParts(p.parts))&&typeof p?.label==='string'&&p.label.trim().length>0&&p.label.length<=80&&s&&
  Object.keys(elementLabels).includes(s['enemy-code'])&&[['enemy-def',0,1e9],['level',1,1000],['duration',1,180],['core',0,1000],['distance',0,1000]].every(([k,min,max])=>typeof s[k]==='number'&&Number.isFinite(s[k])&&s[k]>=min&&s[k]<=max)&&Number.isInteger(s.level);}

export const overloadFields = [
  ['atk-pct', 'atk_pct', '攻撃力'],
  ['element', 'element_bonus', '有利コード'],
  ['max-ammo-pct', 'max_ammo_pct', '最大装弾数'],
  ['charge-speed-pct', 'charge_speed_pct', 'チャージ速度'],
  ['charge-dmg-pct', 'charge_dmg_pct', 'チャージダメージ'],
  ['crit-rate', 'crit_rate', 'クリティカル確率'],
  ['crit-dmg', 'crit_dmg', 'クリティカルダメージ'],
  ['accuracy-pct', 'accuracy_pct', '命中率'],
  ['def-pct', 'def_pct', '防御力'],
];

export function formatOverload(value) {
  return Array.isArray(value) ? value.join(', ') : String(value ?? '');
}

// An untouched input preserves the imported scalar/list representation.
// Lists must remain lists: ammo and charge timing round by option group.
export function parseOverload(text, previous, label = 'オバロ') {
  text = text.trim();
  if (!text) return undefined;
  if (text === formatOverload(previous) && [previous].flat().every(v => typeof v === 'number' && Number.isFinite(v) && v >= 0)) {
    return structuredClone(previous);
  }
  const fields = text.split(/[,、]/).map(s => s.trim());
  if (fields.some(s => !/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(s) || !Number.isFinite(Number(s)))) {
    throw Error(`${label}は0以上の数値で入力してください。複数枠はカンマで区切ります。`);
  }
  const values = fields.map(Number);
  return values.length === 1 ? values[0] : values;
}
