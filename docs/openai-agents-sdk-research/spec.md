# OpenAI Agents SDK 完整调研报告

## 一、调研概述

### 1.1 调研目标

本调研旨在全面了解 OpenAI Agents SDK 的核心功能与架构设计，为后续在 agent-team 项目中应用提供技术参考。

### 1.2 SDK 简介

OpenAI Agents SDK 是一个开源的 Python 库，用于构建代理式 AI 应用。它是 Swarm 框架的生产就绪版本，具有以下特点：

- **轻量级设计**：极少的抽象，学习曲线平缓
- **Python 优先**：使用内置语言特性编排和链式调用 Agent
- **生产就绪**：内置追踪、护栏、测试等企业级功能

### 1.3 核心原语

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenAI Agents SDK                        │
├─────────────────────────────────────────────────────────────┤
│  Agent        - 配备指令和工具的 LLM 实例                    │
│  Handoffs     - Agent 间控制权转移                           │
│  Guardrails   - 输入/输出护栏                                │
│  Tools        - 自定义/托管/MCP 工具                         │
│  Sessions     - 持久化对话记忆层                             │
│  Tracing      - 内置追踪和可视化                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、Agent 创建机制

### 2.1 基本配置

Agent 是 SDK 的核心构建块，是一个配置了指令和工具的 LLM 实例。

**核心属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | str | Agent 名称（必填） |
| `instructions` | str | 系统指令/角色设定 |
| `model` | str | 使用的模型（如 gpt-4o、gpt-5-nano） |
| `tools` | list | 可用工具列表 |
| `handoffs` | list | 可交接的其他 Agent |
| `mcp_servers` | list | MCP 服务器列表 |
| `model_settings` | ModelSettings | 模型参数配置 |
| `output_type` | type | 输出类型（支持 Pydantic 模型） |
| `input_guardrails` | list | 输入护栏 |
| `output_guardrails` | list | 输出护栏 |

### 2.2 创建示例

```python
from agents import Agent, ModelSettings, function_tool

@function_tool
def get_weather(city: str) -> str:
    """returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Haiku agent",
    instructions="Always respond in haiku form",
    model="gpt-5-nano",
    tools=[get_weather],
    model_settings=ModelSettings(
        temperature=0.7,
        max_tokens=500
    )
)
```

### 2.3 模型配置

**模型选择建议：**

| 模型 | 特点 | 适用场景 |
|------|------|----------|
| GPT-4o | 快速、准确 | 大多数场景 |
| o3-pro | 擅长复杂推理 | 复杂推理任务 |
| GPT-5-nano | 轻量、低成本 | 简单任务、护栏检查 |

**工具使用控制：**

```python
from agents import Agent, ModelSettings, StopAtTools

agent = Agent(
    name="Weather Agent",
    tools=[get_weather, sum_numbers],
    # 强制使用工具
    model_settings=ModelSettings(tool_choice="required"),
    # 工具输出直接返回（不经过 LLM 处理）
    tool_use_behavior="stop_on_first_tool",
    # 或针对特定工具停止
    tool_use_behavior=StopAtTools(stop_at_tool_names=["get_weather"])
)
```

**tool_choice 取值：**
- `auto`：LLM 自行决定（默认）
- `required`：强制使用工具
- `none`：禁止使用工具
- 具体工具名：强制使用指定工具

### 2.4 输出类型

支持 Pydantic 模型作为输出类型，实现结构化输出：

```python
from pydantic import BaseModel

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

agent = Agent(
    name="Calendar extractor",
    instructions="Extract calendar events from text",
    output_type=CalendarEvent,
)
```

### 2.5 动态指令

支持通过函数动态生成指令：

```python
def dynamic_instructions(context: RunContextWrapper[UserContext], agent: Agent) -> str:
    return f"The user's name is {context.context.name}. Help them with their questions."

agent = Agent[UserContext](
    name="Triage agent",
    instructions=dynamic_instructions,
)
```

### 2.6 生命周期钩子

支持观察 Agent 生命周期的各种事件：

```python
from agents import Agent, RunHooks, Runner

class LoggingHooks(RunHooks):
    async def on_agent_start(self, context, agent):
        print(f"Starting {agent.name}")

    async def on_llm_end(self, context, agent, response):
        print(f"{agent.name} produced {len(response.output)} output items")

    async def on_agent_end(self, context, agent, output):
        print(f"{agent.name} finished with usage: {context.usage}")

agent = Agent(name="Assistant", instructions="Be concise.")
result = await Runner.run(agent, "Explain quines", hooks=LoggingHooks())
```

