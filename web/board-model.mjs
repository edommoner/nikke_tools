/** Immutable helpers for the visible five-squad board. */
export const emptyTeams=()=>Array.from({length:5},()=>Array(5).fill(''));
export function placeCharacter(teams,team,slot,name){
  if(!Number.isInteger(team)||team<0||team>=5||!Number.isInteger(slot)||slot<0||slot>=5)throw Error('Invalid slot');
  const next=teams.map(row=>[...row]);
  let source;
  for(let t=0;t<next.length;t++)for(let s=0;s<next[t].length;s++)if(name&&next[t][s]===name)source=[t,s];
  if(source?.[0]===team&&source[1]===slot)return next;
  const displaced=next[team][slot];next[team][slot]=name;
  if(source)next[source[0]][source[1]]=displaced;
  return next;
}
export function restoreTeams(raw,owned){
  const next=emptyTeams(),used=new Set();
  for(let t=0;t<5;t++)for(let s=0;s<5;s++){
    const name=raw?.[t]?.[s];
    if(name&&owned.has(name)&&!used.has(name)){next[t][s]=name;used.add(name);}
  }
  return next;
}
export function completeTeams(teams,count=5){return teams.slice(0,count).map((squad,index)=>({squad,index})).filter(t=>t.squad.every(Boolean));}

export function normalizeTeamPreset(raw){
  if(!raw||typeof raw.id!=='string'||!raw.id.startsWith('team:')||typeof raw.name!=='string')return null;
  const name=raw.name.trim(),members=raw.members;
  if(!name||name.length>40||!Array.isArray(members)||members.length!==5||!Array.from(members).every(n=>typeof n==='string'))return null;
  const filled=members.filter(Boolean);
  if(!filled.length||new Set(filled).size!==filled.length)return null;
  return {id:raw.id,name,members:[...members],saved_at:typeof raw.saved_at==='string'?raw.saved_at:''};
}
export function normalizeTeamPresets(list){
  const result=[],ids=new Set();
  if(!Array.isArray(list))return result;
  for(const raw of list){
    const preset=normalizeTeamPreset(raw);
    if(!preset||ids.has(preset.id))continue;
    result.push(preset);ids.add(preset.id);
    if(result.length===50)break;
  }
  return result;
}
export function applyTeamPreset(teams,team,members,owned){
  if(!Number.isInteger(team)||team<0||team>=5)throw Error('Invalid slot');
  const next=teams.map(row=>[...row]),missing=[],moved=[];
  next[team]=members.map(name=>{if(!name||owned.has(name))return name;if(!missing.includes(name))missing.push(name);return '';});
  const placed=new Set(next[team].filter(Boolean));
  for(let t=0;t<next.length;t++)if(t!==team)for(let s=0;s<next[t].length;s++){
    const name=next[t][s];
    if(placed.has(name)){next[t][s]='';moved.push({name,from:t});}
  }
  return {teams:next,moved,missing};
}
export function presetDefaultName(members,labelFn){
  const names=members.filter(Boolean).map(name=>labelFn(name));
  return names.slice(0,2).join('・')+(names.length>2?' ほか':'');
}
