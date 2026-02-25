# -*- coding: utf-8 -*-
"""
IT审计专家Agent - Excel解析器
负责解析各种格式的Excel检查底稿
"""
import pandas as pd
import os
from typing import Dict, List, Any, Optional
import hashlib


class ExcelParser:
    """Excel文件解析器"""
    
    COLUMN_MAPPING = {
        "dimension": {
            "standard": "dimension",
            "aliases": ["一级主题", "项目", "审计领域", "检查类别", "维度", "领域", "主题"],
            "required": True
        },
        "title": {
            "standard": "title",
            "aliases": ["审计项", "标题", "检查项", "问题", "项目名称", "检查内容"],
            "required": True
        },
        "audit_procedure": {
            "standard": "audit_procedure",
            "aliases": ["审计程序", "检查方法", "检查程序", "审计方法", "检查要点"],
            "required": False
        },
        "description": {
            "standard": "description",
            "aliases": ["存在问题", "检查内容", "描述", "问题描述", "详细描述"],
            "required": False
        },
        "severity": {
            "standard": "severity",
            "aliases": ["严重程度", "风险等级", "重要性", "优先级"],
            "required": False,
            "default": "中"
        }
    }
    
    SEVERITY_MAPPING = {
        "高": ["高", "重大", "关键", "严重", "high", "critical", "major"],
        "中": ["中", "一般", "medium", "moderate"],
        "低": ["低", "轻微", "low", "minor"]
    }
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self._raw_data = None
        self._sheets_info = []
    
    def analyze_structure(self) -> Dict[str, Any]:
        ext = os.path.splitext(self.file_path)[1].lower()
        
        if ext in ['.xls', '.xlsx']:
            return self._analyze_excel()
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    def _analyze_excel(self) -> Dict[str, Any]:
        df_dict = pd.read_excel(self.file_path, sheet_name=None, header=None)
        
        result = {
            "file_name": self.file_name,
            "sheets": [],
            "total_rows": 0
        }
        
        for sheet_name, df in df_dict.items():
            sheet_info = self._analyze_sheet(df, sheet_name)
            result["sheets"].append(sheet_info)
            result["total_rows"] += sheet_info["data_rows"]
        
        self._sheets_info = result["sheets"]
        return result
    
    def _analyze_sheet(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        header_row = self._find_header_row(df)
        
        if header_row is not None:
            df_clean = pd.read_excel(
                self.file_path, 
                sheet_name=sheet_name, 
                header=header_row
            )
        else:
            df_clean = df
        
        column_mapping = self._detect_column_mapping(df_clean)
        
        data_rows = len(df_clean)
        for col in df_clean.columns:
            if df_clean[col].isna().all():
                data_rows = 0
                break
        
        return {
            "sheet_name": sheet_name,
            "header_row": header_row,
            "columns": list(df_clean.columns),
            "column_mapping": column_mapping,
            "data_rows": data_rows,
            "shape": df_clean.shape
        }
    
    def _find_header_row(self, df: pd.DataFrame, max_search: int = 10) -> Optional[int]:
        all_aliases = []
        for field_config in self.COLUMN_MAPPING.values():
            all_aliases.extend(field_config["aliases"])
        
        for i in range(min(max_search, len(df))):
            row = df.iloc[i]
            row_values = [str(v).strip() for v in row.values if pd.notna(v)]
            
            matches = sum(1 for v in row_values if v in all_aliases)
            
            if matches >= 2:
                return i
        
        return None
    
    def _detect_column_mapping(self, df: pd.DataFrame) -> Dict[str, str]:
        mapping = {}
        columns = [str(c).strip() for c in df.columns]
        
        for field, config in self.COLUMN_MAPPING.items():
            for col in columns:
                if col in config["aliases"]:
                    mapping[field] = col
                    break
        
        return mapping
    
    def parse(self, sheet_name: str = None) -> List[Dict[str, Any]]:
        ext = os.path.splitext(self.file_path)[1].lower()
        
        if ext in ['.xls', '.xlsx']:
            return self._parse_excel(sheet_name)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    def _parse_excel(self, sheet_name: str = None) -> List[Dict[str, Any]]:
        items = []
        
        df_dict = pd.read_excel(self.file_path, sheet_name=None, header=None)
        
        sheets_to_parse = [sheet_name] if sheet_name else list(df_dict.keys())
        
        for sname in sheets_to_parse:
            if sname not in df_dict:
                continue
            
            df_raw = df_dict[sname]
            header_row = self._find_header_row(df_raw)
            
            if header_row is not None:
                df = pd.read_excel(
                    self.file_path,
                    sheet_name=sname,
                    header=header_row
                )
            else:
                df = df_raw
            
            sheet_items = self._extract_items(df, sname)
            items.extend(sheet_items)
        
        return items
    
    def _extract_items(self, df: pd.DataFrame, sheet_name: str) -> List[Dict[str, Any]]:
        items = []
        column_mapping = self._detect_column_mapping(df)
        
        if "title" not in column_mapping:
            return items
        
        title_col = column_mapping["title"]
        
        for idx, row in df.iterrows():
            title = row.get(title_col)
            
            if pd.isna(title) or str(title).strip() == '':
                continue
            
            if str(title).strip() in self.COLUMN_MAPPING["title"]["aliases"]:
                continue
            
            item = {
                "title": str(title).strip(),
                "source_sheet": sheet_name,
                "source_row": idx + 1,
                "raw_data": {}
            }
            
            if "dimension" in column_mapping:
                dim_val = row.get(column_mapping["dimension"])
                if pd.notna(dim_val):
                    item["dimension"] = str(dim_val).strip()
            
            if "audit_procedure" in column_mapping:
                proc_val = row.get(column_mapping["audit_procedure"])
                if pd.notna(proc_val):
                    item["audit_procedure"] = str(proc_val).strip()
            
            if "description" in column_mapping:
                desc_val = row.get(column_mapping["description"])
                if pd.notna(desc_val):
                    item["description"] = str(desc_val).strip()
            
            if "severity" in column_mapping:
                sev_val = row.get(column_mapping["severity"])
                if pd.notna(sev_val):
                    item["severity"] = self._normalize_severity(str(sev_val).strip())
            
            for col in df.columns:
                val = row.get(col)
                if pd.notna(val):
                    item["raw_data"][str(col)] = str(val)
            
            items.append(item)
        
        return items
    
    def _normalize_severity(self, value: str) -> str:
        value_lower = value.lower()
        
        for severity, aliases in self.SEVERITY_MAPPING.items():
            if value in aliases or value_lower in [a.lower() for a in aliases]:
                return severity
        
        return "中"
    
    def generate_item_code(self, item: Dict[str, Any], index: int) -> str:
        dimension = item.get("dimension", "GEN")
        
        if dimension:
            dim_code = dimension[:3].upper()
        else:
            dim_code = "GEN"
        
        code = f"{dim_code}-{index:04d}"
        return code


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "训练材料/2021年网络安全专自查底稿.xls"
    
    parser = ExcelParser(file_path)
    
    print("=" * 60)
    print("Excel文件结构分析")
    print("=" * 60)
    
    structure = parser.analyze_structure()
    print(f"\n文件名: {structure['file_name']}")
    print(f"总数据行: {structure['total_rows']}")
    
    for sheet in structure['sheets']:
        print(f"\n--- Sheet: {sheet['sheet_name']} ---")
        print(f"表头行: {sheet['header_row']}")
        print(f"数据行: {sheet['data_rows']}")
        print(f"列名映射: {sheet['column_mapping']}")
    
    print("\n" + "=" * 60)
    print("解析审计项")
    print("=" * 60)
    
    items = parser.parse()
    print(f"\n共解析出 {len(items)} 条审计项")
    
    if items:
        print("\n前5条审计项示例:")
        for i, item in enumerate(items[:5], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   维度: {item.get('dimension', 'N/A')}")
            print(f"   审计程序: {item.get('audit_procedure', 'N/A')[:50]}...")