### 2.7 第三方模型支持

通过 LiteLLM 集成第三方模型：

```python
from agents import Agent
from agents.extensions.models.litellm_model import LitellmModel

agent = Agent(
    name="Claude Agent",
    model=LitellmModel(
        model="anthropic/claude-opus-4-20250514",
        api_key="your-api-key",
    )
)
```

---

## 三、意图识别机制

### 3.1 实现原理

意图识别通过 LLM 的自然语言理解能力实现，主要依赖：

1. **系统指令**：定义 Agent 的职责范围
2. **工具描述**：帮助 LLM 理解何时调用工具
3. **Handoff 描述**：帮助 LLM 决定何时转交其他 Agent

### 3.2 分诊 Agent 设计

分诊 Agent 负责意图识别和路由：

```python
from agents import Agent, handoff

billing_agent = Agent(name="Billing agent")
refund_agent = Agent(name="Refund agent")

triage_agent = Agent(
    name="Triage agent",
    instructions="判断用户问题属于账单还是退款领域，并路由到相应的专业 Agent",
    handoffs=[billing_agent, handoff(refund_agent)]
)
```

### 3.3 Handoff 描述优化

使用 `handoff_description` 提供路由提示：

```python
billing_agent = Agent(
    name="Billing agent",
    handoff_description="处理账单查询、费用争议、发票请求"
)
```

### 3.4 推荐提示词前缀

SDK 提供推荐的提示词前缀，帮助 LLM 理解 Handoff：

```python
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

agent = Agent(
    name="Billing agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    <你的其他指令>.""",
)
```

---

## 四、多轮对话实现

### 4.1 Runner 机制

Runner 是执行 Agent 的核心组件：

```python
from agents import Agent, Runner

# 异步运行
result = await Runner.run(agent, "Your question")

# 同步运行
result = Runner.run_sync(agent, "Your question")

# 流式运行
result = Runner.run_streamed(agent, "Your question")
async for event in result.stream_events():
    print(event.type)
```

### 4.2 Agent 循环

Runner 内部执行循环：

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent Loop                             │
├─────────────────────────────────────────────────────────────┤
│  1. 调用 LLM，传入当前输入                                   │
│  2. LLM 产生输出                                            │
│  3. 如果是 final_output → 循环结束，返回结果                  │
│  4. 如果是 handoff → 更新当前 agent 和输入，重新循环          │
│  5. 如果是 tool calls → 执行工具，追加结果，重新循环          │
│  6. 如果超过 max_turns → 抛出 MaxTurnsExceeded 异常          │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 手动对话管理

使用 `to_input_list()` 手动管理对话历史：

```python
async def main():
    agent = Agent(name="Assistant", instructions="Reply very concisely.")

    # 第一轮
    result = await Runner.run(agent, "What city is the Golden Gate Bridge in?")
    print(result.final_output)  # San Francisco

    # 第二轮
    new_input = result.to_input_list() + [{"role": "user", "content": "What state is it in?"}]
    result = await Runner.run(agent, new_input)
    print(result.final_output)  # California
```

### 4.4 服务器托管对话

**使用 conversation_id：**

```python
from openai import AsyncOpenAI

client = AsyncOpenAI()
conversation = await client.conversations.create()
conv_id = conversation.id

result = await Runner.run(agent, user_input, conversation_id=conv_id)
```

**使用 previous_response_id：**

```python
previous_response_id = None

while True:
    result = await Runner.run(
        agent,
        user_input,
        previous_response_id=previous_response_id,
        auto_previous_response_id=True,
    )
    previous_response_id = result.last_response_id
```

---

## 五、上下文窗口管理

### 5.1 本地上下文

传递不暴露给 LLM 的敏感信息：

```python
from dataclasses import dataclass
from agents import Agent, Runner, RunContextWrapper, function_tool

@dataclass
class UserContext:
    user_id: str
    permissions: list

@function_tool
def get_user_data(wrapper: RunContextWrapper[UserContext]) -> str:
    ctx = wrapper.context
    return f"User {ctx.user_id} data"

agent = Agent[UserContext](
    name="DataAgent",
    tools=[get_user_data]
)

result = await Runner.run(
    agent, 
    "Get my data", 
    context=UserContext(user_id="123", permissions=["read"])
)
```

