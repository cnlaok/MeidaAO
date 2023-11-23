# -*- coding: utf-8 -*-
# @Time : 2023/11/21
# @File : rename_folder.py

# 导入所需的类型和模块
import os
import re
import requests
from typing import Tuple, Union, List, Dict
from config import ConfigManager
from colorama import Fore, Style
from api import PlexApi, TMDBApi

# 定义配置文件的路径
CONFIG_FILE = 'config.json'

# 定义MediaRenamer类，用于重命名媒体文件
class MediaRenamer:
    def __init__(self, config_manager: ConfigManager, tmdb_api: TMDBApi, plex_api: PlexApi):
        self.config_manager = config_manager
        self.tmdb_api = tmdb_api
        self.plex_api = plex_api
        self.processed_folders = []

    # 从文件夹名称中提取信息
    def extract_folder_info(self, folder_name: str):
        # 从文件夹名称中提取信息
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

    # 根据命名规则生成新的文件夹名称
    def generate_new_folder_name(self, title: str, year: str, tmdb_id: str = None, naming_rule_index: int = 1):
        naming_rules = {
            1: lambda: f"{title} ({year})",
            2: lambda: f"{title} ({year}) {{tmdb-{tmdb_id}}}" if tmdb_id else f"{title} ({year})",
            3: lambda: f"{title}.{year}.tmdb-{tmdb_id}" if tmdb_id else f"{title} ({year})"
        }
        return naming_rules.get(naming_rule_index, lambda: f"{title} ({year})")()

    # 处理文件夹
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
                        print(f"重命名文件夹时出错: {e}")
        else:
            print("文件夹无需修改")

    # 根据库的类型确定目标文件夹
    def move_folder(self, library_type_index: int, config_manager: ConfigManager):
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

    # 匹配模式1
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
                            print(f"移动文件夹时出错: {e}")

    # 匹配模式2
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
    # 匹配模式3
    def match_mode_3(self, parent_folder_path: str, library_type_index: int, naming_rule_index: int):
        # 遍历父文件夹中的所有文件夹
        for folder_name in os.listdir(parent_folder_path):
            # 获取文件夹的完整路径
            folder_path = os.path.join(parent_folder_path, folder_name)
            print(f"正在处理文件夹：{folder_path}")
            # 如果文件夹已经被处理过，就跳过
            if folder_path in self.processed_folders:
                continue

            # 从文件夹名称中提取标题和年份
            title, year = self.extract_folder_info(folder_name)

            # 初始化匹配内容
            matched_content = None
            # 如果库的类型是电影
            if library_type_index == 1:
                print(f"正在搜索电影中：{title} ({year})")
                # 使用Plex API搜索电影
                matched_content = self.plex_api.search_movie(title)
                # 如果找到了匹配的电影
                if matched_content:
                    print(f"从库中获取电影: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}")
                    # 获取TMDB ID
                    tmdb_id = matched_content['tmdbid']
                    # 生成新的文件夹名称
                    new_folder_name = self.generate_new_folder_name(matched_content['title'], matched_content['year'], tmdb_id, naming_rule_index)
                    # 处理文件夹
                    self.process_folder(folder_path, new_folder_name, matched_content)
            # 如果库的类型是剧集
            elif library_type_index == 2:
                print(f"正在搜索剧集中：{title} ({year})")
                # 使用Plex API搜索剧集
                matched_content = self.plex_api.search_show(title, year)
                # 如果找到了匹配的剧集
                if matched_content:
                    print(f"从库中获取剧集: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}")
                    # 获取TMDB ID
                    tmdb_id = matched_content['tmdbid']
                    # 生成新的文件夹名称
                    new_folder_name = self.generate_new_folder_name(matched_content['title'], matched_content['year'], tmdb_id, naming_rule_index)
                    # 处理文件夹
                    self.process_folder(folder_path, new_folder_name, matched_content)

    # 匹配模式4
    def match_mode_4(self, parent_folder_path: str):
        # 遍历父文件夹中的所有文件夹
        for folder_name in os.listdir(parent_folder_path):
            # 获取文件夹的完整路径
            folder_path = os.path.join(parent_folder_path, folder_name)
            # 如果文件夹已经被处理过，就跳过
            if folder_path in self.processed_folders:
                continue
            # 如果这不是一个文件夹，就跳过
            if not os.path.isdir(folder_path):
                continue

            # 从文件夹名称中提取标题和年份
            title, year = self.extract_folder_info(folder_name)

            # 如果年份不存在，就只使用标题作为文件夹名
            if not year:
                new_folder_name = title
            else:
                # 生成新的文件夹名称
                new_folder_name = self.generate_new_folder_name(title, year, naming_rule_index=1)

            # 处理文件夹
            self.process_folder(folder_path, new_folder_name, None)

