"""Private JSON-lines GPU worker. Keeps one CUDA context warm; no network or files."""
import json,sys
from gpu_selector import Cuda,select_teams
# The upstream adapter configures UTF-8 streams; import before reading stdin.
import engine_worker

def resolve_verification(gpu,cpu):
 """A rejected GPU result must never be published under a CUDA backend label."""
 fields={'total_equal':'total_damage','members_equal':'members','burst_timeline_equal':'burst_timeline','base_stats_equal':'base_stats'}
 check={key:gpu[field]==cpu[field] for key,field in fields.items()}
 check['seed_equal']=gpu.get('seed',0)==cpu.get('seed',0)
 for field in ('burst_policy','requested_burst_policy','burst_patterns','shooting_policy','burst_gauge_mode','parts_state','boss_patterns','boss_timeline','incoming_hits'):
  check[field+'_equal']=gpu.get(field)==cpu.get(field)
 check['matched']=all(check.values())
 if check['matched']:
  gpu['compute']['cpu_verification']=check;return gpu
 cpu['compute']={'requested':'cuda_detail','backend':'cpu','fallback_reason':'GPUとCPUの照合に差があったため、CPUの結果を表示しています。','cpu_verification':check,'gpu_result_rejected':True}
 return cpu

def evaluate_details(bodies,device=None):
 """Common single/batch boundary; one error never shifts another input's result."""
 from detail_gpu import evaluate_full_many,UnsupportedDetail
 if not isinstance(bodies,list) or len(bodies)>32:raise ValueError('Detailed requests must contain at most 32 evaluations')
 rows=[None]*len(bodies);compiled=[];indices=[]
 def cpu_fallback(body,compute):
  result=engine_worker.evaluate(body);result['compute']=compute;return {'result':result}
 for index,body in enumerate(bodies):
  try:
   if not isinstance(body,dict) or type(body.get('verify_detail',False)) is not bool:raise ValueError('Invalid detailed evaluation')
   try:program=engine_worker.evaluate({**body,'_compile_gpu_detail':True})
   except UnsupportedDetail as error:
    rows[index]=cpu_fallback(body,{'requested':'cuda_detail','backend':'cpu','fallback_reason':'この編成には詳細GPUの未対応効果があるため、CPUで詳細計算しました。','unsupported':error.issues});continue
   compiled.append(program);indices.append(index)
  except (Exception,SystemExit) as error:rows[index]={'error':str(error)}
 if compiled:
  try:
   if device is None:device=Cuda()
   outputs=evaluate_full_many(device,compiled)
   if len(outputs)!=len(indices):raise RuntimeError('Detailed batch output length differs')
   for index,result in zip(indices,outputs):
    try:
     if bodies[index].get('verify_detail',False):result=resolve_verification(result,engine_worker.evaluate(bodies[index]))
     rows[index]={'result':result}
    except (Exception,SystemExit) as error:rows[index]={'error':str(error)}
  except UnsupportedDetail as error:
   for index in indices:
    try:rows[index]=cpu_fallback(bodies[index],{'requested':'cuda_detail','backend':'cpu','fallback_reason':'詳細GPUでまとめ計算できなかったため、CPUで詳細計算しました。','unsupported':error.issues})
    except (Exception,SystemExit) as failure:rows[index]={'error':str(failure)}
  except (RuntimeError,OSError) as error:
   # A rejected launch cannot establish any member's GPU result. Discard its
   # context before handling the next request, and label each fallback as CPU.
   if device:device.close()
   device=None
   for index in indices:
    try:rows[index]=cpu_fallback(bodies[index],{'requested':'cuda_detail','backend':'cpu','fallback_reason':'詳細GPUを実行できなかったため、CPUで計算しました。','error':str(error)})
    except (Exception,SystemExit) as failure:rows[index]={'error':str(failure)}
 return rows,device

def main():
 device=None;combat=None
 try:
  for line in sys.stdin:
   request={}
   try:
    request=json.loads(line)
    if request['body']['action'] in ('evaluate_detail','evaluate_detail_batch'):
     body=request['body'];previous=device
     rows,device=evaluate_details(body.get('evaluations') if body['action']=='evaluate_detail_batch' else [body],device)
     if device is not previous:combat=None
     if body['action']=='evaluate_detail_batch':result=rows
     elif 'error' in rows[0]:raise ValueError(rows[0]['error'])
     else:result=rows[0]['result']
    else:
     if device is None:device=Cuda()
     result=None
    if request['body']['action'] in ('evaluate_detail','evaluate_detail_batch'):pass
    elif request['body']['action']=='gpu_probe':
     if list(device.expand([([0]*8,0,[],0xffffffff)],[[1]+[0]*7],[123]))!=[124]:raise RuntimeError('GPU self-check mismatch')
     from gpu_combat import Combat
     if combat is None:combat=Combat(device)
     model={'chars':([100,100,10,1,1,1,1,0,0,100,1,1,200,0,0,0,0,20,2,0]+[0]*24)*5,'effects':[],'enemy':[1,0,0,0,0],'names':['probe']*5}
     check=combat.run([model])['scores'][0]
     if check['damage']!=540 or check['shots']!=5:raise RuntimeError('GPU combat self-check mismatch')
     result={'combat_available':True,'available':True,'device':device.name,'backend':'cuda','verified':True,'persistent':True}
    elif request['body']['action']=='combat_prefilter':
     from gpu_combat import Combat,prefilter
     if combat is None:combat=Combat(device)
     result=prefilter(request['body'],device,combat)
     result['persistent']=True
    elif request['body']['action']=='select':
     result=select_teams(request['body'],device=device)
     result.update(persistent=True,sort_backend='cuda')
    else:raise ValueError('Unknown GPU action')
    response={'id':request['id'],'result':result}
   except (Exception,SystemExit) as error:
    if request.get('body',{}).get('action')=='gpu_probe':response={'id':request.get('id'),'result':{'available':False,'backend':'cpu','reason':str(error)}}
    else:response={'id':request.get('id'),'error':str(error)}
    if device:
     device.close();device=None;combat=None
   print(json.dumps(response,ensure_ascii=True),flush=True)
 finally:
  if device:device.close()

if __name__=='__main__':main()
