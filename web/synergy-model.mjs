/** Pure catalog synergy matching. Relation endpoints are catalog character objects. */
const sameCharacter = (a, b) => a.name === b.name;
const sameSquad = (a, b) => Boolean(a.squad) && a.squad === b.squad;
const burstMatches = (character, value) => character.burst === 'A' || character.burst === value;

export function selectorMatches(selector, provider, receiver) {
  if (selector.excl_self && sameCharacter(provider, receiver)) return false;
  switch (selector.kind) {
    case 'element': return receiver.element === selector.value;
    case 'weapon': return receiver.weapon === selector.value;
    case 'class': return receiver.class === selector.value;
    case 'element_weapon': return receiver.element === selector.element && receiver.weapon === selector.weapon;
    case 'squad': return sameSquad(provider, receiver);
    case 'squad_burst': return sameSquad(provider, receiver) && burstMatches(receiver, selector.value);
    case 'burst': return burstMatches(receiver, selector.value);
    case 'name': return receiver.name === selector.value;
    case 'trait': return receiver.synergy?.traits?.includes(selector.value) ?? false;
    case 'all':
    case 'dynamic': return true;
    default: return false;
  }
}

export function conditionEffect(condition, owner, others) {
  const matches = others.some(other => {
    if (sameCharacter(owner, other)) return false;
    switch (condition.kind) {
      case 'squad_member': return sameSquad(owner, other);
      case 'has_burst': return burstMatches(other, condition.value);
      case 'has_class': return other.class === condition.value;
      default: return false;
    }
  });
  return matches ? (condition.negate ? 'broken' : 'satisfied') : null;
}

export function synergyRelations(basis, candidate, {tiers = ['A', 'B']} = {}) {
  if (basis.some(member => sameCharacter(member, candidate))) return [];
  const relations = [];
  function connect(from, to) {
    for (const entry of from.synergy?.provides ?? []) {
      if (tiers.includes(entry.tier) && selectorMatches(entry.selector, from, to)) {
        relations.push({...entry, from, to, kind: 'provides'});
      }
    }
    if (!tiers.includes('A')) return;
    for (const condition of from.synergy?.conditions ?? []) {
      const effect = conditionEffect(condition, from, [to]);
      if (effect) relations.push({from, to, tier: 'A', kind: 'condition', condition, effect,
        source: condition.source, name: condition.name, favorite: condition.favorite ?? false});
    }
  }
  for (const member of basis) {
    connect(member, candidate);
    connect(candidate, member);
  }
  return relations;
}

export function rankSynergyCandidates(basis, candidates, {tiers = ['A', 'B'], weights = {A: 3, B: 2, C: 1}} = {}) {
  return candidates.map((character, index) => {
    const relations = synergyRelations(basis, character, {tiers});
    const involved = new Set();
    let score = 0;
    for (const relation of relations) {
      if (relation.effect === 'broken') continue;
      score += weights[relation.tier] ?? 0;
      involved.add(sameCharacter(relation.from, character) ? relation.to.name : relation.from.name);
    }
    return {character, relations, basisCount: involved.size, score, index};
  }).filter(entry => entry.basisCount > 0)
    .sort((a, b) => b.basisCount - a.basisCount || b.score - a.score || a.index - b.index)
    .map(({index, score, ...entry}) => entry);
}
