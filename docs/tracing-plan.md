# 追踪机制添加计划

## 一、现状分析

### 1.1 现有代码结构

```
agent-team/
├── agent_framework.py      # 核心 Agent 框架
│   ├── BaseAgent           # Agent 基类
│   ├── CoordinatorAgent    # 协调 Agent
│   └── AgentOrchestrator   # 编排器
├── swarm_agent.py          # LangGraph 状态机
│   ├── supervisor_node     # 协调员节点
│   ├── tech_node           # 技术支持节点
│   ├── order_node          # 订单查询节点
│   ├── refund_node         # 退款售后节点
│   └── product_node        # 产品咨询节点
└── skills/                 # 工具模块
    ├── knowledge_base.py
    ├── order.py
    ├── product.py
    └── refund.py
```

### 1.2 当前日志方式

现有代码使用 `print()` 语句进行简单日志输出：
- `print(f"【初始化】正在构建 {self.role}({self.name})...")`
- `print(f"【{self.role}】接收任务: {input_text[:50]}...")`
- `print(f"【协调员】分析需求并分配任务")`

**问题**：
- 无结构化日志
- 无时间戳
- 无调用链追踪
- 无性能指标
- 无持久化存储

---

## 二、追踪机制设计

### 2.1 追踪架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Trace (追踪)                            │
│  - trace_id: 唯一标识                                        │
│  - workflow_name: 工作流名称                                 │
│  - start_time / end_time: 时间戳                            │
│  - metadata: 元数据                                          │
│  - spans: Span 列表                                          │
├─────────────────────────────────────────────────────────────┤
│                      Span (跨度)                             │
│  - span_id: 唯一标识                                         │
│  - parent_id: 父 Span ID                                     │
│  - span_type: 类型 (agent/llm/tool/handoff)                 │
│  - name: 名称                                                │
│  - start_time / end_time: 时间戳                            │
│  - input / output: 输入输出                                  │
│  - metadata: 元数据                                          │
│  - status: 状态 (success/error)                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Span 类型定义

| Span 类型 | 说明 | 添加位置 |
|-----------|------|----------|
| `agent` | Agent 执行 | BaseAgent.ainvoke |
| `llm` | LLM 调用 | llm.invoke/ainvoke |
| `tool` | 工具调用 | BaseAgent._call_tools |
| `handoff` | Agent 交接 | CoordinatorAgent.analyze_and_assign |
| `workflow` | 工作流 | AgentOrchestrator.run, process_question |

### 2.3 追踪数据结构

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum
import uuid

class SpanType(Enum):
    AGENT = "agent"
    LLM = "llm"
    TOOL = "tool"
    HANDOFF = "handoff"
    WORKFLOW = "workflow"

class SpanStatus(Enum):
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"

@dataclass
class Span:
    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: Optional[str] = None
    span_type: SpanType = SpanType.AGENT
    name: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    input: Any = None
    output: Any = None
    metadata: dict = field(default_factory=dict)
    status: SpanStatus = SpanStatus.RUNNING
    
    @property
    def duration_ms(self) -> int:
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0

@dataclass
class Trace:
    trace_id: str = field(default_factory=lambda: f"trace_{uuid.uuid4().hex[:16]}")
    workflow_name: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    spans: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
```

---

## 三、添加位置分析

### 3.1 agent_framework.py 添加位置

| 位置 | 方法 | 追踪类型 | 追踪内容 |
|------|------|----------|----------|
| 1 | `BaseAgent.__init__` | - | 记录 Agent 初始化信息 |
| 2 | `BaseAgent._call_tools` | `tool` | 工具调用追踪 |
| 3 | `BaseAgent.ainvoke` | `agent` | Agent 执行追踪 |
| 4 | `CoordinatorAgent.analyze_and_assign` | `handoff` | 任务分配追踪 |
| 5 | `AgentOrchestrator.execute_task` | `agent` | 任务执行追踪 |
| 6 | `AgentOrchestrator.run` | `workflow` | 整体流程追踪 |
| 7 | `AgentOrchestrator._summarize_results` | `llm` | 汇总 LLM 调用追踪 |

### 3.2 swarm_agent.py 添加位置

| 位置 | 方法 | 追踪类型 | 追踪内容 |
|------|------|----------|----------|
| 1 | `process_question` | `workflow` | 问题处理流程追踪 |
| 2 | `supervisor_node` | `agent` + `llm` | 协调员节点追踪 |
| 3 | `tech_node` | `agent` + `llm` | 技术支持节点追踪 |
| 4 | `order_node` | `agent` + `llm` | 订单查询节点追踪 |
| 5 | `refund_node` | `agent` + `llm` | 退款售后节点追踪 |
| 6 | `product_node` | `agent` + `llm` | 产品咨询节点追踪 |

### 3.3 skills/ 目录添加位置

| 文件 | 函数 | 追踪类型 | 追踪内容 |
|------|------|----------|----------|
| knowledge_base.py | `search_knowledge_base` | `tool` | 知识库搜索追踪 |
| order.py | `query_order` | `tool` | 订单查询追踪 |
| product.py | `get_product_info` | `tool` | 产品信息追踪 |
| refund.py | `get_refund_policy` | `tool` | 退款政策追踪 |

---

## 四、实现方案

### 4.1 新建追踪模块

创建 `tracing/` 目录：

```
agent-team/
├── tracing/
│   ├── __init__.py          # 导出接口
│   ├── models.py            # 数据模型 (Trace, Span)
│   ├── context.py           # 追踪上下文管理
│   ├── handler.py           # 追踪处理器
│   ├── formatter.py         # 格式化输出
│   └── storage.py           # 存储接口 (可选)
```

### 4.2 核心接口设计

```python
# tracing/__init__.py

