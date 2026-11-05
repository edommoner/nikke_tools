# Team search S1

## Method

Benchmark profile: 206 owned characters; 206 scored; skipped: [].
A = current candidatePool(5, 160, 41), with 33 real regression templates. Its ordered squads exactly match unit8/long-bodies.json.
B = 2,000 uniform ordered 5-tuples, rejection-sampled for burst coverage (seed 42). C = 300 uniform ordered 5-tuples without that constraint (seed 43). Members are distinct; exact ordered duplicates across cohorts are rejected. Each A/all-stage character can fill one missing stage. Order is retained because it affects burst priority.
Battle: 180 s, level 400, enemy DEF 31784 / wind / core 50 px / distance 25 m; auto burst, fixed gauge, no stat deltas. Settings and character potentials are in s1-inputs.json.
Simple score = sum(atk × damage_coeff × fire_rate). The generator uses member potential to truncate/order eligible choices and its sum to rank templates, then samples stochastically; it has no separate scalar squad objective. pool_generator_effective_score therefore records that sum, not a probability or GPU estimate. Pool insertion index is recorded separately and is not a score.
native_detail uses the existing portable_detail.evaluate_many path, batches of 32, 10 host threads. Verification is deferred and never performed; verify_detail=false. These are unverified research rankings. Mandatory API captures live only in an owned temporary batch directory and are deleted after extracting results.

## Rank correlation

| Cohort | n | Spearman | Kendall tau-b |
|---|---:|---:|---:|
| B | 2000 | 0.072636 | 0.049455 |
| A_union_B | 2160 | 0.086482 | 0.059025 |

## Miss rate

“True” means highest detailed damage within the measured A∪B∪C only, not a global optimum. Simple-score top-K uses the same union. Ties use stable row ID (A then B then C); correlations use average ranks and tie-corrected tau-b. Failed rows, if any, are excluded from ranking.

| Detailed top-N | K | Found | Miss rate |
|---:|---:|---:|---:|
| 20 | 100 | 4 | 80.0% |
| 20 | 500 | 5 | 75.0% |
| 20 | 1000 | 8 | 60.0% |
| 20 | 2000 | 19 | 5.0% |
| 100 | 100 | 5 | 95.0% |
| 100 | 500 | 19 | 81.0% |
| 100 | 1000 | 39 | 61.0% |
| 100 | 2000 | 77 | 23.0% |

A contains 21 of the detailed top-100.

## Five disjoint squads

Unchanged bestDisjoint, beam width 256; original candidate order and A feasible groups retained in both runs. A+B appends B. This measures the existing heuristic, not exact set packing.

- A: **22,209,478,879** total damage
  - 토브 / 아르카나 : 포츈 메이트 / 도로시 : 세렌디피티 / 드레이크 / 솔린 : 프로스트 티켓: 3,843,495,874
  - 리타 / 레이 / 아스카 / 모더니아 / 그레이브: 4,439,779,936
  - 리틀 머메이드 / 크라운 / 퀸(마코토) / 유키코 / 마스트 : 로망틱 메이드: 5,116,835,480
  - 브리드 : 사일런트 트랙 / 라피 : 레드 후드 / 아니스 : 스타 / 미하라 : 본딩 체인 / 프리바티: 6,384,984,219
  - 미란다 / 블랑 / 스노우 화이트 : 헤비암즈 / 루주 / 디젤 : 윈터 스위츠: 2,424,383,370
- A+B: **22,679,329,544** total damage
  - 토브 / 아르카나 : 포츈 메이트 / 도로시 : 세렌디피티 / 드레이크 / 솔린 : 프로스트 티켓: 3,843,495,874
  - 리타 / 레이 / 아스카 / 모더니아 / 그레이브: 4,439,779,936
  - 리틀 머메이드 / 크라운 / 퀸(마코토) / 유키코 / 마스트 : 로망틱 메이드: 5,116,835,480
  - 브리드 : 사일런트 트랙 / 라피 : 레드 후드 / 아니스 : 스타 / 미하라 : 본딩 체인 / 프리바티: 6,384,984,219
  - 2B / 마리안 : 퀸 / 팬텀 / 나유타 / 도로시: 2,894,234,035

Change: 469,850,665 (+2.12%).

## Unconstrained C

Of 300 C squads, 129 lack coverage. 115 beat B's median (694,951,205); 23 beat B's 90th percentile (1,252,826,006, nearest-rank threshold). Among C squads lacking coverage, 23 / 0 beat those respective thresholds.

