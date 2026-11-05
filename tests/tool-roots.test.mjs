import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import {mainCheckout, sharedToolEnv} from '../app/tool-roots.mjs';

const main = path.resolve('/repo');
const worktree = path.join(main, '.claude/worktrees/feature');
const files = {
  [path.join(worktree, '.git')]: `gitdir: ${path.join(main, '.git/worktrees/feature')}\n`,
  [path.join(main, '.git/worktrees/feature/commondir')]: '../..\n',
};
const readFile = p => { if (p in files) return files[p]; throw Error('missing ' + p); };
const isFile = p => p in files;
const slang = path.join(main, '.tools/slang-2026.20-Darwin-arm64');
const emsdk = path.join(main, '.tools/emsdk');

test('mainCheckout follows a worktree .git file to the shared checkout', () => {
  assert.equal(mainCheckout(worktree, {readFile, isFile}), main);
  assert.equal(mainCheckout(main, {readFile, isFile: () => false}), null);
});

test('worktree servers borrow the main checkout tools', () => {
  const exists = p => [path.join(slang, 'bin/slangc'), emsdk].includes(p);
  assert.deepEqual(sharedToolEnv(worktree, {env: {}, platform: 'darwin', arch: 'arm64', exists, main}),
    {NIKKE_SLANG_ROOT: slang, NIKKE_EMSDK: emsdk});
});

test('explicit settings, worktree-local tools and the main checkout itself are left alone', () => {
  const exists = () => true;
  assert.deepEqual(sharedToolEnv(worktree, {env: {NIKKE_SLANG_ROOT: '/x', NIKKE_EMSDK: '/y'}, platform: 'darwin', arch: 'arm64', exists, main}), {});
  assert.deepEqual(sharedToolEnv(worktree, {env: {}, platform: 'darwin', arch: 'arm64', exists, main}), {});
  assert.deepEqual(sharedToolEnv(main, {env: {}, platform: 'darwin', arch: 'arm64', exists, main}), {});
  assert.deepEqual(sharedToolEnv(worktree, {env: {}, platform: 'darwin', arch: 'arm64', exists: () => false, main}), {});
  assert.deepEqual(sharedToolEnv(worktree, {env: {}, main: null}), {});
});

test('Windows and Linux use the Python machine names', () => {
  const win = path.join(main, '.tools/slang-2026.20-Windows-AMD64');
  assert.equal(sharedToolEnv(worktree, {env: {}, platform: 'win32', arch: 'x64', exists: p => p === path.join(win, 'bin/slangc.exe'), main}).NIKKE_SLANG_ROOT, win);
  const linux = path.join(main, '.tools/slang-2026.20-Linux-x86_64');
  assert.equal(sharedToolEnv(worktree, {env: {}, platform: 'linux', arch: 'x64', exists: p => p === path.join(linux, 'bin/slangc'), main}).NIKKE_SLANG_ROOT, linux);
});
