# CUMCM 2026 C：含光伏与储能的微电网购电决策

Python implementations of deterministic, day-ahead risk-aware, rolling-forecast,
and variable-price electricity purchasing models. 中文说明为主。

本项目整理已有 C 题计算程序，包含 Q1—Q4 求解、公共储能执行回放，以及
Q3-old / Q3-risk 的可复现实验入口。模型参数和数学求解逻辑沿用研究版本，
本次开源整理主要修复数据路径、模板覆盖和运行目录依赖。

## 模型与代码

| 问题 | 方法 | 代码 |
| --- | --- | --- |
| Q1 | 完整信息 LP；最小购电费用后最小化电池吞吐量 | `code/solve_q1.py` |
| Q2 | 历史净负荷逐时段 90% 分位数 + 日前 MILP | `code/solve_q2.py` |
| Q3 | 0/6/12/18 时刻更新的滚动 LP；可选历史风险下限 | `code/solve_q3.py` |
| Q4-2 | Q2 的逐日波动电价扩展 | `code/solve_q4_2.py` |
| Q4-3 | Q3 的逐日波动电价扩展 | `code/solve_q4_3.py` |

Q2/Q4-2 使用 `scipy.optimize.milp`，Q1/Q3/Q4-3 和公共执行层使用
`scipy.optimize.linprog`，均由 SciPy 提供的 HiGHS 求解器求解。
Q3/Q4-3 当前实现没有充放电二元互斥变量，不应统称为 MILP。

## 安装与运行

推荐 Python 3.13；本项目固定了用于复验的依赖版本。

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

先按 [数据说明](data/README.md) 放入有权使用的附件和结果模板，再执行：

```bash
python run.py --check-inputs
python run.py --question q1
python run.py --question all
# 复算无风险下限的滚动基线：
python run.py --question q3 --variant old
python run.py --question q4_3 --variant old
```

也可以从任意工作目录指定数据和输出位置：

```bash
python /path/to/cumcm2026-c-microgrid/run.py --question all --data-dir /path/to/attachments --output-dir /path/to/generated-results
```

默认结果写入 `results/risk/` 或 `results/old/`，包括结果 Excel 和
`analysis_outputs/*.npz`。同一输出目录重跑会更新生成结果；输入附件和模板不被覆盖。
原始题目、数据附件和 Excel 模板没有随仓库分发。

## 参考结果与解释

下表是原研究版本 2025-02-01 至 2025-12-31 共 334 天的参考汇总，
详见 [CSV](reference_results/model_summary.csv)。不同求解器版本或最优解退化
可能改变逐时段方案，应结合成本、能量平衡和 SOC 边界判断复现结果。
本次发布复验记录见 [REPRODUCIBILITY.md](REPRODUCIBILITY.md)。

| 策略 | 平均日总成本/元 | 平均紧急购电量/(kWh/天) |
| --- | ---: | ---: |
| Q2 | 50832.05 | 473.45 |
| Q3-old | 49662.55 | 2965.67 |
| Q3-risk | 52389.93 | 96.17 |
| Q4-2 | 51286.86 | 481.37 |
| Q4-3-old | 52154.98 | 3012.92 |
| Q4-3-risk | 52887.98 | 98.41 |

Q3-risk 相比 Q3-old 的紧急购电量减少约 96.76%，总成本增加约 5.49%；
Q4-3-risk 对应减少约 96.73%、总成本增加约 1.41%。这些结果表示成本和
紧急购电风险之间的权衡，不能据此宣称风险版本总成本最低。

## 假设与已知边界

- 时间步长 10 min，每天 144 段；沿用原程序把行末 0:00 移至当日序列首位的
  对齐约定。这是循环移位处理，并非按跨日时间戳重新拼接，使用新数据前需复核。
- 储能量范围 1200—10800 kWh，充放电效率均为 0.9，功率上限 5000 kW；
  每日日初与日末储能量均为 6000 kWh。相同终态不代表日内没有充放电。
- 历史窗口 30 天，风险分位数 0.90；本仓库没有宣称其为最优参数。
- **Q3/Q4-3 的计划阶段直接使用当天完整负荷 `L[d]`，仅光伏使用预报。**
  因而这两个模型属于“负荷给定、光伏预测不确定”的离线实验，不能解释为
  对负荷与光伏都严格无未来信息的实时策略。
- 公共执行回放使用整天或整段真实负荷、光伏重新优化。该阶段具有段内后见信息，
  是离线评价，不等同于逐 10 min 的在线控制或真实部署效果。
- 滚动模型允许在计划优化中引入紧急购电变量；实际紧急成本以执行回放结果计。
- 调整费用沿用原程序，相对初始计划累计净变化计费，未逐次叠加所有中间调整费用。
- Q1、Q3/Q4-3 和执行层没有显式充放电互斥；Q2/Q4-2 的计划层有互斥。
  当前实现和论文中的任何更强声明应以代码为准。
- 风险下限采用逐时段最大值，没有建立误差相关性或正式不确定集合。
  固定增加预报更新次数不保证降低成本或紧急购电风险。

## 复验与贡献

```bash
python -m unittest discover -s tests -v
python scripts/validate_results.py --output-dir results/risk
```

测试使用合成数据检查能量平衡、SOC 与模板保护，不需要原始附件。
完整结果校验需要先运行模型。发布版本保留研究计算结果；欢迎通过 Issue
报告可复现问题，修改数学模型时请增加对照并说明与本版本的差异。

代码整理与研究过程使用了 AI 辅助。贡献者应核对数值、假设和结论；本仓库为
研究与学习案例，不代表赛事官方方案，也不声明获奖等级。

## 许可与资料来源

仓库中的原创代码和文档采用 [MIT License](LICENSE)，允许商业使用并要求
保留版权和许可声明。第三方题目、数据、Excel 模板及参考论文的权利仍属于
各自权利人，本许可证不覆盖这些第三方材料。数据获取与放置见 `data/README.md`。
