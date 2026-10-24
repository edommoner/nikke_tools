# 現在の全本体PTXと共通packetのobject経路

## 方針

直接O0 CUBINは現在の全ソースでptxasの割当失敗になった（前回記録）。既存の旧本体ではPTX→再配置可能object→nvJitLinkが実証され、full PTX約15秒／peak506MB、object約6.5秒／267MB、link約0.21秒／85MBだった。これは旧ソースの実測であり、現在の所要メモリ／実行成功を証明しない。共有Slangを切り詰めたりMetalと別の効果実装を作る前に、既存の分離コンパイル経路を現在の全本体へ再利用する。

共通 `compiler-stats` で保存CUDAの原byteとevidenceを検査した。2,221,708byte／886関数／noinline256、最大はadmitDefinitions_0 130,093byte、applyDefinitionFrame_0 74,760byte、executePortableCommands_0 65,890byte。Runtimeの宣言member合計138,916byte／単純整列推定138,952byte。これらは字句統計であり、実際のインライン化やcompilerメモリの原因帰属ではない。今回noinline注釈・共有計算・数値・normalizerを変更していない。

## 現在の全ソース証明書

既存 `compiler-certificate --suite attack-group-long` で元package `/tmp/nikke-long-group60-v2` と保存Metal60ケースを新規独立監査した。現在のgoldenと全input/native/rawが整合し、`research/portable-compiler-full--attack-group-long-source-certificate.json` を登録した。aliasは既存registry由来であり、現在の `gpu/world_attack_group_entry.slang` の全closureとCUDA/MSL指紋を保持する。commands-only entryへ置換しない。証明書自体のcalculation/compiler/cache成功はfalse、entriesは空である。別のMetal証明をsource identityとして参照する。

固定v1のcompiler専用CPU191件は全成功。v4のapp/scripts/GPU retained recordsは全一致、新しい証明書とcompiler certificateテストを加えた。既存compiler whitelistでは未使用のupstream文書IMPL-STATUS.mdが入らないことをprovenanceへ明記し、元文書は変更していない。

Windowsへ固定commit `c1d464f9cb694d425425f3885c7f68a931c3128a` (`codex/current-full-ptx-v1-source`) のpackage/provenanceだけを共有し、`compile-ptx` を1回依頼した。成功済みv4生成cacheを必須にし、CPU/native／Slang再生成・ptxas・link・driver・GPUを実行しない。内60秒／外180秒／2GiB／fresh Job／BelowNormal／gateを維持する。

依頼受付後のstatus取得2回でhostが利用不可となった。実行開始／完了／失敗／PTX生成成功は未確認で、保存結果を取得するまでunknownである。再依頼・claim削除・失敗の再実行はしない。接続復旧を依頼済み。古いsourceのPTXやCUBINを新しい計算の証明へ昇格しない。

## 共通packetの保存artifact stage

`run-gpu-packet.py` に `module-object` と `jit-link-object` を追加した。既存CLIの同名commandへ固定argvで渡すだけで、native tool／link／audit実装は共通の既存コードを使う。親は小さなheader/requestだけを読み、source producer・PTX/cache・tool SHA・元claim・Job等の検査も外側Jobの子内で行う。`--request` は最大16KiBのJSONで、modeごとの全項目一致・絶対path・SHA256の小文字hexを要求し、余計なoptionを拒否する。

module-object request:

```json
{
  "source_package": "C:/proof/OWNER/package",
  "source_capture": "C:/proof/OWNER/compile-ptx/proof",
  "cache_entry": "C:/proof/ptx-cache/EXACT_KEY.json",
  "phases": "C:/proof/OWNER/compile-ptx/proof/phases.jsonl",
  "ptxas": "C:/path/to/pinned/ptxas.exe"
}
```

jit-link-object request:

```json
{
  "object_package": "C:/proof/OWNER/package",
  "object_capture": "C:/proof/OWNER/module-object/proof",
  "object_sha256": "EXACT_64_LOWERCASE_HEX",
  "nvjitlink": "C:/path/to/pinned/nvJitLink_120_0.dll"
}
```

```powershell
& $basePython -B scripts/run-gpu-packet.py --stage module-object --backend cuda `
  --request C:/proof/module-request.json --capture C:/proof/OWNER/module-object `
  --timeout 180 --original-workspace 'C:/Users/owner/Documents/ChatGPT/nikke tools'
# 成功結果を確認してから別claimで --stage jit-link-object を選択する。
```

各工程は独立claim／captureであり、自動fallback・後続実行・retryはない。外180秒／内60秒／2GiBは不変。`diagnostic_verified` と外側の `stage_verified`、環境維持、GPU計算を分ける。service未識別によるCLI exit2は外側成功へ変換しない。object/link成功でもcalculation_verifiedはfalse。固定argv・request不正・偽GPU成功・内側証明成功＋外側失敗の故障注入を含むpacket17検査、全制御391（Windows専用1skip）が成功。新stageの実Windows確認は未実施。

## 保存PTXの利用と所有chain

v2 controllerはv1に対してwrapperとpacketテストの2ファイルだけが変わり、source certificate／全GPU／生成指紋は同じである。まだWindowsへ追加実行は依頼していない。v1のPTX生成が成功した場合だけ、その保存cacheを `NIKKE_CUDA_CACHE_REQUIRED=1` と生成cache必須でv2のcompile-ptxへ入力する。cache miss時は停止し、NVRTCを再実行しない。既存のcompile監査は明示cache hitを証明できる。

通常のsaved-CUBIN providerはproducer package IDとlinked package IDを一致させる。そのためv1 producerをv2 linkへ直接継ぎ足して最終認定しない。v2自身のclaim／captureへ同じ保存PTXをcacheから取り出した後、同じv2 ownerでobject/linkを作る。元v1の証拠は保持する。旧CLIの診断経路は別ownerを監査する用途を持つが、最終providerのID条件を緩めない。

全キャラ認定0・残20model gap・通常UI CPUは継続。現CUDA本体の計算成功は未確認。次は既存PTX結果の取得であり、同じNVRTC実行の再依頼ではない。小さな記録は `research/portable-current-full-compiler-evidence/`、最新状態はcheckpointを参照。
