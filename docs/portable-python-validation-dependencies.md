# 独立oracleのPython依存を実行前に確認する

固定package内で `python scripts/nikke_gpu.py validation-deps --out NEW.json` を実行します。開発checkoutでは `--suite coordinate-landing` を加えます。選択されたテストが独立pow oracleを使う場合、同梱requirements-validation.txtのgmpy2==2.2.1と、distribution metadata・実import版・module path・MPFR版を確認します。`--smoke` は制御テスト群だけの依存範囲です。

インストール・環境変更・GPU・数値検証は行いません。全Python依存の網羅的監査ではなく、現在登録したpow/landingテストの独立MPFR oracleに限定したチェックです。必要なファイルはimmutable payloadに束縛され、存在しなければpackage作成時に拒否します。通常runもCPUテストworker起動前にpython-dependencies.jsonを保存し、不足・版違い・DLL import失敗なら停止します。CPU比較・独立seal・GPU条件を省略する経路ではありません。

Windows v3はgmpy2不足でimport時に停止、compile/GPU0、原capture保持。既存の検証専用envから25file/3379846byteを新しい診断専用dependenciesへコピーし、全SHA一致・gmpy2 2.2.1/MPFR4.2.1 importを確認しました。既存venv/SDK/user-site/PATH/OSの変更とnetwork downloadは0。元wheelのSHAは不明として記録し、コピー後ファイルの一致とimport成功以上の出所認定はしません。

v4 packet06c781aa…は数値/golden/全GPU不変、依存tool/pin同梱とテストだけを追加。Mac関連36・制御525（Win1skip）成功。新8検査は不足・版違い・壊れたextension・metadataと実importの不一致・不正pin・無関係なsuite・成功・worker前停止を含みます。compact投影は既存test_typed_geometry.pyも追加しましたが、元Git byteと一致。Windowsの新runは別captureで初回GPUだけを依頼しています。

Windows v4は依存確認・36検査・40/native26比較・NVRTC2.586690秒/ret0・module読込まで成功し、cuLaunchKernelがcode2で失敗しました。成功launch0/readbackなし/計算未認定。保存CUBIN311824byte/SHAe8550ca1…をfile-only cache-probeでhit確認（0.086559秒、compile/driver/GPU追加0）。GPU空き容量やstack/localは保存記録に無く原因未確定。内Job peak2098597888byteは上限近傍ですが因果関係は未証明です。report commit6ed21084…のJSON2blob（3367byte）をMacでhash検査、package/input/generated指紋も一致。CUBIN/Job原本のMac独立監査ではありません。次は同じcacheを必須にしてcompiler DLLを載せない実行profileを明示的に検証する候補。原失敗/claim保持、cold再試行やcap増大をしない。
