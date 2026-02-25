# LLM校验功能 Spec

## Why
设计文档明确要求：向量模型只能计算语义相似度，无法进行逻辑判断。需要LLM对清洗结果进行二次校验，避免错误合并。

## What Changes
- 新增 `llm_verifier.py` 模块
- 实现LLM批量校验功能
- 整合到清洗流程：向量匹配 → LLM校验 → 入库

## Impact
- Affected code: 
  - `knowledge-work-plugins/it-audit/skills/1-audit-item-collector/scripts/llm_verifier.py` (新建)
  - `knowledge-work-plugins/it-audit/skills/1-audit-item-collector/scripts/cleaner.py` (修改)

## ADDED Requirements

### Requirement: LLM校验模块
系统应提供LLM校验模块，对向量模型的匹配结果进行逻辑校验。

#### Scenario: 审核合并建议
- **WHEN** 向量模型输出合并建议JSON
- **THEN** LLM审核每条建议，判断是否应该合并

#### Scenario: 输出审核意见
- **WHEN** LLM完成审核
- **THEN** 输出JSON格式的审核意见，包含adjustments列表

### Requirement: 迭代审核流程
系统应支持迭代审核，直到LLM确认OK。

#### Scenario: 需要调整
- **WHEN** LLM审核结果为 need_revision
- **THEN** 根据LLM意见调整JSON，再次提交审核

#### Scenario: 审核通过
- **WHEN** LLM审核结果为 approved
- **THEN** 可以执行入库操作

## MODIFIED Requirements

### Requirement: 清洗流程主程序
清洗流程应整合LLM校验环节。

#### Scenario: 完整清洗流程
- **WHEN** 用户执行清洗
- **THEN** 系统执行：Excel解析 → 向量匹配 → LLM校验 → 输出最终结果