### 5.2 模型输入过滤器

在模型调用前编辑输入：

```python
from agents import RunConfig
from agents.run import CallModelData, ModelInputData

def drop_old_messages(data: CallModelData[None]) -> ModelInputData:
    # 只保留最近 5 条消息
    trimmed = data.model_data.input[-5:]
    return ModelInputData(input=trimmed, instructions=data.model_data.instructions)

result = Runner.run_sync(
    agent,
    "Explain quines",
    run_config=RunConfig(call_model_input_filter=drop_old_messages),
)
```

---

## 六、记忆管理体系

### 6.1 Session 概述

Session 提供自动化的对话记忆管理：

```python
from agents import Agent, Runner, SQLiteSession

agent = Agent(name="Assistant", instructions="Reply very concisely.")
session = SQLiteSession("conversation_123")

# 第一轮
result = await Runner.run(agent, "What city is the Golden Gate Bridge in?", session=session)
print(result.final_output)  # San Francisco

# 第二轮 - 自动记住之前的上下文
result = await Runner.run(agent, "What state is it in?", session=session)
print(result.final_output)  # California
```

### 6.2 Session 类型

| Session 类型 | 适用场景 | 说明 |
|--------------|----------|------|
| SQLiteSession | 本地开发、简单应用 | 内置、轻量、文件或内存存储 |
| AsyncSQLiteSession | 异步 SQLite | 基于 aiosqlite |
| RedisSession | 跨服务共享 | 低延迟分布式部署 |
| SQLAlchemySession | 生产环境 | 支持 SQLAlchemy 兼容数据库 |
| OpenAIConversationsSession | OpenAI 托管存储 | 使用 OpenAI Conversations API |
| EncryptedSession | 加密存储 | 包装其他 Session，支持 TTL |

### 6.3 Session 操作

```python
from agents import SQLiteSession

session = SQLiteSession("user_123", "conversations.db")

# 获取所有条目
items = await session.get_items()

# 添加新条目
await session.add_items([
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
])

# 移除并返回最近的条目
last_item = await session.pop_item()

# 清空 Session
await session.clear_session()
```

### 6.4 限制历史记录

```python
from agents import RunConfig, SessionSettings

result = await Runner.run(
    agent,
    "Summarize our recent discussion.",
    session=session,
    run_config=RunConfig(session_settings=SessionSettings(limit=50)),
)
```

### 6.5 自定义历史合并

```python
def keep_recent_history(history, new_input):
    # 只保留最近 10 条历史，然后追加新输入
    return history[-10:] + new_input

result = await Runner.run(
    agent,
    "Continue from the latest updates only.",
    session=session,
    run_config=RunConfig(session_input_callback=keep_recent_history),
)
```

---

## 七、工具调用机制

### 7.1 工具类型概览

| 工具类型 | 执行位置 | 说明 |
|----------|----------|------|
| Hosted OpenAI Tools | OpenAI 服务器 | WebSearchTool, FileSearchTool, CodeInterpreterTool 等 |
| Local Runtime Tools | 本地环境 | ComputerTool, ShellTool, ApplyPatchTool |
| Function Tools | 本地环境 | Python 函数包装 |
| Agents as Tools | 本地环境 | Agent 作为工具调用 |
| MCP Tools | MCP 服务器 | 标准化工具协议 |

### 7.2 自定义函数工具

```python
from agents import Agent, function_tool
from pydantic import BaseModel, Field

class Location(BaseModel):
    lat: float
    long: float

@function_tool
async def fetch_weather(location: Location) -> str:
    """Fetch the weather for a given location.

    Args:
        location: The location to fetch the weather for.
    """
    return "sunny"

# 使用 Pydantic Field 约束参数
@function_tool
def score_a(score: int = Field(..., ge=0, le=100, description="Score from 0 to 100")) -> str:
    return f"Score recorded: {score}"

agent = Agent(name="Assistant", tools=[fetch_weather, score_a])
```

### 7.3 工具超时配置

```python
import asyncio
from agents import function_tool, ToolTimeoutError

@function_tool(timeout=2.0, timeout_behavior="error_as_result")
async def slow_lookup(query: str) -> str:
    await asyncio.sleep(10)
    return f"Result for {query}"
```

### 7.4 工具错误处理

