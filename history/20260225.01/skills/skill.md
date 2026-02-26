# 📚 Skills 工具库说明

## 目录
1. [什么是Skill？](#1-什么是skill)
2. [Skill列表](#2-skill列表)
3. [如何使用Skill](#3-如何使用skill)

---

## 1. 什么是Skill？

**Skill（技能/工具）** 是给Agent用的工具箱！

就像医生的工具箱：
- 🔧 听诊器 = 检查身体
- 💊 药方 = 开药物
- 🩺 体温计 = 量体温

在我们的系统中，每个Skill都是用 `@tool` 装饰器的Python函数。

---

## 2. Skill列表

### 2.1 `search_knowledge_base

**名称：** 知识库检索

**功能：** 在知识库中搜索相关技术信息

**参数：**
- `query` (str): 用户的技术问题描述

**返回：** 知识库中的相关信息

**使用场景：**
- 用户问APP登录问题
- 用户问APP崩溃问题
- 用户问技术故障问题

**示例：**
```python
result = search_knowledge_base("登录问题")
# 返回: 请检查您的用户名和密码是否正确...
```

---

### 2.2 `query_order

**名称：** 订单查询

**功能：** 查询订单信息

**参数：**
- `order_id` (str): 订单编号，格式为ORD开头加数字

**返回：** 订单的详细信息（状态、物流、金额等

**使用场景：**
- 用户问订单状态
- 用户问物流信息
- 用户查ORD001、ORD002等订单

**示例：**
```python
result = query_order("ORD001")
# 返回: 订单 ORD001 信息：
#        状态：已发货
#        物流：顺丰快递 SF1234567890
```

---

### 2.3 `get_product_info`

**名称：** 产品信息查询

**功能：** 获取产品信息

**参数：**
- `product_name` (str): 产品名称

**返回：** 产品的详细信息（价格、库存、规格等）

**使用场景：**
- 用户问无线蓝牙耳机多少钱
- 用户问智能手表功能
- 用户问库存情况

**示例：**
```python
result = get_product_info("无线蓝牙耳机")
# 返回: 无线蓝牙耳机 信息：
#        价格：¥299.00
#        库存：库存充足 (50件)
```

---

### 2.4 `get_refund_policy`

**名称：** 退款政策查询

**功能：** 获取退款和售后政策

**参数：** 无

**返回：** 完整的退款售后政策

**使用场景：**
- 用户问退款流程
- 用户问退货政策
- 用户问售后问题

**示例：**
```python
result = get_refund_policy()
# 返回: 退款售后政策：
#        1. 7天无理由退换...
```

---

## 3. 如何使用Skill？

### 3.1 在代码中导入

```python
from skills import search_knowledge_base, query_order

# 使用Skill
result = search_knowledge_base("登录问题")
print(result)
```

### 3.2 在Agent中使用

在 `swarm_agent.py` 中，每个专家Agent都有自己的Skill列表：

```python
tech_tools = [search_knowledge_base]  # 技术专家的工具箱
order_tools = [query_order]            # 订单专家的工具箱
```

---

## 4. Skill的特点

| 特点 | 说明 |
|------|------|
| 🔧 **模块化 | 每个Skill只做一件事 |
| 📝 **有文档 | 每个Skill都有详细的文档字符串 |
| 🎯 **可复用 | Skill可以被多个Agent使用 |
| 🚀 **易扩展 | 新增Skill很简单 |

---

## 5. 如何添加新的Skill？

只需要三步：

1. 在 `skills/` 目录下创建新文件（或在现有文件中添加）
2. 用 `@tool` 装饰器装饰函数
3. 在 `__init__.py` 中导出

```python
from langchain.tools import tool

@tool
def my_new_skill(param: str) -> str:
    """这是新Skill的说明文档
    
    Args:
        param: 参数说明
        
    Returns:
        返回值说明
    """
    # 实现逻辑
    return "结果"
```

---

## 总结

Skills就是给Agent用的工具箱，让Agent能：
- 📚 查知识库
- 📦 查订单
- 💰 查退款政策
- 🛒 查产品

每个Skill都是一个专业的工具！
