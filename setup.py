#!/usr/bin/env python3
"""
Setup and launch script for lichess-bot + LeMuffinBot engine.
Works on Linux, macOS, and Windows.

Usage:
    LICHESS_BOT_TOKEN=<token> python setup.py
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

CHESSGAME_REPO = "https://github.com/LeMuffinMan/ChessGame.git"
CHESSGAME_DIR = Path("chessgame")
IS_WINDOWS = platform.system() == "Windows"
ENGINE_DEST = Path("engines") / ("uci.exe" if IS_WINDOWS else "uci")
ENGINE_SRC = CHESSGAME_DIR / "target" / "release" / ("uci.exe" if IS_WINDOWS else "uci")


def run(cmd, **kwargs):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def check(tool, hint=""):
    if not shutil.which(tool):
        print(f"Error: '{tool}' not found.{' ' + hint if hint else ''}")
        sys.exit(1)


# --- Engine ---
print("==> Engine")

check("git")
if (CHESSGAME_DIR / ".git").exists():
    print("Updating ChessGame...")
    run(["git", "-C", str(CHESSGAME_DIR), "pull", "--ff-only"])
else:
    print("Cloning ChessGame...")
    run(["git", "clone", "--depth=1", CHESSGAME_REPO, str(CHESSGAME_DIR)])

check("cargo", "Install Rust from https://rustup.rs")
print("Building UCI engine (this takes a minute on first run)...")
run(["cargo", "build", "--release", "--features=native", "--bin", "uci",
     "--manifest-path", str(CHESSGAME_DIR / "Cargo.toml")])

ENGINE_DEST.parent.mkdir(exist_ok=True)
shutil.copy2(ENGINE_SRC, ENGINE_DEST)
if not IS_WINDOWS:
    ENGINE_DEST.chmod(ENGINE_DEST.stat().st_mode | 0o111)
print(f"Engine ready: {ENGINE_DEST}")

# --- Python venv ---
print("\n==> Python")

venv_dir = Path(".venv")
venv_python = venv_dir / ("Scripts" if IS_WINDOWS else "bin") / ("python.exe" if IS_WINDOWS else "python")
pip = venv_dir / ("Scripts" if IS_WINDOWS else "bin") / ("pip.exe" if IS_WINDOWS else "pip")

if not venv_python.exists():
    run([sys.executable, "-m", "venv", str(venv_dir)])

run([str(pip), "install", "--upgrade", "pip", "--no-cache-dir", "-q"])
run([str(pip), "install", "-r", "requirements.txt", "--no-cache-dir", "-q"])

# --- Token ---
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

if "LICHESS_BOT_TOKEN" not in os.environ:
    print("\nError: LICHESS_BOT_TOKEN not found.")
    print("Create a .env file with:  LICHESS_BOT_TOKEN=your_token_here")
    sys.exit(1)

print("\n==> Starting bot")
run([str(venv_python), "lichess-bot.py"])
