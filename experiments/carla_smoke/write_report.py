#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(); p.add_argument("root",type=Path); p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    v=json.loads((a.root/'validation.json').read_text())
    labels={'single60':'单视角','three60':'三个视角','obstacle40':'障碍物反馈控制','stability600':'三个视角长测'}
    table=[]
    for name,label in labels.items():
        r=v[name]
        table.append('| %s | %.0f s | %.3f s | %.4f | %.2f ms | %.2f ms | %.3f%% |' % (label,r['sim_seconds'],r['wall_seconds'],r['rtf'],r['p95_ms'],r['p99_ms'],100*r['overrun_fraction']))
    gpu=[]
    if (a.root/'gpu_monitor.csv').exists():
        with (a.root/'gpu_monitor.csv').open() as f:
            for row in csv.DictReader(f):
                try:gpu.append(float(row[' memory_used_MiB']))
                except (KeyError,ValueError):pass
    gpu_text=('监测窗口内整卡显存峰值约 %.2f GiB（包括桌面及其他进程，不是 CARLA 独占值）。' % (max(gpu)/1024)) if gpu else 'GPU 监测数据不可用。'
    obstacle=v['obstacle40']
    root=a.root.resolve()
    text='''# sheng CARLA 实时闭环基础验证

日期：2026-09-26。已复用 Windows 上现有 CARLA 0.9.15，并在 WSL 建立独立、匹配版本的客户端。**已完成实际传感器到控制的基础闭环和长时间运行验证。尚未接入学习型感知或被研究的语义通信算法，因此这不是算法创新收益证明。**

## 实测结果

| 测试 | 仿真时长 | 墙钟时长 | 实时因子 | 循环 P95 | 循环 P99 | 超过 50 ms 的周期 |
|---|---:|---:|---:|---:|---:|---:|
TABLE

循环耗时包括控制、RPC 推进、传感器等待及处理，排除有意的节拍等待；墙钟总时长包含节拍等待。RTF 为仿真时长除以墙钟时长。目标节拍为 20 Hz。循环计算耗时不是完整感知到执行延迟。

审计总状态：**VALIDATION**。四组正式实验使用同一个脚本版本，逐帧计数、世界帧连续性、传感器对齐、统计重算和运动反馈检查见验证文件。长测每路传感器对应 12000 个测量帧；三视角是三组 RGB + LiDAR，其中两个为固定路侧位置，不是三辆动态协作车。

GPU_TEXT

测试结束后已确认本次车辆和传感器均已销毁，并停止本次启动的 CARLA 服务以释放 GPU；安装与代码保留。清理状态见 `cleanup.json`，使用复现说明中的命令即可重新启动。

## 确实发生了反馈控制

在自车前方约 25 米放置静止车辆，控制器只读取 LiDAR 点云判断前方障碍，并在场景时间 20 秒移除障碍。自车在移除前最低速度 STOP_SPEED m/s，移除后最高速度 RESUME_SPEED m/s；该次运行记录 COLLISIONS 次碰撞事件。该试验验证刹停与恢复功能，不构成统计安全性结论。

相机与 LiDAR 用 frame ID 对齐到当前世界帧的前一帧，控制使用上一轮收到的点云。正式 CSV 中控制调用前的观测年龄为 50 ms（首个未有输入的测量帧除外），随后控制在下一仿真步产生作用。不能将约几毫秒的循环处理时间解释为同等大小的感知到执行延迟。

## 可复用配置与限制

- Windows：`administrator@100.109.48.32`；WSL：`sheng@100.94.183.27`。
- CARLA：已有 `C:\\App\\CARLA_0.9.15\\WindowsNoEditor`，正式 0.9.15 客户端位于 `/home/sheng/mobicom2027_carla_smoke_20260926/venv`，原环境未改动。
- 通过的配置：DirectX 12、Epic、RenderOffScreen、Town10HD_Opt；RGB 640×360，32 线 LiDAR。渲染使用 RTX 4090。
- 初次 Low 配置下切换 Town03 曾出现着色器编译崩溃或访问异常；DirectX 11 的一次短测也曾失去 RPC 响应。失败日志保留，不能声称所有地图/配置均已稳定。
- 早期无限速推进和直接等待同帧相机的脚本失败。正式版本使用明确的 20 Hz 墙钟节拍、预热和帧延迟处理，缺帧会报错，未静默复制图像。
- 这是等待传感器的同步闭环，尚未实现硬截止时间到期时的丢弃/降级。小样本无超时不等于硬实时保证。
- 同机渲染和算法共享 GPU；本轮没有推理深度网络、没有动态 V2X 丢包/带宽调度，不能推断完整算法上线后的吞吐。

## 文件

- [逐项审计](ROOT/validation.json)
- [性能图](ROOT/performance.png)
- [刹停与恢复曲线](ROOT/obstacle_response.png)
- [三视角自车相机样例](ROOT/three60/camera_0.png)
- [实际进程与配置](ROOT/environment_final.json)
- [复现说明](/Users/chen/Documents/ChatGPT/mobi/experiments/carla_smoke/README.md)

后续算法验证应固定感知与规划，对照无通信、广播、强单步 VoI 与组合选择，并显式加入观测空闲/未知区域以及消息到达时间。此前 OPV2V 开环未观察到组合选择优势，这一结论没有因基础平台跑通而改变。
'''
    text=text.replace('TABLE','\n'.join(table)).replace('VALIDATION','全部通过' if v['all_passed'] else '存在未通过项，见 validation.json')
    text=text.replace('GPU_TEXT',gpu_text).replace('STOP_SPEED','%.4f'%obstacle['min_speed_before_clear_mps']).replace('RESUME_SPEED','%.2f'%obstacle['max_speed_after_clear_mps']).replace('COLLISIONS',str(obstacle['collisions'])).replace('ROOT',str(root))
    a.out.write_text(text)


if __name__ == '__main__':main()
