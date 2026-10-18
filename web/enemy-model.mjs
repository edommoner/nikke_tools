import {elementLabels,presetFields} from './roster-model.mjs';
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
