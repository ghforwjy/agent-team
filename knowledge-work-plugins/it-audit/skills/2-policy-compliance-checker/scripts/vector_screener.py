# -*- coding: utf-8 -*-
"""
制度要求向量筛选器
使用向量语义匹配进行制度要求筛选，支持置信度分级
"""
import os
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class ScreeningResult:
    """筛选结果数据类"""
    item_id: int
    item_code: str
    item_title: str
    dimension_name: str
    procedure_text: str
    suggested_type: str
    similarity: float
    confidence_level: str
    need_llm: bool


class PolicyVectorScreener:
    """制度要求向量筛选器 - 向量语义匹配 + 置信度分级"""
    
    HIGH_CONFIDENCE_THRESHOLD = 0.70
    LOW_CONFIDENCE_THRESHOLD = 0.45
    
    VECTOR_TEMPLATES = {
        '建立制度': [
            '制定制度', '建立制度', '编制制度',
            '制定规定', '建立规定', '编制规定',
            '制定办法', '建立办法', '编制办法',
            '制定规程', '建立规程', '编制规程',
            '制定相关制度', '建立相关制度',
            '制定管理制度', '建立管理制度',
            '制定安全制度', '建立安全制度',
            '制定管理规定', '建立管理规定',
        ],
        '定期执行': [
            '每年开展检查', '每季度开展检查', '定期开展检查',
            '每年进行评估', '每季度进行评估', '定期进行评估',
            '每年开展演练', '定期开展演练',
            '每年进行审计', '定期进行审计',
            '每年进行评审', '定期进行评审',
            '定期开展安全检查', '每年进行风险评估',
            '定期进行安全评估', '每年开展审计工作',
        ],
        '人员配备': [
            '配备人员', '设置岗位', '指定人员',
            '配备专职人员', '设置专职岗位',
            '配备安全人员', '设置安全岗位',
            '指定专人负责', '配备专门人员',
            '设置管理人员', '配备管理人员',
            '明确安全责任', '落实安全责任',
        ],
        '岗位分离': [
            '职责分离', '不相容岗位分离', '岗位分离',
            '职责分工', '岗位制衡', '互相监督',
            '不相容职责', '职责相互制约',
        ],
        '文件保存': [
            '保存文档', '留存记录', '归档文件',
            '保存记录', '留存文档', '归档记录',
            '保存档案', '留存档案',
            '保存日志', '留存日志', '归档日志',
        ],
        '建立组织': [
            '成立委员会', '建立委员会', '设立委员会',
            '成立小组', '建立小组', '设立小组',
            '成立部门', '建立部门', '设立部门',
            '成立领导小组', '建立工作组', '设立工作组',
            '建立组织机构', '成立工作机构',
        ]
    }
    
    def __init__(self):
        self.matcher = None
        self.template_vectors = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """延迟初始化，避免导入时加载模型"""
        if self._initialized:
            return
        
        try:
            import importlib.util
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            matcher_path = os.path.join(
                script_dir, '..', '..', '1-audit-item-collector', 'scripts', 'semantic_matcher.py'
            )
            matcher_path = os.path.normpath(matcher_path)
            
            spec = importlib.util.spec_from_file_location("semantic_matcher", matcher_path)
            matcher_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(matcher_module)
            
            self.matcher = matcher_module.SemanticMatcher()
            self.template_vectors = self._build_template_vectors()
            self._initialized = True
            print("向量筛选器初始化完成")
        except Exception as e:
            print(f"向量筛选器初始化失败: {e}")
            raise
    
    def _build_template_vectors(self) -> Dict[str, np.ndarray]:
        """构建各类制度要求的模板向量（取平均值）"""
        template_vectors = {}
        for req_type, texts in self.VECTOR_TEMPLATES.items():
            vectors = self.matcher.encode_batch(texts)
            template_vectors[req_type] = np.mean(vectors, axis=0)
        return template_vectors
    
    def _compute_similarity(self, text: str) -> Tuple[float, str]:
        """
        计算文本与各模板的相似度
        
        Returns:
            (最高相似度, 最匹配的类型)
        """
        if not text or not text.strip():
            return 0.0, ''
        
        vec = self.matcher.model.encode(text)
        
        best_type = ''
        best_sim = 0.0
        
        for req_type, template_vec in self.template_vectors.items():
            sim = self._cosine_similarity(vec, template_vec)
            if sim > best_sim:
                best_sim = sim
                best_type = req_type
        
        return float(best_sim), best_type
    
    def screen(self, items: List[Dict]) -> Tuple[List[ScreeningResult], List[ScreeningResult], int]:
        """
        向量语义筛选 + 置信度分级
        
        Args:
            items: 审计项列表，每项包含 id, item_code, title, dimension_name, procedures
            
        Returns:
            (高置信度结果, 中置信度结果, 跳过数量)
        """
        self._ensure_initialized()
        
        high_confidence_results = []
        medium_confidence_results = []
        skipped_count = 0
        
        print(f"\n开始向量筛选，共 {len(items)} 条审计项...")
        
        for i, item in enumerate(items):
            if (i + 1) % 50 == 0:
                print(f"  已处理 {i + 1}/{len(items)} 条...")
            
            procedures = item.get('procedures', [])
            if isinstance(procedures, list):
                text = ' '.join(procedures)
            else:
                text = str(procedures)
            
            if not text.strip():
                skipped_count += 1
                continue
            
            similarity, suggested_type = self._compute_similarity(text)
            
            if similarity >= self.HIGH_CONFIDENCE_THRESHOLD:
                result = ScreeningResult(
                    item_id=item.get('id'),
                    item_code=item.get('item_code', ''),
                    item_title=item.get('title', ''),
                    dimension_name=item.get('dimension_name', ''),
                    procedure_text=text[:200],
                    suggested_type=suggested_type,
                    similarity=round(similarity, 4),
                    confidence_level='high',
                    need_llm=False
                )
                high_confidence_results.append(result)
            elif similarity >= self.LOW_CONFIDENCE_THRESHOLD:
                result = ScreeningResult(
                    item_id=item.get('id'),
                    item_code=item.get('item_code', ''),
                    item_title=item.get('title', ''),
                    dimension_name=item.get('dimension_name', ''),
                    procedure_text=text[:200],
                    suggested_type=suggested_type,
                    similarity=round(similarity, 4),
                    confidence_level='medium',
                    need_llm=True
                )
                medium_confidence_results.append(result)
            else:
                skipped_count += 1
        
        print(f"筛选完成:")
        print(f"  高置信度（直接确定）: {len(high_confidence_results)} 条")
        print(f"  中置信度（需LLM确认）: {len(medium_confidence_results)} 条")
        print(f"  低置信度（跳过）: {skipped_count} 条")
        
        return high_confidence_results, medium_confidence_results, skipped_count
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def get_template_info(self) -> Dict:
        """获取模板信息"""
        return {
            'template_count': sum(len(v) for v in self.VECTOR_TEMPLATES.values()),
            'type_count': len(self.VECTOR_TEMPLATES),
            'types': list(self.VECTOR_TEMPLATES.keys()),
            'thresholds': {
                'high': self.HIGH_CONFIDENCE_THRESHOLD,
                'low': self.LOW_CONFIDENCE_THRESHOLD
            }
        }


