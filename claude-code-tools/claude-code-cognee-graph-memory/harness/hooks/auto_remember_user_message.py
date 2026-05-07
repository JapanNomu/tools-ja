#!/usr/bin/env python3
"""
UserPromptSubmit hook: ユーザー発言を Cognee グラフ記憶に自動登録

ユーザーが送信したメッセージを、cognee MCP の `remember` 経由で
グラフ記憶に永続登録する。セッション横断で文脈を引き出せるようになる。

仕組み (v0.3.0 アーキテクチャ):
- UserPromptSubmit hook で stdin から prompt を受け取る
- ローカルの一時ファイル ~/.claude/cognee_pending_remembers.jsonl に追記する
- Claude Code 内蔵スケジューラ (loop / CronCreate) で起動するバッチ処理が
  同 Claude Code セッション内で動き、既存の MCP cognee サーバー
  (Claude Code 起動時から常駐の 1 個) を共有して `mcp__cognee__remember` を呼ぶ
  (新たな cognee-mcp プロセスを spawn しない)。

この設計により Ladybug DB ロック競合エラー (`Could not set lock on file`) を回避する: cognee-mcp プロセス数が
1 個のままなので、同 .lbug ファイルに対する同時ロック獲得要求は発生しない。

UserPromptSubmit hook 内で MCP 呼び出しを直接行うと AI のターン開始が
遅延するため、本実装は非同期ファイルキュー方式を採用している。

入力: stdin に JSON {"prompt": "...", "session_id": "..."}
出力: exit 0（常に許可。記録失敗してもメッセージ送信はブロックしない）

設定方法:
  1. このファイルを ~/.claude/hooks/ にコピー
  2. ~/.claude/settings.json の hooks.UserPromptSubmit に登録（settings.example.json 参照）
  3. cognee MCP が登録済みであること（claude mcp list で確認）

設計判断:
- ユーザー発言の "全件" を Cognee に登録する（フィルタしない）
  理由: 記録を絞ると後で必要になった時に取り出せない。
        グラフ記憶は大量蓄積前提で設計されており、検索で抽出できる。
- データセット名は "user_messages"（用途別に分離）
- 記録失敗してもメッセージ送信は絶対にブロックしない（exit 0 固定）
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# import os
# import subprocess

# 記録対象から除外するメッセージのパターン（短すぎる挨拶等）
MIN_LENGTH = 5  # 5文字未満は記録しない（"うん"等の短い相槌は除外）

# 記録時のデータセット名
DATASET_NAME = "user_messages"

# Cognee MCP サーバーへのコマンド
# 配布物のセットアップで claude mcp add cognee した想定
# 直接 Python から呼ぶ場合は PROJECT_ROOT/src/main_src/start_cognee_mcp.py を起動


def queue_remember(message: str, session_id: str) -> None:
    """
    記録対象のメッセージを ~/.claude/cognee_pending_remembers.jsonl に追記する。
    後段の flusher プロセスが順次 remember を実行する想定。
    """
    queue_path = Path.home() / ".claude" / "cognee_pending_remembers.jsonl"
    queue_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "dataset_name": DATASET_NAME,
        "data": f"[ユーザー発言 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}",
    }

    with queue_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        message = data.get("prompt", data.get("message", "")).strip()
        session_id = data.get("session_id", "unknown")

        if not message:
            sys.exit(0)

        if len(message) < MIN_LENGTH:
            sys.exit(0)

        queue_remember(message, session_id)

    except Exception:
        # 記録失敗してもメッセージ送信は絶対にブロックしない
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
