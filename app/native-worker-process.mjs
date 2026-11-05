// A native service owns its descendants so cancellation reaches hosts/compilers.
export function ownNativeProcessGroup(child,enabled,kill=process.kill){
  if(enabled)child.kill=signal=>{
    try{kill(-child.pid,signal||'SIGTERM');return true;}
    catch(error){if(error.code==='ESRCH')return false;throw error;}
  };
  return child;
}
