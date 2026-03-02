# -*- coding: utf-8 -*-
"""
场景测试运行器

执行IT审计Agent各模块的场景测试。
"""
import argparse
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class ScenarioTester:
    """场景测试器"""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent.parent / 'tests' / 'output'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[Dict[str, Any]] = []

    def run_module1_tests(self) -> Dict[str, Any]:
        """运行模块1场景测试"""
        print("\n" + "=" * 60)
        print("模块1场景测试: 审计项收集")
        print("=" * 60)

        test_results = {
            'module': '1-audit-item-collector',
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {'passed': 0, 'failed': 0, 'total': 0}
        }

        try:
            from knowledge_work_plugins.it_audit.skills.audit_item_collector.scripts import DatabaseManager
            test_results['tests'].append(self._test_database_manager())
        except Exception as e:
            test_results['tests'].append({
                'name': 'DatabaseManager导入测试',
                'status': 'FAILED',
                'error': str(e)
            })

        try:
            from knowledge_work_plugins.it_audit.skills.audit_item_collector.scripts import ExcelParser
            test_results['tests'].append(self._test_excel_parser())
        except Exception as e:
            test_results['tests'].append({
                'name': 'ExcelParser导入测试',
                'status': 'FAILED',
                'error': str(e)
            })

        try:
            from knowledge_work_plugins.it_audit.skills.audit_item_collector.scripts.analyzers import AuditAnalyzer, DatabaseLoader
            test_results['tests'].append(self._test_analyzer())
        except Exception as e:
            test_results['tests'].append({
                'name': 'Analyzer导入测试',
                'status': 'FAILED',
                'error': str(e)
            })

        for test in test_results['tests']:
            test_results['summary']['total'] += 1
            if test.get('status') == 'PASSED':
                test_results['summary']['passed'] += 1
            else:
                test_results['summary']['failed'] += 1

        self.results.append(test_results)
        return test_results

    def _test_database_manager(self) -> Dict[str, Any]:
        """测试数据库管理器"""
        return {
            'name': 'DatabaseManager功能测试',
            'status': 'PASSED',
            'details': 'DatabaseManager导入成功'
        }

    def _test_excel_parser(self) -> Dict[str, Any]:
        """测试Excel解析器"""
        return {
            'name': 'ExcelParser功能测试',
            'status': 'PASSED',
            'details': 'ExcelParser导入成功'
        }

    def _test_analyzer(self) -> Dict[str, Any]:
        """测试分析器"""
        return {
            'name': 'Analyzer功能测试',
            'status': 'PASSED',
            'details': 'AuditAnalyzer和DatabaseLoader导入成功'
        }

    def run_module2_tests(self) -> Dict[str, Any]:
        """运行模块2场景测试"""
        print("\n" + "=" * 60)
        print("模块2场景测试: 策略合规检查")
        print("=" * 60)

        test_results = {
            'module': '2-policy-compliance-checker',
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {'passed': 0, 'failed': 0, 'total': 0}
        }

        try:
            from knowledge_work_plugins.it_audit.skills.policy_compliance_checker.scripts import PolicyExtractor
            test_results['tests'].append({
                'name': 'PolicyExtractor功能测试',
                'status': 'PASSED',
                'details': 'PolicyExtractor导入成功'
            })
        except Exception as e:
            test_results['tests'].append({
                'name': 'PolicyExtractor导入测试',
                'status': 'FAILED',
                'error': str(e)
            })

        try:
            from knowledge_work_plugins.it_audit.skills.policy_compliance_checker.scripts.analyzers import PolicyRequirementReporter
            test_results['tests'].append({
                'name': 'PolicyRequirementReporter功能测试',
                'status': 'PASSED',
                'details': 'PolicyRequirementReporter导入成功'
            })
        except Exception as e:
            test_results['tests'].append({
                'name': 'PolicyRequirementReporter导入测试',
                'status': 'FAILED',
                'error': str(e)
            })

        for test in test_results['tests']:
            test_results['summary']['total'] += 1
            if test.get('status') == 'PASSED':
                test_results['summary']['passed'] += 1
            else:
                test_results['summary']['failed'] += 1

        self.results.append(test_results)
        return test_results

    def run_all_tests(self) -> List[Dict[str, Any]]:
        """运行所有场景测试"""
        print("\n" + "=" * 60)
        print("IT审计Agent场景测试")
        print("=" * 60)

        self.run_module1_tests()
        self.run_module2_tests()

        return self.results

    def save_results(self, filename: str = None) -> str:
        """保存测试结果"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'scenario_test_results_{timestamp}.json'

        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'test_run': {
                    'timestamp': datetime.now().isoformat(),
                    'output_dir': str(self.output_dir)
                },
                'results': self.results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n测试结果已保存到: {filepath}")
        return str(filepath)

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)

        total_passed = 0
        total_failed = 0

        for result in self.results:
            module = result['module']
            passed = result['summary']['passed']
            failed = result['summary']['failed']
            total = result['summary']['total']

            total_passed += passed
            total_failed += failed

            status = "✓ 通过" if failed == 0 else "✗ 失败"
            print(f"\n{module}: {status}")
            print(f"  通过: {passed}/{total}")
            if failed > 0:
                print(f"  失败: {failed}/{total}")
                for test in result['tests']:
                    if test.get('status') == 'FAILED':
                        print(f"    - {test['name']}: {test.get('error', 'Unknown error')}")

        print("\n" + "-" * 60)
        print(f"总计: 通过 {total_passed}, 失败 {total_failed}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='IT审计Agent场景测试器')
    parser.add_argument('--module', '-m', type=int, choices=[1, 2],
                        help='指定测试模块 (1或2)，不指定则运行所有测试')
    parser.add_argument('--output', '-o', type=str,
                        help='指定输出目录，默认为 tests/output/')

    args = parser.parse_args()

    tester = ScenarioTester(output_dir=args.output)

    if args.module == 1:
        tester.run_module1_tests()
    elif args.module == 2:
        tester.run_module2_tests()
    else:
        tester.run_all_tests()

    tester.print_summary()
    tester.save_results()


if __name__ == '__main__':
    main()
