"""Whole-squad parity for every character accepted by the current compiler audit.
This reports the rejected catalog too: passing this check does not mean all
characters, favorite stages, or combinations have GPU implementations.
"""
import hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import coverage,body_for
spec=importlib.util.spec_from_file_location('catalog_oracle',ROOT/'scripts/verify-extended-detail.py');full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)


if __name__=='__main__':
 report=verify();(ROOT/'research/detail-catalog-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
