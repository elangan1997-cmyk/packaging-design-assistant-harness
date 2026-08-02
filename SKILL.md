---
name: packaging-design-assistant
description: 对话式包装设计 Harness。用于用户要求生成包装刀模 SVG、可设计 SVG、包装结构模板、包装背标/文案/法规字段排版，或包装 CMF 工艺效果图与视觉质检。
---

# Packaging Design Assistant Harness

## 何时使用

出现以下意图时使用本 Skill：

- 包装设计助理、包装设计 Harness、包装模板。
- 生成刀模 SVG、可复制进 Illustrator 的 SVG、包装结构代码、可设计 SVG。
- 包装背标、包装信息、包装文案、包装法规字段、包装信息排版。
- 包装效果图、CMF 效果图、包装材质、印刷工艺、视觉质检。

## 对话入口

普通用户不需要打开网页或手动运行 CLI。先从自然语言中抽取 action 和参数，再把统一 JSON 请求写入本次任务的临时目录，调用：

```bash
.venv/bin/python scripts/skill_entry.py --request request.json --output output/
```

如果尚未安装 `.venv`，在仓库根目录运行 `./install.sh`。核心流程不需要 Node.js。

## 自动路由

| 用户目标 | action | 模块 |
|---|---|---|
| 盒型 + 尺寸 → 空白刀模/结构 SVG | `structure_template` | Module A |
| 产品资料 + SVG → 字段和面板编排 | `content_layout` | Module B |
| 完成稿 + 材质工艺 → 效果图/QA | `mockup_render` | Module C |
| 判断文件类型和已有信息 | `inspect` | Core |
| 只看将如何处理 | 使用目标 action + `--dry-run` | Core |
| 检查 JSON/SVG | `validate` | Core |
| 检查安装和能力 | `health_check` | Core |

如果用户上传的是完整设计稿并要求效果图，直接进入 Module C；不得强迫先运行 Module A 或 B。

## 最小追问

只问执行确定性任务所缺少的字段。

Module A 至少需要：

- 独立盒型/包装类型。
- 成品长、宽、高与单位。
- 内尺寸或外尺寸；用户未说明时，标记不确定并追问。

当用户没有说明盒型时，不得只回复“请提供盒型”。先展示 Harness 返回的 `choice_prompt.options`，让用户回复盒型名称或序号；保留用户已经提供的尺寸。将 `status: available` 标为“可生成”，将 `status: not_implemented` 标为“开发中”，不得把开发中的选项路由到近似盒型。

对话展示格式：

```text
请选择盒型：
1. 锁底盒（可生成）
2. 手提盒（可生成）
3. 直线盒（开发中）
…
```

当前已确定性实现：

- `锁底盒` / `锁底` / `lock bottom` → `carton.box_v2.lock_bottom`
- `手提盒` / `carry handle` → `carton.box_v2.carry_handle`

盒型2.0 的 `直线盒`、`飞机盒`、`上盖盒`、`同向盖`、`粘底盒`、`挂耳盒`、`纸箱`、`其它` 已分别注册，但在各自完成原脚本回归测试前必须返回 `NOT_IMPLEMENTED`，不得转用已实现盒型或通用近似模板。每个盒型使用一份原脚本 SVG 样本做独立黑盒回归。

纸厚、糊口、出血、安全区可以使用模型的明确默认值，但必须在结果中列出。不能从图片像素猜真实物理尺寸。

Module B 至少需要模板和产品资料。Module C 至少需要完成稿、真实物理尺寸和材质；工艺和重点区域缺失时只做最小追问。空白刀模不能当作完成稿生成效果图。

Module B 当前只使用用户资料与占位规则。不得补写企业、许可证、标准号、认证、成分、功效或其他监管事实。缺少资料时保留 `[待提供：…]`、`[待确认：…]` 占位符，并提示人工复核。

## 工具调用协议

统一请求：

```json
{
  "action": "structure_template",
  "request_id": "",
  "parameters": {}
}
```

锁底盒或手提盒请求参数（替换 `model_code`）：

```json
{
  "action": "structure_template",
  "parameters": {
    "model_code": "carton.box_v2.lock_bottom",
    "dimensions": {
      "length": 100,
      "width": 55,
      "height": 160,
      "unit": "mm",
      "dimension_type": "finished_outer"
    },
    "shrink": 0.7,
    "tuck_height": 15,
    "glue_width": 14
  }
}
```

内容编排请求：

```json
{
  "action": "content_layout",
  "parameters": {
    "template": "/absolute/path/template.svg",
    "brief": "/absolute/path/product-brief.json"
  }
}
```

Module B 成功时读取全部五个输出，重点检查 `missing-fields.md` 和 `review-checklist.md`。它输出包装信息草稿，不代表法律审核或上市许可。

先运行 Dry Run 可检查：路由、输入、缺失字段、Provider、费用风险、预计输出和人工复核项。Dry Run 不得调用真实付费 API。

将入口返回的 JSON 原样视为执行事实。`success: true` 也要读取输出文件和验证报告；`status: not_implemented` 时必须明确告诉用户，不能临时自由画 SVG 或伪装已经完成。

## 模型与确定性代码边界

大模型可以理解用户描述、识别盒型名称、抽取/换算尺寸、发现缺失字段和组织 Schema。

大模型不得自由生成结构 Path、临时编造公式或把视觉近似说成标准刀模。几何、面板、糊口、插舌、防尘翼、切线、压痕、出血、安全区、稳定 ID 和 SVG 序列化必须由已测试的 Module A 代码完成。

## 能力补全

运行 `health_check` 获取 capability manifest。没有真实完成的 action 必须返回 `NOT_IMPLEMENTED`。Module C Provider 未配置时必须明确失败；外部 API 和 Mock 都必须由用户显式允许。Mock 结果必须标记为测试输出和 `manual_review`，不得声称已生成真实效果图。

## 安全边界

- Module A 默认输出 `DESIGN_TEMPLATE`，不承诺可直接生产。
- 任何结构模板都要提示 `REQUIRES_MANUFACTURER_REVIEW`。
- 法规、标签字段和合规结论必须保留来源与人工复核状态。
- 不硬编码用户路径、API Key、Provider 地址或跨 Job 上下文。
- 不用本地合成伪造 CMF 证明，不改写用户原稿文字、Logo 和版式。
- 刀模线不能混入印刷图层；切线和压痕线必须区分。

## 输出协议

向用户返回：

1. 结果状态和 action。
2. 可点击的实际输出文件。
3. 使用的盒型 ID、尺寸、默认值和警告。
4. 验证结果与人工复核项。
5. `DESIGN_TEMPLATE`/Provider/合规边界。

Module C 的材质、工艺、原稿保护和提示词细节按需读取：

- `references/finish-taxonomy.md`
- `references/material-compatibility.md`
- `references/output-format.md`
- `references/prompt-templates.md`
- `references/selection-questions.md`
- `references/structure-recommendations.md`
