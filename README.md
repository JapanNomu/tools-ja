# tools-ja

Claude Code 関連ツールの日本語版ハブリポジトリ。

このリポジトリは、英語版（[JapanNomu/tools](https://github.com/JapanNomu/tools)）と
並行して、日本語ドキュメント・日本語ソースコメント・日本語設定ファイルコメントで
完結したツール群を配布します。

## 含まれるツール

### claude-code-tools/

[Claude Code](https://claude.com/claude-code) と連携するツール群。

- [claude-code-cognee-graph-memory](claude-code-tools/claude-code-cognee-graph-memory/) —
  Claude Code に **セッション横断のグラフ記憶** を追加するモジュール。
  [Cognee](https://github.com/topoteretes/cognee) + Ollama + FastEmbed により
  **完全ローカル動作**（外部APIキー不要・追加費用ゼロ）。
  さらに同梱の **自動蓄積ハーネス** を使えば、Claude Code を使えば使うほど
  ノウハウが Cognee グラフ記憶に貯まり、決定・経緯・関連事実が芋づる式に
  引き出せます。

## ライセンス

各ツールはそれぞれの LICENSE ファイルを同梱しています。各ツールフォルダを参照してください。

## 英語版

英語ドキュメント・英語ソースコメントで完結した版は
[JapanNomu/tools](https://github.com/JapanNomu/tools) で配布しています。
