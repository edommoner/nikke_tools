import {overloadFields} from './roster-model.mjs';

export function cubeEffectLabel(effect, statLabel) {
  return effect ? `${statLabel(effect.stat)} ${effect.direction === 'down' ? '▼' : '▲'}` : '';
}

export function cubeEffectText(effect, level, statLabel) {
  const value = effect?.values?.[String(level)];
  if (!Number.isFinite(value)) return '';
  return `${statLabel(effect.stat)} ${effect.direction === 'down' ? '−' : '+'}${Math.abs(value)}${effect.unit ?? ''}（Lv${level}）`;
}

// A range always has a numeric position, even when the source value is unknown.
export function rangeValue(value, known, touched) {
  return known || touched ? Number(value) : undefined;
}

export function cubeEditorPatch(name, loadedName, level, position) {
  if (!name) return undefined;
  if (name === '__none__') return {name, level: 0};
  if (level !== undefined) return {name, level};
  return name !== loadedName ? {name, level: position} : {name};
}

export const overloadParts = [['머리', '頭'], ['몸통', '胴'], ['팔', '腕'], ['다리', '脚']];
const overloadStats = new Set(overloadFields.map(([, stat]) => stat));

export function overloadValue(table, stat, lv) {
  const value = table?.[stat]?.[lv - 1];
  return Number.isInteger(lv) && lv >= 1 && lv <= 15 && Number.isFinite(value)
    ? Math.round((value * 100 + Number.EPSILON) * 100) / 100 : undefined;
}

export function overloadOptionText(table, stat, lv) {
  const value = overloadValue(table, stat, lv);
  return value === undefined ? '' : `+${value.toFixed(2)}%（Lv${lv}）`;
}

export function normalizeParts(raw) {
  return Object.fromEntries(overloadParts.map(([part]) => [part,
    (Array.isArray(raw?.[part]) ? raw[part] : []).filter(line =>
      Array.isArray(line) && line.length === 2 && overloadStats.has(line[0]) &&
      Number.isInteger(line[1]) && line[1] >= 1 && line[1] <= 15
    ).slice(0, 3).map(([stat, lv]) => [stat, lv])
  ]));
}

function overloadLines(parts, table, stat) {
  return overloadParts.flatMap(([part]) => (parts?.[part] ?? [])
    .filter(([key]) => key === stat).map(([, lv]) => overloadValue(table, stat, lv)));
}

export function partsToEquipSkills(parts, table, stats) {
  return Object.fromEntries(stats.map(stat => {
    const lines = overloadLines(parts, table, stat);
    return [stat, lines.length > 1 ? lines : lines[0] ?? 0];
  }));
}

export function partsMatchEquipSkills(parts, equipSkills, table, stats) {
  const close = (a, b) => Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= 0.010000001;
  return stats.every(stat => {
    const lines = overloadLines(parts, table, stat);
    const stored = equipSkills?.[stat] ?? 0;
    if (!Array.isArray(stored)) return Number.isFinite(stored) && lines.every(Number.isFinite) &&
      Math.abs(lines.reduce((a, b) => a + b, 0) - stored) <= 0.010000001 * Math.max(1, lines.length);
    if (lines.length !== stored.length) return false;
    const sorted = [...stored].sort((a, b) => a - b);
    return [...lines].sort((a, b) => a - b).every((value, i) => close(value, sorted[i]));
  });
}

export function inferPartsFromEquipSkills(equipSkills, table, stats) {
  const parts = normalizeParts(), unresolved = [];
  let placed = 0, full = false;
  for (const stat of stats) {
    const stored = equipSkills?.[stat] ?? 0;
    if (stored === 0 || (Array.isArray(stored) && !stored.length)) continue;
    let levels;
    if (Array.isArray(stored)) {
      levels = stored.map(value => Array.from({length:15}, (_,i) => i+1).find(lv =>
        Number.isFinite(value) && Math.abs(overloadValue(table, stat, lv) - value) <= 0.010000001));
    } else if (Number.isFinite(stored)) {
      for (let n = 1; n <= 12 && !levels; n++) {
        for (let lv = 1; lv <= 15; lv++) {
          if (Math.abs(n * overloadValue(table, stat, lv) - stored) <= 0.010000001 * n) {
            levels = Array(n).fill(lv);
            break;
          }
        }
      }
    }
    if (!levels || levels.some(lv => lv === undefined) || full) {
      unresolved.push(stat);
      continue;
    }
    if (placed + levels.length > 12) {
      full = true;
      unresolved.push(stat);
      continue;
    }
    for (const lv of levels) {
      parts[overloadParts[Math.floor(placed / 3)][0]].push([stat, lv]);
      placed++;
    }
  }
  return {parts, complete: unresolved.length === 0, unresolved};
}

export function overloadLevelTotal(entry, table, stats) {
  let parts = normalizeParts(entry._overload);
  if (entry._overload == null || !partsMatchEquipSkills(parts, entry.equip_skills, table, stats)) {
    const inferred = inferPartsFromEquipSkills(entry.equip_skills, table, stats);
    if (!inferred.complete) return null;
    parts = inferred.parts;
  }
  return overloadParts.flatMap(([part]) => parts[part]).reduce((sum, [,lv]) => sum + lv, 0);
}

export function duplicateEffects(parts) {
  return overloadParts.flatMap(([part]) => {
    const seen = new Set(), duplicates = new Set();
    for (const [stat] of parts?.[part] ?? []) {
      if (seen.has(stat)) duplicates.add(stat);
      seen.add(stat);
    }
    return [...duplicates].map(stat => ({part, stat}));
  });
}
