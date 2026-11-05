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
