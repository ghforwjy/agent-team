# -*- coding: utf-8 -*-
"""
制度合规检查数据库管理器
管理筛选结果的存储和查询
"""
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class ScreeningRecord:
    """筛选记录数据类"""
    id: Optional[int] = None
    item_id: int = 0
    item_code: str = ''
    screening_batch: str = ''
    vector_similarity: float = 0.0
    screening_status: str = 'pending'
    requirement_type: str = ''
    confidence: float = 0.0
    llm_verified: bool = False
    item_title: str = ''
    dimension_name: str = ''
    procedure_text: str = ''


class PolicyDatabaseManager:
    """制度合规检查数据库管理器"""
    
    def __init__(self, db_path: str):
        if not db_path:
            raise ValueError("数据库路径(db_path)必须传入，不能为空")
        
        self.db_path = db_path
        self._ensure_db_dir()
        self.conn = None
    
    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def init_policy_tables(self):
        """初始化制度相关表"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS policy_screening_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                item_code VARCHAR(30) NOT NULL,
                screening_batch VARCHAR(50),
                vector_similarity REAL,
                screening_status VARCHAR(20) DEFAULT 'pending',
                requirement_type VARCHAR(20),
                confidence REAL,
                llm_verified BOOLEAN DEFAULT 0,
                item_title TEXT,
                dimension_name TEXT,
                procedure_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(item_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_screening_status ON policy_screening_results(screening_status);
            CREATE INDEX IF NOT EXISTS idx_screening_batch ON policy_screening_results(screening_batch);
            CREATE INDEX IF NOT EXISTS idx_requirement_type ON policy_screening_results(requirement_type);
        ''')
        
        conn.commit()
        print(f"制度筛选表初始化完成: {self.db_path}")
    
    def generate_batch_id(self) -> str:
        """生成批次号"""
        date_str = datetime.now().strftime("%Y%m%d")
        short_uuid = uuid.uuid4().hex[:6].upper()
        return f"SCREEN-{date_str}-{short_uuid}"
    
    def save_screening_result(self, record: ScreeningRecord) -> int:
        """保存筛选结果"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO policy_screening_results
            (item_id, item_code, screening_batch, vector_similarity, 
             screening_status, requirement_type, confidence, llm_verified,
             item_title, dimension_name, procedure_text, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            record.item_id,
            record.item_code,
            record.screening_batch,
            record.vector_similarity,
            record.screening_status,
            record.requirement_type,
            record.confidence,
            1 if record.llm_verified else 0,
            record.item_title,
            record.dimension_name,
            record.procedure_text
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    def batch_save_screening_results(self, records: List[ScreeningRecord], batch_id: str) -> int:
        """批量保存筛选结果"""
        conn = self.connect()
        cursor = conn.cursor()
        
        count = 0
        for record in records:
            record.screening_batch = batch_id
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO policy_screening_results
                    (item_id, item_code, screening_batch, vector_similarity, 
                     screening_status, requirement_type, confidence, llm_verified,
                     item_title, dimension_name, procedure_text, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    record.item_id,
                    record.item_code,
                    record.screening_batch,
                    record.vector_similarity,
                    record.screening_status,
                    record.requirement_type,
                    record.confidence,
                    1 if record.llm_verified else 0,
                    record.item_title,
                    record.dimension_name,
                    record.procedure_text
                ))
                count += 1
            except Exception as e:
                print(f"保存记录失败 [{record.item_code}]: {e}")
        
        conn.commit()
        return count
    
    def get_screened_item_ids(self) -> Set[int]:
        """获取已筛选的审计项ID集合"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT item_id FROM policy_screening_results')
        return {row[0] for row in cursor.fetchall()}
    
    def get_screening_statistics(self) -> Dict:
        """获取筛选统计信息"""
        conn = self.connect()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) FROM policy_screening_results')
        stats['total'] = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT screening_status, COUNT(*) 
            FROM policy_screening_results 
            GROUP BY screening_status
        ''')
        stats['by_status'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute('''
            SELECT requirement_type, COUNT(*) 
            FROM policy_screening_results 
            WHERE requirement_type IS NOT NULL AND requirement_type != ''
            GROUP BY requirement_type
        ''')
        stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN confidence >= 0.7 THEN 'high'
                    WHEN confidence >= 0.45 THEN 'medium'
                    ELSE 'low'
                END as confidence_level,
                COUNT(*)
            FROM policy_screening_results
            WHERE confidence IS NOT NULL
            GROUP BY confidence_level
        ''')
        stats['by_confidence'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        return stats
    
    def get_all_screening_results(self) -> List[Dict]:
        """获取所有筛选结果"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM policy_screening_results
            ORDER BY vector_similarity DESC
        ''')
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_results_by_type(self, requirement_type: str) -> List[Dict]:
        """按类型获取筛选结果"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM policy_screening_results
            WHERE requirement_type = ?
            ORDER BY vector_similarity DESC
        ''', (requirement_type,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_results_by_confidence(self, level: str) -> List[Dict]:
        """按置信度获取筛选结果"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if level == 'high':
            cursor.execute('''
                SELECT * FROM policy_screening_results
                WHERE confidence >= 0.7
                ORDER BY vector_similarity DESC
            ''')
        elif level == 'medium':
            cursor.execute('''
                SELECT * FROM policy_screening_results
                WHERE confidence >= 0.45 AND confidence < 0.7
                ORDER BY vector_similarity DESC
            ''')
        else:
            cursor.execute('''
                SELECT * FROM policy_screening_results
                WHERE confidence < 0.45
                ORDER BY vector_similarity DESC
            ''')
        
        return [dict(row) for row in cursor.fetchall()]
    
    def clear_all_results(self):
        """清空所有筛选结果"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM policy_screening_results')
        conn.commit()
        print("已清空所有筛选结果")


def main():
    """测试数据库管理器"""
    db_path = r"e:\mycode\agent-team\tests\test_data\test_it_audit.db"
    
    print("=" * 60)
    print("数据库管理器测试")
    print("=" * 60)
    
    db = PolicyDatabaseManager(db_path)
    db.init_policy_tables()
    
    stats = db.get_screening_statistics()
    print(f"\n当前筛选统计:")
    print(f"  总数: {stats.get('total', 0)}")
    print(f"  按状态: {stats.get('by_status', {})}")
    print(f"  按类型: {stats.get('by_type', {})}")
    print(f"  按置信度: {stats.get('by_confidence', {})}")


if __name__ == '__main__':
    main()
