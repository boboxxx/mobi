#!/usr/bin/env python3
"""Descriptive report for a retained failed global replacement candidate."""
import json,hashlib
from pathlib import Path
from fractions import Fraction as F
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert (P/'audit_sheng.json').read_bytes()==(P/'audit_local.json').read_bytes()
    d=read(P/'development_sheng.json');old=read(ROOT/'results/prospective_hypotheses_20261004/summary_sheng.json');c=read(P/'conditional_diagnostic.json');old_map={(r['blueprint'],r['method']):r for r in old['source']};bps=list(d['registry']);names=('Audi','Tesla','Sprinter','Bicycle','Motorcycle','Walker');new={(r['blueprint'],r['family']):r for r in d['summary']};rows=[]
    for bp,name in zip(bps,names):
        gaps=[old_map[bp,m]['oracle_gap_us_p95']/1000 for m in ('joint','ridge','local_mean','local_modes')]+[new[bp,m]['oracle_gap_us_p95']/1000 for m in ('balanced_mean','balanced_modes')]
        rows.append('|'+name+'|'+'|'.join(f'{v:.3f}' for v in gaps)+'|'+str(len(new[bp,'balanced_mean']['excluded_episodes']))+'|'+str(len(new[bp,'balanced_modes']['excluded_episodes']))+'|')
    for r in d['summary']:assert not r['age_overstatements']
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),sharey=True);x=np.arange(6)
    for ax,family,label in zip(axes,('mean','modes'),('Mean hypotheses','Mode hypotheses')):
        ax.bar(x-.18,[old_map[bp,'local_'+family]['oracle_gap_us_p95']/1000 for bp in bps],width=.35,color='#444444',label='Previous score')
        ax.bar(x+.18,[new[bp,'balanced_'+family]['oracle_gap_us_p95']/1000 for bp in bps],width=.35,color='#187a70',label='Type-scaled pose and circle')
        ax.set_xticks(x,names,rotation=25);ax.set_title(label);ax.spines[['top','right']].set_visible(False);ax.set_axisbelow(True);ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('P95 source expiry gap (ms)');axes[0].legend(frameon=False,fontsize=8)
    fig.text(.06,.015,'Previously read corpus: post-test development only. Refused source expiry = zero.\nMotorcycle improves; every other class worsens. No fresh coverage or paid utility claim.',fontsize=9);fig.tight_layout(rect=(0,.08,1,1))
    figures=P/'figures';figures.mkdir(exist_ok=True)
    for suffix in ('png','pdf'):fig.savefig(figures/('development_tradeoff.'+suffix),dpi=180)
    plt.close(fig)
    report='''# 不同观测类型的校准尺度：开发反例与授权回合风险检查

2026-10-04，sheng。新候选已执行，6240 行源数据、3972 次新方法几何检查经独立有理数审计，本地与 sheng 审计逐字节一致。**候选显著改善摩托车，却使其余五类变差，不能作为统一替代方法。** 原有模型、guard、尺度、阈值和独立批次记录均未修改。

## 实际改动与证据地位

原有局部分数把 pose 误差除以 10mm，中心误差除以局部残差尺度；fallback 的大 pose 误差能同时抬高正常观测的圆半径。新方法在 supported 源把两类误差都除以已有局部尺度 σ；fallback 则把 body/pose 误差除以已知车身外接半径 b。每个家族仍只取一个完整回合最大分数。推理使用 ceil(Qσ) 扩张 pose 和中心圆，fallback 使用 ceil(Qb) 的 joint body/pose 集合。

源代码与审计在 `370c6b4` 发布后才在 sheng 执行。此前读过的 prospective_hypotheses 全部是当前候选的开发数据，保留原先 125/60 的分组只为描述比较，不重新赋予其独立测试地位。没有重新训练模型，没有新采集，也没有将旧计时当成新方法的通信费用。

## 六类完整比较

P95 oracle 有效期差，单位 ms。涵盖全部捕获测试源和两个固定查询，拒绝的有效期记零；末两列是新家族全部 60 个计划开发回合中的中心排除回合数。

|类别|Joint|Ridge|旧 mean|旧 modes|新 mean|新 modes|新 mean 排除|新 modes 排除|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
TABLE

摩托车 mean 从 179.461ms 降至 79.876ms，modes 降至 83.451ms。但新 mean 在 Audi/Tesla/Sprinter/Bicycle/Walker 均变差，不能只展示摩托车。摩托车两种新方法都出现 1/60 开发回合中心排除，旧方法是 0/60；固定查询未发现有效期越界，不能抹去集合排除。

![开发取舍](../results/balanced_expiry_20261004/figures/development_tradeoff.png)

这个反例进一步分离了机制：五类的阈值与旧版本完全相同，摩托车的新阈值分别为 `710851/280674` 和 `165640/60159`，低于旧值14.2276。五类变差不是阈值变大，而是把 supported pose 扩张从 Q·10mm 改成 Q·σ，放松了原先有用的几何约束。摩托车获益来自去掉 fallback 在错误单位下对全局 Q 的主导，不需要由此推断其他类型也应放松 pose。

下一候选应保留 supported 的两个原始约束单位，仅改变 fallback 的归一化，同时独立核算其更大的 fallback 集合代价。这是后续假说，尚未执行，不能把当前失败候选的结果当成其验证。

## 授权条件风险：数学流程可实现，当前样本不够

新增精确二项模块针对冻结策略、iid 完整回合，定义 G=本回合至少一次授权，F=至少一次授权引用了中心排除源。条件于被选中回合数 N，被选中的失败标记是 Bernoulli(P(F|G))；使用精确二项检验/上界及预先固定的多重比较预算。这与“每次授权”或“每个查询位置”的条件风险不同，更不是碰撞风险。数据、阈值、选择器必须在独立策略认证前固定。

对旧冻结策略的 6类别×8服务×2速率×2初始化=192 个比较，实际授权回合数每格36–60，失败授权回合数最多1。95% 联合预算下，条件风险上界范围为 **12.851%–26.062%**，**没有一格能通过5%目标**。即使零失败，也至少需要161个被授权的独立回合，不能把数千个相关查询当作数千个样本。新 balanced 方法没有实际计费策略，因此未混入这些旧策略统计。

独立检查器从已审计的原始决策重新统计选中/失败回合，用精确有理数核对 p-value，并以 SciPy beta/binomial 分布作数值参照。9 项主检查还包含随机选中样本量的类型一错误精确积分、非二进制有理数边界和集合覆盖边界。

这些统计方法有先例：[Learn then Test §3.2](https://arxiv.org/html/2110.01052v5)已研究二元选择条件风险；[JAIR 2011](https://arxiv.org/pdf/1401.3880)已研究邻居残差归一化。具体阅读范围及候选取舍在[READING](../experiments/balanced_expiry_20261004/READING.md)，不声称新统计定理。

后续若目标是“随机授权查询”的风险，可在每个独立回合按预先固定的查询流量分布抽一个查询，再对该查询的授权与失败计数。这样避免把同回合相关查询视为独立，并对应给定流量分布下的条件风险；它不自动覆盖新的查询分布或 ego 反馈。此处只提出认证设计，没有伪称获得新认证数据。

## 复核与完成边界

冻结源、输入、sheng 开发结果及日志、局部失败的传输前提检查、双主机几何审计、条件统计独立检查、图表和报告均保留。第一次本地审计在 SCP 尚未完成时发现输入缺失，未产生科学结果；[传输记录](../results/balanced_expiry_20261004/TRANSFER_NOTE.md)保留该失败日志，随后校验归档哈希再重放；科学代码未修补。

本轮排除了“统一放松 pose 的归一化可以普遍改善”的候选，落实了正确计数的授权回合条件风险模块，并明确了独立认证样本缺口。仍未解决统一低保守余量、每次授权风险、未知目标清单、实时 ego 闭环和真实移动网络收益，项目总体目标未完成。没有创建持续研究循环。
'''.replace('TABLE','\n'.join(rows))
    out=ROOT/'research/balanced_expiry_result_20261004.md';out.write_text(report)
    (P/'report_inputs.json').write_text(json.dumps(dict(development_sha256=sha(P/'development_sheng.json'),conditional_sha256=sha(P/'conditional_diagnostic.json'),source_sha256=sha(E/'report.py'),report_sha256=sha(out),fresh_qualification=False),indent=2,sort_keys=True)+'\n')
    print('BALANCED_DEVELOPMENT_REPORT_COMPLETE',flush=True)
if __name__=='__main__':main()
