"""Publish local checkpoint only after the final validation/efficiency decision exists."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research'
def load(n):return json.loads((P/(n+'.json')).read_text())
