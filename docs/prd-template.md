# {Project Name} — Design Spec

## Overview

{一句话描述项目目标}

## Architecture

{技术栈，必须包含：}
- **UI Framework**: {如 PyQt6 ONLY — 必须标注 ONLY 和版本，避免混用}
- **Database**: {如 SQLite}
- **Language**: {如 Python 3.10+}

```
{架构图 — 展示模块间的依赖关系}
```

## Data Model

> **CRITICAL**: 本节是数据库 schema 的唯一真相来源。
> LLM 会以此为准生成 `database_init.sql`。
> 后续所有 service 代码的 SQL 查询必须与此处列名完全一致。
> 不要使用"看起来类似"的列名——必须逐字匹配。

### {table_name}
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| {col} | {type} | {PK/FK/UNIQUE/NOT NULL/DEFAULT} | {说明} |

{每个表重复上述格式}

### Default Data
{如 settings 表的默认值、初始数据等}

## Conventions

> **CRITICAL**: 以下约定是代码生成的基础规则，所有 task 必须遵守。

### Task Ordering (tasks MUST be generated in this order)
1. **Phase 1 — Schema**: 生成 `database_init.sql`，包含所有 CREATE TABLE、INDEX、TRIGGER
2. **Phase 2 — Data Access Layer**: 生成 `DatabaseManager` 和所有 `*_service.py`
3. **Phase 3 — Models**: 生成 `models.py`，字段必须与 Data Model 节完全一致
3. **Phase 4 — UI Views**: 生成 UI 模块，通过 service 层访问数据，不直接写 SQL
4. **Phase 5 — Main Entry**: 生成 `main.py` / `main_window.py`，组装所有模块

### Database Access Rules
- `execute_read()` 返回 `dict`（key = 列名），所有 service 必须用 `row['column_name']` 访问，**禁止** `row[0]` 数字索引
- Service 层是唯一写 SQL 的地方，UI 层禁止内嵌 SQL
- 每个 service 的 `__init__` 必须接收 `DatabaseManager` 实例（依赖注入）
- SQL 中的列名必须与 Data Model 节逐字匹配

### Column Naming Rules
- 主键统一用 `id`（不用 `member_id`、`book_id` 等作为本表主键名）
- 外键用 `{referenced_table_singular}_id`（如 `book_id` REFERENCES `books.id`）
- 时间戳用 `_at` 后缀（`created_at`, `updated_at`）
- 布尔值用 `is_` 前缀（`is_suspended`, `is_paid`）
- 日期用 `_date` 后缀（`checkout_date`, `due_date`）

### UI Framework Rules
- 全项目只用一个 UI 框架版本，从 `import` 语句到使用方式必须一致
- MainWindow 在构造时创建所有 service 实例，通过参数注入到各 view/tab
- 各 view/tab 的 `__init__` 必须声明所需的 service 参数

## Features

### {Feature Name}
- {功能描述}

## Error Handling & Edge Cases

{列出需要处理的边界情况}

## Acceptance Criteria

{可验证的验收标准，每条对应一个可测试的行为}

## Smoke Test Checklist

> 以下操作必须在 smoke test 中全部通过，才算项目完成。

- [ ] 应用启动无报错
- [ ] 添加一条数据 → 列表刷新显示新数据
- [ ] 编辑一条数据 → 列表刷新显示更新
- [ ] 删除一条数据 → 列表刷新移除
- [ ] 搜索/过滤功能正常
- [ ] 关联操作正确（如：借书减少库存，还书增加库存）
