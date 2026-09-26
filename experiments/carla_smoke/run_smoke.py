#!/usr/bin/env python3
"""Infrastructure smoke test, not a semantic-communication method evaluation.

Only this process ticks the world. Ego steering uses public map + ego pose;
emergency braking uses the received ego LiDAR, never obstacle actor state.
Other actors are used only for scenario setup and independent event evaluation.
"""
import argparse
import csv
import hashlib
import json
import math
import queue
import time
from pathlib import Path

import carla
import numpy as np


def percentile(values):
    a = np.asarray(values, dtype=float)
    return {"mean": float(a.mean()), "p50": float(np.percentile(a, 50)),
            "p95": float(np.percentile(a, 95)), "p99": float(np.percentile(a, 99)),
            "max": float(a.max())}


def get_frame(q, frame, timeout=10):
    deadline = time.perf_counter() + timeout
    stale = 0
    while True:
        item = q.get(timeout=max(.001, deadline - time.perf_counter()))
        if item.frame == frame:
            return item, stale
        if item.frame > frame:
            raise RuntimeError("Sensor frame %d is ahead of requested frame %d" % (item.frame, frame))
        stale += 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="100.109.48.32")
    p.add_argument("--port", type=int, default=2000)
    p.add_argument("--map", default="Town10HD_Opt")
    p.add_argument("--sensor-lag", type=int, default=1)
    p.add_argument("--pace-hz", type=float, default=20,
                   help="Wall-clock tick pacing; 0 requests unrestricted throughput")
    p.add_argument("--seconds", type=float, default=60)
    p.add_argument("--views", type=int, choices=[1, 3], default=1)
    p.add_argument("--obstacle", action="store_true")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    client = carla.Client(args.host, args.port); client.set_timeout(30)
    if client.get_client_version() != client.get_server_version():
        raise RuntimeError("CARLA client/server version mismatch")
    world = client.get_world()
    if len(world.get_actors().filter("vehicle.*")):
        raise RuntimeError("Refusing to reset a world containing existing vehicles")
    if world.get_map().name.split("/")[-1] != args.map:
        world = client.load_world(args.map)
    original = world.get_settings()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = .05
    settings.no_rendering_mode = False
    settings.substepping = True
    settings.max_substep_delta_time = .01
    settings.max_substeps = 10
    world.apply_settings(settings)
    actors, sensors, streams, rows, collisions = [], [], {}, [], []
    obstacle = None
    started = time.time()
    try:
        bp = world.get_blueprint_library()
        vehicle_bp = bp.find("vehicle.tesla.model3")
        vehicle_bp.set_attribute("role_name", "mobi_smoke_ego")
        road_map = world.get_map()
        # Select a long straight, non-junction segment using map geometry only.
        spawn = None
        for candidate in road_map.get_spawn_points():
            wp = road_map.get_waypoint(candidate.location)
            ahead = wp.next(25)
            if not wp.is_junction and ahead and not ahead[0].is_junction:
                dyaw = (ahead[0].transform.rotation.yaw - wp.transform.rotation.yaw + 180) % 360 - 180
                if abs(dyaw) < 3:
                    spawn = candidate; break
        if spawn is None:
            raise RuntimeError("No suitable straight spawn")
        ego = world.spawn_actor(vehicle_bp, spawn); actors.append(ego)
        collision_bp = bp.find("sensor.other.collision")
        collision = world.spawn_actor(collision_bp, carla.Transform(), attach_to=ego)
        sensors.append(collision)
        collision.listen(lambda e: collisions.append({"frame": e.frame, "other": e.other_actor.type_id}))
        view_origins = []
        for view in range(args.views):
            if view == 0:
                parent = ego
                cam_pose = carla.Transform(carla.Location(x=1.2, z=2.2))
                lidar_pose = carla.Transform(carla.Location(z=2.2))
            else:
                # Two fixed roadside viewpoints; not extra controlled vehicles.
                parent = None
                rot = carla.Rotation(yaw=spawn.rotation.yaw + (90 if view == 1 else -90), pitch=-10)
                loc = spawn.location + carla.Location(x=15 * view, y=(-12 if view == 1 else 12), z=5)
                cam_pose = carla.Transform(loc, rot)
                lidar_pose = carla.Transform(loc, carla.Rotation())
            view_origins.append({"view": view, "attached_to_ego": view == 0})
            for kind, pose in [("camera", cam_pose), ("lidar", lidar_pose)]:
                name = "%s_%d" % (kind, view)
                if kind == "camera":
                    b = bp.find("sensor.camera.rgb")
                    for key, value in {"image_size_x":"640", "image_size_y":"360", "fov":"90", "sensor_tick":"0.0"}.items():
                        b.set_attribute(key, value)
                else:
                    b = bp.find("sensor.lidar.ray_cast")
                    for key, value in {"channels":"32", "range":"50", "points_per_second":"100000", "rotation_frequency":"20", "sensor_tick":"0.0", "dropoff_general_rate":"0"}.items():
                        b.set_attribute(key, value)
                sensor = world.spawn_actor(b, pose, attach_to=parent) if parent else world.spawn_actor(b, pose)
                sensors.append(sensor); q = queue.Queue(); sensor.listen(q.put); streams[name] = q
        if args.obstacle:
            lead_wp = road_map.get_waypoint(spawn.location).next(25)[0]
            tr = lead_wp.transform; tr.location.z += .5
            lead_bp = bp.find("vehicle.audi.a2"); lead_bp.set_attribute("role_name", "mobi_smoke_obstacle")
            obstacle = world.spawn_actor(lead_bp, tr); actors.append(obstacle)
            obstacle.set_simulate_physics(False)
        # Zero sensor_tick requests every world frame (20 Hz with dt=.05).
        # Allow asynchronous streaming subscriptions to register before ticking.
        time.sleep(.5)
        warmup = 20
        last_lidar = None
        last_lidar_frame = None
        previous_world_frame = None
        prev_location = None
        cumulative_distance = 0.0
        samples = {}
        sample_payloads = {}
        first_sim_time = None
        measured_start = None
        missed_frames = {k: 0 for k in streams}
        counts = {k: 0 for k in streams}
        n_steps = int(round(args.seconds / .05))
        previous_loop_start = None
        for step in range(warmup + n_steps):
            if args.pace_hz and previous_loop_start is not None:
                time.sleep(max(0, previous_loop_start + 1 / args.pace_hz - time.perf_counter()))
            begin = time.perf_counter()
            previous_loop_start = begin
            sim_elapsed = max(0, step - warmup) * .05
            if obstacle is not None and sim_elapsed >= args.seconds / 2:
                obstacle.destroy(); actors.remove(obstacle); obstacle = None
            loc = ego.get_location(); transform = ego.get_transform(); vel = ego.get_velocity()
            speed = math.sqrt(vel.x ** 2 + vel.y ** 2 + vel.z ** 2)
            wp = road_map.get_waypoint(loc)
            options = wp.next(max(4.0, speed * 1.1))
            heading = math.radians(transform.rotation.yaw)
            desired = min(options, key=lambda w: abs((w.transform.rotation.yaw-transform.rotation.yaw+180)%360-180)) if options else wp
            dx = desired.transform.location.x - loc.x; dy = desired.transform.location.y - loc.y
            alpha = math.atan2(dy, dx) - heading
            alpha = math.atan2(math.sin(alpha), math.cos(alpha))
            steer = float(np.clip(math.atan2(2 * 2.9 * math.sin(alpha), max(4, math.hypot(dx,dy))) / .65, -1, 1))
            min_range = 50.0
            if last_lidar is not None:
                # Sensor-relative box excludes road surface and points on ego.
                mask = ((last_lidar[:,0] > 2.8) & (np.abs(last_lidar[:,1]) < 1.0)
                        & (last_lidar[:,2] > -1.5) & (last_lidar[:,2] < .5))
                if mask.any(): min_range = float(last_lidar[mask,0].min())
            hazard = min_range < max(6.0, 3.0 + speed * speed / 8.0)
            target_speed = 0.0 if hazard or step < warmup else 4.0
            throttle = float(np.clip(.4 * (target_speed - speed), 0, .65))
            brake = 1.0 if hazard else float(np.clip(.4 * (speed - target_speed), 0, 1))
            ego.apply_control(carla.VehicleControl(throttle=throttle, steer=steer, brake=brake))
            control_done = time.perf_counter()
            frame = world.tick(20)
            tick_done = time.perf_counter()
            if step < warmup:
                # Prime the GPU pipeline before demanding an aligned bundle.
                # These frames are excluded from all reported performance values.
                time.sleep(.02)
                previous_world_frame = frame
                continue
            sensor_frame = frame - args.sensor_lag
            control_input_frame = last_lidar_frame
            control_input_age_ms = ((previous_world_frame - last_lidar_frame) * 50
                                    if last_lidar_frame is not None else None)
            for name, q in streams.items():
                try:
                    data, stale = get_frame(q, sensor_frame)
                except queue.Empty:
                    raise RuntimeError("%s missing frame %d at world frame %d, step %d" % (name,sensor_frame,frame,step))
                except RuntimeError as exc:
                    raise RuntimeError("%s step=%d world=%d previous_world=%s: %s" % (name,step,frame,previous_world_frame,exc))
                if step >= warmup:
                    if step > warmup: missed_frames[name] += stale
                    counts[name] += 1
                if name.startswith("lidar"):
                    points = np.frombuffer(data.raw_data, dtype=np.float32).reshape(-1,4)
                    if name == "lidar_0": last_lidar = points.copy(); last_lidar_frame = data.frame
                    if name not in samples and step == warmup:
                        samples[name] = {"frame":data.frame, "points":int(len(points)), "finite":bool(np.isfinite(points).all())}
                        sample_payloads[name] = points.copy()
                elif name not in samples and step == warmup:
                    rgb = np.frombuffer(data.raw_data, dtype=np.uint8).reshape(data.height,data.width,4)[:,:,:3]
                    samples[name] = {"frame":data.frame, "width":data.width, "height":data.height, "std":float(rgb.std()), "mean":float(rgb.mean())}
                    sample_payloads[name] = data
            end = time.perf_counter()
            previous_world_frame = frame
            if step >= warmup:
                if measured_start is None: measured_start = begin
                if prev_location is not None: cumulative_distance += loc.distance(prev_location)
                prev_location = loc
                rows.append({"step":step-warmup, "frame":frame, "sim_seconds":sim_elapsed,
                             "sensor_frame":sensor_frame, "control_input_frame":control_input_frame,
                             "control_input_age_ms_before_tick":control_input_age_ms,
                             "loop_ms":(end-begin)*1000, "control_ms":(control_done-begin)*1000,
                             "tick_ms":(tick_done-control_done)*1000, "sensor_wait_ms":(end-tick_done)*1000,
                             "speed_mps":speed, "range_m":min_range, "hazard":int(hazard),
                             "throttle":throttle, "brake":brake, "steer":steer,
                             "x":loc.x, "y":loc.y, "distance_m":cumulative_distance,
                             "obstacle_present":int(obstacle is not None)})
                if (step-warmup+1) % 200 == 0:
                    print(json.dumps({"progress_sim_s":round(sim_elapsed+.05,2), "wall_s":round(end-measured_start,2), "speed":round(speed,2), "collisions":len(collisions)}),flush=True)
        # Include the final pacing interval in the measured wall-clock duration.
        if args.pace_hz:
            time.sleep(max(0, previous_loop_start + 1 / args.pace_hz - time.perf_counter()))
        measured_end = time.perf_counter()
        for name, data in sample_payloads.items():
            if name.startswith("camera"):
                data.save_to_disk(str(out / (name + ".png")))
            else:
                np.save(out / (name + ".npy"), data)
        with (out / "frames.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        summary = {"status":"completed", "kind":"infrastructure_and_simple_lidar_feedback_only",
                   "host":args.host, "client_version":client.get_client_version(), "server_version":client.get_server_version(),
                   "map":world.get_map().name, "views":args.views, "view_origins":view_origins,
                   "obstacle_scenario":args.obstacle, "sensor_hz":20, "fixed_delta_seconds":.05,
                   "sensor_lag_frames":args.sensor_lag, "sensor_tick":0,
                   "wall_clock_pace_hz":args.pace_hz,
                   "warmup_frames":warmup, "sim_seconds":n_steps*.05, "wall_seconds":measured_end-measured_start,
                   "rtf":n_steps*.05/(measured_end-measured_start), "frames":n_steps,
                   "loop_ms":percentile([r['loop_ms'] for r in rows]),
                   "control_ms":percentile([r['control_ms'] for r in rows]),
                   "tick_ms":percentile([r['tick_ms'] for r in rows]),
                   "sensor_wait_ms":percentile([r['sensor_wait_ms'] for r in rows]),
                   "cycles_over_50ms":sum(r['loop_ms']>50 for r in rows),
                   "counts":counts, "discarded_stale_frames":missed_frames, "samples":samples,
                   "distance_m":cumulative_distance, "collisions":collisions,
                   "started_unix":started, "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   "limitations":["No learned perception or semantic communication scheduler", "Synchronous simulation waits for sensors and is not deadline-enforcing real-time deployment", "Rendering quality is set by server launch; see environment manifest; no safety benchmark claim", "Sample files are written after timing ends", "Aligned sensor bundle is delayed by sensor_lag_frames; control consumes the previous bundle"]}
        (out / "summary.json").write_text(json.dumps(summary,indent=2))
        print(json.dumps(summary),flush=True)
    except Exception as exc:
        (out / "error.json").write_text(json.dumps({"type":type(exc).__name__,"error":str(exc),"rows_completed":len(rows)},indent=2))
        raise
    finally:
        for sensor in sensors:
            try: sensor.stop()
            except Exception: pass
        for actor in reversed(sensors + actors):
            try:
                if actor.is_alive: actor.destroy()
            except Exception: pass
        world.apply_settings(original)


if __name__ == "__main__":
    main()
