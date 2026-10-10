"""
Pytest configuration ensuring PYTHONPATH includes both backend and repo root
"""

import sys
from pathlib import Path

tests_dir = Path(__file__).resolve().parent
backend_dir = tests_dir.parent
repo_root = backend_dir.parent

for p in [str(backend_dir), str(repo_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)
