#!/usr/bin/env python3
"""Audit recorded CARLA smoke-test results; do not infer road safety."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    args = p.parse_args()
    report = {}
    for name in ["single60", "three60", "obstacle40", "stability600"]:
        folder = args.root / name
        summary = json.loads((folder / "summary.json").read_text())
        with (folder / "frames.csv").open() as f:
            records = list(csv.DictReader(f))
        n = summary["frames"]
        frames = np.asarray([int(r["frame"]) for r in records])
        sensors = np.asarray([int(r["sensor_frame"]) for r in records])
        latencies = np.asarray([float(r["loop_ms"]) for r in records])
        checks = {
            "completed": summary["status"] == "completed",
            "record_count": len(records) == n,
            "world_frames_contiguous": bool(np.all(np.diff(frames) == 1)),
            "aligned_sensor_lag": bool(np.all(frames - sensors == summary["sensor_lag_frames"])),
            "all_streams_full_count": all(v == n for v in summary["counts"].values()),
            "expected_stream_count": len(summary["counts"]) == 2 * summary["views"],
            "no_stale_frames_after_warmup": all(v == 0 for v in summary["discarded_stale_frames"].values()),
            "p95_recomputes": abs(float(np.percentile(latencies,95)) - summary["loop_ms"]["p95"]) < 1e-6,
            "overruns_recompute": int((latencies > 50).sum()) == summary["cycles_over_50ms"],
            "nonempty_real_sensor_samples": all((v.get("points", 1) > 0 and v.get("std", 1) > 1e-3 and v.get("finite", True)) for v in summary["samples"].values()),
            "car_moved": summary["distance_m"] > 10,
            "rtf_at_least_095": summary["rtf"] >= .95,
            "p95_below_50ms": summary["loop_ms"]["p95"] < 50,
            "control_input_frames_causal": all(int(r["control_input_frame"]) == int(r["frame"])-2
                                                for r in records if r["control_input_frame"]),
        }
        entry = {"checks": checks, "collisions": len(summary["collisions"]),
                 "sim_seconds": summary["sim_seconds"], "wall_seconds": summary["wall_seconds"],
                 "rtf": summary["rtf"], "p95_ms": summary["loop_ms"]["p95"],
                 "p99_ms": summary["loop_ms"]["p99"], "max_ms": summary["loop_ms"]["max"],
                 "overrun_fraction": summary["cycles_over_50ms"] / n,
                 "distance_m": summary["distance_m"], "script_sha256": summary["script_sha256"]}
        if name == "obstacle40":
            before = [r for r in records if float(r["sim_seconds"]) < 20]
            near_stop = [r for r in before if float(r["sim_seconds"]) > 15]
            after = [r for r in records if float(r["sim_seconds"]) > 25]
            checks.update({
                "lidar_hazard_triggered": any(int(r["hazard"]) for r in before),
                "full_braking_command": any(float(r["brake"]) > .99 for r in before),
                "stopped_before_obstacle_removed": min(float(r["speed_mps"]) for r in near_stop) < .2,
                "resumed_after_obstacle_removed": max(float(r["speed_mps"]) for r in after) > 2,
                "no_collision_in_obstacle_smoke": len(summary["collisions"]) == 0,
            })
            entry["min_speed_before_clear_mps"] = min(float(r["speed_mps"]) for r in near_stop)
            entry["max_speed_after_clear_mps"] = max(float(r["speed_mps"]) for r in after)
        entry["passed"] = all(checks.values())
        report[name] = entry
    report["all_passed"] = all(v["passed"] for v in report.values())
    (args.root / "validation.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    if not report["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
