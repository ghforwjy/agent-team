# -*- coding: utf-8 -*-
"""
测试HTML报告中的来源角标功能
"""
import unittest
import re
from pathlib import Path


class TestReportSources(unittest.TestCase):
    """测试报告来源角标功能"""

    @classmethod
    def setUpClass(cls):
        """加载HTML报告内容"""
        cls.report_path = Path(__file__).parent.parent / 'output' / 'report_with_sources.html'
        if not cls.report_path.exists():
            raise FileNotFoundError(f"报告文件不存在: {cls.report_path}")

        with open(cls.report_path, 'r', encoding='utf-8') as f:
            cls.html_content = f.read()

    def test_audit_item_source_badges_exist(self):
        """测试审计项有来源角标"""
        # 查找审计项标题旁的来源角标
        pattern = r'<td[^>]*class="item-title"[^>]*>.*?<span class="source-badge"[^>]*>\d+</span>'
        matches = re.findall(pattern, self.html_content, re.DOTALL)
        self.assertGreater(len(matches), 0, "审计项应该有来源角标")
        print(f"✓ 找到 {len(matches)} 个审计项来源角标")

    def test_procedure_source_badges_exist(self):
        """测试审计程序有来源角标"""
        # 查找审计程序内容旁的来源角标
        pattern = r'<td[^>]*class="procedure-text"[^>]*>.*?<span class="source-badge"[^>]*>\d+</span>'
        matches = re.findall(pattern, self.html_content, re.DOTALL)
        self.assertGreater(len(matches), 0, "审计程序应该有来源角标")
        print(f"✓ 找到 {len(matches)} 个审计程序来源角标")

    def test_source_badge_click_handler(self):
        """测试来源角标有正确的点击事件"""
        # 检查审计项角标有showSources函数
        pattern = r'onclick="showSources\(\d+\)"'
        matches = re.findall(pattern, self.html_content)
        self.assertGreater(len(matches), 0, "审计项角标应该有showSources点击事件")
        print(f"✓ 找到 {len(matches)} 个showSources点击事件")

        # 检查审计程序角标有showProcSource函数
        pattern = r'onclick="showProcSource\(\d+\)"'
        matches = re.findall(pattern, self.html_content)
        self.assertGreater(len(matches), 0, "审计程序角标应该有showProcSource点击事件")
        print(f"✓ 找到 {len(matches)} 个showProcSource点击事件")

    def test_javascript_functions_exist(self):
        """测试JavaScript函数存在"""
        # 检查showSources函数
        self.assertIn('function showSources(itemId)', self.html_content,
                      "应该有showSources函数")
        print("✓ showSources函数存在")

        # 检查showProcSource函数
        self.assertIn('function showProcSource(sourceId)', self.html_content,
                      "应该有showProcSource函数")
        print("✓ showProcSource函数存在")

        # 检查closePopup函数
        self.assertIn('function closePopup(event)', self.html_content,
                      "应该有closePopup函数")
        print("✓ closePopup函数存在")

    def test_source_data_javascript(self):
        """测试来源数据在JavaScript中"""
        # 检查sourcesData变量
        self.assertIn('const sourcesData =', self.html_content,
                      "应该有sourcesData变量")
        print("✓ sourcesData变量存在")

        # 检查sourceIdMap变量
        self.assertIn('const sourceIdMap =', self.html_content,
                      "应该有sourceIdMap变量")
        print("✓ sourceIdMap变量存在")

    def test_source_popup_html(self):
        """测试来源弹窗HTML结构"""
        # 检查弹窗容器
        self.assertIn('id="sourcePopup"', self.html_content,
                      "应该有sourcePopup弹窗容器")
        print("✓ sourcePopup弹窗容器存在")

        # 检查来源列表
        self.assertIn('id="sourceList"', self.html_content,
                      "应该有sourceList来源列表")
        print("✓ sourceList来源列表存在")

    def test_source_badge_style(self):
        """测试来源角标样式"""
        # 检查.source-badge样式定义
        self.assertIn('.source-badge', self.html_content,
                      "应该有.source-badge样式定义")
        print("✓ .source-badge样式定义存在")

        # 检查背景色和文字颜色
        pattern = r'\.source-badge\s*\{[^}]*background:\s*#e8e8e8'
        self.assertRegex(self.html_content, pattern,
                         "来源角标应该有灰色背景")
        print("✓ 来源角标有灰色背景")

        pattern = r'\.source-badge\s*\{[^}]*color:\s*#52c41a'
        self.assertRegex(self.html_content, pattern,
                         "来源角标应该有绿色文字")
        print("✓ 来源角标有绿色文字")

    def test_source_file_not_na(self):
        """测试来源名称不是N/A"""
        # 检查JavaScript中的来源数据不包含N/A
        # 提取sourcesData部分
        pattern = r'const sourcesData = (\[.*?\]);'
        match = re.search(pattern, self.html_content, re.DOTALL)
        if match:
            sources_data = match.group(1)
            # 检查是否还有N/A（应该没有，因为已经用source_type替换了）
            na_count = sources_data.count('"N/A"')
            self.assertEqual(na_count, 0,
                             f"来源数据中不应该有N/A，但找到了{na_count}个")
            print(f"✓ 来源数据中没有N/A")

    def test_report_summary(self):
        """测试报告摘要信息"""
        print("\n=== 报告摘要 ===")

        # 统计审计项数量
        item_pattern = r'<tr class="item-header">'
        item_count = len(re.findall(item_pattern, self.html_content))
        print(f"审计项行数: {item_count}")

        # 统计审计程序数量
        proc_pattern = r'<td[^>]*class="procedure-text"[^>]*>'
        proc_count = len(re.findall(proc_pattern, self.html_content))
        print(f"审计程序单元格数: {proc_count}")

        # 统计来源角标数量
        badge_pattern = r'<span class="source-badge"[^>]*>\d+</span>'
        badge_count = len(re.findall(badge_pattern, self.html_content))
        print(f"来源角标总数: {badge_count}")

        print("================\n")


if __name__ == '__main__':
    unittest.main(verbosity=2)
