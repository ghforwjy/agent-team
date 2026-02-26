
"""
真正的通用Agent框架 - 简化版
支持Skills和MCP工具的通用Agent基类
使用更简单、更可靠的实现方式
"""
import os
import json
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

ark_api_key = os.getenv("ARK_API_KEY").strip()
ark_base_url = os.getenv("ARK_BASE_URL").strip()
ark_chat_model = os.getenv("ARK_CHAT_MODEL").strip()

llm = ChatOpenAI(
    model=ark_chat_model,
    api_key=ark_api_key,
    base_url=ark_base_url,
    temperature=0.7
)


class BaseAgent:
    """
    真正的通用Agent基类
    支持Skills和MCP工具的通用Agent
    """
    
    def __init__(self, name, role, system_prompt, tools=None):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools or []
        self._build_prompt()
    
    def _build_prompt(self):
        """构建Agent提示词"""
        print(f"【初始化】正在构建 {self.role}({self.name})...")
        
        tool_descriptions = ""
        if self.tools:
            tool_descriptions = "\n你可以使用以下工具获取数据：\n"
            for tool in self.tools:
                tool_descriptions += f"- {tool.name}: {tool.description}\n"
        
        self.system_prompt_full = self.system_prompt + tool_descriptions
        
        tool_names = [t.name for t in self.tools]
        print(f"【初始化】{self.role}({self.name}) 构建完成，可用工具: {tool_names}")
    
    def _call_tools(self, text):
        """
        简单的工具调用逻辑
        分析文本，看是否需要调用工具
        """
        results = []
        
        if not self.tools:
            return results
        
        for tool in self.tools:
            tool_name = tool.name
            
            if tool_name == "search_market_info":
                industries = ["AI行业", "新能源汽车", "智能家居"]
                for industry in industries:
                    if industry in text:
                        result = tool.invoke(industry)
                        results.append(result)
            
            elif tool_name == "search_competitor_info":
                companies = ["OpenAI", "比亚迪", "特斯拉"]
                for company in companies:
                    if company in text:
                        result = tool.invoke(company)
                        results.append(result)
            
            elif tool_name == "search_technical_info":
                topics = ["大模型技术", "自动驾驶技术"]
                for topic in topics:
                    if topic in text:
                        result = tool.invoke(topic)
                        results.append(result)
            
            elif tool_name == "search_financial_info":
                topics = ["估值模型", "投资风险"]
                for topic in topics:
                    if topic in text:
                        result = tool.invoke(topic)
                        results.append(result)
        
        return results
    
    async def ainvoke(self, input_text):
        """
        异步调用Agent
        
        Args:
            input_text: 输入文本
            
        Returns:
            Agent执行结果
        """
        print(f"\n【{self.role}】接收任务: {input_text[:50]}...")
        
        tool_results = self._call_tools(input_text)
        
        augmented_input = input_text
        if tool_results:
            augmented_input = input_text + "\n\n参考数据：\n" + "\n".join(tool_results)
        
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=self.system_prompt_full),
            HumanMessage(content=augmented_input)
        ]
        
        result = await llm.ainvoke(messages)
        
        print(f"【{self.role}】任务完成")
        return {"output": result.content}
    
    def invoke(self, input_text):
        """
        同步调用Agent
        
        Args:
            input_text: 输入文本
            
        Returns:
            Agent执行结果
        """
        return asyncio.run(self.ainvoke(input_text))


class AgentConfig:
    """
    Agent配置类
    用于通过配置实例化不同的专家Agent
    """
    
    def __init__(self, name, role, system_prompt, tools=None, description=""):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.description = description
    
    def create_agent(self):
        """
        根据配置创建Agent实例
        
        Returns:
            BaseAgent实例
        """
        return BaseAgent(
            name=self.name,
            role=self.role,
            system_prompt=self.system_prompt,
            tools=self.tools
        )


class TaskAssignment:
    """任务分配类"""
    
    def __init__(self, agent_name, task_description, priority=1):
        self.agent_name = agent_name
        self.task_description = task_description
        self.priority = priority


