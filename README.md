# Packaging Design Assistant Harness

这是一个本地优先、对话驱动的包装设计 Harness。普通用户只需要在 Codex、Claude Code 或其他支持 Skill 的 Agent 中说明包装类型、尺寸和任务目标；Agent 负责调用统一 Python 入口，不需要网页、Web Server 或 Node.js。

## 模块

- **Module A — Structure Template**：确定性生成可复制、可在 Illustrator 中继续编辑的 SVG 结构模板。
- **Module B — Content Layout**：包装字段、来源、规范提示和面板内容编排。
- **Module C — CMF Mockup**：包装材质/工艺建议、效果图 Provider 和视觉质检。

当前 `0.5.0` 已完成架构底座、两个经原脚本回归验证的 Module A 盒型、Module B 内容编排闭环，以及 Module C 的 Provider 调度、视觉 QA 和有限重试。`盒型2.0 / 锁底盒` 和 `盒型2.0 / 手提盒` 可直接生成 SVG；其余八个盒型仍按模型返回 `not_implemented`。Module C 只有在真实 Provider 已配置且用户确认外部调用后才生成真实效果图；Mock 输出始终标记为测试结果并进入人工复核。

## 自然语言使用

安装为 Skill 后可以直接说：

```text
做一个锁底盒，80 × 40 × 120 mm，生成可以复制进 Illustrator 的 SVG 刀模模板。
```

也可以说：

```text
做一个手提盒，100 × 60 × 160 mm，生成 SVG 刀模模板。
```

或：

```text
这是空白刀模和产品资料。把包装字段整理到正面、背面和侧面，不要改刀线。
```

Agent 按 [SKILL.md](SKILL.md) 路由并调用 `scripts/skill_entry.py`。普通用户不必手动运行命令。

如果用户只提供尺寸、没有说明盒型，Harness 返回 `status: needs_input` 和机器可读的 `choice_prompt`。Agent 必须显示盒型选项，让用户用名称或序号选择；已提供的尺寸继续保留。

## 安装

```bash
./install.sh
```

要求 Python 3.9 或更高版本。安装只增加 Python 包和 PyYAML，不安装 Node.js。默认不调用任何付费 API。

## 统一入口

```bash
.venv/bin/python scripts/skill_entry.py \
  --request examples/full-workflow/health-request.json \
  --output output/
```

请求格式：

```json
{
  "action": "structure_template",
  "request_id": "job-001",
  "parameters": {}
}
```

支持的 action：`structure_template`、`content_layout`、`mockup_render`、`inspect`、`route`、`validate`、`health_check`。实际可用状态以健康检查的 capability manifest 为准。

### 已识别的盒型2.0模型

`直线盒`、`锁底盒`、`飞机盒`、`上盖盒`、`同向盖`、`粘底盒`、`挂耳盒`、`手提盒`、`纸箱`、`其它` 已拆成十个模型 ID。当前 `carton.box_v2.lock_bottom` 与 `carton.box_v2.carry_handle` 已完成原脚本回归验证，其余模型返回模型级 `NOT_IMPLEMENTED`。验收策略为每个盒型使用一份原脚本 SVG fixture。

参数示例见 `examples/structure-template/box-v2-lock-bottom.json` 和 `examples/structure-template/box-v2-carry-handle.json`：

```bash
packaging-assistant --output output/ structure \
  --spec examples/structure-template/box-v2-lock-bottom.json
```

注意：盒型2.0 的“手提盒”是折叠纸盒结构，不等同于独立 F5“手提袋 Pro”纸袋结构。

### Module B 内容编排

Module B 接收 Harness 生成的空白 SVG 模板和 JSON 产品资料，输出：

- `content-layout.svg`
- `content-spec.json`
- `source-report.md`
- `missing-fields.md`
- `review-checklist.md`

它只写入 `LAYER_ARTWORK`，不会修改切线、压痕、出血和安全区图层。企业、地址、许可证、标准号、认证、成分和功效等缺失信息使用明确占位符，不会自动编造。当前版本不自动执行法规搜索，所有字段仍需人工复核。

```bash
packaging-assistant --output output/ content \
  --template output/template.svg \
  --brief examples/content-layout/aquarium-salt-brief.json
```

### Module C Provider 效果图与视觉 QA

Module C 支持 Host、OpenAI-compatible、Custom REST 和 Mock 四类适配器。Provider 按配置顺序执行，失败时有限重试和回退；真实外部 Provider 必须设置 `allow_external_api: true`，Mock 必须设置 `allow_mock: true`。API Key 只能通过配置中的环境变量名称读取，不写入仓库、输出或错误记录。

```bash
cp config.example.yaml config.yaml
# 填写真实尺寸、材质、Provider endpoint/model 和环境变量名后：
packaging-assistant --output output/ mockup \
  --artwork completed-artwork.svg \
  --config config.yaml
```

输出 `mockup.png`、`cmf-plan.json`、`generation-record.json`、`visual-qa.json`、`retry-record.json` 和 `review-checklist.md`。视觉 QA 最多自动重试两次；仍不通过、不可修复或使用 Mock 时状态为 `manual_review`。

## CLI

```bash
packaging-assistant inspect <input>
packaging-assistant route <request.json>
packaging-assistant structure --spec <file>
packaging-assistant content --template <svg> --brief <json>
packaging-assistant mockup --artwork <file> --config <yaml>
packaging-assistant run --job <job.json> --dry-run
packaging-assistant validate <file>
packaging-assistant health-check
```

Dry Run 只报告路由、缺失输入、Provider、费用可能性、预计输出和人工复核项，不会调用真实 Provider。

## Python API

```python
from packaging_assistant import run_packaging_request

result = run_packaging_request(
    {
        "action": "health_check",
        "request_id": "python-example",
        "parameters": {},
    }
)
print(result.to_dict())
```

## 安全与精度边界

- 结构输出默认是 `DESIGN_TEMPLATE`，用于设计、排版、效果图和结构沟通。
- 未经印厂确认，不得称为可直接生产或无需复核。
- 切线、压痕、出血、安全区、糊口、纸厚补偿和模切公差必须分别验证。
- CMF 效果图不能替代打样和正式印刷文件。
- 本地代码只做解析、校验、记录和文件管理，不用 Pillow、OpenCV、ImageMagick、FFmpeg 或本地滤镜伪造 CMF。
- 法规和合规内容是辅助建议，必须由有资质人员和实际来源复核。
- 未实现的能力返回 `NOT_IMPLEMENTED`，不会用自由生成结果冒充确定性工具。

## 测试

```bash
python3 -m unittest discover -v
python3 -m compileall -q src scripts tests
```

架构基线见 [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md)，Phase 1 结果见 [reports/PHASE1_REPORT.md](reports/PHASE1_REPORT.md)，Module B 见 [reports/PHASE3_CONTENT_LAYOUT_REPORT.md](reports/PHASE3_CONTENT_LAYOUT_REPORT.md)，Module C 见 [reports/PHASE4_PROVIDER_CMF_REPORT.md](reports/PHASE4_PROVIDER_CMF_REPORT.md)，当前总状态见 [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md)。
