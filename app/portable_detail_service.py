"""Fresh-process product boundary; original preparation mutates upstream aliases."""
import json
import sys
from portable_detail import evaluate

def main():
    try:
        body=json.load(sys.stdin)
        rows=body.get('evaluations')
        if body.get('action')!='evaluate_portable_detail_batch' or not isinstance(rows,list) or len(rows)!=1:
            raise ValueError('One shared detail evaluation per isolated worker is required')
        try:result=[dict(result=evaluate(rows[0]))]
        except (Exception,SystemExit) as error:result=[dict(error=str(error))]
        print(json.dumps(result,ensure_ascii=False,allow_nan=False))
    except (Exception,SystemExit) as error:
        print(json.dumps(dict(error=str(error)),ensure_ascii=False));sys.exit(1)

if __name__=='__main__':main()
