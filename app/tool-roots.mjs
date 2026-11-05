import path from 'node:path';
import os from 'node:os';
import {existsSync, readFileSync, statSync} from 'node:fs';

// Python's platform.machine() names used in the .tools/slang-* folder.
const machines={darwin:{arm64:'arm64',x64:'x86_64'},linux:{arm64:'aarch64',x64:'x86_64'},win32:{x64:'AMD64',arm64:'ARM64'}};
const systems={darwin:'Darwin',linux:'Linux',win32:'Windows'};

/** Main checkout of a Git worktree (`.git` is a file pointing at .git/worktrees/<name>), else null. */
export function mainCheckout(root,{readFile=readFileSync,isFile=p=>{try{return statSync(p).isFile();}catch{return false;}}}={}){
  const dotgit=path.join(root,'.git');
  if(!isFile(dotgit))return null;
  const match=/^gitdir:\s*(.+)\s*$/m.exec(readFile(dotgit,'utf8'));
  if(!match)return null;
  const gitdir=path.resolve(root,match[1].trim());
  let common;
  try{common=path.resolve(gitdir,readFile(path.join(gitdir,'commondir'),'utf8').trim());}catch{return null;}
  return path.basename(common)==='.git'?path.dirname(common):null;
}

/**
 * Environment additions so a server started inside a Git worktree finds the
 * slangc / emsdk installed in the main checkout's .tools. Explicit
 * NIKKE_SLANG_ROOT / NIKKE_EMSDK always win, and tools inside the worktree
 * itself (or the parent folders the Python defaults already check) are kept.
 */
export function sharedToolEnv(root,{env=process.env,platform=process.platform,arch=process.arch,exists=existsSync,main=mainCheckout(root)}={}){
  const extra={};
  if(!main||path.resolve(main)===path.resolve(root))return extra;
  const slangName=`slang-2026.20-${systems[platform]||os.type()}-${machines[platform]?.[arch]||arch}`;
  const slangc=dir=>path.join(dir,'bin',platform==='win32'?'slangc.exe':'slangc');
  if(!env.NIKKE_SLANG_ROOT&&!exists(slangc(path.join(root,'.tools',slangName)))){
    const shared=path.join(main,'.tools',slangName);
    if(exists(slangc(shared)))extra.NIKKE_SLANG_ROOT=shared;
  }
  const emsdkLocal=[path.join(root,'..','.tools','emsdk'),path.join(root,'..','..','.tools','emsdk')];
  if(!env.NIKKE_EMSDK&&!emsdkLocal.some(dir=>exists(dir))){
    const shared=path.join(main,'.tools','emsdk');
    if(exists(shared))extra.NIKKE_EMSDK=shared;
  }
  return extra;
}
