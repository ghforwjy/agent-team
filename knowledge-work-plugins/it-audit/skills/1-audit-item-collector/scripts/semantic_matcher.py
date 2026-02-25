# -*- coding: utf-8 -*-
"""
IT审计专家Agent - 语义匹配模块
负责使用向量模型进行批量语义相似度匹配
"""
import os
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


class SemanticMatcher:
    """语义匹配器 - 使用向量模型进行批量相似度计算"""
    
    SIMILARITY_HIGH = 0.85
    SIMILARITY_MEDIUM = 0.60
    PROCEDURE_SIMILARITY_HIGH = 0.80
    TOP_K = 3
    
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载向量模型"""
        try:
            from sentence_transformers import SentenceTransformer
            import os
            
            os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
            
            model_cache = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'model'))
            snapshot_dir = os.path.join(
                model_cache,
                'models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2',
                'snapshots'
            )
            
            print(f"模型缓存目录: {model_cache}")
            print(f"快照目录: {snapshot_dir}")
            
            if os.path.exists(snapshot_dir):
                snapshots = os.listdir(snapshot_dir)
                if snapshots:
                    model_path = os.path.join(snapshot_dir, snapshots[0])
                    print(f"从本地加载模型: {model_path}")
                    self.model = SentenceTransformer(model_path)
                    print(f"已加载模型: {self.model_name}")
                    return
            
            raise FileNotFoundError(f"模型未找到: {snapshot_dir}")
        except ImportError:
            raise ImportError("请安装sentence-transformers: pip install sentence-transformers")
    
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """批量计算文本向量"""
        return self.model.encode(texts, batch_size=batch_size, show_progress_bar=True, convert_to_numpy=True)
    
    def compute_similarity_matrix(self, new_vectors: np.ndarray, existing_vectors: np.ndarray) -> np.ndarray:
        """计算相似度矩阵"""
        new_vectors = new_vectors / np.linalg.norm(new_vectors, axis=1, keepdims=True)
        existing_vectors = existing_vectors / np.linalg.norm(existing_vectors, axis=1, keepdims=True)
        return np.dot(new_vectors, existing_vectors.T)
    
    def batch_match(self, new_items: List[Dict], existing_items: List[Dict]) -> Dict[str, Any]:
        """
        批量匹配审计项
        
        Args:
            new_items: 新审计项列表，每项包含 {title, dimension, procedure}
            existing_items: 已有审计项列表，每项包含 {id, title, dimension, procedures: [{text}]}
        
        Returns:
            符合设计文档结构的JSON
        """
        new_titles = [item.get('title', '') for item in new_items]
        existing_titles = [item.get('title', '') for item in existing_items]
        
        print(f"计算向量: {len(new_titles)} 条新审计项 vs {len(existing_titles)} 条已有审计项")
        
        new_vectors = self.encode_batch(new_titles)
        
        if not existing_items:
            print("数据库为空，所有审计项将作为新项处理")
            merge_suggestions = []
            for i, new_item in enumerate(new_items, 1):
                merge_suggestions.append({
                    'suggestion_id': f'M{i:03d}',
                    'new_item': {
                        'title': new_item.get('title', ''),
                        'dimension': new_item.get('dimension', ''),
                        'procedure': new_item.get('procedure', '')
                    },
                    'match_result': {
                        'existing_item_id': None,
                        'existing_title': None,
                        'similarity': 0.0,
                        'action': 'new_item'
                    },
                    'vector_confidence': 'high'
                })
            
            result = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'source_file': '',
                'summary': {
                    'total_new_items': len(new_items),
                    'total_existing_items': 0,
                    'suggested_new_items': len(new_items),
                    'suggested_merge_items': 0,
                    'pending_review': 0
                },
                'merge_suggestions': merge_suggestions,
                'pending_review': []
            }
            return result
        
        existing_vectors = []
        for item in existing_items:
            vec = item.get('title_vector')
            if vec is not None:
                existing_vectors.append(vec)
            else:
                existing_vectors.append(None)
        
        need_encode_indices = [i for i, v in enumerate(existing_vectors) if v is None]
        if need_encode_indices:
            need_encode_titles = [existing_titles[i] for i in need_encode_indices]
            encoded = self.encode_batch(need_encode_titles)
            for idx, vec in zip(need_encode_indices, encoded):
                existing_vectors[idx] = vec
        
        existing_vectors = np.array(existing_vectors)
        
        print("计算相似度矩阵...")
        similarity_matrix = self.compute_similarity_matrix(new_vectors, existing_vectors)
        
        merge_suggestions = []
        pending_review = []
        suggestion_counter = 1
        pending_counter = 1
        
        for i, new_item in enumerate(new_items):
            similarities = similarity_matrix[i]
            top_indices = np.argsort(similarities)[-self.TOP_K:][::-1]
            top_candidates = []
            
            for idx in top_indices:
                sim = float(similarities[idx])
                if sim > self.SIMILARITY_MEDIUM:
                    top_candidates.append({
                        'existing_item': existing_items[idx],
                        'similarity': sim
                    })
            
            if not top_candidates:
                merge_suggestions.append(self._create_new_item_suggestion(
                    new_item, suggestion_counter, None, 0.0
                ))
                suggestion_counter += 1
            elif top_candidates[0]['similarity'] > self.SIMILARITY_HIGH:
                best = top_candidates[0]
                procedure_match = self._match_procedure(
                    new_item.get('procedure', ''),
                    best['existing_item'].get('procedures', [])
                )
                
                merge_suggestions.append({
                    'suggestion_id': f'M{suggestion_counter:03d}',
                    'new_item': {
                        'title': new_item.get('title', ''),
                        'dimension': new_item.get('dimension', ''),
                        'procedure': new_item.get('procedure', '')
                    },
                    'match_result': {
                        'existing_item_id': best['existing_item'].get('id'),
                        'existing_title': best['existing_item'].get('title'),
                        'similarity': round(best['similarity'], 2),
                        'action': 'merge'
                    },
                    'procedure_match': procedure_match,
                    'vector_confidence': 'high' if best['similarity'] > 0.90 else 'medium'
                })
                suggestion_counter += 1
            else:
                pending_review.append({
                    'suggestion_id': f'P{pending_counter:03d}',
                    'new_item': {
                        'title': new_item.get('title', ''),
                        'dimension': new_item.get('dimension', ''),
                        'procedure': new_item.get('procedure', '')
                    },
                    'candidates': [
                        {
                            'existing_item_id': c['existing_item'].get('id'),
                            'existing_title': c['existing_item'].get('title'),
                            'similarity': round(c['similarity'], 2)
                        }
                        for c in top_candidates
                    ],
                    'vector_confidence': 'low',
                    'note': '相似度中等，需人工判断'
                })
                pending_counter += 1
        
        new_count = sum(1 for s in merge_suggestions if s['match_result']['action'] == 'new_item')
        merge_count = sum(1 for s in merge_suggestions if s['match_result']['action'] == 'merge')
        
        result = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'source_file': '',
            'summary': {
                'total_new_items': len(new_items),
                'total_existing_items': len(existing_items),
                'suggested_new_items': new_count,
                'suggested_merge_items': merge_count,
                'pending_review': len(pending_review)
            },
            'merge_suggestions': merge_suggestions,
            'pending_review': pending_review
        }
        
        return result
    
    def _create_new_item_suggestion(self, new_item: Dict, counter: int, 
                                     best_match: Optional[Dict], best_sim: float) -> Dict:
        """创建新建审计项的建议"""
        suggestion = {
            'suggestion_id': f'M{counter:03d}',
            'new_item': {
                'title': new_item.get('title', ''),
                'dimension': new_item.get('dimension', ''),
                'procedure': new_item.get('procedure', '')
            },
            'match_result': {
                'existing_item_id': None,
                'existing_title': None,
                'similarity': round(best_sim, 2),
                'action': 'new_item'
            },
            'vector_confidence': 'high'
        }
        
        if best_match:
            suggestion['best_match'] = {
                'existing_item_id': best_match.get('id'),
                'existing_title': best_match.get('title'),
                'similarity': round(best_sim, 2)
            }
        
        return suggestion
    
    def _match_procedure(self, new_procedure: str, existing_procedures: List[Dict]) -> Dict:
        """匹配审计程序"""
        if not new_procedure or not existing_procedures:
            return {
                'existing_procedure': existing_procedures[0].get('text', '') if existing_procedures else None,
                'similarity': 0.0,
                'action': 'new_procedure'
            }
        
        new_vec = self.model.encode(new_procedure)
        
        best_match = None
        best_sim = 0.0
        
        for proc in existing_procedures:
            proc_text = proc.get('text', '')
            if not proc_text:
                continue
            
            proc_vec = self.model.encode(proc_text)
            sim = float(np.dot(new_vec, proc_vec) / (np.linalg.norm(new_vec) * np.linalg.norm(proc_vec)))
            
            if sim > best_sim:
                best_sim = sim
                best_match = proc_text
        
        action = 'merge_procedure' if best_sim > self.PROCEDURE_SIMILARITY_HIGH else 'new_procedure'
        
        return {
            'existing_procedure': best_match,
            'similarity': round(best_sim, 2),
            'action': action
        }
    
    def save_result(self, result: Dict, output_path: str):
        """保存匹配结果到JSON文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"匹配结果已保存: {output_path}")


