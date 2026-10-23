# 段階別バースト通知と候補選択

`event41` (`squad_burst_cast:1/2/3`) を共有Slang実行器へ接続する。名前はsquadだが正本は発動者自身のlistenerのみを通知する。順序はcooldown確定・cast mask更新→自身のburst_cast→自身の段階通知→5人のally_burst_cast。受信者、重複descriptor、budget、再突入、条件による拒否をCPU正本で固定する。

段階は条件判定用の論理段階と、自動候補段階を分ける。レッドフードの標準Aは論理Aのまま自動候補B3、明示段階とlive overrideは優先する。明示指定が候補にあるB1/B2は準備済みの別候補も走査する。live overrideだけでは明示指定扱いにならない。weapon wordの下位3bitは論理段階、bit8..9は自動候補、bit10は明示指定。未知bit、不整合な自動候補/明示指定、非world/noncombatの段階通知をGPUで拒否する。配列・stride・数値演算・normalizerは変更しない。

共通CLIの `squad-stage` は16の独立native契約＋14のraw負例、`squad-stage-rosters` は全81定義のレッドフード3/30秒・明示A・live Aと3秒の期限切れAの7入力。live追加はliteral definition1件を同じ静的準備とnativeへ投入する。元81定義とCPU演算は変更しない。`squad-stage-retention` は旧1405＋追加37の1442入力。実編成の物理traceは既存の容量770と省略数を維持し、全packet/全skill列の個別traceを認定しない。

初期不変パッケージのCPU負例の旧前提と監査adapterの旧未対応前提、world guardの位置誤認、B2と既存stage flagの衝突、明示Aの2巡目候補差は失敗記録を保持。修正後は新しいパッケージで検証し、消費済みclaimの再実行は行わない。CPUの数値期待値や正本をGPUに合わせない。

段階30と実編成7はMetal一致と独立GPU0 sealを確認。集約1442(native1144/拒否298)もMetal全一致・独立seal成功。旧1405の4419747840バイトと入力/native指紋、追加37の個別結果も全保持。既存論理6・callback20・実編成12も変更後Metal一致・全raw保持。CPU95群500検査176.226秒、native事前80.025秒、GPU10.771秒。親比較は1060nativeを同一live親から再利用し84はfreshに照合。静的変換は231/266（base171/203）、旧230入力SHAと残る35拒否を保持し、分類62→54。静的変換、GPU受付、実戦一致は別の認定である。

Windowsは追加操作0。ユーザーは終了/再起動/再接続操作なし、ゲーム/動画の可能性を回答したが、7プロセス終了との因果は未確認。原因unknown・環境保全falseを維持。現ソースのCUDA実機一致は未確認。development_only、全キャラ認定0、通常UI CPU、最終目標未達。次は未対応consumerの確認と残る対象/制御の契約拡張。
