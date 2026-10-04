#!/usr/bin/env python3
"""Restore both immutable lossless archive descriptors before independent audit."""
import subprocess,sys
from pathlib import Path
E=Path(__file__).resolve().parent
for name in ('prepare_archive.py','prepare_capture_archive.py'):
    subprocess.run([sys.executable,str(E/name),'--restore'],check=True)
