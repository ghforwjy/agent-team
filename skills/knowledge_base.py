from langchain.tools import tool

@tool
def search_knowledge_base(query: str) -> str:
    """在知识库中搜索相关技术信息，回答用户的技术问题
    
    Args:
        query: 用户的技术问题描述
        
    Returns:
        知识库中的相关信息
    """
    knowledge_base = {
        "登录问题": "请检查您的用户名和密码是否正确，确保没有区分大小写错误。如果忘记密码，请点击'忘记密码'进行重置。",
        "支付问题": "支付失败通常由以下原因导致：1. 银行卡余额不足；2. 网络连接问题；3. 银行卡未开通网银功能。建议先检查网络连接和账户余额。",
        "APP崩溃": "APP崩溃请尝试以下步骤：1. 清除APP缓存；2. 更新到最新版本；3. 重启设备。如问题仍然存在，请联系技术支持。",
        "订单查询": "您可以在'我的订单'页面查看所有订单状态，包括待支付、待发货、已发货、已完成等状态。"
    }
    
    for key, value in knowledge_base.items():
        if key in query or query in key:
            return value
    return f"知识库中暂无关于 '{query}' 的详细信息，建议联系人工客服。"
