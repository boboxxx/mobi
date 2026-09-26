**语义通信 × 车联网：文献核查记录**

日期：2026-09-26。对应研究设计：mobicom2027_semantic_v2x_proposal.md。

本轮取得 15 份可解析 PDF，并保存提取文本。取得全文不等于逐页复核所有证明和数值：下面按实际阅读范围标记。论文的方法陈述也不代表已独立复现其结果。页面编号指本地 PDF 页码。

**已取得全文，核查核心方法或研究假设**

| 文献与来源 | 本地文件 | 核查范围及选题影响 |
|---|---|---|
| [AutoCast，MobiSys 2022](https://arxiv.org/abs/2112.14947) | papers/autocast-mobisys2022.pdf，16 页 | §3，PDF p3–6：元数据、对象价值、接收状态、MDP 和大小归一化调度；实验部分定位核查。对象—接收者收益累加，不能概括为不考虑链路/决策周期 |
| [RAO，MobiCom 2023](https://ry4nzhu.github.io/publication/robust_real_time/robust_real_time.pdf) | papers/rao-mobicom2023.pdf，15 页 | §4，尤其 PDF p5–6：接收端请求、占用图、运动同步、生产者分配；读取评估设定。按需盲区通信已有完整系统先例 |
| [Where2comm，NeurIPS 2022](https://arxiv.org/abs/2209.12836) | papers/where2comm-neurips2022.pdf，13 页 | 方法中的空间置信图、请求与多轮通信；评估任务。不得将区域选择本身列为新贡献 |
| [How2comm，NeurIPS 2023](https://proceedings.neurips.cc/paper_files/paper/2023/hash/4f31327e046913c7238d5b671f5d820e-Abstract.html) | papers/how2comm-neurips2023.pdf，14 页 | 核查互信息筛选、时空融合和延迟补偿设计；未复算全部表格 |
| [CodeFilling，CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/html/Hu_Communication-Efficient_Collaborative_Perception_via_Information_Filling_with_Codebook_CVPR_2024_paper.html) | papers/codefilling-cvpr2024.pdf，10 页 | §4.2 的信息填充：置信度累积及饱和目标；码本通信；延迟/定位相关评估。不把它误写成纯独立 Top-k |
| [UniV2X，2024](https://arxiv.org/abs/2404.00717) | papers/univ2x.pdf，15 页 | 系统路径：稀疏查询、占用表示、延迟处理和规划评估；注意开环规划指标与真正闭环的区别 |
| [Select2Drive，T-ITS 2025 最终版](https://doi.org/10.1109/TITS.2025.3611377) | papers/select2drive-author-version.pdf，15 页 | §III–IV、Eq22–23：航点请求图、置信/变化掩码、延迟预测；核查闭环和控制开销假设。早期 arXiv 与最终版结果不同，不混用 |
| [CooperTrim，ICLR 2026](https://arxiv.org/abs/2602.13287) | papers/coopertrim.pdf，21 页 | 时间变化度量、分位数与分享量机制、方法中对 conformal 的限定、评估任务。不能宣称它具有常规分布无关 coverage 保证 |
| [Semantic and Task-Oriented V2X Communications: Pushing the Limits of V2X Networks Scalability，2026 预印本](https://arxiv.org/abs/2606.09126) | papers/v2x-scalability2026.pdf，15 页 | §3：理想相关性估计、冗余推断与内容选择；通信模型及相关信息接收指标。相关性如何从真实感知计算并非其已解决问题 |
| [Resilience of Task-Oriented V2X Networks to Incomplete Information Sharing，2026 预印本](https://arxiv.org/abs/2602.18620) | papers/v2x-resilience2026.pdf，10 页 | 错误分类、hard/soft 冗余推断、β 相关性误差模型与仿真结论。没有据此断言作者忽略所有错误相关性 |
| [Goal-Oriented Semantic Communication for Logical Decision Making，2026 预印本](https://arxiv.org/abs/2604.19614) | papers/goal-oriented-logic2026.pdf，15 页 | v2，2026-08-25；§IV–VI、附录 Algorithm1：任务等价状态、证据子集、LogiCity 决策一致率。注意正文复杂度表述与附录枚举子集实现需进一步核对，不据此评价完整理论正确性 |
| [Near-Optimal Bayesian Active Learning with Noisy Observations / EC²，NeurIPS 2010](https://www.cs.cmu.edu/~dgolovin/papers/nips10.pdf) | papers/ec2-neurips2010.pdf，9 页 | PDF p3–6：决策等价类、边切断代理目标、适应次模性条件、短视 VoI 局限。其理论不能直接移植成新网络算法的保证 |

**全文已取得，本轮较浅阅读**

| 文献 | 本地文件 | 实际状态 |
|---|---|---|
| [CoDS: Collaborative Perception via Digital Semantic Communication](https://arxiv.org/abs/2512.22513) | papers/cods-digital.pdf，13 页 | 阅读摘要、引言及方法概览，核查数字语义编码与可靠性筛选；本报告采用公开稿身份，不以未核实期刊信息背书 |
| [CooperDrive: Enhancing Driving Decisions Through Cooperative Perception](https://arxiv.org/abs/2604.14454) | papers/cooperdrive2026.pdf，8 页 | 阅读摘要、架构与实验概况；对象级及实车闭环是关键启发。作者项目页列 ICRA 2026，本文主要引用公开稿，不宣称独立复现实车结果 |
| [The Search for Relevance: A Context-Aware Paradigm Shift in Semantic and Task-Oriented V2X Communications](https://arxiv.org/abs/2508.07394) | papers/v2x-relevance2025.pdf，14 页 | 背景筛读；用于追踪 relevance 思想发展，不承担具体新颖性排除的主要证据 |

Select2Drive 最终版公开作者 PDF：[作者站点](https://rongpeng.info/images/pdfs/papers/2025_Huang_Select2Drive%20Pragmatic%20communications%20for%20real-time%20collaborative%20autonomous%20dr.pdf)。正式卷期：IEEE Transactions on Intelligent Transportation Systems，26(12)，21939–21953，2025。

**未取得全文或未完成全文阅读的相关项**

| 工作 | 已核实部分 | 留下的问题 |
|---|---|---|
| [Plan2comm / Towards Communication-Efficient Cooperative Perception via Planning-Oriented Feature Sharing](https://doi.org/10.1109/TMC.2024.3496856) | Crossref 与 DOI：TMC，24(4)，2551–2563，2025；IEEE 文档 10752404；全文抓取未成功 | 最高优先级。二级索引摘要只用于发现线索；不能凭它排除 redundancy/complementarity 模块与主方案重叠 |
| [UniSense: Spatial-Uncertainty-Aware Collaborative Sensing for Autonomous Driving](https://doi.org/10.1145/3711875.3729130) | MobiSys 2025 [官方录用列表](https://www.sigmobile.org/mobisys/2025/accepted_papers/) | 全文未取得；[作者仓库](https://github.com/LetStarFly/UniSense) 本轮所见仅 README/许可等，不能承诺完整可运行复现 |
| TACToC: Enabling Task-Adaptive Communication System with a Task-Describable Encoder | [MobiCom 2026 官方录用列表](https://www.sigmobile.org/mobicom/2026/accepted.html)、[作者实验室发表页](https://nxc.snu.ac.kr/publications) | 只核实题目/录用；未取得方法全文，不能给出细节对比 |
| [Spontaneous Risk-Aware Selective Cooperative Perception](https://arxiv.org/abs/2511.17461) | 阅读 arXiv HTML 的风险触发、请求和选择设计；预印本 | 本地 PDF 下载未完成；未逐表核验，不引用其提升百分比 |
| [Reason-to-Transmit: Deliberative Adaptive Communication for Cooperative Perception](https://arxiv.org/abs/2603.20308) | 摘要/概要：预算、邻居状态与区域通信选择；预印本 | 未精读；不把所有 context-aware 通信划为新空白 |
| [Value of Information in Feedback Control: Quantification](https://arxiv.org/abs/1812.07534) | 摘要与[作者发表记录](https://johnbaras.com/publication-conferen/value-of-information-in-feedback-control-quantification/)，IEEE TAC 2022 | 理论先例已足以排除“第一次按控制价值通信”；具体定理使用前应重新阅读全文 |

**资源核查与投稿时间**

- [V2Xverse](https://github.com/CollaborativePerception/V2Xverse)：官方 README 支持 CARLA 闭环、检测与航点预测；仅核查文档，没有安装执行。
- [SEE-V2X](https://cisl.ucr.edu/SEE-V2X/)：真实 C-V2X 直接通信数据资源；用于校准/验证无线条件，不能直接证明新负载策略的闭环网络效果。
- [V2V4Real](https://openaccess.thecvf.com/content/CVPR2023/html/Xu_V2V4Real_A_Real-World_Large-Scale_Dataset_for_Vehicle-to-Vehicle_Cooperative_Perception_CVPR_2023_paper.html)：真实 V2V 感知数据；本轮核查论文页面/数据用途，未下载数据。
- [MobiCom 2027 CFP](https://www.sigmobile.org/mobicom/2027/cfp.html)：夏季全文 2026-09-02，冬季日期 TBD；理论、算法和系统均属认可贡献形式。

**核查纪律**

本记录没有断言检索穷尽所有文献；预印本和正式录用论文分开标注；没有将论文自报结果当成本项目结果。特别是 Plan2comm 的未完成核查意味着，主方案的新颖性目前只能是有文献依据的候选判断。正式立项前，应补齐这些直接近邻并把方法目标、可访问输入、消息表示、网络假设和评估任务逐项对齐。
