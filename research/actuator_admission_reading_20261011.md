# 源证据与实际执行间隔：本轮近邻阅读

[Integrated Real-Time Control and Scheduling for Safety Critical Cyber-Physical Systems，RTAS2025作者全文](https://www.sudvarg.com/publications/RTAS2025_Integrated_Control_and_Scheduling.pdf)。核对§II任务/WCET前提、§III Definition4的采样到下一控制生效间隔及Proposition1、§IV切换约束、§V飞行器案例；没有复算所有SOS问题或复现源码。其安全条件覆盖计算期间保留的旧输入和后续控制生效，调度开销也必须计入；不能仅把本次query算完称为及时。本项目推断：可用证据需要在执行边界消费，原预算超支后的永久停车与真实截止失效应分开。但本批原子虚拟执行器不能替代该论文的真实任务/WCET条件。

[Risk Aware Safe Control with Cooperative Sensing for Dynamic Obstacle Avoidance，2511.01403v1作者全文](https://arxiv.org/html/2511.01403v1)。阅读§2安全条件、§3合作感知的Gaussian/Wasserstein建模、§5的实车与100次/情形MC及比较指标；未复现ROS2/IPOPT代码或全部证明。作者比较同MPC下的不同安全过滤器，针对GPS/V2X噪声、控制扰动，报告实车横穿VRU。其间距与时间统计主要在成功运行中计算，成功率定义为满足最小间距，不等于路线完成。本项目推断：保持同场景/同信息强基线，失败也进入全回合统计，同时分别报告“保持分离”和“真正通过路线”。不能把其分布模型或实车证据移植给我们的部分XYZ及虚拟无线。

新的[冻结协议](../experiments/actuator_admission_20261011/PROTOCOL.md)只检验执行时刻准入是否让历史信息的较长前缀成为任务收益，明确源/接收/控制/执行解码CPU与两条无线FIFO。其sensor延迟是定义的50ms模型，不能声称新旧批次的单变量因果差异；旧闭环零完成、旧独立制动分布限制继续保留。整体期刊项目仍需新的独立风险认证、未知场景与硬件执行保障。
