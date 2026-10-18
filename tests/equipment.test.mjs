import test from 'node:test';
import assert from 'node:assert/strict';
import {formatOverload, parseOverload} from '../web/roster-model.mjs';

test('editing unrelated growth preserves imported option groups and their representation', () => {
  for (const original of [0, 12.34, [4.3], [11.12, 11.12, 12.34]]) {
    const parsed = parseOverload(formatOverload(original), original);
    assert.deepEqual(parsed, original);
    if (Array.isArray(original)) assert.notEqual(parsed, original);
  }
  assert.equal(parseOverload('', [4.3, 6.2]), undefined);
  assert.equal(parseOverload('0', [4.3, 6.2]), 0);
});

test('different and equal overload slots remain distinct inputs to the engine', () => {
  assert.deepEqual(parseOverload('11.12, 11.12, 12.34', 0), [11.12, 11.12, 12.34]);
  assert.deepEqual(parseOverload('4.3、4.3、6.2', 0), [4.3, 4.3, 6.2]);
  for (const invalid of ['1,,2', ',1', '1,', '-1', 'Infinity', '1e309', '0x10', '4%']) {
    assert.throws(() => parseOverload(invalid, 0));
  }
  for (const previous of [-1, Infinity, [-1, 4.3]]) {
    assert.throws(() => parseOverload(formatOverload(previous), previous));
  }
});
