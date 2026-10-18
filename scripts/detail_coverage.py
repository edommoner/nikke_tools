"""Reproducible compilation coverage for real characters in a fixed owned roster.
Compilation coverage is not a claim of damage parity; full-squad tests are separate.
"""
import copy,json,sys,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker as a
from detail_gpu import UnsupportedDetail

def body_for(names,duration=30,grown=False):
 chars={n:{k:copy.deepcopy(v) for k,v in a.spec.DEFAULT_CHAR.items() if k in a.spec.GROWTH_KEYS} for n in names}
 for i,c in enumerate(chars.values()):
  c['cube']={'name':'__none__','level':0};c['favorite_stage']=0;c['collection_stage']='SR15' if grown else '없음'
  if grown:c['skill_levels']={'1':3+i,'2':9-i,'3':10};c['affinity']=1+i*6
 return {'profile':{'chars':chars,'_account':{'console':a.spec.DEFAULT_CHAR['console']}},'squad':names,'duration':duration,'level':400,'enemy':{'def':31784,'code':'풍압','core_px':50,'distance':25},'burst_policy':'auto'}

def coverage():
 results=[]
 for name,data in a.META.items():
  if not isinstance(data,dict) or name.startswith(('_','test_')) or a.spec.is_preview(name):continue
  names=[name]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=name][:4]
  try:a.evaluate({**body_for(names),'_compile_gpu_detail':True});results.append({'character':name,'supported':True})
  except UnsupportedDetail as e:results.append({'character':name,'supported':False,'issues':e.issues})
  except (Exception,SystemExit) as e:results.append({'character':name,'supported':False,'setup_error':str(e)})
 count=collections.Counter(i.get('reason','') for r in results for i in r.get('issues',[]))
 return {'supported':sum(r['supported'] for r in results),'characters':len(results),'assumptions':'favorite stage 0, no cube, one target in fixed compatible five-member roster; compile only','reasons':dict(count.most_common()),'results':results}
if __name__=='__main__':
 report=coverage();destination=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'research/detail-coverage.json';destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'supported':report['supported'],'characters':report['characters'],'top_reasons':dict(list(report['reasons'].items())[:6])},ensure_ascii=True))
