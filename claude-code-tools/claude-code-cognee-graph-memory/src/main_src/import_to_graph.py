"""
本番運用中のMDファイル投入スクリプト。

このスクリプトは本番運用中（Claude Code稼働中）に、Cogneeグラフ記憶へ
ノウハウを投入するために使われる。同梱サンプル投入の他、Claude Codeから
随時呼び出される本番投入経路でもある。

使用方法:
  cd <配布用のルートディレクトリ>
  src/venv/bin/python3 src/main_src/import_to_graph.py --target sample
  src/venv/bin/python3 src/main_src/import_to_graph.py --list-targets

ターゲット:
  - sample: 同梱サンプル（knowledge/sample_knowledge/）

注意:
  - 初期投入（大量ファイル）は src/knowledge_src/import_knowledge.py を使う
    （cognify失敗時のリトライ・小分け実行に対応）
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # src/main_src → src → 配布用ルート
WORKSPACE = PROJECT_ROOT.parent
ENV_PATH = PROJECT_ROOT / "config" / ".env"
MCP_COMMAND = str(PROJECT_ROOT / "src" / "main_src" / "start_cognee_mcp.py")


def check_ollama() -> None:
    """Ollama 起動確認と config/.env で指定された LLM モデルの存在確認"""
    env = _load_env()
    llm_model = env.get("LLM_MODEL", "").strip()
    if not llm_model:
        logger.error("config/.env に LLM_MODEL が設定されていません")
        sys.exit(1)

    url = "http://localhost:11434/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        logger.error("Ollama に接続できません: %s", e)
        logger.error("'ollama serve' を実行してから再試行してください")
        sys.exit(1)
    except Exception as e:
        logger.error("Ollama 接続チェックで予期しないエラー: %s", e)
        sys.exit(1)

    model_names = [m.get("name", "") for m in data.get("models", [])]
    if not any(llm_model in name for name in model_names):
        logger.error("%s が見つかりません。利用可能なモデル: %s", llm_model, model_names)
        logger.error("'ollama pull %s' を実行してからやり直してください", llm_model)
        sys.exit(1)

    logger.info("Ollama 接続確認 OK: %s 利用可能", llm_model)


def _load_env() -> dict[str, str]:
    env = os.environ.copy()
    if ENV_PATH.exists():
        try:
            for line in ENV_PATH.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
        except OSError as e:
            logger.warning(".env 読み込みエラー（スキップして続行）: %s", e)
    return env


def make_transport() -> StdioTransport:
    return StdioTransport(
        command=str(PROJECT_ROOT / "src" / "venv" / "bin" / "python3"),
        args=[MCP_COMMAND],
        env=_load_env(),
    )


TARGET_MAP = {
    "sample": {
        "path": PROJECT_ROOT / "knowledge" / "sample_knowledge",
        "dataset_name": "sample_knowledge",
        "description": "同梱サンプルノウハウデータ（動作確認用）",
        "glob": "*.md",
    },
}


def collect_files(target_key: str) -> list[tuple[Path, str]]:
    """対象ファイルと dataset_name のペアリストを返す"""
    if target_key not in TARGET_MAP:
        logger.error("不明なターゲット: %s", target_key)
        sys.exit(1)

    cfg = TARGET_MAP[target_key]
    base_path = cfg["path"]
    if not base_path.exists():
        logger.warning("パスが存在しません: %s", base_path)
        return []

    try:
        files = sorted(base_path.glob(cfg["glob"]))
    except Exception as e:
        logger.error("ファイル列挙エラー (%s): %s", base_path, e)
        sys.exit(1)

    return [(f, cfg["dataset_name"]) for f in files if f.is_file()]


async def import_files(files: list[tuple[Path, str]], dry_run: bool = False) -> None:
    """ファイルを1件ずつ Cognee に投入する"""
    if not files:
        logger.info("投入対象ファイルが0件です。")
        return

    logger.info("投入対象: %d 件", len(files))

    async with Client(make_transport()) as client:
        for i, (file_path, dataset_name) in enumerate(files, 1):
            logger.info("[%d/%d] %s → dataset=%s", i, len(files), file_path.name, dataset_name)
            if dry_run:
                logger.info("  (dry-run: スキップ)")
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
                result = await client.call_tool("remember", {
                    "data": content,
                    "dataset_name": dataset_name,
                })
                text = result.content[0].text if result and result.content else ""
                logger.info("  → %s...", text[:80])
            except Exception as e:
                logger.error("  投入失敗 (%s): %s", file_path.name, e)


def list_targets() -> None:
    """利用可能なターゲット一覧を表示する"""
    logger.info("利用可能なターゲット:")
    for key, cfg in TARGET_MAP.items():
        path = cfg["path"]
        exists = "✅" if path.exists() else "❌ (パス未存在)"
        logger.info("  %s: %s %s", key, cfg["description"], exists)
        logger.info("         パス: %s", path)
    logger.info("  comments: ユーザーコメント記録（--project 00027 等が必要）")


def main() -> None:
    """エントリーポイント"""
    parser = argparse.ArgumentParser(description="MDファイルをCogneeグラフに投入する（本番運用時にClaude Codeから呼ばれる）")
    parser.add_argument("--target", help="投入ターゲット（sample）")
    parser.add_argument("--dry-run", action="store_true", help="ファイル一覧を表示するだけ（投入しない）")
    parser.add_argument("--list-targets", action="store_true", help="利用可能なターゲット一覧を表示")
    args = parser.parse_args()

    if args.list_targets:
        list_targets()
        return

    check_ollama()

    if not args.target:
        parser.print_help()
        sys.exit(1)

    files = collect_files(args.target)
    asyncio.run(import_files(files, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
