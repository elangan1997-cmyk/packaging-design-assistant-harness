# 包装设计助理 Harness 2.0

> 核心用途：把已有的包装平面稿、刀模图或完成设计稿，转成可以直接沟通的立体 CMF 工艺效果图；同时提供确定性刀模 SVG 和内容编排能力。

**English overview** — *Packaging Design Assistant Harness turns existing packaging artwork into presentation-ready CMF mockups while preserving the original layout, text, logo, colors, and structure. It also provides deterministic Illustrator-compatible dielines, content layout, provider orchestration, and visual QA.*

## 核心价值：平面稿 → 包装工艺效果图

客户最难理解的，通常不是一张平面图怎么画，而是这张展开图折成立体包装后到底长什么样、材质和工艺会有什么感觉。

这个 Harness 的首要作用就是解决这个沟通问题：你提供已有的平面展开图、完成设计稿或刀模图，再补充真实尺寸、材质和工艺，它负责规划并生成包装 CMF 效果图流程。

```text
保留这张包装的盒型、文字、Logo、颜色和版式，尺寸 80 × 40 × 120 mm，做哑膜加 Logo 局部 UV 和烫金的包装效果图。
```

它适合三个阶段：

- **方案提案**：让客户先看到折叠后的成品方向，不必只看难理解的展开图。
- **工艺沟通**：提前表达哑膜、烫金/烫银、局部 UV、击凸、镭射银卡等视觉质感。
- **打样前确认**：先发现版式、视角、材质和工艺方向的问题，减少反复修改。

配置真实图像 Provider 后，Module C 可输出 `mockup.png`、`cmf-plan.json`、Provider 生成记录、视觉 QA 和人工复核清单。仓库内的 Demo 使用 Mock Provider，只证明流程契约，不冒充真实 CMF 成片。

效果图会尽量保留原有盒型、文字、Logo、颜色、版式和主视觉，只在指定区域表达材质和工艺。它不能替代打样、正式印前文件或印厂确认。

## 抖音视频示例