from contextlib import contextmanager
from .context import TraceContext
from .handler import TraceHandler

_handler = TraceHandler()

def start_trace(workflow_name: str, metadata: dict = None) -> TraceContext:
    """开始一个新的追踪"""
    return _handler.start_trace(workflow_name, metadata)

def end_trace(trace_id: str) -> None:
    """结束追踪"""
    _handler.end_trace(trace_id)

@contextmanager
def trace(workflow_name: str, metadata: dict = None):
    """追踪上下文管理器"""
    ctx = start_trace(workflow_name, metadata)
    try:
        yield ctx
    finally:
        end_trace(ctx.trace_id)

@contextmanager
def span(span_type: str, name: str, input_data: Any = None, metadata: dict = None):
    """Span 上下文管理器"""
    span_obj = _handler.start_span(span_type, name, input_data, metadata)
    try:
        yield span_obj
    except Exception as e:
        _handler.end_span(span_obj.span_id, status="error", error=str(e))
        raise
    else:
        _handler.end_span(span_obj.span_id)
```

### 4.3 使用示例

**修改前 (agent_framework.py)：**
```python
async def ainvoke(self, input_text):
    print(f"\n【{self.role}】接收任务: {input_text[:50]}...")
    
    tool_results = self._call_tools(input_text)
    # ...
    
    result = await llm.ainvoke(messages)
    
    print(f"【{self.role}】任务完成")
    return {"output": result.content}
```

**修改后：**
```python
async def ainvoke(self, input_text):
    with span("agent", f"{self.name}.ainvoke", input_data=input_text, 
              metadata={"role": self.role}) as s:
        
        tool_results = self._call_tools(input_text)
        s.metadata["tool_calls"] = len(tool_results)
        
        # ...
        
        result = await llm.ainvoke(messages)
        
        s.output = result.content[:100] + "..."
        return {"output": result.content}
```

---

## 五、任务清单

### 5.1 创建追踪模块

| 序号 | 任务 | 文件 | 优先级 |
|------|------|------|--------|
| 1 | 创建数据模型 | `tracing/models.py` | 高 |
| 2 | 创建上下文管理 | `tracing/context.py` | 高 |
| 3 | 创建追踪处理器 | `tracing/handler.py` | 高 |
| 4 | 创建格式化输出 | `tracing/formatter.py` | 中 |
| 5 | 创建导出接口 | `tracing/__init__.py` | 高 |

### 5.2 集成到 agent_framework.py

| 序号 | 任务 | 方法 | 优先级 |
|------|------|------|--------|
| 1 | 添加 Agent 执行追踪 | `BaseAgent.ainvoke` | 高 |
| 2 | 添加工具调用追踪 | `BaseAgent._call_tools` | 高 |
| 3 | 添加任务分配追踪 | `CoordinatorAgent.analyze_and_assign` | 高 |
| 4 | 添加任务执行追踪 | `AgentOrchestrator.execute_task` | 高 |
| 5 | 添加工作流追踪 | `AgentOrchestrator.run` | 高 |
| 6 | 添加汇总追踪 | `AgentOrchestrator._summarize_results` | 中 |

### 5.3 集成到 swarm_agent.py

| 序号 | 任务 | 方法 | 优先级 |
|------|------|------|--------|
| 1 | 添加工作流追踪 | `process_question` | 高 |
| 2 | 添加协调员追踪 | `supervisor_node` | 高 |
| 3 | 添加专家节点追踪 | `tech_node`, `order_node` 等 | 中 |

### 5.4 集成到 skills/

| 序号 | 任务 | 文件 | 优先级 |
|------|------|------|--------|
| 1 | 添加工具追踪装饰器 | `tracing/decorators.py` | 中 |
| 2 | 应用到各工具函数 | `skills/*.py` | 低 |

---

## 六、输出格式

### 6.1 控制台输出

```
┌─────────────────────────────────────────────────────────────┐
│ Trace: trace_abc123                                         │
│ Workflow: Customer Service Flow                             │
│ Duration: 2345ms                                            │
├─────────────────────────────────────────────────────────────┤
│ ┌─ [agent] supervisor (156ms)                               │
│ │  └─ [llm] classify_question (142ms)                      │
│ ├─ [handoff] transfer_to_tech_agent (5ms)                  │
│ └─ [agent] tech_agent (892ms)                              │
│    └─ [llm] generate_response (876ms)                      │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 JSON 输出

```json
{
  "trace_id": "trace_abc123",
  "workflow_name": "Customer Service Flow",
  "start_time": "2025-03-02T10:30:00.000Z",
  "end_time": "2025-03-02T10:30:02.345Z",
  "duration_ms": 2345,
  "spans": [
    {
      "span_id": "span_001",
      "span_type": "agent",
      "name": "supervisor",
      "start_time": "2025-03-02T10:30:00.000Z",
      "end_time": "2025-03-02T10:30:00.156Z",
      "duration_ms": 156,
      "status": "success"
    }
  ]
}
```

---

## 七、验收标准

1. ✅ 所有 Agent 执行都有追踪记录
2. ✅ 所有 LLM 调用都有追踪记录
3. ✅ 所有工具调用都有追踪记录
4. ✅ 追踪数据包含时间戳和耗时
5. ✅ 支持控制台格式化输出
6. ✅ 支持 JSON 格式导出
7. ✅ 不影响现有功能正常运行
