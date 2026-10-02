# 原始论文核查与本轮定位

2026-10-02 搜索作者托管/arXiv 原文，阅读下面列出的段落；未声称逐页精读或数值复现。搜索返回的聚合站、未核实的新综述和无关结果未用于技术结论。

| 论文与实际阅读范围 | 对本次候选的约束 |
|---|---|
| [Orzechowski et al., Tackling Occlusions & Limited Sensor Range with Set-based Safety Verification (2018)](https://arxiv.org/pdf/1807.01262)，§III 观测边界、§V 初始安全/归纳式备份 | 未观测障碍状态区间、边界可达集、以已验证初始状态作归纳起点均已有先例；不能把“使用历史与边界”本身当作新方法。文中传感器/地图可靠性是前提，停止是否安全也依赖场景。 |
| [Zhang & Fisac, Safe Occlusion-aware Autonomous Driving via Game-Theoretic Active Perception (2021)](https://arxiv.org/pdf/2105.08169)，§III 观测与 reach-avoid 定义、§IV 信息结构及后续观测 | 约束可达集保持全部时间段的排除信息，而非只看新鲜度。我们的固定中心排除不变量属于该类集合推理的充分条件，不能声称发现了历史约束可达性。本轮差异仅是可传输、可逐原始射线复核的断链补证接口及其成本，是否有贡献还需强基线实测。 |
| [Zheng et al., Occlusion-Aware Contingency Safety-Critical Planning for Autonomous Vehicles (2025)](https://arxiv.org/html/2502.06359v1)，§II-A 两项假设、§III-A SRQ 与结论局限 | 原文假设可准确识别视场内自由空间，遮挡车辆速度恒定且服从均匀分布，并沿车道运动；同时规划探索/备份轨迹。我们不会把其风险指标直接当成全未知区域的确定性证明，也不会声称新备份控制或优于其实际运动实验。 |

当前问题改为：授权过期后，能否利用已经验证的历史事实与断链期间真正保存的原始观测，重新证明被遮挡区域的条件有效期？到达前仍不能执行过期授权。源观测真实性、尺寸/误差/运动界及对象连续性仍是条件；新接口不能消除这些物理前提。全文最接近历史可达集的强比较应保留，不能只用丢弃历史的冷启动失败来声称原创性。
