"""Additional storage parity and actual workspace size, GPU executes first."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sp=importlib.util.spec_from_file_location('storage_extra_gpu_fixtures',ROOT/'scripts/healing-storage-extra-fixtures.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d);m=d.m;g=m.g
