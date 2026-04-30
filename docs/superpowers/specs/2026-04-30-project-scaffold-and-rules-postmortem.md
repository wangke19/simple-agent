# Project Scaffold & Framework Rules — 设计与实践复盘

> 日期: 2026-04-30
> 项目: simple-agent (AI Vibe Coding 工作流引擎)

## 1. 问题起源

在执行 `python build_with_workflow.py demo/books-library-mgmt-design.md` 时，LLM 生成的代码在运行时报错：

```
AttributeError: type object 'QTabWidget' has no attribute 'North'
```

**根因**: PRD 中明确写了 `PyQt6 ONLY`，但 LLM 仍然输出了 PyQt5 风格的 enum 语法 (`QTabWidget.North` 而非 `QTabWidget.TabPosition.North`)。

追查后发现三层问题：

1. **设计文档约束粒度不够** — 只写了"PyQt6 ONLY"，没有具体说明 scoped enum 语法
2. **Contract 只覆盖 API 签名** — 设计文档中的 UI Framework Rules 没有被转译进 contract
3. **执行时 prompt 拼接链路丢失了原始约束** — `task.description + schema_block + contract_block`，没有一层传递框架规则

核心缺失：**workflow 有 schema_block 和 contract_block，但没有 rules_block**。

## 2. 设计决策

### 两层 AGENT.md 架构

| 层级 | 文件 | 作用 | 生命周期 |
|------|------|------|----------|
| 通用工程规范 | `agent_md_template.md` (随 simple-agent 发布) | 所有项目的工程纪律 | 固定 |
| 项目约束规则 | `{project}/AGENT.md` (每个项目生成) | 框架规则、架构约束、已知坑点 | 从 PRD 动态生成 |

### Scaffold Phase

在 Plan 之前插入新阶段：

```
PRD → Scaffold → Plan → Decompose → Contracts → Execute(含守卫) → Report → Smoke Test
```

Scaffold **不调用 LLM**，纯结构化操作：解析 PRD、检测框架、创建骨架、生成 AGENT.md。

### 框架陷阱知识库

```
src/simple_agent/framework_rules/
├── pyqt6.md      # scoped enums, signal syntax, thread safety
├── flask.md      # session security, SQL injection
├── fastapi.md    # async pitfalls, Pydantic v2
├── react.md      # hooks rules, key prop
└── generic.md    # error handling, logging, security
```

PRD 中声明了某个框架 → 自动将对应的坑点合并进项目 AGENT.md。

### 三层约束

| 层级 | 控制方 | 例子 |
|------|--------|------|
| **骨架** (scaffold) | simple-agent 强制创建 | AGENT.md、入口文件、tests/、.gitignore |
| **规则** (rules) | 写入 AGENT.md，LLM 必须遵守 | 框架版本、命名规范、分层架构 |
| **实现** (impl) | LLM 自由发挥 | 具体算法、UI 布局、内部实现 |

### 实时守卫

在 `_validate_task_output` 中增加检查：

| 检查项 | 说明 | 失败行为 |
|--------|------|----------|
| AGENT.md 完整性 | 关键段不能被删除或清空 | 标记 task 失败 |
| 禁用 import 检测 | 扫描 .py 文件检查违反框架规则的 import | 标记 task 失败 |
| 目录守卫 | tests/ 目录不能被删除 | 标记 task 失败 |

## 3. 实现结果

7 个原子提交：

```
7230b89 feat: add framework rules knowledge base and engineering standards template
d16dc9f feat: add scaffold module with PRD parsing, framework detection, and skeleton creation
dad820c feat: add rules_injection_template to Prompts and scaffold guard messages
8b05be9 feat: integrate scaffold into DevWorkflow with rules_block injection
31373f5 feat: add real-time guard checks for AGENT.md integrity, forbidden imports, and directory structure
7524f63 feat: integrate scaffold phase into build_with_workflow CLI
d4ac8a1 feat: add scaffold & rules section to workflow report
```

关键文件变更：

| 文件 | 职责 |
|------|------|
| `src/simple_agent/scaffold.py` | PRD 解析、框架检测、骨架创建、AGENT.md 生成 |
| `src/simple_agent/framework_rules/*.md` | 各框架已知坑点知识库 |
| `src/simple_agent/agent_md_template.md` | 通用工程规范模板 |
| `src/simple_agent/dev_workflow.py` | scaffold()、rules_block 注入、guard checks |
| `src/simple_agent/prompts.py` | rules_injection_template |
| `src/simple_agent/messages.py` | scaffold 和 guard 相关消息 |
| `build_with_workflow.py` | --skip-scaffold、Phase 0 |

## 4. E2E 验证

```
# Scaffold 检测框架
Frameworks: ['pyqt6']
Rules count: 68

# AGENT.md 包含 PyQt6 enum 规则
## Enum Syntax (CRITICAL)
PyQt6 uses fully-scoped enum names:
- WRONG: QTabWidget.North
- RIGHT: QTabWidget.TabPosition.North

# Guard 检测到禁用 import
Errors: ["GUARD: Forbidden import 'PyQt5' in bad.py (allowed: PyQt6)"]

# CLI flag
--skip-scaffold       Skip scaffold phase (for existing projects)
```

## 5. 经验教训

### Vibe Coding 的核心矛盾

LLM 有创作自由度，但工程项目需要纪律。关键不在于"限制 LLM"，而在于**建立正确的约束边界**：

- **骨架**（目录、入口、配置文件）由 engine 强制，LLM 不碰
- **规则**（框架版本、编码规范）通过 prompt 注入，LLM 遵守
- **实现**（具体代码）完全交给 LLM 自由发挥

### 框架陷阱知识库的价值

LLM 的训练数据中包含大量过时代码（PyQt5、Pydantic v1、Flask 旧模式）。光说"用 PyQt6"不够，必须把具体的 breaking change 写出来。知识库就是这个"具体化"的载体。

### 两层 AGENT.md 的通用性

这个模式不限于 Python 项目。任何 AI 代码生成工具都需要：
1. **工具自身的工程标准**（通用、固定）
2. **每个项目的具体约束**（从设计文档提取、动态生成）

### 测试中发现的问题

现有 workflow 测试中 `test_chinese_prompts_workflow` 等用例会因为 `_validate_task_output` 的 subprocess import check 而挂起（working_dir 默认为 "."，扫描整个项目）。这是已有问题，需要后续修复：将 import check 限制在输出目录而非当前目录。

## 6. 后续方向

- **更多框架规则**：React、Vue、Django、Tauri 等
- **PRD 模板增强**：引导设计者在 PRD 中更完整地描述约束
- **import check 性能优化**：限制扫描范围，避免全项目 subprocess
- **AGENT.md 自愈**：如果 LLM 意外修改了 AGENT.md，自动恢复
