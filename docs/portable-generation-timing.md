# 生成cacheと準備処理の時間計測

前回のWindows core46はSlang2呼び出しの成功記録を最後に全stage90秒でtimeoutした。Slang呼び出し自体は合計0.608秒で、CPU batchは33.685秒だった。Slang終了後にどの処理で止まったかは未確定である。旧runtime/journalにはcacheパス・keyが記録されておらず、保存ファイルの限定読み取りでは当該claim/entryも特定できなかった。推測でcache全体を走査・削除しない。

## 追加した観測

既存 `portable_phase_audit.observe` で生成cacheのidentity、paired validation、read、atomic publicationを包み、reflection・layout assertions・scope snapshot監査も個別に記録する。SDKファイルごとのログは大量のfsyncを招くため出さない。元の関数は引数・返値・例外を保持して完全に実行し、context終了時に復元する。

`Journal.invoke` のreturned/raisedへ `elapsed_seconds` を追加。値は関数自身のentry/exitログ書き込みを除き、内側の呼び出しを含む。入れ子の値は重なるので合算しない。enteredだけの処理には所要時間を作らず、旧journalにも推定値を補わない。共通CLI `status --capture <capture>` はtimed_callsも表示するが、ファイルから現在の生存状態や検証成功を認定しない。

runtimeにはgeneration/NVRTC cacheのパスも保存し、identity確定後にはentry/claimの正確なパスとkeyを観測記録へ残す。これは存在・所有・生存の証明ではなく、停止後に限定した読み取り先を特定するための情報である。claimの取得・解除規則は不変。

## Macの証拠

固定package `8f78d6b5…` を新規展開。core37検査と24 native事前検査の全stageが成功し、外側約3.985秒、shared CLI約3.898秒、CPU tests約3.805秒、gate後verify約0.084秒、CPU worker verify約0.073秒。準備の重複verify除去を含む既存経路を使い、worker検証は省略していない。

同packageの生成準備はcache必須hit・Slang0・NVRTC0・GPU0で成功。sealedのCUDA/Metal正規化指紋・source・reflection検査を保持した。build約0.194秒、そのうちidentity2回が約0.094/0.093秒、read約0.002秒。Macの値からWindowsの遅延原因を推定しない。

固定package内で関連CPU72検査（phase8/cache13/CLI42/packet9）が成功。cache hitのidentity・生成物の全byte保持、正確なrequestパス、監査失敗伝播、observer復元、未完処理の時間非生成を含む。最初のsandbox内phase検査は既存 `ps` に権限がなく失敗し、サンドボックス外の同CPU検査で成功した。GPUによる再検証は行っていない。

Windowsには同じcore37/24事前検査だけを `run-gpu-packet.py --stage cpu --backend cuda --timeout 90` で1回依頼。配布は `codex/cuda-preparation-v2-source` の固定 `b2f72e9049836b82c918c3b21fc9acfba74afced`、package.zipとprovenanceのみ。Slang/NVRTC/driver/GPU/cache-probe/再試行は依頼していない。

## WindowsのCPU計測と修正

v2は60.581秒でexit1、timeoutではない。gate後全件verify38.917秒、CPU worker verify10.447秒、CPU batch全体15.657秒。batchにはworker検証も含まれるので足し合わせない。12検査中11成功、韓国語を含むoverlay診断の `write_text` がcp932で失敗し、残りの検査群と24 native事前検査は未到達だった。前回の全CPU37の33.685秒と、この未完batchの15.657秒を速度比較しない。外側Jobは2GiB/BelowNormal、peak132,665,344B、終了後空、missing0。ただしservice未確認で環境保持はfalse。旧timeoutの原因は引き続きunknown。数値はWindowsチャットの保存結果読取報告で、元captureはWindowsに保持しMac独立raw監査とは数えない。

診断2書き込みをUTF-8明示へ修正し、owned validation childだけ `PYTHONUTF8=1` と `PYTHONIOENCODING=utf-8` を設定した。OSや親環境は変更しない。実際の韓国語を含む7 native overlay witnessをcp932既定で失敗する条件のまま検査し、UTF-8保存・再読込の一致を確認。別の実子プロセスでもUTF-8 modeとUnicode出力・保存、親環境保持を検査する。

全件検証は各ファイルの `is_symlink/is_file/stat` 3照会を1回の `lstat` とregular判定へ統合した。全byte SHAの再読取、全ファイルmembership、worker検証は維持。旧packetの2,667files/40,404,440Bの旧・新レコードが完全一致し、同じサイズの改変・欠落・directory・symlinkを拒否する。Windowsの速度改善はまだ未検証。Macで一度の順序付き比較は実施したが、順序とcacheの影響があるため速度証明にしない。

修正版固定package `4fe0ff04…` はMac新規展開でCPU38＋native24のstageと関連CPU74検査が成功。途中のv3もCPU38成功として保持し、新しいenv修正は別v4 packetとした。Windowsへは `codex/cuda-preparation-v4-source` の `5bc6615d7d694ad0e8aa0eff12a88b1be72f85cf`（2files、ZIP6,881,290B）を共有し、修正版CPU stageだけを1回依頼した。旧stage/claimは再利用しない。結果待ちで、GPU・コンパイラの実行依頼はない。

今回の変更にGPU計算本体・canonical reference・cache identity consumer・strict normalizerの変更はない。旧Metal33/46と戦闘証拠を保持し、全キャラ認定や今回のCUDA数値一致とは数えない。対象別counterへのtyped着弾・所有付き破壊dispatchと、敵弾・敵盾の実戦意味論の接続は引き続き残件である。
