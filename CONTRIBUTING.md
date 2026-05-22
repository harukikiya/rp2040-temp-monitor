# 開発の進め方

本プロジェクトは個人の学習プロジェクトだが、GitHubを使ったチーム開発の作法を
体験する目的で、ブランチ運用、issue管理、PRレビューを実践する。

本プロジェクトは ASPICE V字モデルに準拠した開発プロセスを実践する。
プロセスの詳細は [docs/common/00_overview.md](https://github.com/harukikiya/rp2040-temp-monitor/blob/master/docs/common/00_overview.md) を参照。

## ブランチ運用（GitHub Flow）

### 基本ルール

- `master` ブランチは常に動作する状態を保つ
- 新しい機能や修正は `feature/...` ブランチで行う
- 作業完了後、PR を作成して `master` にマージ
- マージ後はブランチを削除する

### ブランチ命名規則

``` bash
feature/<issue番号>-<簡潔な内容>
```

例：

- `feature/1-boot2-comments`
- `feature/5-linker-script`
- `feature/12-led-blink`

issue 番号を含めることで、後でブランチを見たときに何の作業だったか追跡しやすくなる。

## issue 運用

### 粒度

issue は内容に応じて3系統で管理する：

- **機能実装系**：サブ段階(2-A、2-B、2-C-1 など)ごとに作成
- **インフラ系**：開発基盤の改善（CI、GitHub Pages、pre-commit など）は `INFRA-N` の連番で作成
- **ドキュメント整理系**：既存ドキュメントの構造変更、ASPICE 対応、用語整理などは `DOC-N` の連番で作成

機能実装と開発基盤の改善、ドキュメント整理は別軸で管理することで、進捗の見通しを良くする。

### タイトル形式

機能実装系：

``` bash
[段階番号] 簡潔な内容
```

例：

- `[2-C-2] boot2_w25q080.S にDoxygen ヘッダコメントとセクション解説を追加`
- `[2-C-3] リンカスクリプトの作成`

インフラ系：

``` bash
[INFRA-N] 簡潔な内容
```

例：

- `[INFRA-1] GitHub Actions と GitHub Pages の導入`
- `[INFRA-2] pre-commit hook の導入`

ドキュメント整理系：

```bash
[DOC-N] 簡潔な内容
```

例：

- `[DOC-1] ASPICE プロセスに準拠したドキュメント番号体系への整理`

バグ報告は `[BUG]` プレフィックスでテンプレートを利用する。

### 本文

issue テンプレート（`.github/ISSUE_TEMPLATE/`）に従う。

## Pull Request 運用

### タイトル形式

ブランチ名と同様、issue 番号を含める。

``` bash
[#<issue番号>] 簡潔な内容
```

### 本文

PR テンプレート（`.github/pull_request_template.md`）に従う。

### マージ前チェック

- 関連 issue が解決される内容になっているか
- pre-commit のチェックが通っているか
- ビルドが通るか
- （将来）CI が通っているか

### マージ方法

「Squash and merge」を基本とする。コミット履歴をクリーンに保つ。

## レビュー

1人開発のため、人間によるレビューは行わないが、以下を活用する：

- **Claude Code**：ローカルで PR の差分をレビューしてもらう。プロジェクトの方針は `CLAUDE.md` と `.claude/review/` 配下のレビュー専門ファイルに記述しており、Claude Code が自動的に参照する
- **このプロジェクトでの会話 Claude**：設計判断や方針について議論
- **自己レビュー**：PR 作成前に diff を読み返す

## コミットメッセージ

将来 Conventional Commits を導入予定。当面は以下を守る：

- 1行目に簡潔な要約（50文字程度）
- 必要なら空行を挟んで詳細
- 日本語で書いて良い
- 末尾に `(#<issue番号>)` を含める
