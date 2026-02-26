
"""
法律与财务专家场景的技能工具库
提供法律合规专家和财务专家使用的专业工具
"""
from typing import Dict, List
from langchain.tools import tool

LEGAL_KNOWLEDGE_BASE = {
    "合同审查": {
        "关键条款": "责任限制、赔偿条款、知识产权、数据保护、期限与终止、适用法律",
        "风险等级": "GREEN(可接受)、YELLOW(需协商)、RED(需升级)",
        "审查方法": "基于playbook审查、条款分析、偏离严重度分类、生成修订建议"
    },
    "法律风险评估": {
        "评估框架": "严重性(1-5级) × 可能性(1-5级)",
        "风险等级": "低/中/高/严重",
        "升级标准": "外部律师介入指引"
    },
    "合规检查": {
        "主要法规": "GDPR(欧盟)、CCPA/CPRA(加州)、LGPD(巴西)、POPIA(南非)、PIPEDA(加拿大)、PDPA(新加坡)、Privacy Act(澳大利亚)、PIPL(中国)、UK GDPR(英国)",
        "GDPR要求": "数据保护、72小时违约通知、DPIA、SCCs",
        "DPA审查清单": "主体事项与期限、性质与目的、个人数据类型、数据主体类别、控制者义务、处理者义务、国际传输"
    },
    "NDA分类": {
        "分类标准": "保密期限、保密范围、互易性、责任限制",
        "处理建议": "根据分类结果给出相应的处理建议"
    },
    "会议简报": {
        "内容要求": "背景信息、待讨论议题、行动项建议"
    }
}

FINANCIAL_KNOWLEDGE_BASE = {
    "财务报表": {
        "GAAP标准": "ASC 220/IAS 1(利润表)、ASC 210/IAS 1(资产负债表)、ASC 230/IAS 7(现金流量表)",
        "利润表结构": "收入、成本、毛利、营业费用、营业利润、其他收入/费用、所得税、净利润",
        "资产负债表结构": "流动资产、非流动资产、流动负债、非流动负债、股东权益",
        "现金流量表结构": "经营活动、投资活动、筹资活动"
    },
    "差异分析": {
        "分解方法": "价格/数量分解、费率/组合分解、人力成本分解",
        "瀑布图分析": "可视化展示差异驱动因素",
        "重要性阈值": "通常5-15%"
    },
    "日记账准备": {
        "类型": "应计、预提、折旧、摊销",
        "调整项": "期末调整分录"
    },
    "账户对账": {
        "内容": "核对账户余额、识别调节项",
        "要求": "确保账实相符"
    },
    "月末结账": {
        "清单": "月末结账任务清单",
        "依赖关系": "任务排序和依赖关系管理"
    },
    "审计支持": {
        "SOX合规": "SOX 404控制测试方法",
        "文档标准": "样本选择、文档标准、缺陷分类框架"
    }
}


@tool
def search_legal_knowledge(topic: str) -> str:
    """
    搜索法律相关知识，包括合同审查、合规检查、法律风险评估等

    Args:
        topic: 法律主题，例如"合同审查"、"合规检查"、"GDPR"、"DPA审查"等
    
    Returns:
        法律专业知识
    """
    info = LEGAL_KNOWLEDGE_BASE.get(topic, {})
    if info:
        result = "【法律知识库 - " + topic + "】\n"
        for k, v in info.items():
            result += k + ": " + v + "\n"
        return result
    else:
        for key in LEGAL_KNOWLEDGE_BASE.keys():
            if topic.lower() in key.lower():
                info = LEGAL_KNOWLEDGE_BASE[key]
                result = "【法律知识库 - " + key + "】\n"
                for k, v in info.items():
                    result += k + ": " + v + "\n"
                return result
        return "未找到" + topic + "的法律知识库信息"


@tool
def search_financial_knowledge(topic: str) -> str:
    """
    搜索财务相关知识，包括财务报表、差异分析、日记账准备等

    Args:
        topic: 财务主题，例如"财务报表"、"差异分析"、"GAAP"、"日记账"等
    
    Returns:
        财务专业知识
    """
    info = FINANCIAL_KNOWLEDGE_BASE.get(topic, {})
    if info:
        result = "【财务知识库 - " + topic + "】\n"
        for k, v in info.items():
            result += k + ": " + v + "\n"
        return result
    else:
        for key in FINANCIAL_KNOWLEDGE_BASE.keys():
            if topic.lower() in key.lower():
                info = FINANCIAL_KNOWLEDGE_BASE[key]
                result = "【财务知识库 - " + key + "】\n"
                for k, v in info.items():
                    result += k + ": " + v + "\n"
                return result
        return "未找到" + topic + "的财务知识库信息"


@tool
def get_contract_review_template() -> str:
    """
    获取合同审查模板

    Returns:
        合同审查模板
    """
    return """【合同审查模板】
==============
1. 合同类型识别
2. 用户方立场确认
3. 关键条款分析
   - 责任限制条款
   - 赔偿条款
   - 知识产权条款
   - 数据保护条款
   - 期限与终止条款
   - 适用法律与争议解决
4. 偏离严重度分类(GREEN/YELLOW/RED)
5. 生成修订建议(redline)
6. 谈判优先级建议(Tier 1/2/3)
"""


@tool
def get_financial_statement_template() -> str:
    """
    获取财务报表模板

    Returns:
        财务报表模板
    """
    return """【财务报表模板】
==============
一、利润表
1. 收入
   - 产品收入
   - 服务收入
   - 其他收入
2. 成本
3. 毛利
4. 营业费用
   - 研发费用
   - 销售与营销费用
   - 一般与行政费用
5. 营业利润
6. 其他收入/费用
7. 所得税
8. 净利润

二、资产负债表
1. 资产
   - 流动资产
   - 非流动资产
2. 负债
   - 流动负债
   - 非流动负债
3. 股东权益

三、现金流量表
1. 经营活动现金流
2. 投资活动现金流
3. 筹资活动现金流
"""


@tool
def get_variance_analysis_template() -> str:
    """
    获取差异分析模板

    Returns:
        差异分析模板
    """
    return """【差异分析模板】
==============
1. 差异计算
   - 金额差异：当期-基期
   - 百分比差异：(当期-基期)/|基期|×100
2. 重要性阈值判断
3. 差异分解
   - 数量/价格分解
   - 费率/组合分解
4. 驱动因素分析
5. 瀑布图展示
6. 业务原因说明
7. 趋势判断与行动建议
"""

