# -*- coding: utf-8 -*-
"""
运行制度要求提取流程（使用模拟LLM）
"""
import sys
import os
import json

# 添加路径
sys.path.insert(0, r'e:\mycode\agent-team\knowledge-work-plugins\it-audit\skills')

from policy_compliance_checker.scripts.policy_extractor import PolicyRequirementExtractor


class MockLLM:
    """模拟LLM客户端"""
    
    def __init__(self):
        self.call_count = 0
    
    def chat(self, prompt: str) -> str:
        self.call_count += 1
        print(f"  LLM调用 #{self.call_count}")
        
        # 返回模拟的制度要求提取结果
        # 根据提示词中的审计项数量返回对应的结果
        return json.dumps({
            "batch_id": "MOCK",
            "extract_time": "2024-02-27T10:30:00",
            "total_items": 100,
            "policy_requirements": [
                {
                    "requirement_id": f"REQ-{self.call_count:03d}-001",
                    "source_item_code": "TEST-001",
                    "source_item_title": "测试审计项-建立制度",
                    "source_procedure": "检查是否制定相关制度",
                    "requirement_type": "建立制度",
                    "requirement_detail": {
                        "what": "信息安全管理制度",
                        "scope": "全公司",
                        "content": "制定完善的信息安全管理制度，明确安全责任",
                        "frequency": None,
                        "quantity": None,
                        "qualification": None,
                        "retention_period": None
                    },
                    "related_clues": ["信息安全", "管理制度", "安全责任"],
                    "confidence": 0.92
                },
                {
                    "requirement_id": f"REQ-{self.call_count:03d}-002",
                    "source_item_code": "TEST-002",
                    "source_item_title": "测试审计项-定期执行",
                    "source_procedure": "检查是否每年进行安全评审",
                    "requirement_type": "定期执行",
                    "requirement_detail": {
                        "what": "信息安全评审",
                        "scope": "全公司",
                        "content": "每年至少一次对信息安全管理制度进行评审和修订",
                        "frequency": "每年至少一次",
                        "quantity": None,
                        "qualification": None,
                        "retention_period": None
                    },
                    "related_clues": ["安全评审", "年度评审", "制度修订"],
                    "confidence": 0.88
                }
            ],
            "statistics": {
                "total_requirements": 2,
                "by_type": {
                    "建立制度": 1,
                    "建立组织": 0,
                    "人员配备": 0,
                    "定期执行": 1,
                    "岗位分离": 0,
                    "文件保存": 0
                }
            }
        })


def main():
    print("=" * 80)
    print("运行制度要求提取流程")
    print("=" * 80)
    
    # 配置
    db_path = r"e:\mycode\agent-team\tests\test_data\test_it_audit.db"
    output_dir = r"e:\mycode\agent-team\results"
    
    # 创建LLM客户端
    llm = MockLLM()
    
    # 创建提取器
    extractor = PolicyRequirementExtractor(db_path, llm, output_dir)
    
    print(f"\n批次号: {extractor.batch_id}")
    print(f"输出目录: {output_dir}")
    print()
    
    # 执行提取
    result_path = extractor.extract()
    
    print()
    print("=" * 80)
    print("提取完成")
    print("=" * 80)
    print(f"\n结果文件: {result_path}")
    
    # 读取并显示结果摘要
    with open(result_path, 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    print(f"\n提取统计:")
    print(f"  审计项总数: {result['batch_info']['items_processed']}")
    print(f"  发现制度要求: {result['summary']['total_requirements_found']} 条")
    print(f"  按类型分布:")
    for req_type, count in result['summary']['by_type'].items():
        if count > 0:
            print(f"    - {req_type}: {count} 条")
    
    # 列出所有生成的文件
    print(f"\n生成的文件:")
    batch_id = extractor.batch_id
    for filename in os.listdir(output_dir):
        if batch_id in filename:
            filepath = os.path.join(output_dir, filename)
            size = os.path.getsize(filepath)
            print(f"  - {filename} ({size} bytes)")


if __name__ == '__main__':
    main()
