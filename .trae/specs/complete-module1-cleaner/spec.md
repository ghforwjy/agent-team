# 模块一清洗流程完善 Spec

## Why
语义匹配模块已实现，需要完善数据库结构和清洗流程主程序，实现完整的审计项清洗入库功能。

## What Changes
- 新增 `audit_procedures` 表，支持审计项与审计动作分离
- 创建清洗流程主程序 `cleaner.py`
- 支持从Excel导入 → 向量匹配 → 输出JSON建议文档

## Impact
- Affected code: 
  - `knowledge-work-plugins/it-audit/skills/1-audit-item-collector/scripts/db_manager.py`
  - `knowledge-work-plugins/it-audit/skills/1-audit-item-collector/scripts/cleaner.py` (新建)

## ADDED Requirements

### Requirement: 审计动作表
系统应提供独立的审计动作表，支持一个审计项对应多个审计动作。

#### Scenario: 新增审计动作
- **WHEN** 导入新底稿时发现审计项已存在但审计动作不同
- **THEN** 系统应在 audit_procedures 表中新增一条记录

### Requirement: 清洗流程主程序
系统应提供清洗流程主程序，整合Excel解析、语义匹配、JSON输出。

#### Scenario: 完整清洗流程
- **WHEN** 用户提供Excel文件路径
- **THEN** 系统输出符合设计文档结构的JSON建议文档

## MODIFIED Requirements

### Requirement: 数据库管理模块
数据库管理模块应支持新的表结构。

#### Scenario: 审计动作CRUD
- **WHEN** 调用 insert_procedure 方法
- **THEN** 系统在 audit_procedures 表中插入记录
