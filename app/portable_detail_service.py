"""Fresh-process product boundary; original preparation mutates upstream aliases."""
import json
import sys
from portable_detail import evaluate_many,batch_limit,prepare_browser_wires,finish_browser

def main():
    try:
        body=json.load(sys.stdin)
        rows=body.get('evaluations')
        if body.get('action') not in ('evaluate_portable_detail_batch','prepare_browser_wires','finish_browser') or not isinstance(rows,list) or not 1<=len(rows)<=batch_limit(rows):
            raise ValueError('Shared detail evaluations exceed the backend batch limit')
        action=body['action']
        result=prepare_browser_wires(rows) if action=='prepare_browser_wires' else finish_browser(rows,body.get('uploads')) if action=='finish_browser' else evaluate_many(rows)
        print(json.dumps(result,ensure_ascii=False,allow_nan=False))
    except (Exception,SystemExit) as error:
        print(json.dumps(dict(error=str(error)),ensure_ascii=False));sys.exit(1)

if __name__=='__main__':main()
