"""Publish v32 evidence only after both final verifier processes have passed."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
expected=[('research/detail-boss-buffs-verification.json','cases',40),('research/detail-boss-buffs-long-verification.json','cases',6),('research/detail-boss-buff-boundaries-verification.json','cases',2),('research/detail-normal-acceptance.json','tests_run',77)]
for path,key,n in expected:
 r=read(path);assert r['passed'] and (len(r[key]) if key=='cases' else r[key])==n,path
 assert all(sha(f)==h for f,h in r['source_sha256'].items()),'stale '+path
notes=read('research/boss-gpu-integration-notes.json')
notes['status']='v32 ordered boss buff/dispel lifecycle and two query-cache RNG regressions verified; incoming combat remains CPU-only groundwork'
notes['verification']={'native_and_ptx_battles':40,'native_180_second_battles':6,'capacity_boundary_battles':2,'normal_python_tests':77,'node_tests':26,'normal_api_total':334921663,'compiler_acceptance':{'default_characters':135,'total_default_characters':203,'favorite_contexts':529,'total_favorite_contexts':812},'all_character_parity_proven':False,'browser_interaction_verified_this_phase':False}
notes['incoming_target_transition_cpu_groundwork']={'report':'research/detail-incoming-target-transitions-cpu-reference.json','cases':6,'gpu_implemented':False,'coverage':['Stealth expiry and all-hidden fallback as the live pool changes','Periodic hidden taunter, enemy-target taunt, first live recipient of a group taunt','Downed members excluded; separate boss PRNG state before and after every target selection']}
(ROOT/'research/boss-gpu-integration-notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
path=ROOT/'README.md';text=path.read_text(encoding='utf-8')
paragraph='v32はネイティブ版・PTX版の計40ケース、180秒の6部隊戦闘、敵行動32件・効果256件の境界2ケースで、部隊合計・個人別ダメージ・バースト履歴・毎フレームの敵状態・最終乱数状態をCPU版と照合しました。武器変更終了時とフルバースト終了時のキャッシュ更新で乱数がずれる2件も修正し、回帰ケースに含めています。通常経路のPythonテスト77件、Nodeテスト26件、通常APIのGPU計算・CPU照合・編成まとめ計算・変更前後のキャッシュ分離も通過しました。保存画面データは実際のUIパーサーで検証済みですが、この段階でブラウザー操作を再検証したという意味ではありません。検証は架空の所持データを使っており、実アカウント読込・全キャラ対応・高速化率の証明にはしていません。詳細は`research/detail-boss-buffs-checkpoint.json`に記録しています。'
if paragraph not in text:
 marker='ロザンナは別の未対応効果'
 assert marker in text
 text=text.replace(marker,paragraph+'\n\n'+marker,1);path.write_text(text,encoding='utf-8')
print('Final v32 evidence recorded; full GPU objective remains incomplete.')