[在抖音观看完整介绍视频](https://v.douyin.com/SDDIIfB12Wk/)

视频展示了一个典型的包装 CMF 流程：上传平面展开图，保留原来的版式、文字、颜色和主视觉，再生成带烫金、烫银、局部 UV、击凸或镭射质感的包装效果图。

![包装 CMF Skill 介绍封面](docs/assets/july-11-packaging-cmf-cover.jpg)

![对话输入、SVG 面板拆分和效果图预览](docs/assets/july-11-workflow-strip.jpg)

从左到右分别是：对话中的尺寸/材质输入、SVG 刀模面板拆分、效果图预览。封面和截图用于帮助理解流程，不作为本仓库代码已完成真实生成、尺寸准确或可直接生产的独立证明；文字、刀模和工艺参数仍需与印厂确认。

## 一张图看懂工作流

```mermaid
flowchart LR
    U["已有平面稿 / 完成设计稿<br/>+ 尺寸 + 材质工艺"] --> S["Skill Entry<br/>自然语言路由"]
    S --> I["Request IR<br/>Schema / 证据 / Dry Run"]
    I --> C["Module C<br/>CMF 方案 + Provider + Visual QA"]
    C --> CO["mockup.png<br/>cmf-plan.json / visual-qa.json"]
    I -. 辅助 .-> A["Module A<br/>确定性刀模 SVG"]
    I -. 辅助 .-> B["Module B<br/>内容编排"]
    A --> AO["template.svg"]
    B --> BO["content-layout.svg<br/>来源与复核清单"]
    C --> P["Host / OpenAI-compatible<br/>Custom REST / Mock"]
    CO --> R["设计师检查<br/>印厂确认 / 打样"]
    AO --> R
    BO --> R
```

## 其他能力：刀模和内容编排

CMF 效果图是首要使用场景，结构和内容模块负责把前置文件准备好，或在没有完成设计稿时单独使用：

| 你提供的内容 | Agent 会做什么 | 你会拿到什么 |
|---|---|---|
| 盒型 + 长宽高 | 调用对应的确定性盒型模型 | 可复制进 Illustrator 的 `template.svg` |
| 只有尺寸，没有盒型 | 先列出可用盒型，让你选择 | `choice_prompt`，尺寸自动保留 |
| SVG 刀模 + 产品资料 | 把资料放进安全面板，不碰刀线 | `content-layout.svg`、来源报告和缺失字段清单 |

当前可直接生成 SVG 的盒型：`直线盒`、`锁底盒`、`飞机盒`、`上盖盒`、`同向盖`、`粘底盒`、`挂耳盒`、`手提盒`、`纸箱`。飞机盒按用户提供的 `资源 9.svg` 基准建模，默认保留内尺寸、`0.3 mm` 纸厚和 `5 mm` 出血记录。“其它”盒型明确返回 `NOT_IMPLEMENTED`，不会拿相似盒型顶替。

## 32 秒 Harness Demo

![Packaging Design Assistant Harness 2.0 demo](docs/assets/packaging-assistant-demo.gif)

这段 Demo 展示 A → B → Mock C 的完整编排：结构 SVG、内容布局、CMF Provider 契约和视觉 QA。Mock Provider 只用于测试输出和人工复核，不代表真实图像 Provider 已经配置。

## 60 秒快速运行

需要 Python 3.9+；不需要 Node.js，也不需要安装 Illustrator 脚本。

```bash
git clone https://github.com/elangan1997-cmyk/packaging-design-assistant-harness.git
cd packaging-design-assistant-harness
./install.sh

# 检查本地能力
.venv/bin/packaging-assistant health-check

# 运行完整 A → B → Mock C Demo
.venv/bin/python examples/full-workflow/run_demo.py \
  --output output/full-workflow-demo
```

Demo 会输出 `template.svg`、`content-layout.svg`、CMF 计划、视觉 QA 和人工复核记录。要生成真实效果图，需换成经过确认的 Provider 配置。

## 对话示例

### 重点：生成包装效果图

```text
这是我的包装平面稿。请保留原来的文字、Logo、颜色和版式，尺寸是 80 × 40 × 120 mm。
材质用白卡纸，工艺做哑膜、Logo 局部 UV 和烫金，生成包装工艺效果图。
```

### 辅助：生成刀模 SVG

```text
做一个锁底盒，80 × 40 × 120 mm，生成可以复制进 Illustrator 的 SVG 刀模。
```

### 辅助：没有盒型时先选择

```text
我需要一个 100 × 60 × 160 mm 的包装盒，先给我可以生成的盒型选项。
```

如果用户只说了尺寸、没有说盒型，Harness 会先返回盒型选项；已经提供的尺寸会保留。“其它”盒型返回 `NOT_IMPLEMENTED`，不使用近似结构。

## 三个模块

### Module C — CMF Mockup（首要模块）

输入完成设计稿、真实物理尺寸、材质和工艺。流程保护原稿结构、文字、Logo、版式和颜色，只在指定区域表达 CMF。

空白刀模只能生成结构模板，不能直接当作完成设计稿制作最终 CMF 效果图。

### Module A — Structure Template

将盒型和尺寸转换为可编辑的 Illustrator-compatible SVG。结构输出默认标记为 `DESIGN_TEMPLATE`，不承诺无需印厂复核即可生产。

### Module B — Content Layout

接收 SVG 模板和产品资料，输出 `content-layout.svg`、`content-spec.json`、`source-report.md`、`missing-fields.md` 和 `review-checklist.md`。缺少企业、许可证、标准号、认证、成分或功效信息时使用明确占位符，不自动编造法规事实。

## Provider 预留：DeepSeek-compatible

仓库已经保留 OpenAI-compatible Provider 的配置边界；未来可以增加一个名为 `deepseek-compatible` 的配置别名，而不改变 Module A/B/C 的请求协议。

当前状态：**预留，未默认启用，未在本仓库声明已完成真实 DeepSeek 联调**。不要把它当作已经可用的 CMF 图像 Provider。

```yaml
# config.yaml 的未来预留形态；默认不启用，也不写死 endpoint/model。
# - name: deepseek-compatible
#   type: openai_compatible
#   enabled: false
#   endpoint: ""
#   model: ""
#   api_key_env: DEEPSEEK_API_KEY
```

如果接入的是只支持文本的 DeepSeek-compatible 模型，它可以用于路由、内容规划或结构化输出；Module C 的真实效果图仍必须使用声明支持 `image_generation` 的 Provider，并经过费用确认和视觉 QA。

## CLI 与 Python API

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

统一请求示例：

```json
{
  "action": "structure_template",
  "request_id": "job-001",
  "parameters": {
    "model_code": "carton.box_v2.lock_bottom",
    "dimensions": {
      "length": 80,
      "width": 40,
      "height": 120,
      "unit": "mm",
      "dimension_type": "finished_outer"
    }
  }
}
```

## 安全与精度边界

- 物理尺寸是效果图和结构比例的前置条件，不能从像素或图片尺寸猜测 mm。
- 刀模线、压痕线、出血、安全区、糊口、纸厚补偿和模切公差必须分别验证。
- 本地代码只做解析、校验、记录和文件管理，不用本地滤镜伪造 CMF 证明。
- API Key 只从环境变量读取，不写入仓库、输出或错误记录。
- Provider 未配置、结果为 Mock 或视觉 QA 未通过时，必须明确标记人工复核。
- 效果图不能替代打样、正式印前文件或印厂确认。
- 未实现能力返回 `NOT_IMPLEMENTED`，不会用自由生成结果冒充确定性工具。

## 测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall -q src scripts tests
.venv/bin/python evals/run_evals.py
```

当前基线：53 项自动化测试、12 个 Evals。README 的 Demo 使用 Mock Provider，不能作为真实 CMF 视觉质量证明。

## 审计、实现与参考

详细资料放在这里，避免占用首页的首次阅读路径：

- [CHANGELOG.md](CHANGELOG.md) — 版本变化和能力边界
- [MIGRATION.md](MIGRATION.md) — 从旧版 CMF Skill 迁移
- [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md) — 架构基线
- [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) — 总体实现报告
- [reports/BOX_V2_SUPPLIED_FIXTURE_AUDIT.md](reports/BOX_V2_SUPPLIED_FIXTURE_AUDIT.md) — 盒型 2.0 SVG 样本审计
- [reports/ORIGINAL_SCRIPT_BENCHMARK.md](reports/ORIGINAL_SCRIPT_BENCHMARK.md) — 原脚本对照记录
- [reports/PHASE3_CONTENT_LAYOUT_REPORT.md](reports/PHASE3_CONTENT_LAYOUT_REPORT.md) — Module B
- [reports/PHASE4_PROVIDER_CMF_REPORT.md](reports/PHASE4_PROVIDER_CMF_REPORT.md) — Module C
- [reports/PHASE5_EVALS_REPORT.md](reports/PHASE5_EVALS_REPORT.md) — Evals
- [SKILL.md](SKILL.md) — Agent 路由、追问和输出协议
- [config.example.yaml](config.example.yaml) — Provider 配置模板
