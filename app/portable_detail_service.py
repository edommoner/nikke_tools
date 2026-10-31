"""Fresh-process product boundary; original preparation mutates upstream aliases."""
import json
import sys
from portable_detail import evaluate_many,MAX_PRODUCT_BATCH

def main():
    try:
        body=json.load(sys.stdin)
        rows=body.get('evaluations')
        if body.get('action')!='evaluate_portable_detail_batch' or not isinstance(rows,list) or not 1<=len(rows)<=MAX_PRODUCT_BATCH:
            raise ValueError('One to eight shared detail evaluations per isolated worker required')
        result=evaluate_many(rows)
        print(json.dumps(result,ensure_ascii=False,allow_nan=False))
    except (Exception,SystemExit) as error:
        print(json.dumps(dict(error=str(error)),ensure_ascii=False));sys.exit(1)

if __name__=='__main__':main()
