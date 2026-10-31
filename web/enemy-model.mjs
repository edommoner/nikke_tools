import {elementLabels,presetFields} from './roster-model.mjs';
import {normalizePatterns} from './phase-model.mjs';

const declaredNames={enemy_healing:'敵回復',weighted_incoming:'ダメージ配分',cover_defense:'遮蔽DEF',enemy_ammo:'敵弾倉',enemy_movement:'敵移動',named_range:'範囲・対象数',lock_on:'Lock On'};
const record=value=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&[Object.prototype,null].includes(Object.getPrototypeOf(value));
function finiteJson(value,depth=0){
 if(depth>32)return false;
 if(typeof value==='number')return Number.isFinite(value);
 if(value===null||typeof value==='string'||typeof value==='boolean')return true;
 if(Array.isArray(value))return value.every(v=>finiteJson(v,depth+1));
 return record(value)&&Object.values(value).every(v=>finiteJson(v,depth+1));
}
function normalizeManualCover(value){
 if(!record(value)||!Object.keys(value).length||Object.keys(value).length>5)throw Error('手動遮蔽は部隊内のキャラ名ごとに指定してください。');
 for(const [name,rows] of Object.entries(value)){
  if(!name.trim()||!Array.isArray(rows)||rows.length<1||rows.length>8)throw Error('手動遮蔽はキャラごとに1〜8操作で指定してください。');
  let previous=-1;
  for(const row of rows){
   if(!record(row)||Object.keys(row).length!==3||!['action','t','duration'].every(k=>Object.hasOwn(row,k))||row.action!=='cover'||![row.t,row.duration].every(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0&&v<=180)||row.t<previous)throw Error('手動遮蔽には開始時刻順の action: cover、t、duration（0〜180秒）だけを指定してください。');
   previous=row.t;
  }
 }
 return structuredClone(value);
}
/** Preserve authored declarations; the Python consumers validate mechanics. */
export function normalizeDeclaredScenario(value={}){
 if(!record(value)||!finiteJson(value)||JSON.stringify(value).length>1048576||Object.keys(value).some(k=>!['reference_models','enemy','manual_cover_sequences'].includes(k)))throw Error('宣言モデルは reference_models と任意の enemy.patterns・manual_cover_sequences だけのJSONオブジェクトで、1MB以内にしてください。');
 const models=value.reference_models??{};
 if(!record(models)||Object.keys(models).some(k=>!Object.hasOwn(declaredNames,k)))throw Error('接続済みの宣言モデル名を指定してください。');
 if(value.enemy!==undefined&&(!record(value.enemy)||Object.keys(value.enemy).some(k=>k!=='patterns')||!Object.hasOwn(value.enemy,'patterns')))throw Error('宣言する敵条件は enemy.patterns だけ指定できます。');
 if(!Object.keys(models).length){if(value.enemy!==undefined||value.manual_cover_sequences!==undefined)throw Error('敵行動・手動遮蔽と一緒に reference_models を指定してください。');return {};}
 return {reference_models:structuredClone(models),...(value.enemy===undefined?{}:{enemy:{patterns:normalizePatterns(value.enemy.patterns)}}),...(value.manual_cover_sequences===undefined?{}:{manual_cover_sequences:normalizeManualCover(value.manual_cover_sequences)})};
}
export function normalizeDeclaredTeams(value={}){
 if(!record(value)||Object.keys(value).some(k=>!['0','1','2','3','4'].includes(k)))throw Error('宣言モデルの適用先は部隊1〜5で指定してください。');
 const result={};for(const [team,scenario] of Object.entries(value)){const checked=normalizeDeclaredScenario(scenario);if(checked.reference_models)result[team]=checked;}return result;
}
export function declaredScenarioLabel(value){return [...Object.keys(value?.reference_models||{}).map(k=>declaredNames[k]||k),...(value?.manual_cover_sequences?['手動遮蔽']:[])].join('・');}
export function applyDeclaredScenario(evaluation,value){
 const scenario=normalizeDeclaredScenario(value);if(!scenario.reference_models)return evaluation;
 if(scenario.manual_cover_sequences&&Object.keys(scenario.manual_cover_sequences).some(name=>!evaluation.squad?.includes(name)))throw Error('手動遮蔽の適用先が現在の部隊にいません。部隊のキャラ名で指定し直してください。');
 return {...evaluation,reference_models:scenario.reference_models,...(scenario.enemy?{enemy:{...evaluation.enemy,patterns:scenario.enemy.patterns}}:{}),...(scenario.manual_cover_sequences?{manual_cover_sequences:scenario.manual_cover_sequences}:{})};
}
export const enemyScope=(single,raidCount)=>single?'single':raidCount===1?'union':'solo';
export function groupPresets(records,scope){
 const groups=new Map();
 for(const row of records){const mode=row.mode||'solo';if(scope!=='single'&&mode!==scope)continue;
  const scalar=presetFields.map(k=>row.settings[k]);const key=JSON.stringify(row.patterns?.length||row.parts?.length?[scalar,row.parts||[],row.patterns||[]]:scalar);
  if(!groups.has(key))groups.set(key,{id:'group:'+scope+':'+key,mode:scope,settings:{...row.settings},...(row.parts?.length?{parts:structuredClone(row.parts)}:{}),...(row.patterns?.length?{patterns:structuredClone(row.patterns)}:{}),members:[]});
  groups.get(key).members.push({...row,mode});
 }
 return [...groups.values()].map(group=>{
  const names=[...new Set(group.members.map(p=>p.boss_name||p.label.replace(/^.*? \/ /,'').replace(/（静止近似）/,'')))];
  group.label=`${elementLabels[group.settings['enemy-code']]} / 防御${group.settings['enemy-def'].toLocaleString('ja-JP')} / ${names[0]}${names.length>1?' ほか':''}（${group.members.length}条件）`;
  group.note=`同じ計算入力の${group.members.length}条件をまとめています。敵HP・移動・パーツ・生存など未対応の条件の一致は意味しません。ニケLv${group.settings.level}・コア径${group.settings.core}px・距離${group.settings.distance}mは比較用の設定です。`;
  return group;
 });
}
