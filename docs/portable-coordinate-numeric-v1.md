# 決定的な座標数値規約 v1

ユーザーが選択したCUDA／Metal共通の結果を基準とする方針に沿って、`coordinate-binary64-v1`を実装した。CPU参照と共通Slangが同じ係数・演算順のIRを使う。Metalで2,783入力（共通CPU参照2,771／拒否12）の全word一致と保存結果の独立sealに成功した。GPU実行1回、再試行0。旧CPU正本・Mac／Windowsの1ULP差の歴史資料・公開GPU受付は変更していない。

## 数値契約

- degreeのsin/cosは全有限binary64を対象とし、絶対値の正確な360剰余から90度sectorへ縮約する。軸のsinゼロは入力の符号、cosゼロは正のゼロとする。旧host libmと異なる結果を意図的に持つ新profileである。
- radianのsin/cosは絶対値がbinary64のtau以下の有限値に限定する。pi/2の24bit分割定数6個で縮約し、軸付近の桁落ちを避ける。
- sin19次・cos20次・atan63次の係数を有理数からbinary64へ丸め、各命令後にnearest/evenへ丸める。融合演算を使わない。Metalでは既存の整数によるsoftware binary64を使い、native doubleに依存しない。
- atan2は有限2入力、符号付き軸、min/max比、pi/8境界での縮約を定義する。acosは有限[-1,1]に限定し、`atan2(sqrt((1-x)*(1+x)),x)`を使う。
- sqrtは有限の非負値と負のゼロを対象とし、整数2乗の中点比較とties/evenで決定する。subnormalも対象とする。

`app/portable_coordinate_numeric_v1.py`からSlang全体を生成し、検証前にbyte一致を要求する。契約のmetadata SHAと実装source SHAは別に記録する。比較器の`reference_kind`は`deterministic-common-cpu`。CLIの既存`native`件数欄はこのsuiteでは共通CPU参照数を表し、旧host libm正本との一致を意味しない。

## 独立した精度監査

```sh
python scripts/nikke_gpu.py numeric-audit --samples 2048 --out /tmp/new-numeric-accuracy.json
python scripts/nikke_gpu.py package --suite coordinate-numeric --compact --out /tmp/new-numeric.zip
```

`numeric-audit`はGPU・compiler・native battleを起動せず、独立したAGMのpi、Decimal190桁の収束級数、別のacos変形で比較する。出力は新規作成のみ。10,451入力で最大ULPはdegree sin/cos=1、bounded radian sin/cos=1、atan2=1、acos=2、sqrt=0だった。三角関数の4ULPゲートは標本の経験的検査であり、全入力の誤差証明や正しく丸められた三角関数を主張しない。sqrtの独立比較ゲートは0 ULPである。

Metalの入力133,588byte／出力178,112byte、GPU時間0.001873秒、shared execute全体17.188秒。後者にはSwift起動等を含む。今回`CLANG_MODULE_CACHE_PATH`だけでは既存runnerが専用pathを採ったため、次回は既存の`NIKKE_METAL_MODULE_CACHE`を明示して再利用する。測定目的でのGPU再実行はしない。

最終CPU9件、関連・制御436件（Windows専用1skip）成功。full2,944→compact1,614で全残存record・byte・golden一致。旧scalar640／arcs135／composed97／generation88／mixed81はsource一致を確認しGPU再実行0。保護された正本・binary64・normalizer・compiler cacheのSHAも保持した。

## 残る接続

今回の証明は数値部品のMetal実証であり、CUDA実行は未取得。共通Slang・入力・比較器をWindowsの短いprobeにそのまま使う。本体の全編成再ビルドは不要である。

回転形状caller、幾何arc生成、半径方向の積分、cache key丸め、物理packet／RNGからresident戦闘実行器への接続は未完了。旧shape/area suiteは歴史上のnative host profileとして保持する。全キャラ認証0、20分類のgap、UI CPU・公開受付未対応を維持する。最新の機械可読記録は`research/portable-coordinate-numeric-v1-checkpoint.json`、小さな検証資料は`research/coordinate-numeric-v1-evidence/`にある。

Windows用の固定sourceは`d1a1e210c7510d9b87d4836068f086a3ca3722a3`、再現package IDは`505e0fd6c6615c4fa016c00c728c7205637f1982218537b8eb8862a7efcc3779`。検証依頼の送信はCodex APIの`without an active turn id`エラーで拒否され、実行開始は未確認。idle状態の同じsnapshotを繰り返し取得して待機中と扱わない。`windows-dispatch.json`に失敗を保存した。Windows側で新規作成先・claimを確認してから、元の短い依頼を届ける必要がある。
