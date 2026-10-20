// Keep exact integer seeds across Node's JSON number boundary.
export function portableEventRequest(payload) {
  const seed = payload?.environment?.enemy_targeting?.seed;
  if (typeof seed === 'number' && !Number.isSafeInteger(seed)) {
    throw Error('乱数種は正確な整数で指定してください。大きい値は十進文字列で指定できます。');
  }
  return {...payload, action: 'evaluate_portable_events'};
}
