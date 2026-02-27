# -*- coding: utf-8 -*-
"""
IT审计专家Agent - 数据库管理模块
负责SQLite数据库的创建、连接和基础操作
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            it_audit_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            db_path = os.path.join(it_audit_dir, 'data', 'it_audit.db')
        
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
    
    def init_database(self):
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS audit_dimensions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                parent_id INTEGER,
                level INTEGER DEFAULT 1,
                description TEXT,
                display_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES audit_dimensions(id)
            );
            
            CREATE TABLE IF NOT EXISTS audit_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code VARCHAR(30) UNIQUE NOT NULL,
                dimension_id INTEGER NOT NULL,
                title VARCHAR(500) NOT NULL,
                title_vector BLOB,
                description TEXT,
                criteria TEXT,
                severity VARCHAR(10) DEFAULT '中',
                evidence_required TEXT,
                status VARCHAR(20) DEFAULT 'active',
                version VARCHAR(20) DEFAULT 'v1',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dimension_id) REFERENCES audit_dimensions(id)
            );
            
            CREATE TABLE IF NOT EXISTS audit_procedures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                procedure_text TEXT NOT NULL,
                procedure_type VARCHAR(50),
                procedure_vector BLOB,
                source_id INTEGER,
                is_primary BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES audit_items(id) ON DELETE CASCADE,
                FOREIGN KEY (source_id) REFERENCES audit_item_sources(id)
            );
            
            CREATE TABLE IF NOT EXISTS regulatory_basis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                law_name VARCHAR(100) NOT NULL,
                article VARCHAR(50),
                content TEXT,
                FOREIGN KEY (item_id) REFERENCES audit_items(id)
            );
            
            CREATE TABLE IF NOT EXISTS audit_item_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                source_type VARCHAR(20) NOT NULL,
                source_file VARCHAR(200),
                source_sheet VARCHAR(100),
                source_row INTEGER,
                raw_title VARCHAR(500),
                raw_data TEXT,
                import_batch VARCHAR(50),
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES audit_items(id)
            );
            
            CREATE TABLE IF NOT EXISTS audit_item_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_a_id INTEGER NOT NULL,
                item_b_id INTEGER NOT NULL,
                conflict_type VARCHAR(20) NOT NULL,
                similarity_score FLOAT,
                compare_fields TEXT,
                conflict_details TEXT,
                resolution VARCHAR(20) DEFAULT 'pending',
                resolved_by VARCHAR(50),
                resolution_note TEXT,
                resolved_at TIMESTAMP,
                FOREIGN KEY (item_a_id) REFERENCES audit_items(id),
                FOREIGN KEY (item_b_id) REFERENCES audit_items(id)
            );
            
            CREATE TABLE IF NOT EXISTS audit_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_code VARCHAR(50) UNIQUE NOT NULL,
                task_name VARCHAR(200) NOT NULL,
                target_name VARCHAR(200),
                target_type VARCHAR(50),
                target_files TEXT,
                scope_dimensions TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                auditor VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                note TEXT
            );
            
            CREATE TABLE IF NOT EXISTS audit_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL,
                finding TEXT,
                evidence TEXT,
                recommendation TEXT,
                severity VARCHAR(10),
                responsible_party VARCHAR(100),
                deadline DATE,
                rectification_status VARCHAR(20),
                auditor VARCHAR(50),
                audited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES audit_tasks(id),
                FOREIGN KEY (item_id) REFERENCES audit_items(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_items_dimension ON audit_items(dimension_id);
            CREATE INDEX IF NOT EXISTS idx_items_status ON audit_items(status);
            CREATE INDEX IF NOT EXISTS idx_procedures_item ON audit_procedures(item_id);
            CREATE INDEX IF NOT EXISTS idx_procedures_type ON audit_procedures(procedure_type);
            CREATE INDEX IF NOT EXISTS idx_sources_item ON audit_item_sources(item_id);
            CREATE INDEX IF NOT EXISTS idx_sources_batch ON audit_item_sources(import_batch);
            CREATE INDEX IF NOT EXISTS idx_conflicts_type ON audit_item_conflicts(conflict_type);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON audit_tasks(status);
            CREATE INDEX IF NOT EXISTS idx_results_task ON audit_results(task_id);
            CREATE INDEX IF NOT EXISTS idx_results_status ON audit_results(status);
        ''')
        
        conn.commit()
        print(f"数据库初始化完成: {self.db_path}")
    
    def get_or_create_dimension(self, name: str, code: str = None) -> int:
        conn = self.connect()
        cursor = conn.cursor()
        
        if code is None:
            code = name[:20].upper()
        
        cursor.execute('SELECT id FROM audit_dimensions WHERE name = ?', (name,))
        row = cursor.fetchone()
        
        if row:
            return row['id']
        
        cursor.execute('''
            INSERT INTO audit_dimensions (code, name, level, display_order)
            VALUES (?, ?, 1, 0)
        ''', (code, name))
        conn.commit()
        
        return cursor.lastrowid
    
    def insert_audit_item(self, item: Dict[str, Any]) -> int:
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_items 
            (item_code, dimension_id, title, description, severity, status, version)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            item['item_code'],
            item['dimension_id'],
            item['title'],
            item.get('description', ''),
            item.get('severity', '中'),
            'active',
            'v1'
        ))
        conn.commit()
        
        return cursor.lastrowid
    
    def insert_procedure(self, procedure: Dict[str, Any]) -> int:
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_procedures
            (item_id, procedure_text, procedure_type, source_id, is_primary)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            procedure['item_id'],
            procedure['procedure_text'],
            procedure.get('procedure_type', ''),
            procedure.get('source_id'),
            procedure.get('is_primary', 0)
        ))
        conn.commit()
        
        return cursor.lastrowid
    
    def get_procedures_by_item(self, item_id: int) -> List[Dict]:
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM audit_procedures 
            WHERE item_id = ? 
            ORDER BY is_primary DESC, id
        ''', (item_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def insert_item_source(self, source: Dict[str, Any]) -> int:
        conn = self.connect()
        cursor = conn.cursor()
        
        # 使用本地时间
        from datetime import datetime
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO audit_item_sources
            (item_id, source_type, source_file, source_sheet, source_row, raw_title, raw_data, import_batch, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            source['item_id'],
            source.get('source_type', 'excel'),
            source.get('source_file', ''),
            source.get('source_sheet', ''),
            source.get('source_row', 0),
            source.get('raw_title', ''),
            source.get('raw_data', ''),
            source.get('import_batch', ''),
            local_time
        ))
        conn.commit()
        
        return cursor.lastrowid
    
    def get_sources_by_item(self, item_id: int) -> List[Dict]:
        """获取审计项的所有来源记录"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, source_type, source_file, raw_title, import_batch, imported_at
            FROM audit_item_sources
            WHERE item_id = ?
            ORDER BY imported_at
        ''', (item_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_procedure_source(self, procedure_id: int, source_id: int) -> bool:
        """更新审计程序的来源ID"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE audit_procedures
            SET source_id = ?
            WHERE id = ?
        ''', (source_id, procedure_id))
        conn.commit()
        
        return cursor.rowcount > 0
    
    def item_exists(self, title: str) -> Optional[int]:
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM audit_items WHERE title = ?', (title,))
        row = cursor.fetchone()
        
        return row['id'] if row else None
    
    def get_all_items(self) -> List[Dict]:
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ai.*, ad.name as dimension_name, ad.code as dimension_code
            FROM audit_items ai
            JOIN audit_dimensions ad ON ai.dimension_id = ad.id
            WHERE ai.status = 'active'
            ORDER BY ai.id
        ''')
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_items_with_procedures(self) -> List[Dict]:
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ai.id, ai.item_code, ai.title, ai.dimension_id,
                   ad.name as dimension_name
            FROM audit_items ai
            JOIN audit_dimensions ad ON ai.dimension_id = ad.id
            WHERE ai.status = 'active'
            ORDER BY ai.id
        ''')
        
        items = []
        for row in cursor.fetchall():
            item = dict(row)
            item['procedures'] = self.get_procedures_by_item(item['id'])
            items.append(item)
        
        return items
    
    def get_statistics(self) -> Dict:
        conn = self.connect()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) as cnt FROM audit_dimensions')
        stats['dimensions'] = cursor.fetchone()['cnt']
        
        cursor.execute('SELECT COUNT(*) as cnt FROM audit_items')
        stats['items'] = cursor.fetchone()['cnt']
        
        cursor.execute('SELECT COUNT(*) as cnt FROM audit_item_sources')
        stats['sources'] = cursor.fetchone()['cnt']
        
        cursor.execute('''
            SELECT ad.name, COUNT(ai.id) as cnt
            FROM audit_dimensions ad
            LEFT JOIN audit_items ai ON ad.id = ai.dimension_id
            GROUP BY ad.id
            ORDER BY cnt DESC
        ''')
        stats['by_dimension'] = [(row['name'], row['cnt']) for row in cursor.fetchall()]
        
        return stats


if __name__ == '__main__':
    db = DatabaseManager()
    db.init_database()
    
    stats = db.get_statistics()
    print(f"\n数据库统计:")
    print(f"  维度数: {stats['dimensions']}")
    print(f"  审计项数: {stats['items']}")
    print(f"  来源记录数: {stats['sources']}")
