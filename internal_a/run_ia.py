"""Launcher: `python3 -I -B run_ia.py <command> ...` (isolated mode drops the cwd from sys.path, so set it explicitly)."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ia_eval.cli import main  # noqa: E402

sys.exit(main())
