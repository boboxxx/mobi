#!/usr/bin/env python3
"""Run one CARLA client at a time against an already running empty server."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True, help="New output directory; existing directories are refused")
    p.add_argument("--host", default="100.109.48.32")
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "logs").mkdir()
    runs = [("single60", 60, 1, False), ("three60", 60, 3, False),
            ("obstacle40", 40, 1, True), ("stability600", 600, 3, False)]
    results = []
    for name, seconds, views, obstacle in runs:
        command = [sys.executable, "-u", str(Path(__file__).with_name("run_smoke.py")),
                   "--host", args.host, "--seconds", str(seconds), "--views", str(views),
                   "--out", str(args.out / name)]
        if obstacle: command.append("--obstacle")
        print("START", name, flush=True)
        with (args.out / "logs" / (name + ".log")).open("w") as f:
            process = subprocess.run(command, stdout=f, stderr=subprocess.STDOUT, timeout=1200)
        results.append({"run":name, "returncode":process.returncode, "finished_unix":time.time(), "command":command})
        (args.out / "suite_status.json").write_text(json.dumps(results,indent=2))
        print("FINISH", name, process.returncode, flush=True)
        if process.returncode: raise SystemExit(process.returncode)
    subprocess.run([sys.executable, str(Path(__file__).with_name("validate_results.py")), str(args.out)], check=True)


if __name__ == "__main__": main()
