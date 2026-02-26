#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审计项清洗结果分析工具 - 主入口

Usage:
    python main.py --db-path <数据库路径> [选项]

Examples:
    python main.py --db-path tests/test_data/test_it_audit.db
    python main.py --db-path tests/test_data/test_it_audit.db --output report.html
    python main.py --db-path tests/test_data/test_it_audit.db --export-items items.csv
"""
import sys
from src.cli import main

if __name__ == '__main__':
    sys.exit(main())
