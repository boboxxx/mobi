# 文献增量核查：2026-10-01

本文补充 [9 月阅读记录](literature_reading_log.md)，服务于[更新后的研究判断](update_20261001.md)。检索覆盖协作感知调度、证据有效性、相关信息年龄、闭环驾驶和组合流调度。下面明确区分全文方法核查、摘要阅读和书目线索；没有独立复现这些论文的数值。2026 年预印本不等于已被顶会接收。

| 文献与主来源 | 实际阅读范围 | 对本项目的约束 |
|---|---|---|
| [C-MASS: Combinatorial Mobility-Aware Sensor Scheduling for Collaborative Perception with Second-Order Topology Approximation](https://arxiv.org/abs/2407.00412)，2024 v1 | HTML §§II–V；单体/二体收益回放、二阶拓扑、混合贪心、探索利用及通信资源模型 | 已建模协作互补性，并用信道估计和速率约束分配带宽。不能称其为“信道盲”或声称首次考虑集合收益。需要比较二阶收益调度。 |
| [Share the Unseen: Sequential Reasoning About Occlusions Using Vehicle-to-Everything Technology](https://people.kth.se/~kallej/papers/Share_the_Unseen_ICST2024_Nyberg.pdf)，TCST 33(4), 2025 | 作者 PDF §§III–IV、算法 1–2、实验设定 | 已用带时间戳的空闲区域和可达集处理延迟、乱序观测。保证依赖运动界限和可信空闲观测；未解决不一致、带误差的感知。仅做“旧证据物理失效”不够新。 |
| [JigsawComm: Joint Semantic Feature Encoding and Transmission for Communication-Efficient Cooperative Perception](https://arxiv.org/abs/2511.17843)，2026-03-13 v2 预印本 | HTML §§3.3–3.6、§4、附录 D/E | 学习效用元信息，按网格消除冗余，再按效用/字节选择；包含丢包下的本车特征回退。证明有代理目标和成本假设，不能泛化为驾驶安全保证，也不能将其描述为朴素独立 Top-k。 |
| [TAMP: Timeliness-Oriented Scheduling and Resource Allocation in Multi-Region Collaborative Perception](https://arxiv.org/abs/2601.04542)，2026 预印本 | HTML 系统、方法、评估设定 | 已把 AoI、数据量、感知精度和多区域资源竞争联系起来，使用 Lyapunov 决策。控制信令时延假设可忽略。单纯加入“年龄加权”不是缺口。 |
| [Goal-Oriented Logic-based Semantic Communication for Neuro-Symbolic Reasoning with Applications onto Autonomous Driving](https://arxiv.org/abs/2608.00878)，2026-08 预印本 | HTML 逻辑信息模型、§VIII 驾驶实验 | 已做逻辑证据选择、RSU 推理和 CARLA/LLM 驾驶。小规模实验及均匀证据基线不能替代强调度对照；“逻辑语义 + CARLA”本身不能成为我们的贡献。 |
| [MASS: Mobility-Aware Sensor Scheduling for Collaborative Perception in Autonomous Driving](https://arxiv.org/abs/2302.13029)，公开稿 | HTML 引言、模型和 bandit 方法描述 | 移动视角、时变收益、探索利用已有基础，学习模块须处理真正的未知量，而非重命名普通调度。 |
| [Grouping-Based Cyclic Scheduling Under Age of Correlated Information Constraints](https://ieeexplore.ieee.org/document/10841476/)，TIT 71(3), 2025 | **仅摘要**；DOI 10.1109/TIT.2025.3529497 | 多视角相关信息年龄约束、分组和循环调度已有先例。未读全文，不能断言它缺少某种约束。 |
| [Minimizing Age of Usage Information for Capturing Freshness and Usability of Correlated Data in Edge Computing Enabled IoT Systems](https://doi.org/10.1109/TMC.2023.3312130)，TMC 23(5), 2024 | **仅书目核查**，全文未取得；由 TAMP 参考文献追踪 | “多份证据同时可用”与 AoUI 很接近。补齐全文是独占性创新主张的前置条件，目前不排除已有覆盖。 |
| [Efficient Coflow Scheduling with Varys](https://people.csail.mit.edu/alizadeh/courses/6.888/papers/varys.pdf)，SIGCOMM 2014 | PDF §§2.1–3；coflow 完成与截止时间准入；[官方代码说明](https://github.com/coflow/coflowsim) | 一组数据全部完成才产生收益、共同截止时间、瓶颈优先并非新思想。必须与组合流调度及短视/多步规划比较。 |
| [MDrive: Benchmarking Closed-Loop Cooperative Driving for End-to-End Multi-agent Systems](https://arxiv.org/abs/2605.10904)，2026 预印本 | 摘要及[官方仓库 README/安装说明](https://github.com/ucla-mobility/MDrive)；**未逐节读全文** | 可用作更自然的闭环评估入口。官方套件含 225 个场景；安装说明基于 CARLA 0.9.12，与当前 0.9.15 不可直接假定兼容。 |
| [Plan2comm](https://doi.org/10.1109/TMC.2024.3496856)，TMC 2025 | 本轮再次尝试，**仍未取得全文** | 直接近邻仍未排除。不得写“首次规划驱动语义调度”。 |

## 综合判断（本项目的推断）

现有工作已经分别覆盖“挑哪些伙伴”“挑哪些区域”“信息有多新”“旧空闲观测如何传播”“一组消息何时完成”和“逻辑证据如何影响驾驶”。把这些模块连起来，不自动产生研究创新。

剩余值得有限验证的交叉问题是：**由运动、观测覆盖和候选动作决定的证据有效区间，如何反过来决定采样、传输、刷新和动作提交的顺序？** 必须证明收益无法被使用相同物理有效期的简单 EDF、AoUI、coflow 或有限步信息价值调度解释。我们当前只实现了一个已知 TTL 的小规模动态规划诊断器，没有完成这一证明。

## 可追溯性与阅读限制

全文下载只存于忽略的 `research/papers/update_20261001/`，不上传论文原文。已缓存版本的 URL 与 SHA-256 见 [source_manifest_20261001.json](source_manifest_20261001.json)；未缓存的网页以上述链接及阅读范围为准。未取得全文的条目保留为明确缺口，不用二手摘要补写算法细节。检索不是系统综述，也不能证明不存在更早同类工作。
