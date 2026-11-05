"""Fresh-process product boundary; original preparation mutates upstream aliases."""
import json
import sys
from portable_detail import evaluate_many,batch_limit,prepare_browser_wires,finish_browser,verify_portable_detail,cpu_fallback_portable_detail

def main():
    try:
        body=json.load(sys.stdin)
        rows=body.get('evaluations')
        if body.get('action') not in ('evaluate_portable_detail_batch','prepare_browser_wires','finish_browser','verify_portable_detail','cpu_fallback_portable_detail') or not isinstance(rows,list) or not 1<=len(rows)<=(8 if body.get('action') in ('verify_portable_detail','cpu_fallback_portable_detail') else batch_limit(rows)):
            raise ValueError('Shared detail evaluations exceed the backend batch limit')
        from portable_native import HOST_THREADS
        import os
        budget=body.get('host_threads',os.cpu_count() or 1)
        if type(budget) is not int or not 1<=budget<=(os.cpu_count() or 1):raise ValueError('Invalid host thread budget')
        action=body['action']
        verification=body.get('verification','full')
        token=HOST_THREADS.set(budget)
        try:
            result=cpu_fallback_portable_detail(rows) if action=='cpu_fallback_portable_detail' else verify_portable_detail(rows) if action=='verify_portable_detail' else prepare_browser_wires(rows,verification=verification) if action=='prepare_browser_wires' else finish_browser(rows,body.get('uploads'),verification=verification) if action=='finish_browser' else evaluate_many(rows,verification=verification)
        finally:HOST_THREADS.reset(token)
        print(json.dumps(result,ensure_ascii=False,allow_nan=False))
    except (Exception,SystemExit) as error:
        print(json.dumps(dict(error=str(error)),ensure_ascii=False));sys.exit(1)

if __name__=='__main__':main()