def main():
    """测试语义匹配"""
    matcher = SemanticMatcher()
    
    new_items = [
        {'title': '公司是否建立IT治理委员会', 'dimension': '信息技术治理', 'procedure': '查阅IT治理委员会成立发文'},
        {'title': 'IT治理委员会是否有效运作', 'dimension': '信息技术治理', 'procedure': '查阅IT治理委员会会议记录'},
        {'title': '是否制定数据分类分级管理制度', 'dimension': '数据安全', 'procedure': '查阅数据分类分级管理制度文件'},
        {'title': '是否定期开展网络安全培训', 'dimension': '安全管理', 'procedure': '查阅培训记录'},
    ]
    
    existing_items = [
        {'id': 'IT-GOV-0015', 'title': '是否设立IT治理委员会', 'dimension': '信息技术治理', 
         'procedures': [{'text': '查阅公司是否制定IT治理委员会成立文件'}]},
        {'id': 'IT-DS-0008', 'title': '是否建立数据安全管理制度', 'dimension': '数据安全',
         'procedures': [{'text': '查阅数据安全管理制度文件'}]},
        {'id': 'IT-SEC-0023', 'title': '是否制定安全培训计划', 'dimension': '安全管理',
         'procedures': [{'text': '查阅安全培训计划文件'}]},
        {'id': 'IT-SEC-0045', 'title': '员工是否接受安全意识教育', 'dimension': '安全管理',
         'procedures': [{'text': '查阅培训签到记录'}]},
    ]
    
    result = matcher.batch_match(new_items, existing_items)
    
    print("\n" + "=" * 60)
    print("匹配结果:")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    matcher.save_result(result, 'knowledge-work-plugins/it-audit/data/match_result.json')


if __name__ == '__main__':
    main()