# 获取用户输入
def get_user_input():
    print("请选择匹配模式：")
    print("1. Plex匹配模式")
    print("2. TMDB匹配模式")
    print("3. 格式转换模式")
    print("4. 清理命名模式")

    match_mode_index = int(input("请输入你选择的匹配模式编号（默认为1）:") or "1")

    if match_mode_index not in [1, 2, 3, 4]:
        print("无效的匹配模式。请输入1到4之间的数字。")
        return None

    print("请选择库的类型：")
    print("1. 电影")
    print("2. 剧集")

    library_type_index = int(input("请输入你选择的库的类型编号（默认为1）:") or "1")

    if library_type_index not in [1, 2]:
        print("无效的库类型。请输入1或2。")
        return None

    print("请选择命名规则：")
    print("1. 中文名 (年份)")
    print("2. 中文名 (年份) {tmdb-id}")
    print("3. 中文名.(年份).{tmdb-id}")

    naming_rule_index = int(input("请输入你选择的命名规则的编号（默认为1）:") or "1")

    if naming_rule_index not in [1, 2, 3]:
        print("无效的命名规则。请输入1到3之间的数字。")
        return None

    parent_folder_path = input("请输入父文件夹的路径：")
    if not os.path.isdir(parent_folder_path):
        print("无效的路径。请输入一个有效的目录路径。")
        return None

    return match_mode_index, library_type_index, naming_rule_index, parent_folder_path


# 主函数
def main() -> None:
    # 创建配置管理器实例
    config_manager: ConfigManager = ConfigManager(CONFIG_FILE)
    # 获取服务器信息和密钥
    server_info_and_key: dict = config_manager.get_server_info_and_key()
    # 创建TMDBApi和PlexApi实例
    tmdb_api: TMDBApi = TMDBApi(server_info_and_key['tmdb_api_key'])
    plex_api: PlexApi = PlexApi(server_info_and_key['plex_url'], server_info_and_key['plex_token'], execute_request=False)
    # 创建MediaRenamer实例
    media_renamer: MediaRenamer = MediaRenamer(config_manager, tmdb_api, plex_api)
    print(Fore.RED + '开始程序:' + Style.RESET_ALL)

    # 获取用户输入
    match_mode_index: int
    library_type_index: int
    naming_rule_index: int
    parent_folder_path: str
    match_mode_index, library_type_index, naming_rule_index, parent_folder_path = get_user_input()

    # 验证库类型
    if library_type_index not in [1, 2]:
        print(Fore.RED + "无效的库类型。请输入1或2。" + Style.RESET_ALL)
        return

    # 验证命名规则
    if naming_rule_index not in [1, 2, 3]:
        print(Fore.RED + "无效的命名规则。请输入1到3之间的数字。" + Style.RESET_ALL)
        return

    # 根据匹配模式执行相应的函数
    if match_mode_index == 4:
        media_renamer.match_mode_4(parent_folder_path)
        exit()

    if match_mode_index == 1:
        media_renamer.match_mode_1(parent_folder_path, library_type_index, naming_rule_index, config_manager)
    elif match_mode_index == 2:
        media_renamer.match_mode_2(parent_folder_path, library_type_index, naming_rule_index, config_manager)
    elif match_mode_index == 3:
        media_renamer.match_mode_3(parent_folder_path, library_type_index, naming_rule_index)

# 如果这个脚本是直接运行的，而不是被导入的，那么就运行主函数
if __name__ == "__main__":
    main()
