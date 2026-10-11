# 重建与独立核对动态观测诊断

在仓库根运行。`sheng_full_data.tar.xz` 是24,866,776B的无损包，保留全部660份原始NPZ、660份报文、24场景记录（含2失败）、sheng科学JSON/实测费用/日志/独立审计/服务器停止记录。完整解压数据约158MB；hash和逐文件清单随包保存。Git发布压缩包和主要可读结果，不重复提交全部原始NPZ。

```sh
python experiments/joint_motion_audit_20261011/restore.py
python -m unittest discover -s experiments/joint_motion_expiry_20261011 -p 'test_*.py' -v
python experiments/joint_motion_audit_20261011/verify.py \
  --capture results/joint_motion_expiry_20261011/capture \
  --analysis results/joint_motion_expiry_20261011/sheng \
  --out /tmp/joint_motion_audit.json
```

恢复程序核对包hash及全部文件，已有文件必须逐字节一致，拒绝覆盖。验证程序用精确条带消元替代生产多边形剪裁，重算3960个前缀、所有收费/时间许可及汇总，核对全部回波和报文hash。

本地重算要numpy；无需CARLA包，因为capture只在实际捕获时导入CARLA。选一个**不存在**的新输出目录：

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python \
  experiments/joint_motion_expiry_20261011/analyze.py \
  --capture results/joint_motion_expiry_20261011/capture \
  --out /tmp/mobi-joint-motion-recomputed \
  --fees-from results/joint_motion_expiry_20261011/sheng/fees.json
```

费用回放保留sheng当批实测采集/编译/解码费用；新机器实测时长另记timing，不冒充两端相同性能。若省略fees-from，将测新的费用，付费许可可能不同。通信20Mbps/20ms是固定模型，不是实测无线。原CARLA捕获程序及启动/停止脚本已冻结，不应覆盖原结果重跑；再次捕获需要新协议和新结果单元。

本批为已登记单行人的动态感知开发诊断。没有独立IID认证、未知目标覆盖、实际ego闭环或完整路线实验；采样真值核对不证明连续真实动力学或真实道路安全。
