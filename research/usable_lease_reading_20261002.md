# 可用有效期与既有语义价值方法：本轮正文核查

本轮取得以下三篇作者/机构托管 PDF，阅读了列出的相关正文段落；没有声称逐页精读全文或复现其学习模型。两轮算法实验只与项目内匹配的完整证明方法比较，不是对下列系统的性能复现。

| 文献及实际阅读位置 | 与当前问题最接近的内容 | 对选题的约束 |
|---|---|---|
| [Where2comm，NeurIPS 2022，正文 §4.2–4.3、§5 与附录局限讨论](https://arxiv.org/pdf/2209.12836) | 用检测置信度、请求图和稀疏特征决定传输位置；低置信度也可能来自遮挡，其他节点的请求用于补充信息。评价关注检测 AP 与字节量。 | “只发送关键空间位置”和“缺信息时请求补充”已有明确工作。我们须检验的是原始观测能支持多长的条件证明及到达后的可用时间，不能把检测置信度直接当作未知区域为空的证明。 |
| [Goal-oriented Semantic Communications for Robotic Waypoint Transmission: The Value and Age of Information Approach，arXiv:2312.13182，正文 §V-B 与 §VI](https://arxiv.org/pdf/2312.13182) | AoI 计时并结合与预测目标位置的距离来排序指令，搭配发送端强化学习和重复传输；以 UAV 路径误差评价。 | 任务价值随时间/状态变化、到达顺序未必是最佳执行顺序，都已有研究。本项目的剩余有效期须来自可重算的条件几何，不能只重新命名 VoI。该版本的实验也不能直接证明我们的车身占据和制动合同。 |
| [A Spatial Model for Using the Age of Information in Cooperative Driving Applications，MSWiM 2022，正文 §3–§4](https://www.tkn.tu-berlin.de/bib/heinovski2022spatial/heinovski2022spatial.pdf) | 用相对方位与距离加权 PAoI 和目标 AoI，在 Veins/IEEE 802.11p 中分析相关链路的新鲜度及信标资源。 | 空间相关性与时效联合考虑并不新颖。本研究需保留所有与观测相容的未知障碍，并说明这种证明语义能否带来强基线不能解释的收益。 |

这里的区别是研究问题的定义，**不是已经证明的原创性**。删减冗余覆盖、贪心集合覆盖、堆惰性更新和 C++ 实现均不能单独作为 MobiCom 算法创新。当前实验若被强贪心/快速修复解释，应如实记录，而不是以弱实现或免费事后选择制造优势。
