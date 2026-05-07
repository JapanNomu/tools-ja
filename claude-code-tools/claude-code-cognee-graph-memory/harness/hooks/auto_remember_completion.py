#!/usr/bin/env python3
"""
Stop hook: AI 応答完了時の要点を Cognee グラフ記憶に自動登録

AI（Claude Code）が応答を完了したタイミングで、その応答の要点を
Cognee グラフ記憶に登録する。セッション横断で「AI が何をしたか」を
辿れるようにする。

Stop hook は AI のターン終了時に呼ばれる。Claude Code が出力した
最後のメッセージ（assistant message）を取得し、要点を抽出して
記録する。

仕組み（auto_remember_user_message.py と同じキュー方式・v0.3.0 アーキテクチャ）:
- Stop hook で stdin から transcript を受け取る
- 最後の assistant message を抽出
- ~/.claude/cognee_pending_remembers.jsonl に追記
- Claude Code 内蔵スケジューラ (loop / CronCreate) で起動するバッチ処理が
  同 Claude Code セッション内で動き、既存の MCP cognee サーバーを共有して
  `mcp__cognee__remember` を呼ぶ (新たな cognee-mcp プロセスを spawn しない)。
  この設計により Ladybug DB ロック競合エラー (`Could not set lock on file`) を回避する。

入力: stdin に JSON {"transcript_path": "...", "session_id": "..."} など
出力: exit 0（常に許可。記録失敗してもターン終了はブロックしない）

設計判断:
- AI の応答全文は冗長になるため、先頭・末尾の要点のみ記録（最大2000文字）
- データセット名は "ai_responses"（user_messages とは分離）
- ファイル変更があった場合は別途 incidents/decisions データセットに記録する
  hook を追加してもよい（本サンプルでは ai_responses 一本にまとめる）

設定方法:
  1. このファイルを ~/.claude/hooks/ にコピー
  2. ~/.claude/settings.json の hooks.Stop に登録（settings.example.json 参照）
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# import os

# 記録時のデータセット名
DATASET_NAME = "ai_responses"

# 記録する応答の最大文字数（先頭＋末尾を切り出す）
MAX_HEAD_CHARS = 1000
MAX_TAIL_CHARS = 1000


def extract_last_assistant_message(transcript_path: str) -> str:
    """
    transcript ファイル（JSONL形式）から最後の assistant message のテキストを抽出する。
    Claude Code の transcript は1行1JSON。assistant の content[].text を連結する。
    """
    path = Path(transcript_path)
    if not path.exists():
        return ""

    last_assistant_text = ""
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # role=assistant のメッセージを記録
                role = entry.get("role") or entry.get("type", "")
                if role != "assistant":
                    continue

                content = entry.get("content") or entry.get("message", {}).get("content", [])
                if isinstance(content, str):
                    last_assistant_text = content
                elif isinstance(content, list):
                    parts = []
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            parts.append(c.get("text", ""))
                    if parts:
                        last_assistant_text = "\n".join(parts)
    except Exception:
        return ""

    return last_assistant_text


def truncate(text: str) -> str:
    """応答が長すぎる場合は先頭と末尾を残して中略する"""
    if len(text) <= MAX_HEAD_CHARS + MAX_TAIL_CHARS:
        return text
    head = text[:MAX_HEAD_CHARS]
    tail = text[-MAX_TAIL_CHARS:]
    return f"{head}\n\n... (中略) ...\n\n{tail}"


def queue_remember(message: str, session_id: str) -> None:
    queue_path = Path.home() / ".claude" / "cognee_pending_remembers.jsonl"
    queue_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "dataset_name": DATASET_NAME,
        "data": f"[AI応答 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}",
    }

    with queue_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        transcript_path = data.get("transcript_path", "")
        session_id = data.get("session_id", "unknown")

        if not transcript_path:
            sys.exit(0)

        text = extract_last_assistant_message(transcript_path)
        if not text:
            sys.exit(0)

        truncated = truncate(text)
        queue_remember(truncated, session_id)

    except Exception:
        # 記録失敗してもターン終了は絶対にブロックしない
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
