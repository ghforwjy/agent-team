import os
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from skills import search_knowledge_base, query_order, get_product_info, get_refund_policy

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

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "add"]
    next: str
    question: str

supervisor_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个电商客服协调员。请分析用户的问题，判断它属于以下哪一类：
[A. 技术问题] - 网站故障、APP使用问题、功能异常
[B. 订单查询] - 订单状态、物流信息、支付问题
[C. 退款售后] - 退款申请、退货流程、售后服务
[D. 产品咨询] - 商品信息、库存查询、促销活动

请只回复类别代号（A/B/C/D），不要回复其他任何内容。"""),
    ("human", "{question}")
])

tech_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个技术支持专家，请根据知识库信息回答用户的技术问题。你可以使用以下知识库信息：\n" + 
     "登录问题：请检查您的用户名和密码是否正确，确保没有区分大小写错误。如果忘记密码，请点击'忘记密码'进行重置。\n" +
     "APP崩溃：APP崩溃请尝试以下步骤：1. 清除APP缓存；2. 更新到最新版本；3. 重启设备。如问题仍然存在，请联系技术支持。"),
    ("human", "{input}")
])

order_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个订单查询专家，请回答用户的订单问题。你可以查询以下示例订单：\n" +
     "ORD001：状态已发货，物流顺丰快递SF1234567890，金额¥299.00，商品无线蓝牙耳机x1\n" +
     "ORD002：状态待支付，物流尚未发货，金额¥599.00，商品智能手表x1\n" +
     "ORD003：状态已完成，物流已签收，金额¥199.00，商品手机壳x2"),
    ("human", "{input}")
])

refund_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个退款售后专家，请指导用户完成退款申请流程。退款政策如下：\n" +
     "1. 7天无理由退换：商品收到后7天内，未使用且包装完好可申请退换\n" +
     "2. 质量问题：30天内出现质量问题，可免费退换或维修\n" +
     "3. 退款流程：进入'我的订单'→选择订单→点击'申请退款'→填写原因提交→等待审核(1-3工作日)→款项3-5工作日原路返回"),
    ("human", "{input}")
])

product_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个产品咨询专家，请回答用户的产品问题。产品信息如下：\n" +
     "无线蓝牙耳机：价格¥299.00，库存充足(50件)，规格：蓝牙5.3，续航24小时，主动降噪\n" +
     "智能手表：价格¥599.00，库存紧张(3件)，规格：1.4英寸屏幕，心率监测，GPS定位\n" +
     "手机壳：价格¥99.00，库存充足(100件)，规格：硅胶材质，防摔设计"),
    ("human", "{input}")
])

def supervisor_node(state: AgentState):
    print(f"\n【协调员】正在分析问题...")
    question = state["question"]
    response = llm.invoke(supervisor_prompt.format(question=question))
    category = response.content.strip()
    print(f"【协调员】问题分类为：{category}")
    return {
        "messages": [response],
        "next": category
    }

def tech_node(state: AgentState):
    print(f"\n【技术支持专家】正在处理...")
    question = state["question"]
    result = llm.invoke(tech_prompt.format(input=question))
    return {
        "messages": [AIMessage(content=result.content)],
        "next": "END"
    }

def order_node(state: AgentState):
    print(f"\n【订单查询专家】正在处理...")
    question = state["question"]
    result = llm.invoke(order_prompt.format(input=question))
    return {
        "messages": [AIMessage(content=result.content)],
        "next": "END"
    }

def refund_node(state: AgentState):
    print(f"\n【退款售后专家】正在处理...")
    question = state["question"]
    result = llm.invoke(refund_prompt.format(input=question))
    return {
        "messages": [AIMessage(content=result.content)],
        "next": "END"
    }

def product_node(state: AgentState):
    print(f"\n【产品咨询专家】正在处理...")
    question = state["question"]
    result = llm.invoke(product_prompt.format(input=question))
    return {
        "messages": [AIMessage(content=result.content)],
        "next": "END"
    }

def router(state: AgentState):
    return state["next"]

workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("tech_agent", tech_node)
workflow.add_node("order_agent", order_node)
workflow.add_node("refund_agent", refund_node)
workflow.add_node("product_agent", product_node)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    router,
    {
        "A": "tech_agent",
        "B": "order_agent",
        "C": "refund_agent",
        "D": "product_agent",
        "END": END
    }
)

workflow.add_edge("tech_agent", END)
workflow.add_edge("order_agent", END)
workflow.add_edge("refund_agent", END)
workflow.add_edge("product_agent", END)

app = workflow.compile()

def process_question(question: str):
    initial_state = {
        "messages": [HumanMessage(content=question)],
        "question": question,
        "next": ""
    }
    
    result = app.invoke(initial_state)
    final_message = result["messages"][-1]
    return final_message.content

def main():
    print("=" * 70)
    print("🐝 蜂群式Agent智能客服系统 - 真正使用LangChain + LangGraph")
    print("=" * 70)
    print("\n技术栈：")
    print("  ✅ LangChain - LLM集成和Prompt模板")
    print("  ✅ LangGraph - 状态机工作流")
    print("  ✅ 豆包大模型 - 火山方舟API")
    print("=" * 70)
    print("\n请输入您的问题（输入 'quit' 退出）：\n")
    
    while True:
        user_input = input("用户: ")
        
        if user_input.lower() in ['quit', 'exit', '退出']:
            print("\n感谢使用，再见！")
            break
        
        try:
            response = process_question(user_input)
            print(f"\n客服: {response}\n")
            print("-" * 70)
        except Exception as e:
            print(f"\n【错误】发生异常: {str(e)}\n")
            print("-" * 70)

if __name__ == "__main__":
    main()
