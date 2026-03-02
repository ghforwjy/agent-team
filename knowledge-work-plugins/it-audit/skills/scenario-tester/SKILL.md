# IT审计场景测试器

## 功能概述

场景测试器用于对IT审计Agent进行常态化场景测试，验证各模块功能的正确性。

## 测试场景

### 模块1测试场景
- **审计项收集测试**: 验证Excel解析、数据清洗、数据库存储流程
- **数据分析测试**: 验证分析器统计功能、报告生成功能

### 模块2测试场景
- **制度要求提取测试**: 验证从制度文档中提取审计要求的准确性
- **合规检查测试**: 验证策略合规检查功能

## 使用方法

```bash
# 运行所有场景测试
python -m knowledge_work_plugins.it_audit.skills.scenario_tester.scripts.runner

# 运行指定模块测试
python -m knowledge_work_plugins.it_audit.skills.scenario_tester.scripts.runner --module 1
python -m knowledge_work_plugins.it_audit.skills.scenario_tester.scripts.runner --module 2

# 指定输出目录
python -m knowledge_work_plugins.it_audit.skills.scenario_tester.scripts.runner --output ./test_results
```

## 输出说明

测试结果默认输出到 `tests/output/` 目录，包含：
- 测试执行日志
- 测试结果报告
- 错误详情（如有）

## 依赖

- 模块1: `1-audit-item-collector`
- 模块2: `2-policy-compliance-checker`
- 测试数据库: `tests/fixtures/it_audit_test.db`