```python
from agents import function_tool, RunContextWrapper

def my_custom_error_function(context: RunContextWrapper, error: Exception) -> str:
    print(f"Tool call failed: {error}")
    return "An internal server error occurred. Please try again later."

@function_tool(failure_error_function=my_custom_error_function)
def get_user_profile(user_id: str) -> str:
    if user_id == "user_123":
        return "User profile retrieved."
    else:
        raise ValueError(f"Could not retrieve profile for {user_id}")
```

### 7.5 OpenAI 托管工具

```python
from agents import Agent, FileSearchTool, WebSearchTool, CodeInterpreterTool

agent = Agent(
    name="Assistant",
    tools=[
        WebSearchTool(),
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=["VECTOR_STORE_ID"],
        ),
        CodeInterpreterTool(tool_config=CodeInterpreter(
            container={"type": "auto"},
            type="code_interpreter"
        )),
    ],
)
```

### 7.6 Agent 作为工具

```python
from agents import Agent, Runner

spanish_agent = Agent(
    name="Spanish agent",
    instructions="Translate to Spanish"
)

orchestrator_agent = Agent(
    name="Orchestrator",
    instructions="You are a translation agent.",
    tools=[
        spanish_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate to Spanish"
        )
    ],
)
```

### 7.7 MCP 集成

**托管 MCP：**

```python
from agents import Agent, HostedMCPTool

agent = Agent(
    name="Assistant",
    tools=[
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "gitmcp",
                "server_url": "https://gitmcp.io/openai/codex",
                "require_approval": "never",
            }
        )
    ],
)
```

**本地 MCP (stdio)：**

```python
from agents import Agent
from agents.mcp import MCPServerStdio

async with MCPServerStdio(
    name="Filesystem Server",
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"],
    },
) as server:
    agent = Agent(name="Assistant", mcp_servers=[server])
    result = await Runner.run(agent, "List the files.")
```

**Streamable HTTP MCP：**

```python
from agents.mcp import MCPServerStreamableHttp

async with MCPServerStreamableHttp(
    name="HTTP Server",
    params={
        "url": "http://localhost:8000/mcp",
        "headers": {"Authorization": "Bearer token"},
    },
    cache_tools_list=True,
) as server:
    agent = Agent(name="Assistant", mcp_servers=[server])
```

---

## 八、Agent Teams (Swarm) 模式

### 8.1 Handoff 机制

Handoff 是 Agent 之间的控制权转移：

```python
from agents import Agent, handoff, RunContextWrapper

# 专业 Agent
billing_agent = Agent(name="Billing agent")
refund_agent = Agent(name="Refund agent")

# 回调函数
def on_handoff(ctx: RunContextWrapper[None]):
    print("Handoff called")

# 创建 Handoff
handoff_obj = handoff(
    agent=billing_agent,
    on_handoff=on_handoff,
    tool_name_override="transfer_to_billing",
    tool_description_override="Transfer to billing agent",
)

# 分诊 Agent
triage_agent = Agent(
    name="Triage agent",
    handoffs=[billing_agent, handoff(refund_agent)]
)
```

### 8.2 Handoff 输入

支持传递结构化数据：

```python
from pydantic import BaseModel

class EscalationData(BaseModel):
    reason: str

async def on_handoff(ctx: RunContextWrapper[None], input_data: EscalationData):
    print(f"Escalation reason: {input_data.reason}")

handoff_obj = handoff(
    agent=escalation_agent,
    on_handoff=on_handoff,
    input_type=EscalationData,
)
```

### 8.3 输入过滤器

控制传递给下一个 Agent 的输入：

```python
from agents import handoff
from agents.extensions import handoff_filters

handoff_obj = handoff(
    agent=faq_agent,
    input_filter=handoff_filters.remove_all_tools,
)
```

### 8.4 Handoff vs Agent-as-Tool

| 特性 | Handoff | Agent-as-Tool |
|------|---------|---------------|
| 控制权 | 完全转移 | 保留在编排者 |
| 对话历史 | 传递给下一个 Agent | 不传递 |
| 适用场景 | 模块化自治 | 集中式协调 |
| 可见性 | 较低 | 较高 |
| 返回值 | 无（继续对话） | 返回结果 |

### 8.5 编排模式

**Manager 模式 (Agent-as-Tool)：**

