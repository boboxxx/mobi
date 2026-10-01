# 感知误差与时间对齐的增量核查

本轮阅读服务于逐射线误差传播实现，不代表完成系统综述或排除了所有近邻。查询时间：2026-10-01。

| 主来源 | 实际阅读范围 | 对当前项目的约束 |
|---|---|---|
| [CARLA 0.9.15 传感器文档](https://carla.readthedocs.io/en/0.9.15/ref_sensors/#semantic-lidar-sensor) | LiDAR / semantic LiDAR 的采样与输出说明 | 同一 measurement 内物理状态不更新。完整帧不能被直接当作真实滚动传感器运动实验；本轮方位角生成的逐射线时间必须标为假设时间模型。 |
| [PwC: Statistical Safety Assurances for Navigation with Learning-Based Perception，arXiv 2403.08185v3](https://arxiv.org/html/2403.08185v3) | 摘要、§III–V 与 §VI 开头，尤其环境级校准、有限离散状态集、视场内限制及集合滤波 | 已有通过共形校准降低感知漏检并支持安全规划的研究。保证依赖代表性独立同分布环境和指定状态覆盖；主要针对静态环境。不能用本项目的少数重复帧宣称同等级的泛化保证，也不能声称首次处理感知不确定性。 |
| [An Efficient Reachability-Based Framework for Provably Safe Autonomous Navigation in Unknown Environments，2019](https://arxiv.org/abs/1905.00532) | 搜索返回的作者摘要；全文 HTML 获取失败，未作全文核查 | 未知环境在线安全与计算效率已有 Hamilton–Jacobi 可达性路线。不能把“未知空间 + 高效安全计算”作为独占性新概念。 |

当前实现的确定性输入盒约束与统计校准保证不同。前者在盒约束成立时传播误差；后者需要适当的数据与抽样条件才能给出概率保证。当前输入坐标误差是明示参数，既没有用真实传感器标定得到，也没有由本轮蒙特卡洛测试推导覆盖概率。后续若使用学习感知，必须另行构建环境级校准/测试划分，不能把本轮静态帧拆成训练与测试来制造泛化证据。

本轮算法上的可核查增量是：同一几何与运动契约下，把每条射线不同的坐标误差和年龄传给中心排除条件，并与最佳统一误差阈值作同条件比较；计算加速通过与全网格参考逐项相等来验证。这仍不是新颖性已成立的结论。