## Kernel coverage

Backends: {'native_detail': 2406, 'cpu': 54}. Distinct observed characters: 206; appearing in successful native squads: 206.

| Fallback reason | Squads |
|---|---:|
| Ordinary lock markers require their checked BODY/ADD product composition | 16 |
| Shared battle status: 8 (history capacity exceeded) | 14 |
| Weighted product composition requires a checked plain, actual-shot group or coordinate battle entry | 9 |
| Named modifier carriers require their checked ordinary BODY product entry | 9 |
| [{'character': '슈가', 'effect': '블랙 타이푼 5', 'reason': "[{'reason': 'effect fields: target_code'}]"}] | 2 |
| Shared battle status: 64 | 1 |
| Enemy magazines require a checked plain, modifier or actual-shot group BODY/ADD product prefix | 1 |
| Cover DEF composition requires a connected BODY/PART modifier or shot-group product battle | 1 |
| Plain upstream projectile early-return row required | 1 |

The character-specific diagnostic names 슈가 (Sugar), effect 블랙 타이푼 5, unsupported effect field target_code, in two squads. Other diagnostics describe compositions or runtime capacity/status; no individual cause is assigned from co-occurrence.

All affected squad IDs, members, reasons and unsupported effect contexts are retained in the summary JSON. Characters appearing in a failed/fallback squad are co-occurrences, not proof each character is unsupported.

