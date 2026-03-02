# IT 审计完整流程使用指南

## 📋 概述

本指南介绍如何使用 IT 审计系统的完整流程，包括：
- **模块 1**：审计项收集（从 Excel 导入）
- **模块 2**：制度要求筛选（向量+LLM 两阶段）
- **自动报告**：生成完整的分析报告

## 🎯 快速开始

### 方式 1：使用配置文件（推荐）

```bash
# 使用正式环境配置
python run_full_pipeline.py --config formal

# 使用测试环境配置
python run_full_pipeline.py --config test
```

### 方式 2：直接指定参数

```bash
python run_full_pipeline.py \
    --db "knowledge-work-plugins/it-audit/data/it_audit.db" \
    --output "knowledge-work-plugins/it-audit/output" \
    --excel "path/to/audit_items.xlsx"
```

## 📁 数据库配置

系统支持多套数据库环境，通过配置文件管理：

### 配置文件位置
`knowledge-work-plugins/it-audit/db_config.json`

### 配置示例
```json
{
  "formal": {
    "name": "正式环境",
    "db_path": "knowledge-work-plugins/it-audit/data/it_audit.db",
    "output_dir": "knowledge-work-plugins/it-audit/output",
    "description": "生产环境数据库"
  },
  "test": {
    "name": "测试环境",
    "db_path": "tests/test_data/test_it_audit.db",
    "output_dir": "tests/output",
    "description": "测试环境数据库"
  },
  "dev": {
    "name": "开发环境",
    "db_path": "dev/it_audit_dev.db",
    "output_dir": "dev/output",
    "description": "开发环境数据库"
  }
}
```

## 🚀 使用方法

### 1. 完整流程（模块 1 + 模块 2）

**使用配置文件：**
```bash
python run_full_pipeline.py \
    --config formal \
    --excel "docs/IT 审计项.xlsx"
```

**直接指定参数：**
```bash
python run_full_pipeline.py \
    --db "knowledge-work-plugins/it-audit/data/it_audit.db" \
    --output "knowledge-work-plugins/it-audit/output" \
    --excel "docs/IT 审计项.xlsx"
```

### 2. 仅运行模块 2（已有审计项）

**使用配置文件：**
```bash
python run_full_pipeline.py --config formal
```

**直接指定参数：**
```bash
python run_full_pipeline.py \
    --db "knowledge-work-plugins/it-audit/data/it_audit.db" \
    --output "knowledge-work-plugins/it-audit/output"
```

### 3. 强制全量重新筛选

```bash
python run_full_pipeline.py \
    --config formal \
    --force-full
```

## 📊 参数说明

### 必需参数（二选一）

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--config` | `-c` | 使用配置文件中的环境 | `--config formal` |
| `--db` | `-d` | 直接指定数据库路径 | `--db "path/to/db.db"` |

### 可选参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--excel` | `-e` | Excel 文件路径（模块 1 输入） | 无 |
| `--output` | `-o` | 输出目录 | 配置文件中指定 |
| `--force-full` | `-f` | 强制全量筛选 | 增量模式 |
| `--stats` | `-s` | 仅显示统计信息 | 执行筛选 |

## 📈 输出内容

### 1. 控制台输出

**模块 1 输出：**
```
======================================================================
模块 1：审计项收集
======================================================================
开始收集审计项：docs/IT 审计项.xlsx
导入批次：20260302-143025
------------------------------------------------------------
✓ 总审计项数：293
✓ 新增审计项：157
✓ 跳过已有：136
✓ 错误：0
⏱️  耗时：12.34 秒
```

**模块 2 输出：**
```
======================================================================
模块 2：制度要求筛选（向量+LLM 两阶段）
======================================================================
增量筛选模式：已筛选 136 条，待筛选 157 条

=== 阶段 1：向量语义筛选 ===
筛选完成:
  高置信度（直接确定）: 0 条
  中置信度（需 LLM 确认）: 0 条
  低置信度（跳过）: 157 条

=== 阶段 2：LLM 校验向量模型分类 ===
LLM 校验完成，共处理 135 条，总耗时：334.95 秒

======================================================================
模块 2 完成
======================================================================
✓ 总处理：293 条
✓ 高置信度：1 条（直接确认）
✓ 中置信度：135 条（LLM 校验）
✓ LLM 校验：135 条
✓ LLM 修正：37 条
⏱️  耗时：377.42 秒
```