```python
booking_agent = Agent(...)
refund_agent = Agent(...)

customer_facing_agent = Agent(
    name="Customer-facing agent",
    instructions="Handle all user communication. Call tools when needed.",
    tools=[
        booking_agent.as_tool(tool_name="booking_expert", tool_description="..."),
        refund_agent.as_tool(tool_name="refund_expert", tool_description="..."),
    ],
)
```

**Handoff 模式：**

```python
triage_agent = Agent(
    name="Triage agent",
    instructions="Help users. Hand off to specialists when needed.",
    handoffs=[booking_agent, refund_agent],
)
```

### 8.6 架构示例

```
                    ┌─────────────────┐
                    │  Triage Agent   │
                    │   (分诊代理)     │
                    └────────┬────────┘
                             │ handoffs
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
      ┌───────────┐  ┌───────────┐  ┌───────────┐
      │ Science   │  │ History   │  │ Support   │
      │ Manager   │  │ Manager   │  │ Manager   │
      └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
            │              │              │
      ┌─────┼─────┐  ┌─────┼─────┐  ┌─────┼─────┐
      ▼     ▼     ▼  ▼     ▼     ▼  ▼     ▼     ▼
    Phys  Chem  Med Pol   War   Cul Order Refund Ticket
```

---

## 九、可视化监控

### 9.1 Tracing 概述

SDK 内置追踪功能，自动记录：
- 模型调用 (generation_span)
- 工具调用 (function_span)
- Agent 交接 (handoff_span)
- 护栏触发 (guardrail_span)
- Agent 运行 (agent_span)

### 9.2 使用 Trace

```python
from agents import Agent, Runner, trace

async def main():
    agent = Agent(name="Joke generator", instructions="Tell funny jokes.")

    with trace("Joke workflow"):
        first_result = await Runner.run(agent, "Tell me a joke")
        second_result = await Runner.run(agent, f"Rate this joke: {first_result.final_output}")
```

### 9.3 自定义 Span

```python
from agents import trace, custom_span

with trace("Workflow"):
    with custom_span("Research"):
        # 研究任务
        pass
    with custom_span("Generation"):
        # 生成任务
        pass
```

### 9.4 RunConfig 配置

```python
from agents import RunConfig

result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(
        workflow_name="My Workflow",
        trace_id="trace_123",
        group_id="conversation_456",
        tracing_disabled=False,
        trace_include_sensitive_data=True,
        trace_metadata={"user_id": "123"},
    ),
)
```

### 9.5 可视化图表

```python
from agents.extensions.visualization import draw_graph

draw_graph(triage_agent, filename="agent_graph")
```

### 9.6 Guardrails (护栏)

**输入护栏：**

```python
from agents import (
    Agent, GuardrailFunctionOutput, InputGuardrailTripwireTriggered,
    RunContextWrapper, Runner, TResponseInputItem, input_guardrail
)
from pydantic import BaseModel

class MathHomeworkOutput(BaseModel):
    is_math_homework: bool
    reasoning: str

guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking for math homework help.",
    output_type=MathHomeworkOutput,
)

@input_guardrail
async def math_guardrail(
    ctx: RunContextWrapper[None], 
    agent: Agent, 
    input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_math_homework,
    )

agent = Agent(
    name="Customer support agent",
    input_guardrails=[math_guardrail],
)
```

**执行模式：**

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| Parallel (默认) | 护栏与 Agent 并行执行 | 最佳延迟 |
| Blocking | 护栏完成后才执行 Agent | 成本优化、避免副作用 |

```python
@input_guardrail(run_in_parallel=False)
async def blocking_guardrail(ctx, agent, input):
    # Agent 会等待护栏完成
    ...
```

**输出护栏：**

```python
from agents import output_guardrail, OutputGuardrailTripwireTriggered

@output_guardrail
async def output_validator(ctx, agent, output):
    # 验证输出
    return GuardrailFunctionOutput(
        tripwire_triggered=not is_valid(output)
    )
```

**工具护栏：**

```python
from agents import (
    function_tool, tool_input_guardrail, tool_output_guardrail,
    ToolGuardrailFunctionOutput
)

@tool_input_guardrail
def block_secrets(data):
    args = json.loads(data.context.tool_arguments or "{}")
    if "sk-" in json.dumps(args):
        return ToolGuardrailFunctionOutput.reject_content("Remove secrets.")
    return ToolGuardrailFunctionOutput.allow()

@tool_output_guardrail
def redact_output(data):
    if "sk-" in str(data.output or ""):
        return ToolGuardrailFunctionOutput.reject_content("Sensitive data.")
    return ToolGuardrailFunctionOutput.allow()

@function_tool(
    tool_input_guardrails=[block_secrets],
    tool_output_guardrails=[redact_output],
)
def classify_text(text: str) -> str:
    return f"length:{len(text)}"
```

