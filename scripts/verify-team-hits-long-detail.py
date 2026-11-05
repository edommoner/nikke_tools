"""Native 180-second raw D/Rumani regression across repeated burst/expiry cycles."""
import copy,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('team_long',ROOT/'scripts/verify-team-hits-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
