# -*- coding: utf-8 -*-
"""
下载 sentence-transformers 模型
"""
import os
import sys
import requests
from tqdm import tqdm

# 设置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:1080'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:1080'

# 模型信息
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
BASE_URL = f'https://huggingface.co/sentence-transformers/{MODEL_NAME}/resolve/main/'

# 目标目录
TARGET_DIR = os.path.join(os.path.dirname(__file__), 'model', 'Sentence-BERT')

# 确保目录存在
os.makedirs(TARGET_DIR, exist_ok=True)

# 需要下载的文件
FILES = [
    'config.json',
    'config_sentence_transformers.json',
    'model.safetensors',
    'modules.json',
    'sentence_bert_config.json',
    'tokenizer_config.json',
    'tokenizer.json',
    'vocab.txt'
]

def download_file(url, save_path):
    """下载文件"""
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(save_path, 'wb') as file, tqdm(
        desc=os.path.basename(save_path),
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

def main():
    """主函数"""
    print(f"开始下载模型: {MODEL_NAME}")
    print(f"目标目录: {TARGET_DIR}")
    
    for file in FILES:
        url = BASE_URL + file
        save_path = os.path.join(TARGET_DIR, file)
        
        print(f"\n下载: {file}")
        try:
            download_file(url, save_path)
            print(f"✓ 下载完成: {file}")
        except Exception as e:
            print(f"✗ 下载失败: {file} - {e}")
    
    print("\n=== 下载完成 ===")
    print(f"模型已下载到: {TARGET_DIR}")

if __name__ == '__main__':
    main()
