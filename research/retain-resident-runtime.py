"""GPU0 retention: original frozen golden, saved capture auditors and exact bytes."""
import argparse,hashlib,importlib.util,json,struct,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('retention_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


def main(baseline,candidate,golden,output):
    with output.open('x',encoding='utf-8') as stream:stream.write('{}\n')
    started=time.perf_counter();report=dict(passed=False,gpu_calls=0,scope='Byte retention against a previously verified immutable golden; not a new GPU dispatch or standalone calculation certification')
    try:
        old=cli.load(golden);n=len(old['entries']);ow=786432*4
        for capture in (baseline,candidate):
            cli.check_records(capture,cli.load(capture/'artifacts.json')['files'])
            e=cli.load(capture/'evidence.json');result=cli.load(capture/'result.json')
            assert result['calculation_verified'] and e['gpu_execution_verified'] and e['transport']['command_status']=='completed'
            assert e['transport']['cases']==n and (capture/'readback.bin').stat().st_size==n*ow
            assert e['input_sha256']==old['input_sha256']
        def digest_file(path):
            h=hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda:stream.read(4*1024*1024),b''):h.update(chunk)
            return h.hexdigest()
        for capture in (baseline,candidate):assert digest_file(capture/'input.bin')==old['input_sha256']
        comparison=cli.load(candidate/'comparison.json')
        assert comparison['entries']==old['entries'],'Saved native/input/output fingerprints changed'
        from portable_specs import LIMITS
        begin=LIMITS['LAZY_BANK_BASE']*4;end=begin+LIMITS['LAZY_BANK_WORDS']*4
        a=hashlib.sha256();b=hashlib.sha256()
        with (baseline/'readback.bin').open('rb') as left,(candidate/'readback.bin').open('rb') as right:
            for i,expected in enumerate(old['entries']):
                previous=left.read(ow);current=right.read(ow)
                assert len(previous)==len(current)==ow
                if previous!=current:
                    byte=next(j for j,(x,y) in enumerate(zip(previous,current)) if x!=y)
                    raise ValueError(f'First retained word differs: case {i}, word {byte//4}')
                assert hashlib.sha256(current).hexdigest()==expected['output_sha256']
                assert not any(memoryview(current)[begin:end]),'Lazy bank not cleared'
                a.update(previous);b.update(current)
            assert not left.read(1) and not right.read(1)
        assert a.hexdigest()==b.hexdigest()==old['output_sha256']
        assert cli.load(candidate/'evidence.json')['output_sha256']==b.hexdigest()
        report.update(passed=True,inputs=n,all_input_raw_native_fingerprints_equal=True,all_raw_words_equal=True,lazy_banks_zero=True,output_bytes=n*ow,output_sha256=b.hexdigest(),baseline_golden_sha256=digest_file(golden))
    except BaseException as error:
        report['error']=type(error).__name__+': '+str(error);raise
    finally:
        report['elapsed_seconds']=time.perf_counter()-started
        cli.write(output,report)
    print(json.dumps(report))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','candidate','golden','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();main(a.baseline,a.candidate,a.golden,a.out)
