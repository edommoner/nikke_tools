"""Seeded cross-character checks for new predicate users and supported peers."""
import json,sys,random,hashlib,importlib.util
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import UnsupportedDetail
from detail_coverage import a,body_for,coverage
spec=importlib.util.spec_from_file_location('mixed_predicate_oracle',ROOT/'scripts/verify-predicates-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def inputs():
 current=coverage();accepted=[r['character'] for r in current['results'] if r['supported']]
 old=json.loads((ROOT/'research/detail-coverage-lists.json').read_text(encoding='utf-8'));previous={r['character'] for r in old['results'] if r['supported']};new=[n for n in accepted if n not in previous]
 rng=random.Random(20261016);out=[];seen=set();rejected=[];attempts=0
 while len(out)<6 and attempts<1000:
  attempts+=1;chosen=rng.sample(new,2);chosen+=rng.sample([n for n in accepted if n not in chosen],3);rng.shuffle(chosen)
  if tuple(chosen) in seen:continue
  seen.add(tuple(chosen));i=len(out);body=body_for(chosen,30,True);body['enemy'].update(code='풍압' if i%2==0 else '전격',core_px=0 if i%3==0 else 50,distance=10 if i%2==0 else 35)
  try:compiled=a.evaluate({**body,'_compile_detail':True})
  except UnsupportedDetail as e:rejected.append({'squad':chosen,'issues':e.issues});continue
  if {c['_detail_stage'] for c in compiled['program']['chars']}!={1,2,3}:continue
  out.append(body)
 assert len(out)==6,'insufficient compilable B1/B2/B3 mixes'
 return out,attempts,rejected
