# 核心工具介绍

## LangChain - "积木盒子"

**LangChain是什么？**

想象你要搭一个机器人，LangChain就是给你准备好了各种积木：
- 连接大模型的积木
- 连接数据库的积木  
- 调用工具的积木
- 记忆对话的积木

**在代码中的使用：**

```python
from langchain_openai import ChatOpenAI  # 连接大模型的积木
from langchain.tools import tool          # 定义工具的装饰器

llm = ChatOpenAI(
    model="doubao-seed-2-0-mini-260215",  # 用哪个模型
    api_key="你的密钥",                        # 开门钥匙
    base_url="https://ark.cn-beijing.volces.com/api/v3",  # 地址
)
```

## LangGraph - "流程图画板"

**LangGraph是什么？**

想象你要画一个工作流程图：
```
开始 → 判断问题类型 → 分支1（技术问题） → 结束
                    ↓
                  分支2（订单问题） → 结束
```

LangGraph就是帮你画这种流程图的工具，让多个Agent像流水线一样工作！

## 技术栈总结

| 技术 | 用途 | 版本 |
|------|------|------|
| **Python** | 主要编程语言 | 3.10+ |
| **LangChain** | Agent框架和工具集成 | 0.3.x |
| **LangGraph** | 工作流状态管理 | 0.2.x |
| **豆包大模型** | 智能理解和生成 | doubao-seed-2-0-mini |
| **火山方舟API** | 大模型API服务 | v3 |

## 核心依赖

```
langchain
langchain-openai
langgraph
```
