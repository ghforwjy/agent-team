#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载Sentence-BERT模型的Pooling层配置
"""
import os
import json
import urllib.request
import ssl

# 创建SSL上下文（忽略证书验证）
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Hugging Face模型仓库URL
base_url = "https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/main"

# 需要下载的文件
files_to_download = [
    "1_Pooling/config.json",
]

# 本地保存路径
save_dir = "e:/mycode/agent-team/model/Sentence-BERT"

os.makedirs(os.path.join(save_dir, "1_Pooling"), exist_ok=True)

for file_path in files_to_download:
    url = f"{base_url}/{file_path}"
    local_path = os.path.join(save_dir, file_path)
    
    print(f"下载: {url}")
    try:
        urllib.request.urlretrieve(url, local_path)
        print(f"  保存到: {local_path}")
        
        # 验证JSON
        with open(local_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            print(f"  内容: {json.dumps(content, indent=2)}")
    except Exception as e:
        print(f"  错误: {e}")

print("\n下载完成!")
