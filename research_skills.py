
"""
调研场景的技能工具库
提供各类专家agent使用的专业工具
"""
from typing import Dict, List
from langchain.tools import tool

MARKET_DATABASE = {
    "AI行业": {
        "市场规模": "2025年全球AI市场规模约为1.2万亿美元，预计到2030年将达到5万亿美元",
        "主要参与者": "OpenAI、Google DeepMind、Anthropic、百度文心一言、阿里云通义千问",
        "增长趋势": "年增长率约45%，预计未来5年保持高速增长",
        "应用领域": "自然语言处理、计算机视觉、自动驾驶、医疗诊断、金融分析"
    },
    "新能源汽车": {
        "市场规模": "2025年全球新能源汽车销量约3000万辆，市场渗透率达35%",
        "主要参与者": "特斯拉、比亚迪、宁德时代、蔚来、理想汽车、小鹏汽车",
        "增长趋势": "年增长率约60%，预计2028年销量将突破6000万辆",
        "技术路线": "纯电动、插电混动、增程式、氢燃料电池"
    },
    "智能家居": {
        "市场规模": "2025年全球智能家居市场规模约1.5万亿美元",
        "主要参与者": "亚马逊Echo、小米米家、华为鸿蒙智联、Google Home、Apple HomeKit",
        "增长趋势": "年增长率约35%，智能家居设备普及率快速提升"
    }
}

COMPETITOR_DATABASE = {
    "OpenAI": {
        "公司简介": "成立于2015年，美国人工智能研究公司，非营利组织转型商业运营",
        "核心产品": "GPT系列大模型、DALL-E图像生成、Sora视频生成",
        "竞争优势": "技术领先、生态完善、开发者社区活跃",
        "最新动态": "2025年推出GPT-5，支持多模态超长时间上下文"
    },
    "比亚迪": {
        "公司简介": "中国新能源汽车和电池制造商，全球最大新能源车企",
        "核心产品": "王朝系列、海洋系列、DM-i插混、刀片电池",
        "竞争优势": "垂直整合、成本控制、电池技术领先",
        "最新动态": "2025年销量突破600万辆，海外市场快速扩张"
    },
    "特斯拉": {
        "公司简介": "美国电动汽车和能源公司，市值最高车企之一",
        "核心产品": "Model 3/Y/S/X、Cybertruck、FSD完全自动驾驶",
        "竞争优势": "品牌溢价、软件定义汽车、超级充电网络"
    }
}

TECHNICAL_DATABASE = {
    "大模型技术": {
        "技术架构": "Transformer架构、自注意力机制、预训练+微调范式",
        "关键技术": "RLHF人类反馈强化学习、MoE混合专家模型、上下文窗口扩展",
        "发展趋势": "模型规模持续扩大、多模态融合、小模型专业化",
        "技术挑战": "推理成本高、幻觉问题、对齐安全性、可解释性"
    },
    "自动驾驶技术": {
        "技术路线": "纯视觉方案、激光雷达方案、多传感器融合",
        "关键技术": "计算机视觉、SLAM同步定位与建图、路径规划、决策控制",
        "发展趋势": "L2+快速普及、L3逐步落地、L4/L5仍在探索",
        "技术挑战": "长尾场景、法规政策、成本控制、伦理问题"
    }
}

FINANCIAL_DATABASE = {
    "估值模型": {
        "DCF模型": "现金流折现模型，适合成熟企业长期估值",
        "可比公司分析法": "参考同行业公司估值倍数",
        "市盈率PE": "股价/每股收益，反映市场对公司盈利预期",
        "市销率PS": "股价/每股销售额，适合高增长企业"
    },
    "投资风险": {
        "技术风险": "技术迭代过快导致技术落后",
        "市场风险": "市场竞争激烈，份额下降",
        "政策风险": "政策监管变化",
        "财务风险": "现金流紧张，资金链断裂"
    }
}


@tool
def search_market_info(industry: str) -> str:
    """
    搜索行业市场信息，包括市场规模、主要参与者、增长趋势等

    Args:
        industry: 行业名称，例如"AI行业"、"新能源汽车"等
    
    Returns:
        行业市场信息
    """
    info = MARKET_DATABASE.get(industry, f"未找到{industry}的市场信息")
    if isinstance(info, dict):
        return "【市场信息】\n" + "\n".join([f"{k}: {v}" for k, v in info.items()])
    else:
        return info


@tool
def search_competitor_info(company: str) -> str:
    """
    搜索竞争对手公司信息

    Args:
        company: 公司名称
    
    Returns:
        公司信息
    """
    info = COMPETITOR_DATABASE.get(company, f"未找到{company}的信息")
    if isinstance(info, dict):
        return "【竞争对手信息】\n" + "\n".join([f"{k}: {v}" for k, v in info.items()])
    else:
        return info


@tool
def search_technical_info(topic: str) -> str:
    """
    搜索技术相关信息

    Args:
        topic: 技术主题
    
    Returns:
        技术信息
    """
    info = TECHNICAL_DATABASE.get(topic, f"未找到{topic}的技术信息")
    if isinstance(info, dict):
        return "【技术信息】\n" + "\n".join([f"{k}: {v}" for k, v in info.items()])
    else:
        return info


@tool
def search_financial_info(topic: str) -> str:
    """
    搜索财务和投资相关信息

    Args:
        topic: 财务/投资主题
    
    Returns:
        财务信息
    """
    info = FINANCIAL_DATABASE.get(topic, f"未找到{topic}的财务信息")
    if isinstance(info, dict):
        return "【财务信息】\n" + "\n".join([f"{k}: {v}" for k, v in info.items()])
    else:
        return info


@tool
def get_research_templates(research_type: str) -> str:
    """
    获取调研报告模板

    Args:
        research_type: 调研类型
    
    Returns:
        调研模板
    """
    templates = {
        "行业研究": """
行业调研报告模板
==============
1. 行业概述
2. 市场规模与增长趋势
3. 竞争格局分析
4. 技术发展趋势
5. 投资机会与风险
6. 结论与建议
        """,
        "竞品分析": """
竞品分析报告模板
===============
1. 竞品概述
2. 产品对比
3. 优劣势分析
4. 市场策略
5. 发展建议
        """
    }
    return templates.get(research_type, "通用调研报告")
