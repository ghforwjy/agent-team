# 审计项清洗结果分析工具 - 规格文档

## 项目概述

开发一个独立的数据分析程序，用于分析IT审计项清洗流程的结果，帮助用户直观了解清洗过程和结果是否合理。

## 核心功能需求

### 1. 数据展示功能（优先级：最高）

#### 1.1 审计项列表展示
- 展示最终得到的所有审计项
- 字段：ID、标题、维度、审计程序数量、来源记录数
- 支持按维度筛选
- 支持搜索/过滤

#### 1.2 审计动作列表展示
- 展示所有审计程序（动作）
- 字段：所属审计项ID、审计项标题、程序内容、来源
- 支持按审计项分组显示

### 2. 统计分析功能（优先级：高）

#### 2.1 基础统计
- 审计项总数
- 审计程序总数
- 维度分布统计
- 平均每个审计项的程序数

#### 2.2 清洗过程分析
- 各场景导入数据统计
- 新增 vs 复用审计项比例
- 新增审计程序数量

### 3. 数据对比功能（优先级：中）

#### 3.1 跨年度对比
- 2021 vs 2022 审计项对比
- 相似度分布分析
- 复用/新建决策分析

## 技术架构

### 目录结构
```
audit-analysis-tool/
├── spec.md              # 本规格文档
├── task_list.md         # 任务清单
├── checklist.md         # 验收检查清单
├── src/                 # 源代码
│   ├── __init__.py
│   ├── data_loader.py   # 数据加载模块
│   ├── models.py        # 数据模型
│   ├── analyzer.py      # 分析模块
│   ├── reporter.py      # 报告生成模块
│   └── cli.py           # 命令行界面
├── tests/               # 测试代码
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_analyzer.py
│   └── test_reporter.py
├── templates/           # HTML报告模板
│   └── report_template.html
└── main.py              # 程序入口
```

### 技术栈
- Python 3.8+
- SQLite3（读取清洗结果数据库）
- pandas（数据分析）
- jinja2（HTML模板）

## 数据模型

### AuditItem（审计项）
```python
{
    "id": int,
    "item_code": str,
    "title": str,
    "dimension": str,
    "procedure_count": int,
    "source_count": int,
    "procedures": List[AuditProcedure],
    "sources": List[ItemSource]
}
```

### AuditProcedure（审计程序/动作）
```python
{
    "id": int,
    "item_id": int,
    "item_title": str,  # 冗余字段，方便展示
    "procedure_text": str,
    "is_primary": bool,
    "source_type": str
}
```

## 界面设计

### 命令行界面
```bash
# 基础分析
python main.py --db-path <数据库路径>

# 生成HTML报告
python main.py --db-path <数据库路径> --output report.html

# 导出审计项列表
python main.py --db-path <数据库路径> --export-items items.csv

# 导出审计动作列表
python main.py --db-path <数据库路径> --export-procedures procedures.csv
```

### HTML报告结构
1. 概览仪表板（统计卡片）
2. 审计项列表（表格，可排序）
3. 审计动作列表（表格，按审计项分组）
4. 维度分布图表
5. 清洗过程分析

## 验收标准

### 功能验收
- [ ] 能正确读取清洗结果数据库
- [ ] 审计项列表展示完整、准确
- [ ] 审计动作列表展示完整、准确
- [ ] 统计数据计算正确
- [ ] HTML报告生成正常
- [ ] CSV导出功能正常

### 测试验收
- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] 代码覆盖率 > 80%

## 开发计划

按照模块逐个实现，每个模块包含：
1. 实现代码
2. 单元测试
3. 集成测试
4. 验收通过后再进入下一个模块

模块顺序：
1. 数据加载模块
2. 数据模型
3. 分析模块
4. 报告生成模块
5. CLI界面
6. 集成测试
