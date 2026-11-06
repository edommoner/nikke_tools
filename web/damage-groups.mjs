/** Static buff amounts, not uptime-weighted damage contributions. */
export const damageGroups = [
  {id:'1',mark:'①',label:'係数',full:'① 係数（通常攻撃ダメージ倍率）'},
  {id:'2',mark:'②',label:'攻撃力',full:'② 攻撃力・防御'},
  {id:'3',mark:'③',label:'ボーナス',full:'③ ボーナス（会心・コア）'},
  {id:'4',mark:'④',label:'チャージ',full:'④ チャージ'},
  {id:'5',mark:'⑤',label:'種類別',full:'⑤ ダメージ種類別（攻撃ダメージ・バースト・貫通など）'},
  {id:'6',mark:'⑥',label:'被ダメ',full:'⑥ 被ダメージ（敵の被ダメージ増加・分割）'},
  {id:'7',mark:'⑦',label:'優越',full:'⑦ 優越コード'},
];
export const countGroup = {id:'count',label:'回数系',full:'攻撃回数・回転（どのグループにも属さない）'};
const bounded = (value, fallback, min, max) => value == null || !Number.isFinite(Number(value))
  ? fallback : Math.max(min, Math.min(max, Math.trunc(Number(value))));
export function activeEffects(profile, favoriteStage) {
  const effects = profile?.effects ?? [], slots = profile?.favorite_slots ?? [];
  if (!slots.length) return effects;
  const stage = bounded(favoriteStage, 3, 0, 3);
  return effects.filter(effect => {
    const slot = Number(effect.source?.match(/스킬(\d+)/)?.[1]), i = slots.indexOf(slot);
    const favorite = i >= 0 && i + 1 <= stage ? i + 1 : null;
    return (effect.favorite ?? null) === favorite;
  });
}
export function effectValue(effect, skillLevel) {
  const level = bounded(skillLevel, 10, 1, 10);
  const value = effect.values ? effect.values[String(level)] : effect.fixed;
  const stack = Number.isInteger(effect.max_stack) && effect.max_stack >= 1 ? effect.max_stack : 1;
  return typeof value === 'number' && Number.isFinite(value) ? Math.abs(value) * stack : null;
}
const includesScope = (effect, includeSelf) => ['ally','enemy'].includes(effect.scope) || (includeSelf && effect.scope === 'self');
export function damageValue(entry) {
  if (entry.value === null) return '値なし';
  const flat = ['max_ammo_flat','ammo_charge_flat','pellet_count'].includes(entry.stat);
  return `+${flat ? Number(entry.value.toFixed(1)) : entry.value.toFixed(1)}${flat ? '' : '%'}`;
}
export function teamDamageGroups(members, {includeSelf=false} = {}) {
  const groups = damageGroups.map(({id}) => ({id,total:0,entries:[]})), count = {entries:[]}, unknown = [];
  for (const member of members) {
    const seen = new Set();
    for (const effect of activeEffects(member.profile, member.favoriteStage)) {
      if (!includesScope(effect, includeSelf)) continue;
      const group = groups.find(g => g.id === effect.group);
      if (!group && effect.group !== 'count') continue;
      const key = JSON.stringify([effect.name,effect.stat,effect.scope]);
      if (seen.has(key)) continue;
      seen.add(key);
      const slot = effect.source?.match(/스킬(\d+)/)?.[1];
      const value = effectValue(effect,member.skillLevels?.[slot]);
      const entry = {name:member.name,stat:effect.stat,scope:effect.scope,source:effect.source,value,caster_based:!!effect.caster_based};
      (group ?? count).entries.push(entry);
      if (group && value !== null) group.total += value;
      if (value === null) unknown.push(entry);
    }
  }
  return {groups,count,unknown};
}
export function providesGroup(profile, groupIds, {includeSelf=false,favoriteStage} = {}) {
  const selected = new Set(groupIds);
  return activeEffects(profile,favoriteStage).some(effect => selected.has(effect.group) &&
    includesScope(effect, includeSelf));
}
