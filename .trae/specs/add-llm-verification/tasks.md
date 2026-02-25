# Tasks

- [x] Task 1: 创建LLM校验模块 llm_verifier.py
  - [x] SubTask 1.1: 实现 LLMVerifier 类，支持配置API
  - [x] SubTask 1.2: 实现 verify_merge_suggestions 方法，批量审核合并建议
  - [x] SubTask 1.3: 实现Prompt模板，符合设计文档结构
  - [x] SubTask 1.4: 解析LLM返回的JSON格式审核意见

- [x] Task 2: 修改清洗流程主程序 cleaner.py
  - [x] SubTask 2.1: 在 clean_from_excel 方法中集成LLM校验
  - [x] SubTask 2.2: 实现迭代审核逻辑（调整 → 再审核）
  - [x] SubTask 2.3: 输出最终审核通过的JSON

- [x] Task 3: 测试完整流程
  - [x] SubTask 3.1: 使用测试数据验证LLM校验功能
  - [x] SubTask 3.2: 验证迭代审核流程

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
