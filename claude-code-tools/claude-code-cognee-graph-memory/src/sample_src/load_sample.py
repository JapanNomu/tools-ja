"""
同梱サンプルノウハウを Cognee グラフ記憶に投入するスクリプト。

セットアップ後の動作確認用。内部で
`src/main_src/import_to_graph.py --target sample` を呼び出すだけのラッパー。

使用方法:
    cd <配布用のルートディレクトリ>
    src/venv/bin/python3 src/sample_src/load_sample.py
"""
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # src/sample_src → src → 配布用ルート
IMPORT_SCRIPT = PROJECT_ROOT / "src" / "main_src" / "import_to_graph.py"
PYTHON = PROJECT_ROOT / "src" / "venv" / "bin" / "python3"


def main() -> None:
    """src/main_src/import_to_graph.py --target sample を呼び出す"""
    if not IMPORT_SCRIPT.exists():
        print(f"エラー: {IMPORT_SCRIPT} が見つかりません", file=sys.stderr)
        sys.exit(1)

    if not PYTHON.exists():
        print(f"エラー: venvのPythonが見つかりません: {PYTHON}", file=sys.stderr)
        print("セットアップ手順（docs/SETUP.md）に従ってvenvを作成してください", file=sys.stderr)
        sys.exit(1)

    # import_to_graph.py に処理を委譲
    result = subprocess.run(
        [str(PYTHON), str(IMPORT_SCRIPT), "--target", "sample"],
        cwd=str(PROJECT_ROOT),
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
