# Constraint Validation Pipeline — 设计文档

> 日期: 2026-04-30
> 项目: simple-agent (AI Vibe Coding 工作流引擎)
> 提交: b3ad469

## 1. 问题起源

在执行 `python build_with_workflow.py demo/books-library-mgmt-design.md` 时，LLM 生成的 SQL 与 PRD Data Model 不匹配：

```
PRD 要求: settings.setting_key / settings.setting_value
实际生成: settings.key / settings.value

PRD 要求: fines 表包含 member_id, days_overdue, payment_date, payment_amount
实际生成: 缺少这四列
```

**追查信息流链路**后发现三层约束丢失：

```
PRD 原文 (完整约束)
├── Architecture          ✅ 写入 AGENT.md
├── Conventions           ✅ 写入 AGENT.md
├── Data Model            ❌ 未写入 AGENT.md ← 关键缺失
├── Features              ❌ 未写入
└── Acceptance Criteria   ❌ 未写入
```

## 2. 根因分析

### 断点 1：Data Model 没进 AGENT.md

`scaffold.py` 的 `generate_agent_md()` 只提取了 Architecture、Conventions、UI Framework Rules 三个 section，**遗漏了 Data Model**。PRD 里的 `NOT "key"`、`NOT "value"`、`NOT "genre"` 这些关键约束从未进入 `rules_block`。

### 断点 2：Plan 分解丢失细节

Plan 阶段把 PRD 摘要成 21 个简短 task description。Task 1 变成 "Write database_init.sql with exact schema" — 只有一句话，没有列定义。

### 断点 3：Schema 反馈循环（最严重）

一旦 Task 1 生成了错误的 SQL：

```
错误 SQL → _refresh_schema_block() 标记为 "GROUND TRUTH"
         → 后续所有任务看到错误的列名
         → services/tabs 照抄错误列名
         → 错误自我强化
```

### 核心结论

**不是上下文过长导致的幻觉，也不是记忆管理问题，而是信息在 pipeline 中被结构性截断了。** Data Model 作为最关键的约束数据，从未进入任何注入环节。

## 3. 设计决策

### 四层约束保护

| 层级 | 机制 | 控制方 | 触发时机 |
|------|------|--------|----------|
| **Scaffold** | Data Model 写入 AGENT.md | engine 强制 | Phase 0 (scaffold) |
| **Pre-task** | AGENT.md section 完整性验证 + auto-restore | engine 强制 | 每个任务执行前 |
| **Post-task** | PRD-aware SQL schema 验证 | engine 强制 | 每个任务完成后 |
| **Schema block** | Mismatch warning 注入 | prompt 注入 | 每次刷新 schema_block |

### 信息流修复后的链路

```
PRD Data Model (完整列定义)
  → parse_data_model_columns() 解析为 {table: [columns]}
  → generate_agent_md() 写入 AGENT.md 的 ## Data Model 节
  → _build_rules_block() 从 AGENT.md 读取并注入每个任务 prompt
  → 任务 prompt 包含: task.description + rules_block(含 Data Model) + schema_block + contract_block

每任务执行前:
  validate_agent_md_sections() → 缺失则从 snapshot auto-restore

每任务完成后:
  _validate_sql_against_prd() → 生成的 SQL vs PRD 列名交叉验证

schema_block 注入时:
  如果 SQL 与 PRD 不匹配 → 追加 WARNING 告知 LLM 修正
```

### Data Flow

```
┌─────────┐    parse_prd_sections()    ┌──────────────┐
│   PRD   │ ──────────────────────────→│ prd_sections │
└─────────┘                            └──────┬───────┘
                                              │
                    ┌─────────────────────────┤
                    │                         │
                    ▼                         ▼
         generate_agent_md()      parse_data_model_columns()
                    │                         │
                    ▼                         ▼
           ┌──────────────┐         ┌────────────────────┐
           │  AGENT.md    │         │ _prd_table_columns │
           │ (含 Data     │         │ {table: [columns]} │
           │  Model 节)   │         └────────┬───────────┘
           └──────┬───────┘                  │
                  │                          │
                  ▼                          ▼
         _build_rules_block()     _validate_sql_against_prd()
                  │                          │
                  ▼                          ▼
         注入每个任务 prompt          post-task 验证
                                           +
                                  _refresh_schema_block()
                                  mismatch warning 注入
```

## 4. 关键实现

### 4.1 parse_data_model_columns()

解析 PRD Data Model section 的 markdown 表格，提取每个表的列名。

```python
def parse_data_model_columns(data_model_text: str) -> dict[str, list[str]]:
    # 解析 ### table_name 下的 | Column | Type | ... 表格
    # 返回 {"books": ["id", "title", "author", ...], ...}
```

- 纯 regex，不调用 LLM
- 跳过分隔行 (`|--`) 和表头 (`| Column`)
- 只提取合法标识符列名

### 4.2 validate_agent_md_sections()

验证 AGENT.md 是否包含所有必要 section。

```python
def validate_agent_md_sections(
    agent_md_path: str,
    required_sections: list[str],
    original_content: str = "",
) -> list[str]:
    # 检查文件是否存在、是否为空
    # 检查每个 required section 的 ## heading 是否存在
    # 检查内容是否大幅缩水 (< 50%)
```

检查项：
1. 文件是否存在
2. 内容是否为空
3. 每个 required section (`## Architecture`, `## Data Model` 等) 是否存在
4. 内容是否大幅缩水 (原始内容的 50% 以下)

### 4.3 Pre-task 验证 + Auto-restore

