# Packaging Design Assistant Harness

这是一个本地优先、对话驱动的包装设计 Harness。普通用户只需要在 Codex、Claude Code 或其他支持 Skill 的 Agent 中说明包装类型、尺寸和任务目标；Agent 负责调用统一 Python 入口，不需要网页、Web Server 或 Node.js。

## 模块

- **Module A — Structure Template**：确定性生成可复制、可在 Illustrator 中继续编辑的 SVG 结构模板。
- **Module B — Content Layout**：包装字段、来源、规范提示和面板内容编排。
- **Module C — CMF Mockup**：包装材质/工艺建议、效果图 Provider 和视觉质检。

当前 `0.1.0` 是 Phase 1 架构底座。核心路由、IR、Job Workspace、CLI、Skill Entry、健康检查和 Mock Provider 已实现；Module A 的具体盒型、Module B 内容写入和 Module C 图片生成在通过各自测试前会明确返回 `not_implemented`。原有 CMF 参考资料完整保留。

## 自然语言使用

安装为 Skill 后可以直接说：

```text
做一个反插口盒，80 × 40 × 120 mm，生成可以复制进 Illustrator 的 SVG 刀模模板。
```

或：

```text
这是完成稿。哑银卡纸，Logo 烫黑金，产品名击凸，给我 CMF 建议和效果图工作流。
```

Agent 按 [SKILL.md](SKILL.md) 路由并调用 `scripts/skill_entry.py`。普通用户不必手动运行命令。

## 安装

```bash
./install.sh
```

要求 Python 3.9 或更高版本。基础安装无第三方运行时依赖，不安装 Node.js，也不调用付费 API。

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
- 法规和合规内容是辅助建议，必须由有资质人员和实际来源复核。
- 未实现的能力返回 `NOT_IMPLEMENTED`，不会用自由生成结果冒充确定性工具。

## 测试

```bash
python3 -m unittest discover -v
python3 -m compileall -q src scripts tests
```

架构基线见 [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md)，Phase 1 结果见 [reports/PHASE1_REPORT.md](reports/PHASE1_REPORT.md)。
