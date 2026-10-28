# ADR-0007: 執筆支援ツール ubCode の採用

## ステータス

   採択（2026-10-28、PR #87 にて採択）

## 文脈

要件と検証ケースは、MyST の原稿に sphinx-needs の need として書いている。誤りを検出する
手段は Sphinx のビルド（`-W`、`needs_warnings`、フィールドのスキーマ）と metadata_lint で
あり、いずれもビルドを実行して初めて結果が出る。リンク先 ID の書き誤り、列挙値の誤り、
ID の重複は、書いている最中には分からない。

need は 97 件（システム要件 7、ソフトウェア要件 38、アーキテクチャ要件 6、検証ケース 46）
に増え、検証条件の need 化（#78）でさらに増える。needs MCP サーバー（#81）で Claude Code
から要件を引けるようになったが、これもビルド後の needs.json を読む。

ubCode（useblocks GmbH）は sphinx-needs 用の VS Code 拡張と CLI（`ubc`）である。原稿を
独自のエンジンで索引し、診断、ホバー、定義へのジャンプ、プレビュー、トレースグラフを
ビルドなしで提供する。クローズドソースの商用ソフトウェアだが、OSI 承認ライセンスで
全ソースを公開している OSS プロジェクトには無償で提供される。本リポジトリは公開かつ
BSD-3-Clause であり、この条件を満たす。

#86 で ubCode を試用し、結果を #86 に記録した。判断に関わる事実は次のとおりである。

- ubCode は `conf.py` を読まず、`ubproject.toml` から設定を読む。need の設定を写した
  `docs/ubproject.toml` を置いても、Sphinx の出力（needs.json）は変わらない
- `conf.py` から need の設定を消し、`needs_from_toml` で同じファイルを読ませても、
  同一の needs.json になる。設定は Sphinx と ubCode で共有できる
- 解釈が Sphinx と異なる点がある。フィールドのスキーマで `type` を省略すると、Sphinx は
  補って通すが、ubCode は設定エラーにする（`status` で発生し、`type` を明示して解消した）
- ubCode のドキュメントには `needs_warnings` の記載がない。エディタでは評価されない前提とする
- Sphinx の自作拡張は ubCode では実行されない。#78 で予定している自作 directive が
  生成する need は、ubCode からは見えない

なお、useblocks が以前提供していた OSS の sphinx-needs 用 VS Code 拡張は、非推奨・
保守終了となっている。

## 検討した選択肢

### 選択肢A: 現状のまま、ビルドと metadata_lint だけで検査する

利点：

- 新しいツールへの依存がない

欠点：

- 誤りが分かるのはビルドの後であり、書いている最中には確認できない

### 選択肢B: ubCode を執筆支援として採用し、合否の判定はビルドに残す

利点：

- 書いている最中に誤りが分かる。プレビュー、need のカード、トレースグラフで、
  ビルドせずに内容を確認できる
- Python 環境を必要としない。VS Code に拡張を入れるだけで使える
- 設定ファイル（`ubproject.toml`）は sphinx-needs も読める形式である。ubCode をやめても
  設定の置き場所として残るため、ツールへの縛り付けが小さい

欠点：

- クローズドソースへの依存である。提供条件の変更や、0.x 版での仕様変更の影響を受ける
- `needs_from_toml` で一本化するまで、`conf.py` と `ubproject.toml` の二重管理になる
- Sphinx と解釈が異なる箇所があり、両方で通る書き方にそろえる必要がある
- 自作拡張が生成する need は ubCode から見えない

### 選択肢C: 同等のエディタ支援を自作する

利点：

- 仕組みを理解でき、プロジェクトに合わせて作り込める。needs MCP サーバー（#81・#85）の
  延長として学習の価値がある

欠点：

- 書いている最中に検査するには、needs.json ではなく原稿そのものを解析する必要があり、
  工数が大きい

## 決定

選択肢B を採用する。運用は次のとおりとする。