在 `execute()`, `resume()`, `retry_failed()` 的任务循环中，**每个任务执行前**运行验证：

```python
if self._scaffold_result and self._scaffold_result.required_sections:
    section_errors = validate_agent_md_sections(...)
    if section_errors:
        # 从 scaffold snapshot 恢复 AGENT.md
        Path(agent_md_path).write_text(original_agent_md)
        logger.info("AGENT.md restored from scaffold snapshot")
```

### 4.4 _validate_sql_against_prd()

对比生成的 `.sql` 文件中的列名与 PRD Data Model 中的列名。

```python
@staticmethod
def _validate_sql_against_prd(
    working_dir: str,
    prd_table_columns: dict[str, list[str]],
) -> list[str]:
    # 扫描 .sql 文件，提取 CREATE TABLE 的实际列名
    # 与 prd_table_columns 对比
    # 报告缺失的列
```

### 4.5 Schema Block Mismatch Warning

`_refresh_schema_block()` 在注入前验证 SQL 与 PRD 是否一致：

```python
if self._prd_table_columns:
    prd_errors = self._validate_sql_against_prd(...)
    if prd_errors:
        schema_text += "WARNING: Generated SQL does NOT match PRD Data Model!"
        schema_text += "The Data Model columns in AGENT.md are CORRECT."
```

打断反馈循环：即使错误 SQL 存在于磁盘，任务 prompt 会包含警告，告知 LLM 以 AGENT.md 中的 Data Model 为准。

### 4.6 ScaffoldResult 扩展

```python
@dataclass
class ScaffoldResult:
    output_dir: str
    agent_md_path: str
    detected_frameworks: list[str]
    rules_count: int
    original_agent_md: str = ""                    # AGENT.md 原始快照
    required_sections: list[str] = field(...)      # 必须保留的 sections
```

## 5. 变更文件

| 文件 | 变更 |
|------|------|
| `src/simple_agent/scaffold.py` | +`parse_data_model_columns()`, +`validate_agent_md_sections()`, Data Model 写入 AGENT.md, ScaffoldResult 扩展 |
| `src/simple_agent/dev_workflow.py` | +`_prd_table_columns` 字段, +`_validate_sql_against_prd()`, pre-task 验证 + auto-restore, schema_block mismatch warning |
| `src/simple_agent/prompts.py` | schema_injection_template 增加 Data Model 优先声明 |
| `src/simple_agent/messages.py` | +`guard_agent_md_section_missing`, +`guard_schema_mismatch` |
| `src/simple_agent/__init__.py` | 导出新符号 |
| `tests/unit/test_scaffold.py` | +10 tests |
| `tests/unit/test_workflow.py` | +4 tests |

**总计**: +293 行, 14 个新测试, 7 个文件

## 6. 测试覆盖

| 测试 | 验证内容 |
|------|----------|
| `test_parse_data_model_columns_basic` | 解析单表列名 |
| `test_parse_data_model_columns_multiple_tables` | 解析多表 |
| `test_parse_data_model_columns_empty` | 空输入返回空 |
| `test_generate_agent_md_includes_data_model` | AGENT.md 包含 Data Model |
| `test_generate_agent_md_without_data_model` | 无 Data Model 时向后兼容 |
| `test_validate_agent_md_sections_all_present` | 所有 section 存在时无错误 |
| `test_validate_agent_md_sections_missing` | section 缺失时报错 |
| `test_validate_agent_md_sections_deleted_file` | 文件删除时报错 |
| `test_validate_agent_md_sections_shrunk` | 内容缩水时报错 |
| `test_run_scaffold_captures_original_content` | scaffold 快照正确保存 |
| `test_validate_sql_against_prd_match` | SQL 匹配时无错误 |
| `test_validate_sql_against_prd_missing_columns` | 列名不匹配时报告缺失 |
| `test_validate_sql_against_prd_no_prd` | 空 PRD 列名时向后兼容 |
| `test_refresh_schema_block_includes_mismatch_warning` | 不匹配时注入 WARNING |

## 7. 经验教训

### 约束丢失的本质

Vibe Coding 工作流的核心矛盾是 LLM 自由度 vs 工程约束。问题不在于 LLM "不听话"，而在于**约束信息是否真正到达了 LLM 的输入**。

检查信息流的方法：从最终执行的 prompt 开始反向追踪，看每一层传递是否完整。不能假设"PRD 写了约束 = LLM 知道约束"。

### Schema 反馈循环的危害

一旦错误进入系统并被标记为 "ground truth"，后续所有任务都会基于错误信息工作。这种正反馈循环比单点错误严重得多，因为：

1. 错误会传播到所有下游文件
2. 验证机制本身（schema_block）变成了错误的放大器
3. 重试机制无法修复，因为每次重试都看到同样的错误 "ground truth"

解法：在 feedback loop 中注入校验信号（mismatch warning），让 LLM 知道当前 schema 可能是错误的。

### Scaffold Snapshot 的价值

保存 AGENT.md 原始快照，使得任务执行期间的任何 LLM 修改（包括意外删除、截断、重写）都可以自动恢复。这把 AGENT.md 从"可修改的文件"变为"engine 管控的不可变约束源"。

## 8. 后续方向

- **更多 PRD section 注入**: Features、Error Handling、Acceptance Criteria 等是否也需要写入 AGENT.md
- **Task description 增强**: Plan 分解时保留更多 PRD 细节，避免摘要丢失约束
- **Contract 生成与 Data Model 关联**: Contract 中的方法签名应自动校验列名与 Data Model 一致
- **性能优化**: `_validate_sql_against_prd()` 在大项目中的 SQL 文件扫描效率
