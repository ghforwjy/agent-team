# -*- coding: utf-8 -*-
"""
数据加载模块

从SQLite数据库加载审计项、审计程序、来源记录等数据。
"""
import sqlite3
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from .models import AuditItem, AuditProcedure, ItemSource, DimensionStats


class DatabaseLoader:
    """数据库加载器"""

    def __init__(self, db_path: str):
        """
        初始化加载器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    def connect(self) -> 'DatabaseLoader':
        """
        连接数据库

        Returns:
            self，支持链式调用

        Raises:
            FileNotFoundError: 数据库文件不存在
            sqlite3.Error: 数据库连接错误
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")

        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            raise sqlite3.Error(f"数据库连接失败: {e}")

        return self

    def close(self) -> None:
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> 'DatabaseLoader':
        """上下文管理器入口"""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        self.close()

    def _execute(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """
        执行SQL查询

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            查询结果行列表
        """
        if not self.cursor:
            raise RuntimeError("数据库未连接，请先调用connect()")

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_statistics(self) -> Dict[str, int]:
        """
        获取基础统计数据

        Returns:
            包含各项统计数据的字典
        """
        stats = {}

        # 审计项总数
        rows = self._execute("SELECT COUNT(*) FROM audit_items")
        stats['total_items'] = rows[0][0] if rows else 0

        # 审计程序总数
        rows = self._execute("SELECT COUNT(*) FROM audit_procedures")
        stats['total_procedures'] = rows[0][0] if rows else 0

        # 来源记录总数
        rows = self._execute("SELECT COUNT(*) FROM audit_item_sources")
        stats['total_sources'] = rows[0][0] if rows else 0

        # 维度总数
        rows = self._execute("SELECT COUNT(*) FROM audit_dimensions")
        stats['total_dimensions'] = rows[0][0] if rows else 0

        return stats

    def load_audit_items(self, dimension: Optional[str] = None) -> List[AuditItem]:
        """
        加载审计项列表

        Args:
            dimension: 按维度筛选（可选）

        Returns:
            审计项列表
        """
        query = """
            SELECT i.id, i.item_code, i.title, i.description,
                   i.severity, i.status, i.created_at, i.updated_at,
                   d.name as dimension
            FROM audit_items i
            LEFT JOIN audit_dimensions d ON i.dimension_id = d.id
        """
        params = ()

        if dimension:
            query += " WHERE d.name = ?"
            params = (dimension,)

        query += " ORDER BY i.id"

        rows = self._execute(query, params)

        items = []
        for row in rows:
            item = AuditItem(
                id=row['id'],
                item_code=row['item_code'],
                title=row['title'],
                dimension=row['dimension'] or '未分类',
                description=row['description'],
                severity=row['severity'] or '中',
                status=row['status'] or 'active',
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            items.append(item)

        return items

    def load_procedures_by_item(self, item_id: int) -> List[AuditProcedure]:
        """
        加载指定审计项的所有程序

        Args:
            item_id: 审计项ID

        Returns:
            审计程序列表
        """
        query = """
            SELECT p.id, p.item_id, p.procedure_text,
                   p.procedure_type, p.is_primary, p.source_id, p.created_at,
                   i.title as item_title
            FROM audit_procedures p
            LEFT JOIN audit_items i ON p.item_id = i.id
            WHERE p.item_id = ?
            ORDER BY p.is_primary DESC, p.id
        """

        rows = self._execute(query, (item_id,))

        procedures = []
        for row in rows:
            proc = AuditProcedure(
                id=row['id'],
                item_id=row['item_id'],
                item_title=row['item_title'],
                procedure_text=row['procedure_text'],
                procedure_type=row['procedure_type'],
                is_primary=bool(row['is_primary']),
                source_id=row['source_id'],
                created_at=row['created_at']
            )
            procedures.append(proc)

        return procedures

    def load_all_procedures(self) -> List[AuditProcedure]:
        """
        加载所有审计程序

        Returns:
            审计程序列表
        """
        query = """
            SELECT p.id, p.item_id, p.procedure_text,
                   p.procedure_type, p.is_primary, p.source_id, p.created_at,
                   i.title as item_title
            FROM audit_procedures p
            LEFT JOIN audit_items i ON p.item_id = i.id
            ORDER BY p.item_id, p.is_primary DESC, p.id
        """

        rows = self._execute(query)

        procedures = []
        for row in rows:
            proc = AuditProcedure(
                id=row['id'],
                item_id=row['item_id'],
                item_title=row['item_title'],
                procedure_text=row['procedure_text'],
                procedure_type=row['procedure_type'],
                is_primary=bool(row['is_primary']),
                source_id=row['source_id'],
                created_at=row['created_at']
            )
            procedures.append(proc)

        return procedures

    def load_sources_by_item(self, item_id: int) -> List[ItemSource]:
        """
        加载指定审计项的所有来源记录

        Args:
            item_id: 审计项ID

        Returns:
            来源记录列表
        """
        query = """
            SELECT id, item_id, source_type, source_file,
                   source_sheet, source_row, raw_title,
                   import_batch, imported_at
            FROM audit_item_sources
            WHERE item_id = ?
            ORDER BY imported_at DESC
        """

        rows = self._execute(query, (item_id,))

        sources = []
        for row in rows:
            source = ItemSource(
                id=row['id'],
                item_id=row['item_id'],
                source_type=row['source_type'],
                source_file=row['source_file'],
                source_sheet=row['source_sheet'],
                source_row=row['source_row'],
                raw_title=row['raw_title'],
                import_batch=row['import_batch'],
                imported_at=row['imported_at']
            )
            sources.append(source)

        return sources

    def load_dimension_stats(self) -> List[DimensionStats]:
        """
        加载各维度的统计数据

        Returns:
            维度统计列表
        """
        query = """
            SELECT
                d.name as dimension_name,
                COUNT(DISTINCT i.id) as item_count,
                COUNT(DISTINCT p.id) as procedure_count
            FROM audit_dimensions d
            LEFT JOIN audit_items i ON d.id = i.dimension_id
            LEFT JOIN audit_procedures p ON i.id = p.item_id
            GROUP BY d.id, d.name
            ORDER BY item_count DESC
        """

        rows = self._execute(query)

        stats = []
        for row in rows:
            stat = DimensionStats(
                dimension_name=row['dimension_name'],
                item_count=row['item_count'],
                procedure_count=row['procedure_count']
            )
            stats.append(stat)

        return stats

    def load_items_with_details(self, dimension: Optional[str] = None) -> List[AuditItem]:
        """
        加载审计项及其关联的详细数据

        Args:
            dimension: 按维度筛选（可选）

        Returns:
            包含详细数据的审计项列表
        """
        # 加载基础审计项
        items = self.load_audit_items(dimension)

        # 加载每个审计项的程序和来源
        for item in items:
            item.procedures = self.load_procedures_by_item(item.id)
            item.sources = self.load_sources_by_item(item.id)
            item.procedure_count = len(item.procedures)
            item.source_count = len(item.sources)

        return items

    def get_procedure_stats(self) -> Dict[str, Any]:
        """
        获取审计程序统计信息

        Returns:
            程序统计数据字典
        """
        stats = {}

        # 程序长度统计
        query = """
            SELECT
                MIN(LENGTH(procedure_text)) as min_length,
                MAX(LENGTH(procedure_text)) as max_length,
                AVG(LENGTH(procedure_text)) as avg_length,
                COUNT(CASE WHEN LENGTH(procedure_text) = 0 OR procedure_text IS NULL THEN 1 END) as empty_count
            FROM audit_procedures
        """
        rows = self._execute(query)
        if rows:
            row = rows[0]
            stats['min_length'] = row['min_length'] or 0
            stats['max_length'] = row['max_length'] or 0
            stats['avg_length'] = round(row['avg_length'] or 0, 2)
            stats['empty_count'] = row['empty_count']

        # 每个审计项的程序数统计
        query = """
            SELECT
                COUNT(*) as item_count,
                procedure_count
            FROM (
                SELECT item_id, COUNT(*) as procedure_count
                FROM audit_procedures
                GROUP BY item_id
            )
            GROUP BY procedure_count
            ORDER BY procedure_count
        """
        rows = self._execute(query)
        stats['distribution'] = {row['procedure_count']: row['item_count'] for row in rows}

        return stats
