
"""
SKILL.md 文件加载器
读取 knowledge-work-plugins/ 下的所有 SKILL.md 文件
"""
import os
import re
from pathlib import Path


class SkillLoader:
    """
    SKILL.md 文件加载器
    """
    
    def __init__(self, plugins_dir="knowledge-work-plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.skills = {}
        self._load_all_skills()
    
    def _parse_frontmatter(self, content):
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if match:
            frontmatter_content = match.group(1)
            main_content = content[match.end():]
            
            frontmatter = {}
            for line in frontmatter_content.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()
            
            return frontmatter, main_content
        
        return {}, content
    
    def _load_skill_file(self, skill_path):
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frontmatter, main_content = self._parse_frontmatter(content)
            
            skill_name = frontmatter.get('name', skill_path.parent.name)
            
            return {
                'name': skill_name,
                'description': frontmatter.get('description', ''),
                'content': main_content,
                'full_content': content,
                'path': str(skill_path),
                'category': self._get_category(skill_path)
            }
        except Exception as e:
            print("  load fail: " + str(skill_path) + " " + str(e))
            return None
    
    def _get_category(self, skill_path):
        parts = skill_path.parts
        if 'legal' in parts:
            return 'legal'
        elif 'finance' in parts:
            return 'finance'
        return 'unknown'
    
    def _load_all_skills(self):
        if not self.plugins_dir.exists():
            print("  plugins dir not exist: " + str(self.plugins_dir))
            return
        
        print("  scanning plugins dir: " + str(self.plugins_dir))
        
        skill_files = list(self.plugins_dir.rglob("SKILL.md"))
        
        print("  found " + str(len(skill_files)) + " SKILL.md files")
        
        for skill_path in skill_files:
            skill = self._load_skill_file(skill_path)
            if skill:
                skill_key = skill['category'] + "." + skill['name']
                self.skills[skill_key] = skill
                print("    loaded: " + skill_key)
        
        print("  success loaded " + str(len(self.skills)) + " skills")
    
    def get_skill(self, category, name):
        key = category + "." + name
        return self.skills.get(key)
    
    def get_skills_by_category(self, category):
        result = []
        for skill in self.skills.values():
            if skill['category'] == category:
                result.append(skill)
        return result
    
    def get_all_skills(self):
        return self.skills


def create_skill_loader():
    return SkillLoader()

