"""Owned Windows native child held suspended until its inherited Job is checked.

This is a launch adapter for the shared object engine, not another job runner.
CPython's _winapi keeps the primary thread handle that Popen normally closes.
"""
import contextlib,ctypes as C,math,os,subprocess,sys

CREATE_SUSPENDED=0x4
BELOW_NORMAL=0x4000


def resume_function():
    from ctypes import wintypes as W
    dll=C.WinDLL('kernel32',use_last_error=True)
    dll.ResumeThread.argtypes=[W.HANDLE];dll.ResumeThread.restype=W.DWORD
    def resume(handle):
        count=dll.ResumeThread(handle)
        if count==0xffffffff:raise C.WinError(C.get_last_error())
        return count
    return resume


class SuspendedNativeProcess:
    def __init__(self,argv,*,cwd,stdin,stdout,stderr,shell,creationflags,api=None,get_handle=None,startup_factory=None,resume=None):
        if shell is not False or stdin!=subprocess.DEVNULL or creationflags!=BELOW_NORMAL:
            raise ValueError('Native launch requires DEVNULL, no shell and BelowNormal only')
        if not isinstance(argv,list) or not argv or any(not isinstance(x,str) or '\0' in x for x in argv):
            raise ValueError('Native launch requires a string argument list')
        if api is None:import _winapi as api
        if get_handle is None:
            from msvcrt import get_osfhandle
            get_handle=get_osfhandle
        self._api=api;self._resume=resume or resume_function();self.args=argv
        self._handle=None;self._thread=None;self.returncode=None;self.resumed=False
        startup=(startup_factory or subprocess.STARTUPINFO)();startup.dwFlags|=api.STARTF_USESTDHANDLES
        try:
            with contextlib.ExitStack() as stack:
                null=stack.enter_context(open(os.devnull,'rb'))
                inherited=[];current=api.GetCurrentProcess()
                for stream in (null,stdout,stderr):
                    handle=api.DuplicateHandle(current,get_handle(stream.fileno()),current,0,True,api.DUPLICATE_SAME_ACCESS)
                    stack.callback(api.CloseHandle,handle);inherited.append(handle)
                startup.hStdInput,startup.hStdOutput,startup.hStdError=inherited
                startup.lpAttributeList={'handle_list':inherited}
                # Only duplicated stdio handles are inherited. No breakaway flag.
                sys.audit('subprocess.Popen',argv[0],subprocess.list2cmdline(argv),str(cwd),None)
                self._handle,self._thread,self.pid,self.thread_id=api.CreateProcess(argv[0],subprocess.list2cmdline(argv),None,None,True,creationflags|CREATE_SUSPENDED,None,str(cwd),startup)
        except BaseException:
            if self._handle is not None:
                try:self.terminate();self.wait(timeout=5)
                finally:self.close()
            raise

    def release(self):
        if self._thread is None or self.resumed:raise RuntimeError('Native launch gate already consumed or closed')
        previous=self._resume(self._thread)
        if previous!=1:raise RuntimeError('Unexpected native primary thread suspend count')
        self.resumed=True
        return dict(protocol='create-suspended-v1',created_suspended=True,creation_flags=BELOW_NORMAL|CREATE_SUSPENDED,
                    primary_thread_id=self.thread_id,resume_previous_count=previous)

    def poll(self):
        if self.returncode is None:
            if self._handle is None:raise RuntimeError('Native process handle closed before exit observation')
            status=self._api.WaitForSingleObject(self._handle,0)
            if status==self._api.WAIT_OBJECT_0:self.returncode=self._api.GetExitCodeProcess(self._handle)
            elif status!=self._api.WAIT_TIMEOUT:raise RuntimeError('Unexpected native wait status')
        return self.returncode

    def wait(self,timeout):
        if type(timeout) not in (int,float) or not math.isfinite(timeout) or not 0<=timeout<=55:raise ValueError('Native wait must be bounded by55 seconds')
        if self.returncode is None:
            status=self._api.WaitForSingleObject(self._handle,math.ceil(timeout*1000))
            if status==self._api.WAIT_TIMEOUT:raise subprocess.TimeoutExpired(self.args,timeout)
            if status!=self._api.WAIT_OBJECT_0:raise RuntimeError('Unexpected native wait status')
            self.returncode=self._api.GetExitCodeProcess(self._handle)
        return self.returncode

    def terminate(self):
        if self.poll() is None:self._api.TerminateProcess(self._handle,1)

    def close(self):
        try:
            if self._thread is not None:
                handle,self._thread=self._thread,None;self._api.CloseHandle(handle)
        finally:
            if self._handle is not None:
                handle,self._handle=self._handle,None;self._api.CloseHandle(handle)


def validate_launch(launch):
    if not isinstance(launch,dict) or launch.get('protocol')!='create-suspended-v1' or launch.get('created_suspended') is not True or launch.get('creation_flags')!=BELOW_NORMAL|CREATE_SUSPENDED or launch.get('resume_previous_count')!=1 or type(launch.get('primary_thread_id')) is not int or launch['primary_thread_id']<=0:
        raise ValueError('Native launch gate not verified')
    return launch
