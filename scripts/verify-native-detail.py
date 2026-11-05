"""Compare native GPU code, portable GPU PTX and independent whole-squad CPU."""
import sys,json,hashlib,time,importlib.util
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import body_for,a

if __name__=='__main__':
 r=verify();(ROOT/'research/detail-native-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
