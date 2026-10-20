"""Publish local checkpoint only after the final validation/efficiency decision exists."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research'
def load(n):return json.loads((P/(n+'.json')).read_text())
def main():
 v=load('portable-burst-charge-validation');assert v['passed'] and v['efficiency_evaluated'] and not v['production_optimization_adopted']
 m=load('portable-combat-metal');t=load('portable-burst-charge-transfer-completed');w=load('portable-burst-charges-v75-execution')
 checkpoint=dict(v,wire_abi='0x50455670',verified_commit=v['source_commit'],previous_checkpoint=dict(proof_commit=v['previous_proof_commit'],report='Git baseline portable-combat-checkpoint.json'),
   input_words=86016,output_words=159744,input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],metal_verified=True,cuda_verified=True,
   metal_report='portable-combat-metal.json',cuda_report='windows-portable-burst-charge-v75.json',windows_report='windows-portable-burst-charge-v75.json',
   windows_execution_metadata='portable-burst-charges-v75-execution.json',windows_execution=w['execution'],cuda_verification_mode='fresh current-source full3331 core;Mac broad and HP20 separate',
   windows_checks_this_stage=dict(current_gpu_sessions=1,superseded_v74_gpu_sessions=1,transfer_gpu_sessions=0),
   source_provenance=dict(fixed_shared_source_commit=v['source_commit'],windows_source_commit=v['source_commit'],previous_proof_commit=v['previous_proof_commit']),
   validation_receipt='portable-burst-charge-validation.json',generated_source_comparison=t['normalized_generated_sha256'],
   normal_ui_backend='cpu',normal_ui_connected=False,all_characters_supported=False,
   next_work=['Connect HP-derived attack preserving native arithmetic/selector semantics','Connect remaining controls and enemy world scheduling','Certify all203 characters and variants'])
 (P/'portable-combat-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n')
 s=load('portable-burst-charge-work-state');s.update(efficiency_evaluation_performed=True,efficiency_status='completed;candidate-rejected',current_validation='portable-burst-charge-validation.json',validation_complete=True);(P/'portable-burst-charge-work-state.json').write_text(json.dumps(s,indent=2)+'\n')
 summary='''## 2026-10-20 バースト充填速度・射撃中スキル係数を共通化

固定ソース `20e213b`、ABI `0x50455670`。`burst_charge_speed_pct` を共通Slangの射撃・スキル加算へ接続しました。付与者の元ゲージ基準値と初回通常命中を保持し、物理射撃内の同期スキルでは、その射撃中の武器係数を使います。スキルのゲージ用バフは名前付き通知前に取得した値を保持します。入力86016／出力159744 wordsを維持し、CPUの戦闘経過をGPUへ渡していません。

新310正例・71拒否を共通化し、Metal／CUDAの全3331入力（2835正例・496拒否）が成功しました。旧2950入力のABI以外の入力・全出力と、初期版3231入力の全出力を保持しています。Windows v75はBelowNormal・120秒上限の実GPU1回、110.52秒で終了。許可済み2ファイルをGit経由で取得し、親コミット・パス・byte数・SHA・全入力・全出力・展開結果・CPU回帰・限定正規化した生成CUDA／MSLを照合しました。元Windows作業とサービスを保持、残存検証0、転送のGPU再実行0です。旧版v74も短い1回を実行しましたが、修正版の認証根拠には使いません。

Mac全41ゲート・単体254件・実編成130条件・既存HTTP APIが成功しました。実編成128条件が既存CPU観測項目と完全一致、ベクハク2条件は従来のHP／最大HPだけの既知差分を固定値で検査します。条件付きHP20例は今回Macで実行しましたが、Windows v75の新規実行範囲は共通コア3331入力です。APIには今回専用の充填速度ケースを追加しておらず、既存経路の回帰検査です。

初期化器への履歴フィールド反映漏れと、武器変更の同期スキルがCPU28・Metal19となる未収録条件を別々に検出・修正しました。失敗入力とreadbackを保持し、後者は元simulateを使う40条件へ拡張して検証しています。以前の原因未特定Metal差分は未解決として保持し、今回の修正と混同しません。

全検証・Windows転送・プロセス終了後、ヒット数のbinary64変換を再利用する候補を別コピーで測定しました。基準・候補の3331＋HP20入力は全入出力一致です。局所5負荷×1024入力、交互順・warmup後3標本の結果と採否は `research/portable-burst-charge-efficiency-decision.json` に記録し、候補は不採用、検証済みソースを維持しました。CUDA速度・実編成全体・物理ピークメモリの改善を意味しません。

定義事前検査の候補65体、愛蔵品257/812条件・全4段階64体、未受付効果300件です。全変種認証0/203・通常画面CPUを維持します。証拠は `research/portable-burst-charge-validation.json`、[充填速度の契約](portable-burst-charge-speed-design.md)、[次のHP由来攻撃力設計](portable-atk-from-hp-design.md)を参照してください。後者はCPU基本60条件・混合順位60条件だけを調査し、GPU受付はまだ有効にしていません。

'''
 for name in ('mac-handoff.md','mac-migration.md','portable-combat-runtime.md'):
  p=ROOT/'docs'/name;text=p.read_text();first,rest=text.split('\n',1);assert summary.splitlines()[0] not in text;p.write_text(first+'\n\n'+summary+rest.lstrip('\n'))
 d=ROOT/'docs/portable-burst-charge-speed-design.md';text=d.read_text().replace('効率測定は別コピーで実行中です。','全検証・転送終了後、別コピーの効率化候補は全3331＋HP20入力の入出力保持を確認しましたが、局所測定の採用条件を満たさず不採用です。記録は `portable-burst-charge-benchmark.json` と `portable-burst-charge-efficiency-decision.json` にあります。');d.write_text(text)
 print('Checkpoint and handoff updated;normal UI CPU;full goal incomplete')
if __name__=='__main__':main()