1. **位置づけ**：ubCode は、執筆中の検査、プレビュー、ナビゲーションの補助とする。
   成果物（HTML、needs.json）と合否の判定は、引き続き Sphinx のビルド（`-W`）、
   metadata_lint、pytest が担う。ubCode の診断は CI のゲートにしない
2. **設定**：`docs/ubproject.toml` に置く。`conf.py` の need の設定（`needs_types`・
   `needs_fields`・`needs_links`）を写し、`needs_from_toml` で一本化するまでは両方を
   同時に変更する。`needs_warnings` と `needs_build_json` は `conf.py` だけに置く
3. **書き方**：Sphinx と ubCode の両方で通る書き方にそろえる。フィールドのスキーマには
   `type` を明示する
4. **CI**：CI では `ubc` を使わない。CI/CD での利用にはシステムライセンスが必要とされて
   おり、OSS の扱いが及ぶかを確認できていないため
5. **ライセンス**：OSS 向けの無償の条件で利用する。リポジトリの非公開化など、条件を
   外れる使い方をする場合は商用ライセンスが必要になる
6. **対象外**：Pharaoh（`ubc agent`）は実験的機能のため使わない

## 理由

誤りの発見を、ビルドの後から書いている最中へ前倒しできることが、採用の主な理由である。
need が増えるほど、ビルドを往復して誤りを探す負担は大きくなる。

合否の判定をビルドに残すことで、ubCode と Sphinx の解釈の差（`needs_warnings`、
自作拡張）が品質の判定を損なわない。ubCode が使えなくなっても、ビルドと CI は
そのまま動き続ける。補助に限定するからこそ、クローズドソースへの依存を受け入れられる。

設定ファイルを Sphinx と共有できることも、判断を後押しした。ubCode をやめる場合でも、
`ubproject.toml` は `needs_from_toml` による設定の置き場所として使い続けられる。

自作（選択肢C）は学習の価値があるが、書いている最中の検査には原稿の解析が要る。
needs MCP サーバーは needs.json を読む設計であり、その延長では実現できない。

## 影響

ポジティブな影響：

- 書いている最中に、リンク切れや列挙値の誤りに気付ける
- レビュー前の自己点検で、プレビューとトレースグラフを使える

ネガティブな影響：

- 一本化までの間、`conf.py` と `ubproject.toml` の二重管理が技術的負債になる
- #78 の自作 directive が生成する need は ubCode から見えない。検証ケースからのリンクが、
  エディタ上でリンク切れとして表示される見込みである。対処は #78 で決める
- PlantUML のプレビューは Mermaid への変換による簡易表示である。図の確認は、
  引き続きビルドで行う

後続の作業（別 issue で行う）：

- `needs_from_toml` による設定の一本化。#78 で need の type・フィールド・リンクを
  追加する前に行い、二重管理の期間を短くする。あわせて、Makefile の `conf.py` の
  変更検知に `ubproject.toml` を加える
- `.devcontainer/devcontainer.json` への拡張の追加
- `needs_warnings` を、ubCode でも評価されるスキーマ検証へ移せるかの検討

関連する要件：なし（開発基盤）

将来の見直し条件：

- ubCode の提供条件が変わった場合
- 一本化の後も、Sphinx と ubCode の解釈の差が執筆の妨げになる場合
- CI で `ubc` を使う必要が生じた場合（ライセンスを確認のうえ、本 ADR を改訂する）

## 関連

- 関連要件: なし
- 関連 ADR: ADR-0004（needs.json を突合先とするメタデータ管理。ubCode の採用は突合先を変えない）
- 関連 issue: #86（試用と評価）、#78（検証条件の need 化）、#81・#85（needs MCP サーバー）
- 参考資料: ubCode documentation 0.38.0（useblocks GmbH、<https://ubcode.useblocks.com/>）、
  License configuration（<https://ubcode.useblocks.com/usage/ublicense.html>）
