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
