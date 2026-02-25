# Tasks

- [x] Task 1: 更新数据库管理模块，支持 audit_procedures 表
  - [x] SubTask 1.1: 在 db_manager.py 中添加 create_procedures_table 方法
  - [x] SubTask 1.2: 添加 insert_procedure 方法
  - [x] SubTask 1.3: 添加 get_procedures_by_item 方法
  - [x] SubTask 1.4: 重新初始化数据库

- [x] Task 2: 创建清洗流程主程序 cleaner.py
  - [x] SubTask 2.1: 实现 clean_from_excel 方法，整合 Excel 解析和语义匹配
  - [x] SubTask 2.2: 实现从数据库读取已有审计项的功能
  - [x] SubTask 2.3: 输出符合设计文档结构的 JSON 文件

- [x] Task 3: 测试完整清洗流程
  - [x] SubTask 3.1: 使用训练材料中的 Excel 文件测试
  - [x] SubTask 3.2: 验证输出的 JSON 结构正确

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
