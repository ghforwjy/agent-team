# IT审计专家Agent - 文档导航

本文档目录包含IT审计专家Agent的设计、开发和测试相关文档。

## 文档清单

### 1. 设计方案
**[IT审计专家Agent设计方案.md](./IT审计专家Agent设计方案.md)**
- 整体架构设计
- 功能模块划分
- 技术选型说明
- 数据流程设计

### 2. 详细设计
**[模块一详细设计计划.md](./模块一详细设计计划.md)**
- 数据库表结构设计
- 审计项与审计动作分离方案
- 语义清洗流程详细设计
- API接口定义

### 3. 代码补充计划
**[模块1代码补充计划.md](./模块1代码补充计划.md)**
- 待补充功能清单
- 代码修改点说明
- 实现优先级排序

### 4. 测试场景设计
**[模块1测试场景设计计划.md](./模块1测试场景设计计划.md)**
- 5个测试场景详细说明
- 测试数据准备
- 预期结果定义

## 相关代码位置

### 核心模块代码
```
knowledge-work-plugins/it-audit/skills/1-audit-item-collector/scripts/
├── cleaner.py              # 清洗流程主程序
├── semantic_matcher.py     # 语义匹配模块
├── llm_verifier.py         # LLM校验模块
├── excel_parser.py         # Excel解析器
└── db_manager.py           # 数据库管理
```

### 测试程序
```
tests/
├── test_module1_cleaner.py           # 5个测试场景的主测试程序
├── test_data/
│   ├── test_it_audit.db             # 测试数据库
│   ├── audit_items_2021.xlsx        # 2021年测试数据
│   └── audit_items_2022.xlsx        # 2022年测试数据
└── results/                          # 测试结果输出目录
```

**运行测试命令：**
```bash
python tests/test_module1_cleaner.py
```

### 数据分析程序
```
audit-analysis-tool/
├── main.py                 # 分析工具入口
├── src/
│   ├── data_loader.py     # 数据加载
│   ├── analyzer.py        # 分析逻辑
│   ├── reporter.py        # 报告生成
│   └── cli.py             # 命令行接口
└── output/                # 分析报告输出目录
    ├── report.html        # HTML格式报告
    ├── items.csv          # 审计项导出
    └── procedures.csv     # 审计程序导出
```

**运行分析工具命令：**
```bash
# 生成HTML报告
python audit-analysis-tool/main.py --db-path tests/test_data/test_it_audit.db --group-by-item --output audit-analysis-tool/output/report.html

# 命令行查看统计
python audit-analysis-tool/main.py --db-path tests/test_data/test_it_audit.db --group-by-item
```

## 数据库位置

### 测试数据库
- **路径：** `tests/test_data/test_it_audit.db`
- **用途：** 运行测试场景时使用
- **内容：** 包含2021和2022年导入的审计项数据

### 正式数据库
- **路径：** `knowledge-work-plugins/it-audit/data/it_audit.db`
- **用途：** 生产环境使用（当前为空）

## 快速开始

1. **查看设计方案**：阅读 [IT审计专家Agent设计方案.md](./IT审计专家Agent设计方案.md)
2. **了解详细设计**：阅读 [模块一详细设计计划.md](./模块一详细设计计划.md)
3. **运行测试**：执行 `python tests/test_module1_cleaner.py`
4. **查看分析结果**：运行分析工具生成HTML报告

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-02-25 | 初始设计方案 |
| v2.0 | 2026-02-25 | 模块一详细设计 |
| v2.1 | 2026-02-26 | 添加测试场景和数据分析工具 |