---

## 十、RunConfig 配置详解

### 10.1 配置选项

```python
from agents import RunConfig, SessionSettings

run_config = RunConfig(
    # 模型配置
    model="gpt-4o",
    model_provider=OpenAIProvider(),
    model_settings=ModelSettings(temperature=0.7),
    
    # Session 配置
    session_settings=SessionSettings(limit=50),
    session_input_callback=keep_recent_history,
    
    # 护栏配置
    input_guardrails=[...],
    output_guardrails=[...],
    handoff_input_filter=...,
    
    # 追踪配置
    tracing_disabled=False,
    tracing=TracingConfig(...),
    trace_include_sensitive_data=True,
    workflow_name="My Workflow",
    trace_id="trace_123",
    group_id="conversation_456",
    trace_metadata={"user_id": "123"},
    
    # 工具配置
    tool_error_formatter=format_rejection,
)
```

### 10.2 错误处理

```python
from agents import RunErrorHandlerInput, RunErrorHandlerResult

def on_max_turns(data: RunErrorHandlerInput[None]) -> RunErrorHandlerResult:
    return RunErrorHandlerResult(
        final_output="I couldn't finish within the turn limit.",
        include_in_history=False,
    )

result = Runner.run_sync(
    agent,
    "Analyze this long transcript",
    max_turns=3,
    error_handlers={"max_turns": on_max_turns},
)
```

---

## 十一、异常类型

| 异常 | 说明 |
|------|------|
| AgentsException | 所有异常的基类 |
| MaxTurnsExceeded | 超过最大轮数限制 |
| ModelBehaviorError | 模型产生意外输出 |
| ToolTimeoutError | 工具调用超时 |
| UserError | 用户代码错误 |
| InputGuardrailTripwireTriggered | 输入护栏触发 |
| OutputGuardrailTripwireTriggered | 输出护栏触发 |

---

## 十二、与现有项目集成建议

### 12.1 现有项目分析

| 组件 | 现状 | 集成建议 |
|------|------|----------|
| Agent 框架 | agent_framework.py | 可直接采用 SDK 模式 |
| Agent 实现 | finance_agent.py, legal_agent.py | 迁移到 SDK Agent 类 |
| Skills 系统 | skills/ 目录 | 通过 @function_tool 转换 |
| MCP 配置 | .mcp.json 文件 | 使用 SDK MCP 集成 |
| 多 Agent 协作 | 需要重构 | 采用 Handoff 或 Agent-as-Tool 模式 |

### 12.2 迁移步骤

1. **安装 SDK**：`pip install openai-agents`
2. **转换 Agent**：将现有 Agent 类迁移到 SDK Agent
3. **转换 Skills**：使用 @function_tool 装饰器
4. **集成 MCP**：使用 MCPServerStdio 或 HostedMCPTool
5. **添加护栏**：实现输入/输出护栏
6. **启用追踪**：配置 Tracing 和可视化

### 12.3 代码迁移示例

**现有代码：**

```python
class FinanceAgent:
    def __init__(self):
        self.name = "Finance Agent"
    
    def process(self, query):
        # 处理逻辑
        pass
```

**迁移后：**

```python
from agents import Agent, function_tool

@function_tool
def analyze_finances(query: str) -> str:
    """分析财务数据"""
    # 处理逻辑
    return "分析结果"

finance_agent = Agent(
    name="Finance Agent",
    instructions="你是一个财务分析专家",
    tools=[analyze_finances],
)
```

---

## 十三、参考资料

1. **官方文档**：https://openai.github.io/openai-agents-python/
2. **OpenAI Platform**：https://platform.openai.com/docs/
3. **MCP 协议**：https://modelcontextprotocol.io/
4. **LiteLLM**：https://docs.litellm.ai/
5. **GitHub 仓库**：https://github.com/openai/openai-agents-python

---

## 十四、版本信息

- SDK 版本：openai-agents (最新)
- 发布日期：2025年3月
- Python 版本要求：3.8+
