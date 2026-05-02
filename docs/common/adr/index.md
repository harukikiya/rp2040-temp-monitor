# Architecture Decision Records

本プロジェクトの重要な設計判断を記録する。
要件の `rationale` フィールドでは収まらない、
複数の選択肢比較や経緯を含む判断を ADR として記録する。

## ADR一覧

```{toctree}
:maxdepth: 1

0001-integrated-adc-dma-driver
0002-inter-core-data-flow
```

## 新規ADRの追加

新しい ADR を追加する場合は、`template.md` をコピーして
`NNNN-kebab-case-title.md` の形式でファイルを作成する。
番号は連番で、欠番は作らない。

## ADRのステータス

- **提案中**: レビュー待ち、まだ採択されていない
- **採択**: 現在有効な決定
- **却下**: 検討したが採用しなかった
- **廃止**: もう使われていない
- **置換(ADR-XXXXによる)**: 別のADRに更新された

採択された決定が後に変更される場合、元のADRを
「廃止」または「置換」とし、新しいADRを作成する。
元のADRは削除しない(履歴として残す)。
