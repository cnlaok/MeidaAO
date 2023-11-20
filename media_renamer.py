# -*- coding: utf-8 -*-
# @Time : 2023/11/03
# @File : media_renamer.py

import os
import re
from api import PlexApi, TMDBApi
from config import ConfigManager
import requests


class MediaRenamer:
    def __init__(self, config_manager: ConfigManager, tmdb_api: TMDBApi, plex_api: PlexApi):
        self.config_manager = config_manager
        self.tmdb_api = tmdb_api
        self.plex_api = plex_api
        self.processed_folders = []

    def extract_folder_info(self, folder_name: str):
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
            title = chinese_titles[0] if chinese_titles else english_title
        title = title.strip()
        return title, year

    def generate_new_folder_name(self, title: str, year: str, tmdb_id: str = None, naming_rule_index: int = 1):
        naming_rules = {
            1: lambda: f"{title} ({year})",
            2: lambda: f"{title} ({year}) {{tmdb-{tmdb_id}}}" if tmdb_id else f"{title} ({year})",
            3: lambda: f"{title}.{year}.tmdb-{tmdb_id}" if tmdb_id else f"{title} ({year})"
        }
        return naming_rules.get(naming_rule_index, lambda: f"{title} ({year})")()

    def get_user_input(self):
        print("请选择匹配模式：")
        print("1. Plex匹配模式")
        print("2. TMDB匹配模式")
        print("3. 格式转换模式")
        print("4. 清理命名模式")
        print("5. 电影文件命名")

        match_mode_index = int(input("请输入你选择的匹配模式编号（默认为1）:") or "1")

        if match_mode_index not in [1, 2, 3, 4, 5]:
            print("Invalid match mode. Please enter a number between 1 and 5.")
            return None

        print("请选择库的类型：")
        print("1. 电影")
        print("2. 剧集")

        library_type_index = int(input("请输入你选择的库的类型编号（默认为1）:") or "1")

        if library_type_index not in [1, 2]:
            print("Invalid library type. Please enter either 1 or 2.")
            return None

        print("请选择命名规则：")
        print("1. 中文名 (年份)")
        print("2. 中文名 (年份) {tmdb-id}")
        print("3. 中文名.(年份).{tmdb-id}")

        naming_rule_index = int(input("请输入你选择的命名规则的编号（默认为1）:") or "1")

        if naming_rule_index not in [1, 2, 3]:
            print("Invalid naming rule. Please enter a number between 1 and 3.")
            return None

        parent_folder_path = input("请输入父文件夹的路径：")
        if not os.path.isdir(parent_folder_path):
            print("Invalid path. Please enter a valid directory path.")
            return None

        return match_mode_index, library_type_index, naming_rule_index, parent_folder_path

    def process_folder(self, folder_path: str, new_folder_name: str, match_data: dict):
        print(f"正在处理文件夹：{folder_path}")
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
                        print("-" * 50)
                    except OSError as e:
                        print(f"Error renaming folder: {e}")
        else:
            print("文件夹无需修改")

    def match_mode_1(self, parent_folder_path: str, library_type_index: int, naming_rule_index: int):
        for folder_name in os.listdir(parent_folder_path):
            folder_path = os.path.join(parent_folder_path, folder_name)
            print(f"正在处理文件夹：{folder_path}")
            if folder_path in self.processed_folders:
                continue

            title, year = self.extract_folder_info(folder_name)

            matched_content = None
            if library_type_index == 1:
                print(f"正在搜索电影中：{title} ({year})")
                matched_content = self.plex_api.search_movie(title)
                if matched_content:
                    print(f"从库中获取电影: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}")
                    tmdb_id = matched_content['tmdbid']
                    new_folder_name = self.generate_new_folder_name(matched_content['title'], matched_content['year'], tmdb_id, naming_rule_index)
                    self.process_folder(folder_path, new_folder_name, matched_content)
            elif library_type_index == 2:
                print(f"正在搜索剧集中：{title} ({year})")
                matched_content = self.plex_api.search_show(title, year)
                if matched_content:
                    print(f"从库中获取剧集: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}")
                    tmdb_id = matched_content['tmdbid']
                    new_folder_name = self.generate_new_folder_name(matched_content['title'], matched_content['year'], tmdb_id, naming_rule_index)
                    self.process_folder(folder_path, new_folder_name, matched_content)

    def match_mode_2(self, parent_folder_path: str, library_type_index: int, naming_rule_index: int):
        for folder_name in os.listdir(parent_folder_path):
            folder_path = os.path.join(parent_folder_path, folder_name)
            print(f"Processing folder: {folder_path}")
            if folder_path in self.processed_folders:
                continue

            title, year = self.extract_folder_info(folder_name)

            matched_content = None
            if library_type_index == 1:
                print(f"Searching in movies: {title} ({year})")
                matched_content = self.tmdb_api.search_movie(title)
                if matched_content and matched_content['results']:
                    matched_movie = matched_content['results'][0]
                    print(f"Found in TMDB: {matched_movie['title']} ({matched_movie['release_date'][:4]}) {{tmdb-{matched_movie['id']}}}")
                    tmdb_id = matched_movie['id']
                    new_folder_name = self.generate_new_folder_name(matched_movie['title'], matched_movie['release_date'][:4], tmdb_id, naming_rule_index)
                    self.process_folder(folder_path, new_folder_name, matched_movie)
            elif library_type_index == 2:
                print(f"Searching in TV shows: {title} ({year})")
                matched_content = self.tmdb_api.search_tv(title)
                if matched_content and matched_content['results']:
                    matched_show = matched_content['results'][0]
                    print(f"Found in TMDB: {matched_show['name']} ({matched_show['first_air_date'][:4]}) {{tmdb-{matched_show['id']}}}")
                    tmdb_id = matched_show['id']
                    new_folder_name = self.generate_new_folder_name(matched_show['name'], matched_show['first_air_date'][:4], tmdb_id, naming_rule_index)
                    self.process_folder(folder_path, new_folder_name, matched_show)

    def match_mode_3(self, parent_folder_path: str, library_type_index: int, naming_rule_index: int):
        for folder_name in os.listdir(parent_folder_path):
            folder_path = os.path.join(parent_folder_path, folder_name)
            print(f"正在处理文件夹：{folder_path}")
            if folder_path in self.processed_folders:
                continue

            title, year = self.extract_folder_info(folder_name)

            matched_content = None
            if library_type_index == 1:
                print(f"正在搜索电影中：{title} ({year})")
                matched_content = self.plex_api.search_movie(title)
                if matched_content:
                    print(f"从库中获取电影: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}")
                    tmdb_id = matched_content['tmdbid']
                    new_folder_name = self.generate_new_folder_name(matched_content['title'], matched_content['year'], tmdb_id, naming_rule_index)
                    self.process_folder(folder_path, new_folder_name, matched_content)
            elif library_type_index == 2:
                print(f"正在搜索剧集中：{title} ({year})")
                matched_content = self.plex_api.search_show(title, year)
                if matched_content:
                    print(f"从库中获取剧集: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}")
                    tmdb_id = matched_content['tmdbid']
                    new_folder_name = self.generate_new_folder_name(matched_content['title'], matched_content['year'], tmdb_id, naming_rule_index)
                    self.process_folder(folder_path, new_folder_name, matched_content)

    def match_mode_4(self, parent_folder_path: str):
        for folder_name in os.listdir(parent_folder_path):
            folder_path = os.path.join(parent_folder_path, folder_name)
            if folder_path in self.processed_folders:
                continue

            title, year = self.extract_folder_info(folder_name)

            new_folder_name = self.generate_new_folder_name(title, year, naming_rule_index=1)

            self.process_folder(folder_path, new_folder_name, None)
