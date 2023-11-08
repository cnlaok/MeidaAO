# -*- coding: utf-8 -*-
# @Time : 2023/11/03
# @File : media_renamer.py

import os
import re
from api import PlexApi, TMDBApi
from config import ConfigManager
import requests
from logger import LoggerManager

logger_manager = LoggerManager()
logger = logger_manager.logger   
handler_to_remove = logger.handlers[0] 
logger.removeHandler(handler_to_remove)


class MediaRenamer:
    def __init__(self, config_manager, tmdb_api, plex_api):  # 添加tmdb_api和plex_api作为参数
        self.config_manager = config_manager
        self.tmdb_api = tmdb_api  # 添加这一行
        self.plex_api = plex_api  # 添加这一行
        self.processed_folders = []

    def extract_folder_info(self, folder_name):
        folder_name = re.sub(r'\{tmdb-\d+\}', '', folder_name)
        year = re.search(r'\((\d{4})\)', folder_name)
        if year:
            year = year.group().strip('()')
        else:
            year = re.search(r'(\d{4})', folder_name)
            if year:
                year = year.group()
        folder_without_year = re.sub(str(year), '', folder_name) if year else folder_name
        chinese_titles = re.findall(r'[\u4e00-\u9fff0-9：，]+', folder_without_year)
        english_title = ' '.join(re.findall(r'[a-zA-Z\s]+(?![^\(]*\))', folder_without_year))
        if not chinese_titles and not english_title:
            title = ''.join(re.findall(r'(?<!\()\d+(?!\))', folder_without_year))
        else:
            title = chinese_titles[0] if chinese_titles else english_title  # 只提取第一个中文词
        title = title.strip()
        return title, year


    def generate_new_folder_name(self, title, year, tmdb_id=None, naming_rule_index=1):

        naming_rules = {
            1: lambda: f"{title} ({year})",
            2: lambda: f"{title} ({year}) {{tmdb-{tmdb_id}}}" if tmdb_id else f"{title} ({year})",
            3: lambda: f"{title}.{year}.tmdb-{tmdb_id}" if tmdb_id else f"{title} ({year})"
        }
        return naming_rules.get(naming_rule_index, lambda: f"{title} ({year})")()

    def get_user_input(self):
        logger.info("\033[34m请选择匹配模式：\033[0m")
        logger.info("\033[34m1. Plex匹配模式\033[0m")
        logger.info("\033[34m2. TMDB匹配模式\033[0m")
        logger.info("\033[34m3. 格式转换模式\033[0m")
        logger.info("\033[34m4. 清理命名模式\033[0m")

        match_mode_index = int(input("\033[32m请输入你选择的匹配模式编号（默认为1）:\033[0m ") or "1")

        if match_mode_index not in [1, 2, 3, 4]:
            logger.info("Invalid match mode. Please enter a number between 1 and 4.")
            return None

        logger.info("\033[34m请选an择库的类型：\033[0m")
        logger.info("\033[34m1. 电影\033[0m")
        logger.info("\033[34m2. 剧集\033[0m")

        library_type_index = int(input("\033[32m请输入你选择的库的类型编号（默认为1）:\033[0m ") or "1")

        if library_type_index not in [1, 2]:
            logger.info("Invalid library type. Please enter either 1 or 2.")
            return None

        logger.info("\033[34m请选择命名规则：\033[0m")
        logger.info("\033[34m1. 中文名 (年份)\033[0m")
        logger.info("\033[34m2. 中文名 (年份) {tmdb-id}\033[0m")
        logger.info("\033[34m3. 中文名.(年份).{tmdb-id}\033[0m")

        naming_rule_index = int(input("\033[32m请输入你选择的命名规则的编号（默认为1）:\033[0m ") or "1")

        if naming_rule_index not in [1, 2, 3]:
            logger.info("Invalid naming rule. Please enter a number between 1 and 3.")
            return None

        parent_folder_path = input("请输入父文件夹的路径：")

        return match_mode_index, library_type_index, naming_rule_index, parent_folder_path

    def process_folder(self, folder_path, new_folder_name, match_data):
        logger.info(f"正在处理文件夹：{folder_path}")
        folder_name = os.path.basename(folder_path)  # 获取文件夹名字
        # 生成新的文件夹路径
        parent_folder_path = os.path.dirname(folder_path)
        new_folder_path = os.path.join(parent_folder_path, new_folder_name)
        # 重命名文件夹
        if folder_name != new_folder_name:
            if not os.path.exists(new_folder_path):
                if os.path.exists(folder_path):
                    try:
                        os.rename(folder_path, new_folder_path)
                        logger.info(f"修改前文件夹名：{folder_name}")
                        logger.info(f"修改后文件夹名：{new_folder_name}")
                        logger.info("-" * 50)
                    except Exception as e:
                        logger.info(f"Error renaming folder: {e}")
        else:
            logger.info("\033[92m文件夹无需修改；\033[0m")  # 使用ANSI转义码来打印绿色文本

    def match_mode_1(self, parent_folder_path, library_type_index, naming_rule_index):
        for folder_name in os.listdir(parent_folder_path):
            folder_path = os.path.join(parent_folder_path, folder_name)
            logger.info(f"正在处理文件夹：{folder_path}")  
            if folder_path in self.processed_folders:
                continue

            title, year = self.extract_folder_info(folder_name)

            # 在Plex数据中查找匹配
            matched_content = None
            if library_type_index == 1:  # 假设1代表电影
                logger.info(f"正在搜索电影中：{title} ({year})")  
                matched_content = self.plex_api.search_movie(title)
                if matched_content:
                    logger.info(f"从库中获取电影: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}")
                    tmdb_id = matched_content['tmdbid']  # 获取tmdbid
                    new_folder_name = self.generate_new_folder_name(matched_content['title'], matched_content['year'], tmdb_id, naming_rule_index)
                    # 执行重命名操作
                    self.process_folder(folder_path, new_folder_name, matched_content)
            elif library_type_index == 2:  # 假设2代表剧集
                logger.info(f"正在搜索剧集中：{title} ({year})")  
                matched_content = self.plex_api.search_show(title, year)
                if matched_content:
                    logger.info(f"从库中获取剧集: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}")
                    tmdb_id = matched_content['tmdbid']  # 获取tmdbid
                    new_folder_name = self.generate_new_folder_name(matched_content['title'], matched_content['year'], tmdb_id, naming_rule_index)
                    # 执行重命名操作
                    self.process_folder(folder_path, new_folder_name, matched_content)