class CoordinatorAgent(BaseAgent):
    """
    真正的协调Agent
    通过大模型分析需求、分解任务、指派给专家
    """
    
    def __init__(self, available_agents, name="coordinator", role="协调员"):
        self.available_agents = available_agents
        
        system_prompt = self._build_coordinator_prompt()
        
        super().__init__(
            name=name,
            role=role,
            system_prompt=system_prompt,
            tools=[]
        )
    
    def _build_coordinator_prompt(self):
        """构建协调员系统提示词"""
        agents_description = "\n".join([
            f"- {config.name}: {config.role} - {config.description}"
            for config in self.available_agents.values()
        ])
        
        json_template = '''{
    "task_assignments": [
        {
            "agent_name": "agent_name",
            "task_description": "详细的任务描述",
            "priority": 1
        }
    ],
    "explanation": "简要解释任务分配的理由"
}'''
        
        return f"""你是一位专业的任务协调员。你的职责是：
1. 分析用户的需求
2. 将复杂任务分解为多个子任务
3. 为每个子任务选择最合适的专家Agent
4. 生成任务分配计划

可用的专家Agent：
{agents_description}

请以JSON格式返回任务分配计划，格式如下：
{json_template}

注意：
- 只返回JSON，不要返回其他内容
- priority数字越小优先级越高
- 可以同时指派多个Agent并行执行
"""
    
    async def analyze_and_assign(self, user_request, previous_results=""):
        """
        分析用户需求并分配任务
        
        Args:
            user_request: 用户需求
            previous_results: 之前的调研结果（用于迭代）
            
        Returns:
            任务分配列表
        """
        print(f"\n{'='*70}")
        print(f"【协调员】分析需求并分配任务")
        print(f"{'='*70}")
        
        input_text = user_request
        if previous_results:
            input_text = f"用户原始需求: {user_request}\n\n之前的调研结果: {previous_results}\n\n请根据以上信息继续分析并分配任务。"
        
        result = await self.ainvoke(input_text)
        content = result["output"]
        
        try:
            decision = json.loads(content)
            task_assignments_data = decision.get("task_assignments", [])
            explanation = decision.get("explanation", "")
            
            task_assignments = []
            for ta_data in task_assignments_data:
                ta = TaskAssignment(
                    agent_name=ta_data["agent_name"],
                    task_description=ta_data["task_description"],
                    priority=ta_data.get("priority", 1)
                )
                task_assignments.append(ta)
            
            print(f"【协调员】任务分配理由: {explanation}")
            print(f"【协调员】分配了 {len(task_assignments)} 个任务")
            
            return task_assignments
            
        except Exception as e:
            print(f"【协调员】解析任务分配失败: {e}")
            print(f"【协调员】原始响应: {content}")
            
            return []


class AgentOrchestrator:
    """
    Agent编排器
    管理多个Agent的执行和结果汇总
    """
    
    def __init__(self, coordinator, agent_configs):
        self.coordinator = coordinator
        self.agent_configs = agent_configs
        self.agent_instances = {}
        
        self._initialize_agents()
    
    def _initialize_agents(self):
        """初始化所有专家Agent实例"""
        print(f"\n【编排器】初始化专家Agent...")
        
        for name, config in self.agent_configs.items():
            agent = config.create_agent()
            self.agent_instances[name] = agent
        
        print(f"【编排器】所有专家Agent初始化完成")
    
    async def execute_task(self, task_assignment):
        """
        执行单个任务
        
        Args:
            task_assignment: 任务分配
            
        Returns:
            任务执行结果
        """
        agent_name = task_assignment.agent_name
        
        if agent_name not in self.agent_instances:
            return {
                "agent_name": agent_name,
                "success": False,
                "error": f"Agent {agent_name} 不存在"
            }
        
        agent = self.agent_instances[agent_name]
        
        try:
            result = await agent.ainvoke(task_assignment.task_description)
            
            return {
                "agent_name": agent_name,
                "agent_role": agent.role,
                "success": True,
                "output": result["output"],
                "task_description": task_assignment.task_description
            }
        except Exception as e:
            return {
                "agent_name": agent_name,
                "success": False,
                "error": str(e)
            }
    
    async def execute_tasks_concurrently(self, task_assignments):
        """
        并发执行多个任务
        
        Args:
            task_assignments: 任务分配列表
            
        Returns:
            任务执行结果列表
        """
        print(f"\n【编排器】并发执行 {len(task_assignments)} 个任务...")
        
        tasks = [
            self.execute_task(ta)
            for ta in task_assignments
        ]
        
        results = await asyncio.gather(*tasks)
        
        print(f"【编排器】所有任务执行完成")
        
        return results
    
    async def run(self, user_request, max_rounds=2):
        """
        运行完整的调研流程
        
        Args:
            user_request: 用户需求
            max_rounds: 最大轮数
            
        Returns:
            最终调研报告
        """
        all_results = []
        previous_summary = ""
        
        for round_num in range(1, max_rounds + 1):
            print(f"\n{'='*80}")
            print(f"【第 {round_num} 轮调研】")
            print(f"{'='*80}")
            
            task_assignments = await self.coordinator.analyze_and_assign(
                user_request,
                previous_summary
            )
            
            if not task_assignments:
                print(f"【编排器】没有任务分配，结束调研")
                break
            
            results = await self.execute_tasks_concurrently(task_assignments)
            
            all_results.extend(results)
            
            summary = self._summarize_results(user_request, all_results)
            previous_summary = summary
        
        return previous_summary
    
    def _summarize_results(self, user_request, results):
        """汇总结果生成报告"""
        print(f"\n【汇总器】正在生成调研报告...")
        
        results_text = "\n\n".join([
            f"【{r.get('agent_role', r['agent_name'])}】\n{r.get('output', r.get('error', ''))}"
            for r in results
        ])
        
        summary_prompt = f"""你是调研报告汇总专家。请根据以下各专家的调研结果，生成一份完整、专业的调研报告。

用户原始需求：{user_request}

各专家调研结果：
{results_text}

请生成结构清晰、内容全面的调研报告。"""
        
        summary = llm.invoke(summary_prompt)
        
        print(f"【汇总器】调研报告生成完成")
        
        return summary.content