| Squad ID | Backend | Members | Reason |
|---:|---|---|---|
| 177 | cpu | 파스칼 / 홍련 / 밀크 : 블루밍 바니 / 베이 / 앵커 | [{"reason": "Weighted product composition requires a checked plain, actual-shot group or coordinate battle entry"}] |
| 234 | cpu | 벨벳 / 퀸(마코토) / 레이 / 자칼 / 클레이 | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 241 | cpu | 미사토 / 벨벳 / 에이드 / 루드밀라 / 아스카 : WILLE | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 273 | cpu | 스노우 화이트 / 아크레인저 블랙 / 볼륨 / 니힐리스타 / 벨벳 | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 299 | cpu | 시그널 / iDoll 플라워 / 레이 / 스노우 화이트 : 이노센트 데이즈 / 스노우 화이트 : 헤비암즈 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 319 | cpu | 미사토 / 벨벳 / 히메노 / 누아르 / 루주 | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 356 | cpu | 미사토 / 람 / 라플라스 : 얼티밋 히어로 / 솔져 E.G. / 베이 | [{"reason": "Weighted product composition requires a checked plain, actual-shot group or coordinate battle entry"}] |
| 366 | cpu | 미사토 / K / 벨벳 / iDoll 썬 / 릴리 | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 401 | cpu | 사쿠라 : 블룸 인 서머 / 라피 : 레드 후드 / 홍련 : 흑영 / 자칼 / 아이기스 | [{"reason": "Shared battle status: 64"}] |
| 460 | cpu | 앵커 : 이노센트 메이드 / 사쿠라 / 길티 / 벨벳 / 길로틴 : 윈터 슬레이어 | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 491 | cpu | 자칼 / 클레이 / 일레그 : 붐 앤 쇼크 / 렘 / 스노우 화이트 : 헤비암즈 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 515 | cpu | 벨벳 / 아니스 : 스파클링 서머 / 니힐리스타 / 라푼젤 : 퓨어 그레이스 / 레이블 | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 530 | cpu | 마나 / 베이 / 벨벳 / 마르차나 / 소라 | [{"reason": "Enemy magazines require a checked plain, modifier or actual-shot group BODY/ADD product prefix"}] |
| 570 | cpu | 메어리 / 마리 / 엠마 / 레이 (가칭) / 사쿠라 (SR) | [{"reason": "Named modifier carriers require their checked ordinary BODY product entry"}] |
| 597 | cpu | 노아 / 스노우 화이트 : 헤비암즈 / 클레어 / 일레그 / 티아 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 653 | cpu | 프로덕트 08 / 솔린 : 프로스트 티켓 / 레이 / 베이 / 아스카 : WILLE | [{"reason": "Weighted product composition requires a checked plain, actual-shot group or coordinate battle entry"}] |
| 699 | cpu | 레이 (가칭) / 릴리 / 토브 / 아스카 / 엠마 | [{"reason": "Named modifier carriers require their checked ordinary BODY product entry"}] |
| 778 | cpu | 벨벳 / 엑시아 / 미카 : 스노우 버디 / 사쿠라 / A2 | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 787 | cpu | 율하 / 폴리 / 미사토 / 벨벳 / 토브 | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 859 | cpu | 레드 후드 / 벨벳 / 파스칼 / 클레이 / 모더니아 | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 875 | cpu | 슈가 / 프림 / 일레그 : 붐 앤 쇼크 / A2 / 도라 | [{"reason": "[{'character': '슈가', 'effect': '블랙 타이푼 5', 'reason': \"[{'reason': 'effect fields: target_code'}]\"}]"}] |
| 912 | cpu | 레이 (가칭) / 마리 / 에밀리아 / 도로시 / 밀크 : 블루밍 바니 | [{"reason": "Named modifier carriers require their checked ordinary BODY product entry"}] |
| 934 | cpu | 스노우 화이트 : 헤비암즈 / 네온 / 헬름 / 은화 : 택티컬 업 / 솔져 O.W. | [{"reason": "Cover DEF composition requires a connected BODY/PART modifier or shot-group product battle"}] |
| 966 | cpu | 일레그 / 베이 / 네로 / 얀 / A2 | [{"reason": "Weighted product composition requires a checked plain, actual-shot group or coordinate battle entry"}] |
| 985 | cpu | N102 / 레이 (가칭) / 모리 / 메어리 / 앵커 | [{"reason": "Named modifier carriers require their checked ordinary BODY product entry"}] |
| 1015 | cpu | 2B / 토브 / 스노우 화이트 : 헤비암즈 / 크러스트 / 사쿠라 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 1087 | cpu | 이사벨 / 벨로타 : 펌킨 위치 / 벨벳 / 트리나 / 미사토 | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 1218 | cpu | 루마니 / 미하라 / 앤 : 미라클 페어리 / 프로덕트 08 / 스노우 화이트 : 헤비암즈 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 1245 | cpu | 레이블 / 레이 (가칭) / 애드미 / 아스카 / 아비스타 | [{"reason": "Named modifier carriers require their checked ordinary BODY product entry"}] |
| 1251 | cpu | 스노우 화이트 : 헤비암즈 / 엠마 : 택티컬 업 / 블랑 / 클레이 / 질 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 1258 | cpu | iDoll 썬 / 아니스 : 스파클링 서머 / 앵커 / 맥스웰 / 베이 | [{"reason": "Weighted product composition requires a checked plain, actual-shot group or coordinate battle entry"}] |
| 1290 | cpu | 맥스웰 / 민트 / 벨벳 / 앵커 / E.H. | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 1328 | cpu | 벨벳 / 도로시 / 솔져 F.A. / 프로덕트 23 / 레이 | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 1445 | cpu | 드레이크 / 폴크방 / 벨벳 / 파스칼 / 니힐리스타 | [{"reason": "Shared battle status: 8 (history capacity exceeded)"}] |
| 1491 | cpu | 미사토 / 벨로타 / 신 / 스노우 화이트 : 헤비암즈 / 누아르 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 1511 | cpu | 밀크 : 블루밍 바니 / 앤 : 미라클 페어리 / 미카 : 스노우 버디 / 레이 (가칭) / 스노우 화이트 : 헤비암즈 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 1512 | cpu | 사쿠라 : 블룸 인 서머 / 클레이 / 미사토 / 스노우 화이트 : 헤비암즈 / 에밀리아 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 1569 | cpu | 엠마 / 스노우 화이트 : 헤비암즈 / 마나 / 센티 / 니힐리스타 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 1704 | cpu | 팬텀 / 벨벳 / 드레이크 : 그레이트 빌런 / 스노우 화이트 : 헤비암즈 / 노이즈 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 1765 | cpu | 프림 / 레이 (가칭) / 사쿠라 / 마키마 / 스노우 화이트 | [{"reason": "Named modifier carriers require their checked ordinary BODY product entry"}] |
| 1768 | cpu | 솔져 E.G. / 베이 / 얀 / 아스카 / iDoll 플라워 | [{"reason": "Weighted product composition requires a checked plain, actual-shot group or coordinate battle entry"}] |
| 1778 | cpu | 벨벳 / 사쿠라 (SR) / 이사벨 / 스노우 화이트 : 헤비암즈 / 프로덕트 12 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 1816 | cpu | 바이퍼 / 베이 / 미사토 / 블랑 / 레이븐 | [{"reason": "Weighted product composition requires a checked plain, actual-shot group or coordinate battle entry"}] |
| 1855 | cpu | 레이 (가칭) / 도로시 / 길로틴 / 마리 / 아크레인저 블랙 | [{"reason": "Named modifier carriers require their checked ordinary BODY product entry"}] |
| 1902 | cpu | 리틀 머메이드 / 스노우 화이트 : 헤비암즈 / 니힐리스타 / 홍련 : 흑영 / 벨로타 : 펌킨 위치 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 1904 | cpu | 미사토 / 프리카 / 누아르 / 베이 / 메이든 : 아이스 로즈 | [{"reason": "Weighted product composition requires a checked plain, actual-shot group or coordinate battle entry"}] |
| 1943 | cpu | 에이드 : 에이전트 바니 / 미사토 / 은화 : 택티컬 업 / 레이 (가칭) / 레오나 | [{"reason": "Named modifier carriers require their checked ordinary BODY product entry"}] |
| 1950 | cpu | 미사토 / 길티 : 마이티 바니 / 스노우 화이트 : 헤비암즈 / 미카 / 백학 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 2043 | cpu | 스노우 화이트 : 헤비암즈 / 밀크 : 블루밍 바니 / 비스킷 / 율리아 / 솔린 : 프로스트 티켓 | [{"reason": "Plain upstream projectile early-return row required"}] |
| 2121 | cpu | 크라운 / 일레그 : 붐 앤 쇼크 / 프리카 / 슈가 / 리타 | [{"reason": "[{'character': '슈가', 'effect': '블랙 타이푼 5', 'reason': \"[{'reason': 'effect fields: target_code'}]\"}]"}] |
| 2176 | cpu | 니힐리스타 / 람 / 앤 : 미라클 페어리 / 레이블 / 스노우 화이트 : 헤비암즈 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 2179 | cpu | iDoll 오션 / 시그널 / 벨벳 / 솔져 E.G. / 스노우 화이트 : 헤비암즈 | [{"reason": "Ordinary lock markers require their checked BODY/ADD product composition"}] |
| 2387 | cpu | 마스트 : 로망틱 메이드 / 크라운 / 베이 / 아스카 / 렘 | [{"reason": "Weighted product composition requires a checked plain, actual-shot group or coordinate battle entry"}] |
| 2456 | cpu | 홍련 / 레이 / 소다 / 레이 (가칭) / 마르차나 | [{"reason": "Named modifier carriers require their checked ordinary BODY product entry"}] |

