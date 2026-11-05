"""Lightweight host readiness and optional CPU startup; never launches a GPU."""
import argparse,json,platform,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def command(args):
    result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=30)
    return dict(passed=result.returncode==0,output=(result.stdout+result.stderr).strip()[:200])
