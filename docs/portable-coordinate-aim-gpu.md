# 手動照準・カメラ調停の共通GPU接続

`coordinate-aim`190入力（共通CPU166／明示拒否24）がM5 Metalで一致し、保存rawからGPU禁止の独立監査でsealした。前のmatrix151を保持し、30操作world＋IR拒否8＋strict競合拒否1を加えた。全キャラ認証0／モデルgap20／公開GPU閉鎖／UI CPU／全体目標未達。Windowsでの今回のCUDA計算は未実証。

## 同じ実行器への接続

CUDA／Metal共通Slangのcomplete resident executorへ、手動aim要求・既存click等の要求合流、優先度／新要求edgeによる既存調停、focus-only squad sequence、調停後の5人分の照準bankを接続した。状態窓4種、アンカー5種、burst使用者gate、casterとraw buff名による有限expiry照会、動的reload_totalを扱う。次burst予測は実FB開始差の外挿を優先し、未観測時は既存burst候補規則とready clockからstage鎖を計算する。

フレーム前半の定時skillは前回の点を読み、調停後のphysicalは今回の点を読む。照準点をslot参照だけで持たず、x/yのbinary64を保持するため、core移動・対象消滅・同frame破壊でも旧点が勝手に変わらない。shared cameraでは各カメラ担当が自分の手動点を持ち、focus／全burstの他射手は先頭カメラを追う。0値focus markerもpresenceとして扱う。

Geometry cacheは同じGeometryのまま(ax,ay,R,grow)を完全照合する。手動点はGeometry.auto_aimへ上書きせず、core形状だけを既存の最初の等価Geometry代表へ揃える。旧profileの自動照準経路はcompile時のflagで残す。元CPU、software binary64、pow／整数変換の本体は変更しない。

## Wireと実consumerの配置

input108792wordの後ろへ著者指定の736wordを追加し、全体109528word。1人8entry、core／slot、priority、window／anchor、offset／len、gate、raw buff名ID、最大16のfocus-only sequenceを渡す。runtimeの選択・開閉時刻・照準点・shot時刻をCPUで計算して入力しない。literal offset／lenが5アンカー全部でbinary64のまま残るunitも追加した。

outputは1310720wordのまま。既存CF_END919840からGeometry cache BASE920000までの160wordを使い、実layout生成器・physical arena監査・group owner無効guard・cache境界を再利用して検査する。Runtime structへのfield追加はなく、実Metal reflection／transportのstride138952byteを保持した。group owner／group-trigger62は引き続き拒否する。

7059frameについて、時刻・owner・camera・phase／cast mask・各射手のtargetと点を2種類の非暗号64bit rolling digestとframe数で照合し、最後の5照準bankは全wordを比較した。これは各frameの全raw trace保存とは別の検査。戦闘／fraction通知／ordered packet／Geometry cacheの全entryとtableは従来の比較器をそのまま使い、全readbackのSHAも独立sealで固定する。reserved header190件とunused bank tailも確認した。

旧151のinput prefixと元native指紋136件を保持。新しい照準領域640byte／入力を除く全791578240byteも、以前の保存rawと直接比較して一致した。旧full raw指紋を新profileへ転用していない。

## 失敗・時間・再利用

初版Metalは旧151が成功し、新30のうち26件に差分が出た。7件はcombat_start等のspanをwireへ書いておらず長さ0で初期化拒否、残りはlanding cacheが明示aimをautoへ戻していた。照準bankだけを保存rawで切り分けると22件一致、1件は誤った物理点による破壊差、7件は初期化拒否だった。native正本・比較項目を変更せず両原因を修正し、アンカーwireの検査を追加。v2はCPU／生成のみとし、明示burst候補走査も既存規則へ揃えたv3を別packageで実行した。失敗raw／report／source／claimを保持、同claim再実行0。

新GPU2回（初版失敗1、修正版成功1）。修正版190入力でGPU3.698529秒、初回pipeline91.077731秒、shared execute100.810055秒。実行時Slang0／generation cache必須hit。速度倍率の比較ではない。Windows新規依頼0。read-only snapshotはrevision78・idleで、live GPU jobも今回のCUDA結果も確認していない。

通常81／合成97／core120／cache133の生成CUDA/MSLは、同じpaired generatorで過去の保存物と全byte一致した。strict normalizer・CUDA compile cacheのキー規則は変えない。旧binary再利用の生成条件の証拠であり、新aim entryのWindows計算や実cache hitの証拠ではない。source-only compiler証明書は独立した保存Metal再監査から作り、NVRTC／driverの成功とは区別する。

最初の空き容量gateは不合格でGPU0。既存rawと失敗／成功rawを全byte／SHA／inode保持で疎化し、計2970705920byte回収した。raw削除0、190入力と1GiB reserveを保持。最終CPU90／control416（Windows専用1skip）、model-check成功。full3062→compact1753の全残存fileの実byteと、実証済みGPU source identityを確認した。

```sh
python scripts/nikke_gpu.py package --suite coordinate-aim --compact --out /tmp/new-aim.zip
# 新規展開したpackageをcwdとして実行する。
python scripts/nikke_gpu.py run --backend metal --cpu-only --capture /tmp/new-aim-cpu
```

8entry／16sequence等のprivate容量制約と、group／ADD／scene混在の未接続を保持する。武器変更フレームのreload_total参照実体、他操作軸との複雑な競合、複数cycle・異なるburst候補構成等は追加照合が必要。sampling RNG・全元定義・公開受付も未完了。次はこれらの合成とgroup／ADDのwriter領域・caller統合を優先する。集約は`research/portable-coordinate-aim-gpu-checkpoint.json`、共有証拠は`research/coordinate-aim-gpu-v1-evidence/`。
