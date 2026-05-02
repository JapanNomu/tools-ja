#!/usr/bin/env python3
"""
Cognee MCP サーバー起動スクリプト

Claude Code の MCP 設定から呼び出される。
配布用ルートを自動解決し、config/.env を環境変数に読み込んでから
venv 内の cognee-mcp を起動する。

登録コマンド:
  claude mcp add cognee --scope user src/main_src/start_cognee_mcp.py
"""
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# このファイルの場所から配布用ルートを動的に解決する
# src/main_src/start_cognee_mcp.py → src/main_src → src → 配布用ルート
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
ENV_FILE = PROJECT_ROOT / "config" / ".env"
VENV_BIN = PROJECT_ROOT / "src" / "venv" / "bin"
COGNEE_MCP = VENV_BIN / "cognee-mcp"


def load_env_file(path: Path) -> None:
    """.env の KEY=VALUE を os.environ に読み込む。

    cognee-mcp 子プロセスは execv で os.environ を継承するため、
    config/.env に設定された LLM_API_KEY / LLM_ENDPOINT /
    SYSTEM_ROOT_DIRECTORY などを cwd に依存せず cognee ランタイムへ
    確実に渡せる。既存の環境変数は .env の値より優先する。
    """
    if not path.exists():
        logger.warning(".env が見つかりません: %s （未読み込みで継続）", path)
        return

    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def main() -> None:
    # cognee-mcp バイナリの存在確認
    if not COGNEE_MCP.exists():
        logger.error("cognee-mcp が見つかりません: %s", COGNEE_MCP)
        logger.error("セットアップ手順に従って venv を作成してください")
        sys.exit(1)

    # config/.env を環境変数に読み込み、cognee-mcp 子プロセスへ伝播させる
    load_env_file(ENV_FILE)

    # プロジェクトルートをカレントディレクトリに設定（Cognee 内部で
    # cwd 基準の相対パス解決を行う処理があるため）
    os.chdir(PROJECT_ROOT)
    logger.info("起動: %s", COGNEE_MCP)

    try:
        # 現在のプロセスを cognee-mcp に置き換える（メモリ効率のため execv を使用）
        os.execv(str(COGNEE_MCP), [str(COGNEE_MCP)])
    except OSError as e:
        logger.error("cognee-mcp の起動に失敗しました: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
