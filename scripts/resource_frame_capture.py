"""Compose read-only end-of-frame witnesses with existing squad comparators."""
import ast,inspect,sys,textwrap
from contextlib import ExitStack
from functools import lru_cache
from unittest.mock import patch

@lru_cache(maxsize=8)
def frame_point(simulate):
 lines,first=inspect.getsourcelines(simulate);tree=ast.parse(textwrap.dedent(''.join(lines)))
 steps=[n for n in ast.walk(tree) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='t' and isinstance(n.value,ast.Name) and n.value.id=='DT']
 assert len(steps)==1,'Expected one authoritative frame boundary'
 return simulate.__code__,first+steps[0].lineno-1

class FrameCapture:
 def __init__(self,gpu,project):self.gpu_module=gpu;self.project=project;self.samples=[];self.final_samples=[];self.gpu={};self.program=None
 def __enter__(self):
  from calculator import timeline
  code,end=frame_point(timeline.simulate);self.previous=sys.gettrace();self.original_settrace=sys.settrace;original_gpu=self.gpu_module.evaluate_full
  def evaluate(device,compiled,*args,**kwargs):
   self.program=compiled['program'];result=original_gpu(device,compiled,*args,**kwargs);self.gpu.update(result);return result
  def settrace(fn):
   if fn is None or fn is self.previous:return self.original_settrace(fn)
   def combined(frame,event,arg):
    onward=fn(frame,event,arg)
    if frame.f_code is code and event=='line' and frame.f_lineno==end:
     self.samples.extend(self.project(frame.f_locals['bm'],frame.f_locals['t'],self))
    if frame.f_code is code and event=='return':
     self.final_samples.extend(self.project(frame.f_locals['bm'],frame.f_locals['duration'],self))
    return combined if onward is not None else None
   return self.original_settrace(combined)
  self.stack=ExitStack();self.stack.enter_context(patch.object(self.gpu_module,'evaluate_full',evaluate));self.stack.enter_context(patch.object(sys,'settrace',settrace));return self
 def __exit__(self,*exc):
  self.original_settrace(self.previous);return self.stack.__exit__(*exc)
