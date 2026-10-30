#!/usr/bin/env python3
"""Compatibility entry point for the maintained offline-builder guide renderer."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "offline-installer/tools/render_rollout_guides.py"), run_name="__main__")
