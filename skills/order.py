from langchain.tools import tool

@tool
def query_order(order_id: str) -> str:
    """查询订单信息，包括订单状态、物流信息、金额等
    
    Args:
        order_id: 订单编号，格式为ORD开头加数字，如ORD001
        
    Returns:
        订单的详细信息
    """
    order_database = {
        "ORD001": {
            "status": "已发货",
            "logistics": "顺丰快递 SF1234567890",
            "amount": "¥299.00",
            "items": "无线蓝牙耳机 x1"
        },
        "ORD002": {
            "status": "待支付",
            "logistics": "尚未发货",
            "amount": "¥599.00",
            "items": "智能手表 x1"
        },
        "ORD003": {
            "status": "已完成",
            "logistics": "已签收",
            "amount": "¥199.00",
            "items": "手机壳 x2"
        }
    }
    
    if order_id in order_database:
        order = order_database[order_id]
        return f"订单 {order_id} 信息：\n状态：{order['status']}\n物流：{order['logistics']}\n金额：{order['amount']}\n商品：{order['items']}"
    return f"未找到订单 {order_id} 的信息，请确认订单号是否正确。"
