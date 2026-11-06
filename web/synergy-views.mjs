/** Pure team views. Members are catalog metadata with optional growth settings. */
import {activeEffects,effectValue,damageGroups} from './damage-groups.mjs';
import {selectorMatches,conditionEffect,teamSynergy} from './synergy-model.mjs';
import {selectorLabel,conditionLabel,statShortLabel} from './synergy-labels.mjs';

const metaOf = member => member.meta ?? member;
const profileOf = member => metaOf(member).damage_groups ?? member.profile;
const ids = [...damageGroups.map(group => group.id),'count'];

/** Receiver arrays contain indexed giver entries; dynamic[g] is never assigned. */
export function receivedEffects(members, {includeSelf=false} = {}) {
  const receivers = members.map(() => []), dynamic = members.map(() => []);
  members.forEach((member,from) => {
    const seen = new Set();
    for (const effect of activeEffects(profileOf(member),member.favoriteStage)) {
      if (!ids.includes(effect.group)) continue;
      const key = JSON.stringify([effect.name,effect.stat,effect.scope]);
      if (seen.has(key)) continue;
      seen.add(key);
      const slot = effect.source?.match(/스킬(\d+)/)?.[1];
      const entry = {from,stat:effect.stat,group:effect.group,
        value:effectValue(effect,member.skillLevels?.[slot]),scope:effect.scope,
        source:effect.source,dynamic:false,
        conditional:effect.scope === 'ally' && effect.selector?.kind === 'trait' && !!effect.selector.rule};
      const selector = effect.selector;
      if (effect.scope === 'ally' && selector?.kind === 'dynamic') {
        dynamic[from].push({...entry,dynamic:true});
        continue;
      }
      members.forEach((receiver,r) => {
        if (effect.scope === 'enemy' ||
            (effect.scope === 'self' && includeSelf && from === r) ||
            (effect.scope === 'ally' && selector && selectorMatches(selector,metaOf(member),metaOf(receiver)))) {
          receivers[r].push(entry);
        }
      });
    }
  });
  return {receivers,dynamic};
}

export function receiveSummary(members, opts) {
  const {receivers,dynamic} = receivedEffects(members,opts);
  return receivers.map(entries => {
    const groups = Object.fromEntries(damageGroups.map(({id}) => [id,{total:0,from:[]}]));
    const count = [];
    for (const entry of entries) {
      if (entry.group === 'count') {
        if (!count.includes(entry.stat)) count.push(entry.stat);
      } else {
        const group = groups[entry.group], name = metaOf(members[entry.from]).name;
        group.total += entry.value ?? 0;
        if (!group.from.includes(name)) group.from.push(name);
      }
    }
    return {groups,count,dynamic:dynamic.flat()};
  });
}

export function synergyMatrix(members, {includeSelf=false} = {}) {
  const {receivers,dynamic} = receivedEffects(members,{includeSelf});
  const cells = members.map(() => members.map(() => ({groups:new Set(),entries:[]})));
  receivers.forEach((entries,r) => {
    for (const entry of entries) {
      if (entry.from === r && !includeSelf) continue;
      const cell = cells[entry.from][r];
      cell.groups.add(entry.group);
      cell.entries.push(entry);
    }
  });
  return {cells,dynamic};
}

const selectorKey = selector => JSON.stringify(Object.entries(selector).sort(([a],[b]) => a.localeCompare(b)));
function sortedStats(owner, entries) {
  const damage = new Set((owner.damage_groups?.effects ?? []).map(effect => effect.stat));
  return [...new Set(entries.map(entry => entry.stat))].sort((a,b) => Number(damage.has(b))-Number(damage.has(a)));
}
const statText = stats => [...new Set(stats.map(statShortLabel))].join('・');

/** Resolve each owner's opposite branches once for all team views. */
export function teamViewConditions(members) {
  const result = [], metas = members.map(metaOf);
  for (const owner of metas) {
    const conditions = owner.synergy?.conditions ?? [], seen = new Set();
    for (const condition of conditions) {
      const key = JSON.stringify([condition.kind,condition.value]);
      if (seen.has(key)) continue;
      seen.add(key);
      const pair = conditions.filter(c => c.kind === condition.kind && c.value === condition.value);
      const positive = pair.find(c => !c.negate), negative = pair.find(c => c.negate);
      const present = conditionEffect({...condition,negate:false},owner,metas) === 'satisfied';
      const holds = present ? positive : negative;
      result.push({owner,condition:holds ?? positive ?? negative,
        effect:holds ? 'satisfied' : positive && !present ? 'unmet' : 'broken',
        paired:!!(positive && negative)});
    }
  }
  return result;
}

/** Text remains structured so the UI can translate character names with label(). */
export function synergyPoints(members) {
  const metas = members.map(metaOf), data = teamSynergy(metas), wasted = new Map();
  for (const {owner,entry} of data.unmatched) {
    const key = JSON.stringify([owner.name,selectorKey(entry.selector)]);
    if (!wasted.has(key)) wasted.set(key,{kind:'wasted',owner:owner.name,selector:entry.selector,entries:[]});
    wasted.get(key).entries.push(entry);
  }
  const warnings = [...wasted.values()].map(({entries,...item}) => {
    const stats = sortedStats(metas.find(meta => meta.name === item.owner),entries);
    return {...item,stats,statsText:statText(stats)};
  });
  const ok = [];
  for (const {owner,condition,effect} of teamViewConditions(metas)) {
    const item = {owner:owner.name,condition,conditionText:conditionLabel(condition)};
    if (effect === 'satisfied') ok.push({kind:'condition-ok',...item});
    else warnings.push({kind:effect === 'unmet' ? 'condition-missing' : 'condition-broken',...item});
  }
  const links = data.links.map(link => {
    const stats = sortedStats(link.from,link.relations);
    return {kind:'link',from:link.from.name,to:link.to.name,tier:link.tier,stats,statsText:statText(stats),
      reasons:[...new Set(link.relations.filter(entry => entry.tier === 'B').map(entry => selectorLabel(entry.selector)))]};
  }).sort((a,b) => a.tier.localeCompare(b.tier));
  const priority = {wasted:0,'condition-missing':1,'condition-broken':2};
  warnings.sort((a,b) => priority[a.kind]-priority[b.kind]);
  const count = data.global.reduce((sum,item) => sum+item.entries.length,0);
  return [...warnings,...links,...ok,...(count ? [{kind:'info',count}] : [])];
}