## Time, storage and validation

Evaluation wall time: 822.417 s; 334.316 ms/squad (end to end, including preparation, native dispatch, decoding and cleanup). Total script wall time: 824.973 s.
Free disk before/after: 34.904 / 34.904 GiB. Storage preflight passed with a 512 MiB extra-byte budget and 20 GiB reserve. No raw captures retained.
node --test tests/*.test.mjs: 168 passed; only the allowed sandbox HTTP listener test failed (listen EPERM). No product Python files changed. Research rank metrics checked against perfect, reversed and tied examples.

Reproduce from the worktree with Python 3.12:

```sh
python3.12 research/team-search/measure_s1.py \
  --benchmark /Users/edo/Documents/ChatGPT/nikke_tools/.portable-recovery/proofs/claude-product-standard-phase0-v1-20261102/native-backend-v1/unit8/long-bodies.json \
  --report /Users/edo/Documents/ChatGPT/nikke_tools/.portable-recovery/proofs/claude-product-standard-phase0-v1-20261102/team-search-v1/s1-report.md
```

Final checks: Python compilation; all 2,460 row counts, distinct membership, scores, B coverage, pending native verification, five-team disjointness/totals and temporary capture cleanup; git diff --check. Product edits only remove rankCombatPool and its two unused tests.

## Decision

The current sum-potential score is inadequate for aggressive shortlisting in this scenario: top-500 misses 81.0% of the measured detailed top-100. Investment in a better L2 is justified by this sample; first close the reported kernel composition/capacity gaps, then measure a proposed surrogate against this baseline. These data do not establish which new surrogate will work.

This single profile/scenario and 2,300 random squads cannot certify a global top-K or a safe hard burst constraint. All-character coverage remains a prerequisite before building a new L2.

Raw data: `research/team-search/s1-results.jsonl`; summary: `research/team-search/s1-summary.json`; inputs: `research/team-search/s1-inputs.json`. No commit or push.
