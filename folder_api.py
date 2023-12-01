# -*- coding: utf-8 -*-
# @Time : 2023/11/21
# @File : folder_api.py

import os
import re
from typing import Tuple, Union, List, Dict

class FolderAPI:
    def __init__(self):
        pass

    # 从文件夹名称中提取信息
    def extract_folder_info(self, folder_name: str) -> Tuple[str, str]:
        # 从文件夹名称中提取信息
        folder_name = re.sub(r'\{tmdb-\d+\}', '', folder_name)
        folder_name = re.sub(r'4K', '', folder_name)
        year = re.search(r'\((\d{4})\)', folder_name)
        if year:
            year = year.group().strip('()')
        else:
            year = re.search(r'(\d{4})', folder_name)
            if year:
                year = year.group()
        folder_without_year = re.sub(str(year), '', folder_name) if year else folder_name
        chinese_titles = re.findall(r'[\u4e00-\u9fff0-9a-zA-Z：，·]+', folder_without_year)
        english_title = ' '.join(re.findall(r'[a-zA-Z\s]+(?![^\(]*\))', folder_without_year))
        if not chinese_titles and not english_title:
            title = ''.join(re.findall(r'(?<!\()\d+(?!\))', folder_without_year))
        else:
            title = chinese_titles[0] if chinese_titles else english_title
        title = title.strip()
        return title, year

    # 处理文件夹
    def process_folder(self, folder_path: str, new_folder_name: str, match_data: dict) -> None:
        folder_name = os.path.basename(folder_path)
        parent_folder_path = os.path.dirname(folder_path)
        new_folder_path = os.path.join(parent_folder_path, new_folder_name)
        if folder_name != new_folder_name:
            if not os.path.exists(new_folder_path):
                if os.path.exists(folder_path):
                    try:
                        os.rename(folder_path, new_folder_path)
                        print(f"修改前文件夹名：{folder_name}")
                        print(f"修改后文件夹名：{new_folder_name}")
                    except OSError as e:
                        print(f"重命名文件夹时出错: {e}")
        else:
            print("文件夹无需修改")

    def clean_folder_name(self, folder_name: str) -> str:
        # 定义一个映射表将特殊字符替换为合法字符
        char_map = {
            '<': '＜',
            '>': '＞',
            ':': '：',
            '"': '＂',
            '/': '／',
            '\\': '＼',
            '|': '｜',
            '?': '？',
            '*': '＊'
        }
        for char, replacement in char_map.items():
            folder_name = folder_name.replace(char, replacement)
        return folder_name
