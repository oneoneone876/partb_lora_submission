# Part B: LoRA Fine-tuning for SVG Logo Generation

## 1. 作业目标

本作业使用 Gemma 3 270M 作为基础模型，在 logo-detailed-prompt 数据集上进行 LoRA 参数高效微调，使模型能够根据文字描述生成完整的 SVG logo。完成内容包括：设计 SVG 自动评分函数、训练 LoRA adapter、分别评估基础模型和微调模型，并提交可复现的配置、代码和模型权重。

## 2. 数据集与任务形式

训练数据来自 `logo-detailed-prompt` 项目，包含详细的 logo 文字描述和对应 SVG 输出。训练集共 219 条样本，验证集共 17 条样本。每条样本使用聊天格式组织：system message 规定模型是 SVG logo generator，user message 给出设计要求，assistant message 给出 SVG 文本。

训练时只对 assistant 输出的 SVG token 计算损失，以避免模型把学习能力浪费在重复输入提示词上。

## 3. Reward 设计

在 `reward.py` 中实现了面向 SVG 输出的组合奖励函数，主要包含以下部分：

1. **有效性（Validity）**：检查输出是否包含 SVG 标签、是否能被 XML 解析，且是否具有合理的 `viewBox`。
2. **结构（Structure）**：统计 `path`、`rect`、`circle`、`ellipse`、`polygon`、`line` 等常见 SVG 图元，鼓励生成包含实际图形结构的 SVG。
3. **几何合理性（Geometry）**：检查坐标是否明显超出 `0 0 256 256` 画布范围。
4. **配色（Palette）**：检查是否使用 `fill`、`stroke` 或颜色属性，并鼓励较小且相对一致的颜色集合。
5. **提示词一致性（Prompt fidelity）**：根据提示中出现的颜色和形状关键词，检查输出中是否有对应的 SVG 表达。
6. **退化惩罚（Penalty）**：对空输出、重复片段、异常短输出等情况扣分。

该 reward 主要用于比较基础模型和 LoRA 模型的相对表现，不等价于人工主观美学评价。

## 4. 微调配置

| 项目 | 配置 |
|---|---|
| 基础模型 | Gemma 3 270M |
| 微调方法 | LoRA |
| LoRA rank | 8 |
| LoRA alpha | 16 |
| LoRA dropout | 0.05 |
| 学习率 | 2e-4 |
| 训练轮数 | 8 epochs |
| batch size | 1 |
| 梯度累积 | 8 steps |
| 最大序列长度 | 2048 |
| 随机种子 | 42 |
| 生成策略 | greedy decoding，max_new_tokens=1400 |

LoRA 训练的可训练参数为 1,898,496，总参数为 269,996,672，可训练参数占比约 0.7032%，因此只保存 adapter 权重即可复用微调结果。

## 5. 训练过程

训练在 Kaggle 的 GPU 环境中完成。训练共执行 112 个优化步骤，最终训练损失约为 0.8153；验证损失在训练过程中下降到约 0.7847，说明模型能够学习数据集中 SVG 输出的文本模式和结构格式。

## 6. 自动评估结果

在 17 条验证样本上，使用相同的生成参数分别评估基础模型和 LoRA 微调模型。结果如下：

| Model | Mean reward | Validity | Structure | Geometry | Palette | Prompt fidelity | Penalty |
|---|---:|---:|---:|---:|---:|---:|---:|
| Base Gemma 3 270M | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| LoRA model | 0.050882 | 0.058824 | 0.058824 | 0.058824 | 0.000000 | 0.050000 | -0.058824 |
| Delta (LoRA - Base) | +0.050882 | +0.058824 | +0.058824 | +0.058824 | 0.000000 | +0.050000 | -0.058824 |

## 7. 结果分析

LoRA 模型的平均 reward 高于基础模型，说明微调使 270M 基础模型开始生成部分可识别的 SVG 结构，并在几何范围和提示词关键词覆盖方面获得了非零得分。基础模型在本评估设置下没有得到有效的 SVG reward。

不过绝对 reward 仍然较低，尤其是 palette 项为 0，且仍存在退化惩罚。这表明小规模模型在较长的结构化 SVG 生成任务上仍容易出现不完整输出、配色信息不足或图形细节较少的问题。reward 的提升应理解为格式和结构上的初步改善，而不是 logo 视觉质量已经达到较高水平。

可能的改进方向包括：增加训练数据量、延长训练或调整学习率、使用更大的基础模型、提高验证时的输出 token 上限，以及加入基于渲染图像的人工或视觉模型评估。

## 8. 提交内容

本仓库包含：

- `adapter/adapter_model.safetensors`：训练得到的 LoRA 权重；
- `adapter/adapter_config.json`：LoRA 配置；
- `reward.py`：SVG reward 实现；
- `train_config.yaml`：训练配置；
- `results.json`：结构化评估结果；
- `report.md`：本实验报告。

## 9. 结论

本作业成功完成了 Gemma 3 270M 的 LoRA 微调流程和基础模型对比评估。LoRA 模型相对于基础模型取得了 `+0.050882` 的平均 reward 提升，证明该微调过程对 SVG 结构化输出具有正向作用；但模型整体输出质量仍有较大提升空间。
