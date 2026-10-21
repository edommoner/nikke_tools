"""Read-only Windows process roles and JobObject membership for short GPU proofs.

Command lines are read only to classify roles and are never saved or returned.
This observer never starts/stops a service or assigns any process to a job.
"""
import contextlib
import ctypes as C
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time
from unittest.mock import patch


def normalize_snapshot(rows,listeners,workspace,validation_root,observer_script=None):
 def norm(value):return str(value or '').replace('\\','/').lower()
 workspace=norm(workspace).rstrip('/');validation_root=norm(validation_root).rstrip('/');observer_script=norm(observer_script)
 if not workspace or not validation_root:raise ValueError('Explicit original and isolated workspace paths required')
 ports={int(r['pid']) for r in listeners};saved=[];candidates=[];unknown=[]
 for row in rows:
  name=norm(row.get('Name'))
  if name not in ('python.exe','pythonw.exe','node.exe'):continue
  pid=int(row['ProcessId']);command=norm(row.get('CommandLine'));path=str(row.get('ExecutablePath') or '')
  flags=dict(observer_script_reference=bool(observer_script and observer_script in command),original_workspace_reference=workspace in command,validation_reference=validation_root in command,server_script='server.mjs' in command,gpu_service_script='gpu_service.py' in command,command_available=bool(command))
  service_script=flags['server_script'] or flags['gpu_service_script']
  role='observer' if pid==os.getpid() or flags['observer_script_reference'] else 'validation' if flags['validation_reference'] else 'nikke_service' if service_script and (flags['original_workspace_reference'] or pid in ports) else 'service_candidate' if service_script else 'unknown' if not command else 'unrelated'
  created=row.get('CreationTicks');created=str(created) if created is not None else None
  item=dict(pid=pid,ppid=int(row.get('ParentProcessId') or 0),name=str(row['Name']),path=path,creation_filetime_ticks=created,role=role,classification=flags)
  saved.append(item)
  if role=='service_candidate':candidates.append(pid)
  if role=='unknown' or not path or created is None:unknown.append(pid)
 # A child gpu_service may use a relative script path. A positively identified
 # original server parent supplies role evidence; arbitrary runtime paths do not.
 services={r['pid'] for r in saved if r['role']=='nikke_service'}
 for row in saved:
  if row['role']=='service_candidate' and row['classification']['gpu_service_script'] and row['ppid'] in services:
   row['role']='nikke_service';candidates.remove(row['pid']);services.add(row['pid'])
 uncertain=bool(candidates or unknown or any(int(r['pid']) not in {p['pid'] for p in saved} for r in listeners))
 status='unverified' if uncertain else 'identified' if services else 'absent'
 return dict(schema=1,observed_unix_ns=time.time_ns(),processes=saved,listeners=[dict(pid=int(r['pid']),port=int(r['port'])) for r in listeners],nikke_service_pids=sorted(services),service_status=status,uncertain_process_pids=sorted(set(candidates+unknown)),command_lines_saved=False)


def capture_snapshot(workspace,validation_root,powershell='powershell.exe'):
 if os.name!='nt':raise RuntimeError('Windows process capture requires Windows')
 script="""[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
$ErrorActionPreference='Stop'
$rows=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(python|pythonw|node)\\.exe$'} | ForEach-Object { [ordered]@{ ProcessId=$_.ProcessId; ParentProcessId=$_.ParentProcessId; Name=$_.Name; ExecutablePath=$_.ExecutablePath; CommandLine=$_.CommandLine; CreationTicks=if($_.CreationDate){$_.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString()}else{$null} } })
$ports=@(Get-NetTCPConnection -State Listen | Where-Object {$_.LocalPort -in @(4317,4333)} | ForEach-Object { [ordered]@{pid=$_.OwningProcess;port=$_.LocalPort} })
[ordered]@{rows=$rows;listeners=$ports} | ConvertTo-Json -Depth 6 -Compress
"""
 result=subprocess.run([powershell,'-NoProfile','-NonInteractive','-Command',script],capture_output=True,encoding='utf-8-sig',timeout=20)
 if result.returncode:raise RuntimeError('Windows process snapshot unavailable; no command lines retained')
 try:data=json.loads(result.stdout)
 except (ValueError,TypeError):raise RuntimeError('Invalid process snapshot; no command lines retained') from None
 observer_script=str(Path(sys.argv[0]).resolve()) if sys.argv[0].endswith('.py') else None
 return normalize_snapshot(data['rows'],data['listeners'],workspace,validation_root,observer_script)


def compare_snapshots(before,after):
 def identity(row):return row['pid'],row['path'].lower(),row['creation_filetime_ticks']
 current={identity(r) for r in after['processes']};missing=[r for r in before['processes'] if r['role'] not in ('validation','observer') and identity(r) not in current]
 services=[r for r in before['processes'] if r['role']=='nikke_service'];service_known=before['service_status']!='unverified' and after['service_status']!='unverified'
 service_ok=service_known and all(identity(r) in current for r in services) and (before['service_status']!='absent' or after['service_status']=='absent')
 return dict(all_monitored_processes_preserved=not missing,missing_existing_processes=missing,identified_nikke_service_preservation_verified=service_ok,nikke_service_status_before=before['service_status'],nikke_service_status_after=after['service_status'],termination_cause='unknown' if missing else None,command_lines_saved=False)


