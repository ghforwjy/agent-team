from langchain.tools import tool

@tool
def get_product_info(product_name: str) -> str:
    """获取产品信息，包括价格、库存、规格等
    
    Args:
        product_name: 产品名称，如"无线蓝牙耳机"、"智能手表"等
        
    Returns:
        产品的详细信息
    """
    product_database = {
        "无线蓝牙耳机": {
            "price": "¥299.00",
            "stock": "库存充足 (50件)",
            "spec": "蓝牙5.3，续航24小时，主动降噪"
        },
        "智能手表": {
            "price": "¥599.00",
            "stock": "库存紧张 (3件)",
            "spec": "1.4英寸屏幕，心率监测，GPS定位"
        },
        "手机壳": {
            "price": "¥99.00",
            "stock": "库存充足 (100件)",
            "spec": "硅胶材质，防摔设计"
        }
    }
    
    for name, info in product_database.items():
        if product_name in name or name in product_name:
            return f"{name} 信息：\n价格：{info['price']}\n库存：{info['stock']}\n规格：{info['spec']}"
    return f"未找到产品 '{product_name}' 的信息。"