### 2. 分析报告

**HTML 报告包含：**
- 统计概览卡片
- LLM 校验统计（确认数、修正数、修正率）
- 类型分布饼图
- 筛选结果明细表格（支持筛选、排序）
- 向量建议 → 最终类型对比

**CSV 报告包含：**
- 完整的筛选结果数据
- 可用于进一步分析

## 🔄 增量筛选机制

**默认行为（推荐）：**
- ✅ 自动跳过已筛选的审计项
- ✅ 只处理新导入的审计项
- ✅ 节省时间和 LLM 调用成本

**强制全量模式：**
- 使用 `--force-full` 参数
- 重新筛选所有审计项
- 适用于模型改进后的重新评估

## 📋 典型使用场景

### 场景 1：首次导入并筛选

```bash
# 使用正式环境
python run_full_pipeline.py \
    -c formal \
    -e "docs/IT 审计项.xlsx"
```

### 场景 2：新增审计项后筛选

```bash
# 自动增量模式，只处理新增项
python run_full_pipeline.py \
    -c formal \
    -e "docs/new_items.xlsx"
```

### 场景 3：模型改进后重新筛选

```bash
# 强制全量重新筛选
python run_full_pipeline.py \
    -c formal \
    -f
```

### 场景 4：查看统计信息

```bash
# 不执行筛选，仅查看当前统计
python run_full_pipeline.py \
    -c formal \
    --stats
```

## ⚙️ 环境配置

### 1. 创建配置文件

在 `knowledge-work-plugins/it-audit/` 目录下创建 `db_config.json`：

```json
{
  "formal": {
    "name": "正式环境",
    "db_path": "knowledge-work-plugins/it-audit/data/it_audit.db",
    "output_dir": "knowledge-work-plugins/it-audit/output"
  },
  "test": {
    "name": "测试环境",
    "db_path": "tests/test_data/test_it_audit.db",
    "output_dir": "tests/output"
  }
}
```

### 2. 配置 LLM API

创建 `.env` 文件（项目根目录）：

```bash
# LLM API 配置
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_API_KEY=your_api_key_here
ARK_CHAT_MODEL=general-pro-32k-250115
```

## 📊 性能参考

**测试数据：** 293 条审计项

| 阶段 | 处理数量 | 耗时 | 说明 |
|------|---------|------|------|
| 模块 1 | 293 条 | ~12 秒 | Excel 导入 |
| 模块 2-阶段 1 | 293 条 | ~25 秒 | 向量筛选 |
| 模块 2-阶段 2 | 135 条 | ~335 秒 | LLM 校验（20 条/批） |
| **总计** | 293 条 | **~372 秒** | 约 6.2 分钟 |

## ⚠️ 注意事项

1. **数据库选择**：
   - 正式环境：`knowledge-work-plugins/it-audit/data/it_audit.db`
   - 测试环境：`tests/test_data/test_it_audit.db`
   - 通过配置文件或直接参数指定

2. **增量筛选**：
   - 基于 `policy_screening_results` 表中的 `item_id`
   - 已筛选的审计项会自动跳过

3. **LLM 调用**：
   - 需要配置 LLM API
   - 中置信度项才会调用 LLM（约占 30-50%）

4. **输出报告**：
   - HTML 报告：可视化展示，支持交互
   - CSV 报告：用于数据分析和导出

## 📚 相关文档

- [模块 1 设计文档](docs/modules/module1-collector.md)
- [模块 2 设计文档](docs/modules/module2-checker.md)
- [LLM 分析方案](docs/modules/phase2-llm-analysis-plan-revised.md)
- [测试场景](docs/testing/test-scenarios.md)

## ✅ 完成标志

运行成功后，你会看到：
```
✅ 所有流程完成！
📄 报告位置：knowledge-work-plugins/it-audit/output/screening_report_20260302_143025.html
```
