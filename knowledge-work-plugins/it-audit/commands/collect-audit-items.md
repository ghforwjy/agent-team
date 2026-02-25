---
name: collect-audit-items
description: 从Excel文件收集审计项并导入数据库
---

请帮我将Excel审计底稿导入到审计项数据库中。

## 使用方式

1. **提供Excel文件路径**
   ```
   请导入 训练材料/2021年网络安全专自查底稿.xls
   ```

2. **Agent将自动执行以下步骤**:
   - 分析Excel文件结构
   - 智能识别列名映射
   - 向您确认映射关系
   - 执行导入
   - 报告导入结果

## 支持的功能

- 自动识别表头位置
- 智能列名映射
- 重复检测
- 来源追溯记录
- 批次管理

## 相关文件

- Skill: [audit-item-collector](../skills/1-audit-item-collector/SKILL.md)
- 列名映射指南: [column-mapping-guide](../skills/1-audit-item-collector/references/column-mapping-guide.md)
