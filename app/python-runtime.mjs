import path from 'node:path';
import os from 'node:os';
import {existsSync} from 'node:fs';

export function resolvePython({platform=process.platform,env=process.env,home=os.homedir(),exists=existsSync}={}) {
  if (env.NIKKE_PYTHON) return env.NIKKE_PYTHON;
  if (platform==='win32') {
    const bundled=path.join(env.USERPROFILE || home,'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe');
    return exists(bundled) ? bundled : 'python';
  }
  return 'python3';
}
