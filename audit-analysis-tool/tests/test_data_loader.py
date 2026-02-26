# -*- coding: utf-8 -*-
"""
数据加载模块单元测试
"""
import unittest
import sqlite3
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import DatabaseLoader
from src.models import AuditItem, AuditProcedure, ItemSource


class TestDatabaseLoader(unittest.TestCase):
    """测试DatabaseLoader类"""

    def setUp(self):
        """测试前准备：创建临时数据库"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')

        # 创建测试数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建表结构
        cursor.executescript('''
            CREATE TABLE dimensions (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );

            CREATE TABLE audit_items (
                id INTEGER PRIMARY KEY,
                item_code TEXT NOT NULL,
                dimension_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                severity TEXT DEFAULT '中',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dimension_id) REFERENCES dimensions(id)
            );

            CREATE TABLE audit_procedures (
                id INTEGER PRIMARY KEY,
                item_id INTEGER NOT NULL,
                procedure_text TEXT NOT NULL,
                procedure_type TEXT,
                is_primary INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES audit_items(id)
            );

            CREATE TABLE item_sources (
                id INTEGER PRIMARY KEY,
                item_id INTEGER NOT NULL,
                source_type TEXT NOT NULL,
                source_file TEXT,
                source_sheet TEXT,
                source_row INTEGER,
                raw_title TEXT,
                import_batch TEXT,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES audit_items(id)
            );
        ''')

        # 插入测试数据
        cursor.executemany('INSERT INTO dimensions (id, name) VALUES (?, ?)', [
            (1, '安全'),
            (2, '合规'),
            (3, '运维')
        ])

        cursor.executemany('''
            INSERT INTO audit_items (id, item_code, dimension_id, title, description, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [
            (1, 'SEC-001', 1, '检查防火墙配置', '检查防火墙规则是否正确', '高'),
            (2, 'SEC-002', 1, '检查访问控制', '检查用户权限设置', '中'),
            (3, 'COM-001', 2, '检查合规文档', '检查合规性文档完整性', '中')
        ])

        cursor.executemany('''
            INSERT INTO audit_procedures (id, item_id, procedure_text, is_primary)
            VALUES (?, ?, ?, ?)
        ''', [
            (1, 1, '查看防火墙配置文件', 1),
            (2, 1, '检查防火墙日志', 0),
            (3, 2, '查看用户权限列表', 1),
            (4, 3, '检查文档完整性', 1)
        ])

        cursor.executemany('''
            INSERT INTO item_sources (id, item_id, source_type, source_file, raw_title)
            VALUES (?, ?, ?, ?, ?)
        ''', [
            (1, 1, 'excel', 'test.xlsx', '防火墙配置检查'),
            (2, 1, 'excel', 'test.xlsx', '防火墙规则检查'),
            (3, 2, 'excel', 'test.xlsx', '访问控制检查'),
            (4, 3, 'manual', None, '合规文档检查')
        ])

        conn.commit()
        conn.close()

        self.loader = DatabaseLoader(self.db_path)

    def tearDown(self):
        """测试后清理"""
        self.loader.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_connect_success(self):
        """测试成功连接数据库"""
        result = self.loader.connect()
        self.assertIsInstance(result, DatabaseLoader)
        self.assertIsNotNone(self.loader.conn)
        self.assertIsNotNone(self.loader.cursor)

    def test_connect_file_not_found(self):
        """测试连接不存在的文件"""
        loader = DatabaseLoader('/nonexistent/path.db')
        with self.assertRaises(FileNotFoundError):
            loader.connect()

    def test_context_manager(self):
        """测试上下文管理器"""
        with DatabaseLoader(self.db_path) as loader:
            self.assertIsNotNone(loader.conn)
        # 退出上下文后应自动关闭
        self.assertIsNone(loader.conn)

    def test_get_statistics(self):
        """测试获取统计数据"""
        with self.loader:
            stats = self.loader.get_statistics()

        self.assertEqual(stats['total_items'], 3)
        self.assertEqual(stats['total_procedures'], 4)
        self.assertEqual(stats['total_sources'], 4)
        self.assertEqual(stats['total_dimensions'], 3)

    def test_load_audit_items(self):
        """测试加载审计项"""
        with self.loader:
            items = self.loader.load_audit_items()

        self.assertEqual(len(items), 3)
        self.assertIsInstance(items[0], AuditItem)
        self.assertEqual(items[0].title, '检查防火墙配置')
        self.assertEqual(items[0].dimension, '安全')

    def test_load_audit_items_by_dimension(self):
        """测试按维度筛选审计项"""
        with self.loader:
            items = self.loader.load_audit_items(dimension='安全')

        self.assertEqual(len(items), 2)
        for item in items:
            self.assertEqual(item.dimension, '安全')

    def test_load_procedures_by_item(self):
        """测试加载指定审计项的程序"""
        with self.loader:
            procedures = self.loader.load_procedures_by_item(1)

        self.assertEqual(len(procedures), 2)
        self.assertIsInstance(procedures[0], AuditProcedure)
        self.assertEqual(procedures[0].item_id, 1)
        self.assertTrue(procedures[0].is_primary)

    def test_load_all_procedures(self):
        """测试加载所有程序"""
        with self.loader:
            procedures = self.loader.load_all_procedures()

        self.assertEqual(len(procedures), 4)
        self.assertIsInstance(procedures[0], AuditProcedure)

    def test_load_sources_by_item(self):
        """测试加载来源记录"""
        with self.loader:
            sources = self.loader.load_sources_by_item(1)

        self.assertEqual(len(sources), 2)
        self.assertIsInstance(sources[0], ItemSource)
        self.assertEqual(sources[0].item_id, 1)

    def test_load_dimension_stats(self):
        """测试加载维度统计"""
        with self.loader:
            stats = self.loader.load_dimension_stats()

        self.assertEqual(len(stats), 3)
        # 安全维度有2个审计项，3个程序
        security_stat = next(s for s in stats if s.dimension_name == '安全')
        self.assertEqual(security_stat.item_count, 2)
        self.assertEqual(security_stat.procedure_count, 3)

    def test_load_items_with_details(self):
        """测试加载带详细数据的审计项"""
        with self.loader:
            items = self.loader.load_items_with_details()

        self.assertEqual(len(items), 3)
        # 检查第一个审计项的详细数据
        item = items[0]
        self.assertEqual(len(item.procedures), 2)
        self.assertEqual(len(item.sources), 2)
        self.assertEqual(item.procedure_count, 2)
        self.assertEqual(item.source_count, 2)

    def test_get_procedure_stats(self):
        """测试获取程序统计"""
        with self.loader:
            stats = self.loader.get_procedure_stats()

        self.assertIn('min_length', stats)
        self.assertIn('max_length', stats)
        self.assertIn('avg_length', stats)
        self.assertIn('empty_count', stats)
        self.assertIn('distribution', stats)

        # 检查分布：1个审计项有2个程序，2个审计项各有1个程序
        self.assertEqual(stats['distribution'].get(1), 2)
        self.assertEqual(stats['distribution'].get(2), 1)


if __name__ == '__main__':
    unittest.main()
