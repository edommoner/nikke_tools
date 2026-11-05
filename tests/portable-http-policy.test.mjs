import test from 'node:test';
import assert from 'node:assert/strict';
import {portableEventRequest} from '../app/portable_http_policy.mjs';
import {server} from '../server.mjs';

test('safe integer seeds and unrelated request fields are preserved', () => {
  for (const seed of [0, 1, Number.MAX_SAFE_INTEGER]) {
    const input = {environment: {enemy_targeting: {seed}}, backend: 'metal', script: [1]};
    const saved = structuredClone(input);
    const result = portableEventRequest(input);
    assert.deepEqual(input, saved);
    assert.deepEqual(result, {...saved, action: 'evaluate_portable_events'});
  }
  assert.deepEqual(portableEventRequest({backend: 'cuda'}), {backend: 'cuda', action: 'evaluate_portable_events'});
});

test('decimal uint64 text remains exact through JSON round trip', () => {
  const text = '18446744073709551615';
  const input = JSON.parse(JSON.stringify({environment: {enemy_targeting: {seed: text}}}));
  assert.equal(portableEventRequest(input).environment.enemy_targeting.seed, text);
});

test('already-rounded unsafe JSON numbers cannot reach the worker', () => {
  const rounded = JSON.parse('{"environment":{"enemy_targeting":{"seed":9007199254740993}}}');
  assert.equal(rounded.environment.enemy_targeting.seed, 9007199254740992);
  assert.throws(() => portableEventRequest(rounded), /乱数種/);
  for (const seed of [Number.MAX_SAFE_INTEGER + 1, 1.5, Infinity, NaN]) {
    assert.throws(() => portableEventRequest({environment: {enemy_targeting: {seed}}}), /乱数種/);
  }
});

test('HTTP route rejects an unsafe numeric seed before GPU execution', async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    const response = await fetch(`http://127.0.0.1:${server.address().port}/api/portable-events`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: '{"environment":{"enemy_targeting":{"seed":9007199254740993}}}'
    });
    assert.equal(response.status, 400);
    assert.match((await response.json()).error, /乱数種/);
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
});
