# Windows観測の短い診断

arc arena v1のcompile-onlyは、内側の開始ゲート前のprocess snapshotで停止しました。外側9.571秒／内側1.403秒、timeoutなし。両Jobは終了後member0・cleanup errorなしですが、before／afterの全process観測がなく、containment／preservationの成功認定はできません。Slang・NVRTC・資源解析・GPUはすべて0。原claimと失敗を保持します。出所は `research/coordinate-arc-arena-evidence/windows-compile-v1/` です。

従来の観測器はPowerShellの失敗を一律メッセージへ変換していたため、原因の切り分けができませんでした。現在は同じqueryをtry/catchで囲み、setup／processes／listeners／serializeの段階・数値category・HRESULTだけを記録します。コマンド行・stderr・任意exception messageは保存しません。失敗時のゲート閉鎖、20秒timeout、元のprocess／listener queryは維持。再試行・観測省略・fallbackは追加しません。

共通CLIのCPU入口:

```sh
python scripts/nikke_gpu.py snapshot-check --original-workspace EXISTING_ORIGINAL \
  --validation-root EXISTING_ISOLATED --out EXISTING_ISOLATED/NEW.json
```

出力は絶対パスで、元workspaceと分離したvalidation directory内の新規JSONを要求します。reportを先に排他作成し、同名への再呼出しをquery前に拒否します。通常のcompile claimを消去・再利用しません。Windowsでは既存の低優先度・2GiB・fresh Job/start gateのCPU wrapperから、30秒以内で1回だけ診断します。これはCUDA compiler／driver／module／kernelを呼ばず、snapshot取得成功と環境preservation／計算成功を明確に分けます。観測器だけの成功はbefore/after preservation証明になりません。

12故障注入検査で、native非ゼロexit・段階／数値code・非JSON／不正schema・秘密文字列・部分rows・timeout・二重query・出力先分離を検査し、既存observer11検査も維持しました。共通制御は計555件（Windows専用1skip）。MacでCLIのplatform拒否・report作成・exit1も確認済みです。Windowsで新観測器を使った実queryは次の診断対象です。

## 2026-11-01 実行modeと有限codeの実証

Windows保存85fe12d6はGet-CimInstance Win32_Process(operation1)がCimException(type1)、native_code2で失敗、permission modeはuse_default。Microsoft [MI_Result](https://learn.microsoft.com/en-us/windows/win32/api/mi/ne-mi-mi_result) の2はACCESS_DENIED。現在のsnapshot-checkは同じCIM例外domain＋codeの組だけreason_code=cim_access_denied、他の例外/codeはunknownと表示する。再queryや観測省略は行わない。

同じobserverを正規require_escalated経路で一度だけ実行したe412a000ではsnapshot取得成功、2.800秒、Jobは2GiBを前後とも実測確認・終了後空・cleanup正常。Windows管理者昇格/UAC/ACL/WMI/service設定変更0。サービス識別unverified/不明8件、before/after保全・CUDA計算の成功ではない。過去7process消失の原因とも結び付けない。今後の必要なWindows検証は通常のツール承認経路を用い、原拒否/claimを保持し、同じSDK処理を再試行しない。記録research/product-windows-observation-permission-v1.json。
