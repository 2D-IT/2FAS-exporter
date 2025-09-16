import argparse
import os
import shutil
from typing import List


def _find_pycache_dirs(root: str, skip_dirs: List[str]) -> List[str]:
    found = []
    for cur, dirs, files in os.walk(root, topdown=False):
        base = os.path.basename(cur)
        if base in skip_dirs:
            continue
        for d in dirs:
            if d == "__pycache__":
                found.append(os.path.join(cur, d))
    return found


def _find_pyc_files(root: str, skip_dirs: List[str]) -> List[str]:
    found = []
    for cur, dirs, files in os.walk(root):
        base = os.path.basename(cur)
        if base in skip_dirs:
            dirs[:] = []
            continue
        for f in files:
            if f.endswith(".pyc") or f.endswith(".pyo"):
                found.append(os.path.join(cur, f))
    return found


def clean_pycache_main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove __pycache__ folders (and optionally .pyc files).",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root directory to clean (default: current directory)",
    )
    parser.add_argument(
        "--pyc",
        action="store_true",
        help="Also remove .pyc/.pyo files.",
    )
    parser.add_argument(
        "--include-venv",
        action="store_true",
        help="Include .venv folder in cleaning (skipped by default).",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output.",
    )

    args = parser.parse_args()
    root = os.path.abspath(args.path)

    if not os.path.exists(root):
        print(f"❌ Path does not exist: {root}")
        return 1

    skip_dirs = [".git", "node_modules", "build", "dist", "__pycache__"]
    if not args.include_venv:
        skip_dirs.append(".venv")

    pycache_dirs = _find_pycache_dirs(root, skip_dirs)
    pyc_files = _find_pyc_files(root, skip_dirs) if args.pyc else []

    if args.verbose or args.dry_run:
        for p in pycache_dirs:
            print(("DRY-RUN " + p) if args.dry_run else ("Remove " + p))
        for f in pyc_files:
            print(("DRY-RUN " + f) if args.dry_run else ("Remove " + f))

    removed_dirs = 0
    removed_files = 0

    if not args.dry_run:
        for d in pycache_dirs:
            try:
                shutil.rmtree(d)
                removed_dirs += 1
            except Exception as e:
                print(f"⚠️ Failed to remove {d}: {e}")
        for f in pyc_files:
            try:
                os.remove(f)
                removed_files += 1
            except Exception as e:
                print(f"⚠️ Failed to remove {f}: {e}")

    print(
        f"✅ Clean complete. __pycache__ removed: {removed_dirs if not args.dry_run else len(pycache_dirs)}; "
        f".pyc files removed: {removed_files if not args.dry_run else len(pyc_files)}",
    )

    return 0
