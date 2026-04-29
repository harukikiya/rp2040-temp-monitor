# RP2040 Temperature Monitor

RP2040内蔵温度センサを使った学習用ベアメタルファームウェアプロジェクト。
DMA、I2C、リングバッファ、デュアルコアの動作を実機で観察する。

## 構成

第1フェーズはC言語、第2フェーズでRust移植を行う。
要件・設計ドキュメントは sphinx-needs で管理。

## 開発環境

VSCode + Dev Containersが前提。リポジトリを開いて`Reopen in Container`を選択すれば環境が立ち上がる。

## ドキュメントのビルド

```bash
make html
```

成果物は`_build/html/index.html`で閲覧できる。

## ローカルサーバで確認

```bash
make serve
```

`http://localhost:8080`でブラウザから確認できる。

## ステータス

段階0：ドキュメント基盤構築中
