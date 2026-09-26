# CARLA Windows–WSL 闭环验证

> 审计更正：此基础 smoke test 的连接、传感器吞吐、帧连续性和运行时测量有效；`obstacle40` 的障碍归因无效。新障碍车辆在首个同步 tick 前被 `set_simulate_physics(False)` 固定于默认原点，普通 LiDAR 几何规则实际响应了环境点。不要使用该组结果证明障碍检测或安全控制。后续 `carla_v2x_full` 实验使用正常物理 actor、语义实例 ID 和 occupied→free 门槛检查。

本实验验证服务、实际传感器流、反馈控制和性能，不评估语义通信创新，也不使用学习型感知网络。

## 机器与环境

- Windows SSH：`administrator@100.109.48.32`；WSL SSH：`sheng@100.94.183.27`。
- 已有 Windows 集成版：`C:\App\CARLA_0.9.15\WindowsNoEditor`。
- 独立 WSL 客户端：`/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python`，正式版 CARLA 0.9.15。未修改原有 carla 环境。
- 工作目录：`/home/sheng/mobicom2027_carla_smoke_20260926`。
- 数据经 Windows 的 Tailscale 地址传输；本次测试中 WSL 默认网关路径超时，未修改防火墙。

## 启动与复现

当前采用 Windows SSH 前台会话保持服务运行。先核查是否已有实例，避免争用同一端口；不要同时启动两个 tick 客户端。

Windows 命令（在安装目录执行）：

```bat
CarlaUE4\Binaries\Win64\CarlaUE4-Win64-Shipping.exe CarlaUE4 -dx12 -RenderOffScreen -nosound -unattended -carla-rpc-port=2000 -quality-level=Epic -ResX=640 -ResY=360
```

WSL 命令：

```bash
cd /home/sheng/mobicom2027_carla_smoke_20260926
venv/bin/python src/run_smoke.py --seconds 60 --views 1 --out results/new_single60
venv/bin/python src/run_smoke.py --seconds 60 --views 3 --out results/new_three60
venv/bin/python src/run_smoke.py --seconds 40 --views 1 --obstacle --out results/new_obstacle40
venv/bin/python src/run_smoke.py --seconds 600 --views 3 --out results/new_stability600
```

也可用一个顺序入口运行全部测试和审计，输出目录必须是新目录：

```bash
venv/bin/python src/run_suite.py --out results/repeat_suite_01
```

默认地图为 Town10HD_Opt，不需要动态切换地图。每次退出销毁本次 actors 并恢复启动前的世界设置。已有其他车辆时脚本拒绝运行，防止影响已有实验。

## 闭环定义

- 自车用公开道路地图、自车位姿和速度进行简单路径跟踪；LiDAR 前方点云触发制动。没有使用障碍车辆真值作感知输入。
- 相机为 640×360 RGB，LiDAR 为 32 线、50 米范围、每秒 100000 点配置；均按每个世界 tick 采样。
- 三视角指自车及两个固定路侧传感器位置，每个位置一组相机和 LiDAR；不是三辆动态协作车，也没有协作消息选择。
- 同步仿真步长 0.05 秒，墙钟节拍目标 20 Hz。预热 20 帧不计入性能统计。
- 读取 world frame−1 的一致传感器帧；控制使用上一轮已经收到的 LiDAR。CSV 保存世界帧、观测帧和控制输入帧，不能把传感器延迟当成零。
- `loop_ms` 包含控制计算、RPC tick、传感器等待和数据处理，排除有意的节拍等待；RTF 使用包含节拍等待的总墙钟时间计算。图片和点云样例在计时结束后保存。
- 本实现会等待传感器，超时即报错。它不实现严格的 deadline 到期降级，因此接近 1 的 RTF 不能等同于硬实时保证。
- 障碍测试在前方 25 米设置静止车辆，20 秒时移除；检测停止与重新起步是否由观测变化触发。

## 已遇到的问题与记录边界

- Low 画质下从默认地图切换 Town03：DirectX 12 出现 shader compilation fatal，DirectX 11 出现访问异常。错误记录保留；不能据此声称所有地图均可用。
- DirectX 11、Epic 下的短时挂载传感器诊断出现 RPC 失去响应，未产生新崩溃记录，已停止该实验实例。
- 相机是 GPU 流水线，不能假定 world.tick 后必定立即返回同帧图像。无限速推进的初次脚本出现帧遗漏/等待错误；正式实验采用墙钟节拍和显式帧号对齐，遇到缺帧仍失败，不静默补帧。
- `pilot10_paced` 是首个通过的十秒测试，其中样例文件保存仍在计时范围；正式四组实验已将该项移出计时。不能直接混合不同脚本版本的尾延迟。

## 审计

各组 `summary.json` 保存版本、计数、指标、传感器样例统计和脚本 SHA-256；`frames.csv` 可重算延迟与控制响应。验证命令：

```bash
venv/bin/python src/validate_results.py /home/sheng/mobicom2027_carla_smoke_20260926/results
```

正式结果需要同时检查 `validation.json`、`suite_status.json` 和实际图像。基础设施通过不能证明新的语义通信算法有收益。