def main():
    """测试向量筛选器"""
    import sqlite3
    
    db_path = r"e:\mycode\agent-team\tests\test_data\test_it_audit.db"
    
    print("=" * 60)
    print("向量筛选器测试")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ai.id, ai.item_code, ai.title, ad.name as dimension_name
        FROM audit_items ai
        JOIN audit_dimensions ad ON ai.dimension_id = ad.id
        WHERE ai.status = 'active'
        ORDER BY ai.id
        LIMIT 50
    ''')
    
    items = []
    for row in cursor.fetchall():
        item = dict(row)
        cursor.execute('''
            SELECT procedure_text FROM audit_procedures
            WHERE item_id = ? ORDER BY is_primary DESC, id
        ''', (item['id'],))
        item['procedures'] = [r[0] for r in cursor.fetchall()]
        items.append(item)
    
    conn.close()
    
    print(f"加载了 {len(items)} 条审计项")
    
    screener = PolicyVectorScreener()
    high, medium, skipped = screener.screen(items)
    
    print("\n" + "=" * 60)
    print("高置信度结果示例:")
    print("=" * 60)
    for r in high[:5]:
        print(f"  [{r.item_code}] {r.item_title[:30]}")
        print(f"    类型: {r.suggested_type}, 相似度: {r.similarity:.4f}")
    
    print("\n" + "=" * 60)
    print("中置信度结果示例:")
    print("=" * 60)
    for r in medium[:5]:
        print(f"  [{r.item_code}] {r.item_title[:30]}")
        print(f"    类型: {r.suggested_type}, 相似度: {r.similarity:.4f}")


if __name__ == '__main__':
    main()
