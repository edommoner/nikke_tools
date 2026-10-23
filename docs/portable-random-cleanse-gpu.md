# 有害効果所持者の抽選と解除を共通GPUへ接続

`allies_random_with_debuff:0..5` の直接 `debuff_cleanse` をprivate共通Slangへ接続した。既存のMT抽選、carrier所属、死亡・復活、解除処理を再利用し、CUDAとMetalの計算を分岐させない。通常UIはCPU、旧入口のselector20拒否を保持する。全キャラ・全特殊効果の完成ではない。

## 検証した意味

- 生存する有害効果所持者を編成順に候補化し、本人も含む。`harmful_irremovable` は候補に含むが解除しない。
- MTの同じ抽選器で0〜5人を非復元抽出。空候補・要求0は乱数状態を保持し、singletonでも乱数を消費する。
- 既存解除器で、各人の古い `harmful` から所属だけを外す。共有効果の他人の所属とbeneficial・解除不能効果を保持する。
- 期限切れ、効果を保持したままの戦闘不能、生存者filter、復活後の再候補化、失った常時効果の再付与、毎射撃の付与→解除を確認した。
- `max_trigger` は使い切ったら抽選しない。残数があれば候補の存在確認で抽選し、空なら権利を使わず、対象がいればdispatch内でもう一度抽選する。この順序を共通継続処理へ追加した。

正本契約は基礎18＋live/count12＋budget6＋ココア全71定義3/30秒の2＝38。ココア3秒は解除0回、30秒は1回で、候補が空の原実編成である。有害効果を実際に解除する正例は合成契約で検証した。正本のdispatch・sample・seedを1回ずつ呼ぶ観測器について、合成36契約で全battle/trace/random最終状態とsample/対象解決/get_buffs/有害判定回数の保持を検査した。GPUでは全battle・全skill trace、順序付き抽選、全624語MTと位置、最終carrier所属を比較する。3秒の抽選0回も、実際のnative seed直後のMT状態と照合する。各dispatch前後のnative所属記録を、GPUが全時点で個別出力したとは数えない。

## 固定実行と修復

最初の169入力（native126/拒否43）はApple M5で成功し独立seal済み。その後budget6契約から追加順序を実装し、別packageの175入力を1回実行した。GPU dispatchは終了したが、比較ケースにownerがなくKeyErrorになった。元package/capture/raw/claim/失敗判定を保持し、owner0とGPU前の必須検査を追加したpackageへ移行した。GPU source・入力・native golden全一致を検査して共通CLI replayを実行し、全175（native132/拒否43）が一致、独立sealも成功した。175のGPU再実行は0。

最終packageは `49ebd5d05e4bef8ee3b45e677529bf4e9c159c15f5da00ac3ae1584b9160b5da`。元dispatchは `82a827762ccba430b3e9f4d5140ff0955d0ef0fb4c96a10b9992641da94fd9dc`。両者のsource/input/native goldenは完全一致である。最終goldenは `research/portable-world-random-cleanse-retention-short-expected.json`。個別50入力suiteは開発専用のままで、集約goldenから個別証明を捏造しない。

CPU-onlyの15群125テスト（skip0）は単体計19.826秒・native事前132入力10.400秒。本実行では単体計19.051秒・native10.691秒、Metal175は4.365秒だった。owner必須検査を追加した最終8テストと、その後の分類更新8＋既存11テストも成功した。CUDA/MSL生成はgeneration-onlyで事前確認し、本実行は生成cache必須hit・Slang追加0。Windows/NVRTC/driver/CUDA GPUは実行していないため、現CUDAの成立や速度を認定しない。

旧125の全input52200000B/output393216000B、先の169の全input70574400B/output531628032Bは全byte一致、native指紋も保持した。Runtime反射・stride138952・wire容量・既存数値・normalizer・canonical CPU・旧CUDA・Windows wrapperは不変。GPU変更はrecipient/revival/dispatchの3共有ファイルとprivate入口だけで、厳密な逆投影ledgerと故障注入で他の変更を拒否する。

## 未対応分類と残件

全266profileの静的監査ではココアのpackingが追加され237/266、base177/203となり、分類は42→41。旧236入力SHA、残る拒否理由と分類code順序は保持した。静的packingをGPU実戦認定へ加算しない。分類器は記録済み38契約・scoped Metal175を案内するが、全体GPU/全キャラ認定フラグはfalseを維持する。

次はperiodic tick・別種の有害carrier・免疫・広い通知/対象の混在、敵から有害効果を受ける全定義実編成、現CUDAと全カタログの検証を進める。新private入口で旧全1612を再実行した証拠はない。Windowsの7プロセス終了原因はunknown、環境保全は未認定のまま。

容量は175入力の未圧縮input/output623582404B＋14GiB予備を実空きで確認した。replayの複製分も同様に予算化した。既存CLIによるゼロ領域回収は全byte/SHA/path/inodeを保持し、raw・claim・失敗記録の削除は0。checkpointと選別したJSON/ログは `research/portable-random-cleanse-gpu-checkpoint.json` と `research/random-cleanse-gpu-evidence/` に保存する。
