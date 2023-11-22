# -*- coding: utf-8 -*-
# @Time : 2023/11/21
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

    def move_folder(self, library_type_index: int, config_manager: ConfigManager):
        # 根据库的类型确定目标文件夹
        if library_type_index == 1:
            target_folder = config_manager.movies_folder
        else:
            print("请选择要移动到的文件夹：")
            print("1. 剧集")
            print("2. 动漫")
            print("3. 国剧")
            print("4. 纪录")
            print("5. 美剧")
            print("6. 日韩剧")
            print("7. 体育")
            print("8. 综艺")
            folder_index = int(input("请输入你选择的文件夹编号（默认为1）:") or "1")
            target_folder = {
                1: config_manager.shows_folder,
                2: config_manager.anime_folder,
                3: config_manager.chinese_drama_folder,
                4: config_manager.documentary_folder,
                5: config_manager.american_drama_folder,
                6: config_manager.japanese_korean_drama_folder,
                7: config_manager.sports_folder,
                8: config_manager.variety_show_folder
            }.get(folder_index, config_manager.shows_folder)
        return target_folder

    def match_mode_1(self, parent_folder_path: str, library_type_index: int, naming_rule_index: int, config_manager: ConfigManager):
        move_all_folders = input("是否要移动所有匹配的文件夹？(y/n，默认为y)：")
        if move_all_folders.lower() == 'y' or not move_all_folders:
            target_folder = self.move_folder(library_type_index, config_manager)
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
            elif library_type_index == 2:
                print(f"正在搜索剧集中：{title} ({year})")
                matched_content = self.plex_api.search_show(title, year)

            if matched_content:
                print(f"从库中获取内容: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}")
                tmdb_id = matched_content['tmdbid']
                new_folder_name = self.generate_new_folder_name(matched_content['title'], matched_content['year'], tmdb_id, naming_rule_index)
                new_folder_path = os.path.join(parent_folder_path, new_folder_name)  # 新添加的代码行
                self.process_folder(folder_path, new_folder_name, matched_content)
                if move_all_folders.lower() == 'y':
                    target_path = os.path.join(target_folder, new_folder_name)
                    if not os.path.exists(target_path):
                        try:
                            os.rename(new_folder_path, target_path)
                            print(f"文件夹已成功移动到：{target_path}")
                        except OSError as e:
                            print(f"Error moving folder: {e}")


    def match_mode_2(self, parent_folder_path: str, library_type_index: int, naming_rule_index: int, config_manager: ConfigManager):
        move_all_folders = input("是否要移动所有匹配的文件夹？(y/n，默认为y)：")
        if move_all_folders.lower() == 'y' or not move_all_folders:
            target_folder = self.move_folder(library_type_index, config_manager)
        for folder_name in os.listdir(parent_folder_path):
            folder_path = os.path.join(parent_folder_path, folder_name)
            print(f"正在处理文件夹：{folder_path}")
            if folder_path in self.processed_folders:
                continue

            title, year = self.extract_folder_info(folder_name)

            matched_content = None
            if library_type_index == 1:
                print(f"正在搜索电影中：{title} ({year})")
                matched_content = self.tmdb_api.search_movie(title)
                # 如果搜索结果为空，提示用户手动输入
                if matched_content is None:
                    title = input("未找到匹配的电影。请手动输入标题（留空表示跳过）：")
                    year = input("请手动输入年份（留空表示跳过）：")
                    # 如果用户输入不为空，再次进行搜索
                    if title and year:
                        matched_content = self.tmdb_api.search_movie(title)
            elif library_type_index == 2:
                print(f"正在搜索剧集中：{title} ({year})")
                matched_content = self.tmdb_api.search_tv(title)
                # 如果搜索结果为空，提示用户手动输入
                if matched_content is None:
                    title = input("未找到匹配的剧集。请手动输入标题（留空表示跳过）：")
                    year = input("请手动输入年份（留空表示跳过）：")
                    # 如果用户输入不为空，再次进行搜索
                    if title and year:
                        matched_content = self.tmdb_api.search_tv(title)

            if matched_content and matched_content['results']:
                # 获取匹配到的第一部电影或剧集的信息
                first_matched_content = matched_content['results'][0]

                # 从电影或剧集信息中获取标题、年份和TMDB ID
                title = first_matched_content['title'] if library_type_index == 1 else first_matched_content['name']
                year = first_matched_content['release_date'][:4] if library_type_index == 1 else first_matched_content['first_air_date'][:4]
                tmdb_id = first_matched_content['id']

                print(f"从库中获取内容: {title} ({year}) {{tmdbid-{tmdb_id}}}")
                new_folder_name = self.generate_new_folder_name(title, year, tmdb_id, naming_rule_index)
                new_folder_path = os.path.join(parent_folder_path, new_folder_name)  # 新添加的代码行
                self.process_folder(folder_path, new_folder_name, matched_content)
                if move_all_folders.lower() == 'y':
                    target_path = os.path.join(target_folder, new_folder_name)
                    if not os.path.exists(target_path):
                        try:
                            os.rename(new_folder_path, target_path)
                            print(f"文件夹已成功移动到：{target_path}")
                        except OSError as e:
                            print(f"Error moving folder: {e}")

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