def inspect_job(job,process):
 if os.name!='nt':raise RuntimeError('Windows JobObject inspection requires Windows')
 from ctypes import wintypes as W
 dll=job.dll
 dll.QueryInformationJobObject.argtypes=[W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.POINTER(W.DWORD)];dll.QueryInformationJobObject.restype=W.BOOL
 dll.GetProcessTimes.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p];dll.GetProcessTimes.restype=W.BOOL
 created,exit_time,kernel,user=(C.c_uint64() for _ in range(4))
 if not dll.GetProcessTimes(W.HANDLE(int(process._handle)),C.byref(created),C.byref(exit_time),C.byref(kernel),C.byref(user)):raise C.WinError(C.get_last_error())
 class ProcessEntry(C.Structure):
  _fields_=[('size',W.DWORD),('usage',W.DWORD),('pid',W.DWORD),('heap',C.c_size_t),('module',W.DWORD),('threads',W.DWORD),('parent',W.DWORD),('priority',W.LONG),('flags',W.DWORD),('exe',W.WCHAR*260)]
 dll.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD];dll.CreateToolhelp32Snapshot.restype=W.HANDLE
 dll.Process32FirstW.argtypes=[W.HANDLE,C.POINTER(ProcessEntry)];dll.Process32FirstW.restype=W.BOOL
 dll.Process32NextW.argtypes=[W.HANDLE,C.POINTER(ProcessEntry)];dll.Process32NextW.restype=W.BOOL
 snapshot=dll.CreateToolhelp32Snapshot(2,0)
 if not snapshot or snapshot==C.c_void_p(-1).value:raise C.WinError(C.get_last_error())
 parent=None
 try:
  entry=ProcessEntry();entry.size=C.sizeof(entry);more=dll.Process32FirstW(snapshot,C.byref(entry))
  while more:
   if entry.pid==process.pid:parent=int(entry.parent);break
   more=dll.Process32NextW(snapshot,C.byref(entry))
 finally:dll.CloseHandle(snapshot)
 parent_source='os_process_snapshot'
 if parent is None:
  pre=getattr(job,'_observed_record',{}).get('pre_gate')
  if pre and process.poll() is not None and pre['child_creation_filetime_ticks']==str(created.value):parent=pre['child_ppid'];parent_source='pre_gate_snapshot_same_process_handle_after_exit'
  else:raise RuntimeError('Validation child absent from OS process snapshot')
 capacity=64
 while True:
  buffer=C.create_string_buffer(8+capacity*C.sizeof(C.c_size_t));returned=W.DWORD()
  success=dll.QueryInformationJobObject(job.handle,3,buffer,len(buffer),C.byref(returned));assigned,count=struct.unpack_from('<II',buffer.raw)
  if success and count<=capacity:
   members=sorted(int(v) for v in (C.c_size_t*count).from_buffer(buffer,8));break
  if C.get_last_error()!=234 or capacity>=4096:raise C.WinError(C.get_last_error())
  capacity=min(4096,max(capacity*2,assigned))
 peak=None
 if hasattr(job,'limit_info_type'):
  limits=job.limit_info_type();returned=W.DWORD()
  if not dll.QueryInformationJobObject(job.handle,9,C.byref(limits),C.sizeof(limits),C.byref(returned)):raise C.WinError(C.get_last_error())
  peak=int(limits.peak_job)
 return dict(child_pid=process.pid,child_ppid=parent,parent_observation=parent_source,observed_unix_ns=time.time_ns(),wrapper_pid=os.getpid(),child_creation_filetime_ticks=str(created.value),job_members=members,job_peak_memory_bytes=peak)


@contextlib.contextmanager
def observe_job(module,path,reader=inspect_job):
 """Observe the existing containment class; require a fresh single-child job."""
 path=Path(path)
 if path.exists():raise ValueError('Fresh job evidence path required')
 records=[];original=module.WindowsJob
 def save():
  with path.open('w',encoding='utf-8') as stream:json.dump(dict(schema=1,records=records,observer_assigns_processes=False),stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
 class ObservedJob(original):
  def __init__(self,process):
   super().__init__(process);self._observed_process=process;self._observed_record=dict(child_pid=process.pid,wrapper_pid=os.getpid(),pre_gate=None,pre_gate_verified=False,post_wait=None,inspection_error=None);records.append(self._observed_record)
   try:
    facts=reader(self,process);self._observed_record['pre_gate']=facts
    if facts['child_pid']!=process.pid or facts['child_ppid']!=os.getpid() or facts['job_members']!=[process.pid] or not facts['child_creation_filetime_ticks']:raise RuntimeError('Fresh validation job identity/membership not established')
    self._observed_record['pre_gate_verified']=True;save()
   except BaseException as error:
    self._observed_record['inspection_error']=type(error).__name__
    try:save()
    finally:original.close(self)
    raise
  def close(self):
   if self.handle and hasattr(self,'_observed_record'):
    try:
     self.terminate_and_wait(timeout=5)
     self._observed_record['post_wait']=reader(self,self._observed_process)
    except BaseException as error:
     self._observed_record['inspection_error']=type(error).__name__
     if not getattr(self,'termination_waited',False):raise
    finally:
     try:save()
     finally:original.close(self)
   else:original.close(self)
 try:
  with patch.object(module,'WindowsJob',ObservedJob):yield records
 finally:
  save()
