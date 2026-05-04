# 設計決定の記録

## グラフ記憶エンジンに Cognee を採用した理由

Cogneeを採用した理由: グラフDB（Cognee 1.0.4以降は Ladybug DB・1.0.3までは KuzuDB）とベクトルDB（LanceDB）と埋め込みモデル（FastEmbed）が内蔵されており、追加インストール不要で完全ローカル動作。外部APIキー不要・追加費用ゼロ要件を満たす。

## MCPスコープを scope=user にした理由

Claude CodeへのMCP登録をscope=userにした理由: scope=projectにすると特定プロジェクト以外のClaude Codeセッションからアクセスできなくなる。グラフ記憶は全プロジェクト横断で参照できることがこのシステムの本質。

## LLMに Ollama + qwen2.5:14b を採用した理由

Ollama + qwen2.5:14b を採用した理由: 完全ローカル動作・外部APIキー不要・既存のOllama環境をそのまま利用可能。エンティティ抽出に十分な性能を持ち、追加費用がゼロ。Cognee の structured output 要件に対し、ローカルLLMの中で唯一動作確認済（v0.1.x マトリクス検証で 20/20 全勝）。

## MCP transport に stdioモードを採用した理由

Claude Codeとの通信にstdioモードを採用した理由: ポートを使用しないため他のサービスとの衝突がない。Claude Codeが子プロセスとして直接起動するため、HTTPサーバーを別途立ち上げる必要がない。
