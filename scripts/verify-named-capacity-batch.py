"""Mixed high-ID masks and an empty program in actual concurrent native batches."""
import hashlib,importlib.util,json,math
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('named_mask_batch',ROOT/'scripts/verify-named-capacity-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
