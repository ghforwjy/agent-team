# -*- coding: utf-8 -*-
"""
数据模型模块

定义审计项、审计程序、来源记录等数据模型。
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ItemSource:
    """审计项来源记录"""
    id: int
    item_id: int
    source_type: str
    source_file: Optional[str] = None
    source_sheet: Optional[str] = None
    source_row: Optional[int] = None
    raw_title: Optional[str] = None
    import_batch: Optional[str] = None
    imported_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'item_id': self.item_id,
            'source_type': self.source_type,
            'source_file': self.source_file,
            'source_sheet': self.source_sheet,
            'source_row': self.source_row,
            'raw_title': self.raw_title,
            'import_batch': self.import_batch,
            'imported_at': self.imported_at
        }


@dataclass
class AuditProcedure:
    """审计程序（审计动作）"""
    id: int
    item_id: int
    procedure_text: str
    item_title: Optional[str] = None  # 冗余字段，方便展示
    procedure_type: Optional[str] = None
    is_primary: bool = False
    source_id: Optional[int] = None  # 关联的来源ID
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'item_id': self.item_id,
            'item_title': self.item_title,
            'procedure_text': self.procedure_text,
            'procedure_type': self.procedure_type,
            'is_primary': self.is_primary,
            'source_id': self.source_id,
            'created_at': self.created_at
        }

    def __str__(self) -> str:
        """字符串表示"""
        text = self.procedure_text[:50] + '...' if len(self.procedure_text) > 50 else self.procedure_text
        return f"AuditProcedure(id={self.id}, item_id={self.item_id}, text='{text}')"


@dataclass
class AuditItem:
    """审计项"""
    id: int
    item_code: str
    title: str
    dimension: str
    description: Optional[str] = None
    severity: str = '中'
    status: str = 'active'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # 关联数据
    procedures: List[AuditProcedure] = field(default_factory=list)
    sources: List[ItemSource] = field(default_factory=list)

    # 统计字段（由分析器计算）
    procedure_count: int = 0
    source_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'item_code': self.item_code,
            'title': self.title,
            'dimension': self.dimension,
            'description': self.description,
            'severity': self.severity,
            'status': self.status,
            'procedure_count': self.procedure_count,
            'source_count': self.source_count,
            'procedures': [p.to_dict() for p in self.procedures],
            'sources': [s.to_dict() for s in self.sources]
        }

    def __str__(self) -> str:
        """字符串表示"""
        title = self.title[:40] + '...' if len(self.title) > 40 else self.title
        return f"AuditItem(id={self.id}, code='{self.item_code}', title='{title}', dimension='{self.dimension}')"


@dataclass
class DimensionStats:
    """维度统计"""
    dimension_name: str
    item_count: int
    procedure_count: int

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'dimension_name': self.dimension_name,
            'item_count': self.item_count,
            'procedure_count': self.procedure_count
        }


@dataclass
class AnalysisResult:
    """分析结果"""
    # 基础统计
    total_items: int = 0
    total_procedures: int = 0
    total_sources: int = 0
    total_dimensions: int = 0

    # 平均值
    avg_procedures_per_item: float = 0.0
    avg_sources_per_item: float = 0.0

    # 分布统计
    items_with_multiple_procedures: int = 0
    max_procedures_count: int = 0

    # 维度统计
    dimension_stats: List[DimensionStats] = field(default_factory=list)

    # 详细数据
    items: List[AuditItem] = field(default_factory=list)
    procedures: List[AuditProcedure] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_items': self.total_items,
            'total_procedures': self.total_procedures,
            'total_sources': self.total_sources,
            'total_dimensions': self.total_dimensions,
            'avg_procedures_per_item': self.avg_procedures_per_item,
            'avg_sources_per_item': self.avg_sources_per_item,
            'items_with_multiple_procedures': self.items_with_multiple_procedures,
            'max_procedures_count': self.max_procedures_count,
            'dimension_stats': [d.to_dict() for d in self.dimension_stats],
            'items': [i.to_dict() for i in self.items],
            'procedures': [p.to_dict() for p in self.procedures]
        }
