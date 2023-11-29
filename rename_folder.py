# -*- coding: utf-8 -*-
# @Time : 2023/11/21
# @File : rename_folder.py

# 导入所需的类型和模块
import os
import re
import shutil
from typing import Tuple, Union, List, Dict
from config import ConfigManager
from colorama import Fore, Style
from api import PlexApi, TMDBApi

class MediaRenamer:
    def __init__(self):
        # 创建配置管理器实例
        self.config_manager = ConfigManager('config.json')
        # 获取服务器信息和密钥
        server_info_and_key = self.config_manager.get_server_info_and_key()
        # 创建TMDBApi和PlexApi实例
        self.tmdb_api = TMDBApi(server_info_and_key['tmdb_api_key'])
        self.plex_api = PlexApi(server_info_and_key['plex_url'], server_info_and_key['plex_token'], execute_request=False)

        self.processed_folders = []

        # 获取用户输入
        self.match_mode_index, self.library_type_index, self.naming_rule_index, self.parent_folder_path = self.get_user_input()      
        # 根据库的类型确定目标文件夹
        user_input = input("你确定要移动吗？[Enter] 确认，[n] 取消\t").lower()
        if self.match_mode_index in [1, 2] and (not user_input or user_input == 'y'):
            self.target_folder = self.move_folder(self.library_type_index, self.config_manager)
            # 在这里添加移动文件的代码
        else:
            self.target_folder = self.parent_folder_path
            print("选择不移动文件。")
            # 在这里添加不移动文件的代码


        # 根据命名规则确定文件夹标题格式
        self.folder_title_format = {
            1: lambda title, year, tmdb_id: f"{title} ({year})",
            2: lambda title, year, tmdb_id: f"{title} ({year}) {{tmdb-{tmdb_id}}}" if tmdb_id else f"{title} ({year})",
            3: lambda title, year, tmdb_id: f"{title}.{year}.tmdb-{tmdb_id}" if tmdb_id else f"{title} ({year})"
        }.get(self.naming_rule_index, lambda title, year, tmdb_id: f"{title} ({year})")

    def get_user_input(self):
        print(Fore.GREEN + "请选择匹配模式：" + Style.RESET_ALL)
        print("1. Plex匹配模式")
        print("2. TMDB匹配模式")
        print("3. 格式转换模式")
        print("4. 清理命名模式")

        match_mode_index = int(input("请输入你选择的匹配模式编号（默认为1）:") or "1")

        if match_mode_index not in [1, 2, 3, 4]:
            print(Fore.RED + "无效的匹配模式。请输入1到4之间的数字。" + Style.RESET_ALL)
            return None

        print(Fore.GREEN + "请选择库的类型：" + Style.RESET_ALL)
        print("1. 电影")
        print("2. 剧集")

        library_type_index = int(input("请输入你选择的库的类型编号（默认为1）:") or "1")

        if library_type_index not in [1, 2]:
            print(Fore.RED + "无效的库类型。请输入1或2。" + Style.RESET_ALL)
            return None

        print(Fore.GREEN + "请选择命名规则：" + Style.RESET_ALL)
        print("1. 中文名 (年份)")
        print("2. 中文名 (年份) {tmdb-id}")
        print("3. 中文名.(年份).{tmdb-id}")

        naming_rule_index = int(input("请输入你选择的命名规则的编号（默认为1）:") or "1")

        if naming_rule_index not in [1, 2, 3]:
            print(Fore.RED + "无效的命名规则。请输入1到3之间的数字。" + Style.RESET_ALL)
            return None

        parent_folder_path = input("请输入你的目录路径：")
        if not os.path.isdir(parent_folder_path):
            print(Fore.RED + "无效的路径。请输入一个有效的目录路径。" + Style.RESET_ALL)
            return None

        return match_mode_index, library_type_index, naming_rule_index, parent_folder_path

    # 从文件夹名称中提取信息
    def extract_folder_info(self, folder_name: str):
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
    def process_folder(self, folder_path: str, new_folder_name: str, match_data: dict):
        folder_name = os.path.basename(folder_path)
        parent_folder_path = os.path.dirname(folder_path)
        new_folder_path = os.path.join(parent_folder_path, new_folder_name)
        if folder_name != new_folder_name:
            if not os.path.exists(new_folder_path):
                if os.path.exists(folder_path):
                    try:
                        os.rename(folder_path, new_folder_path)
                        print(Fore.GREEN + "修改前文件夹名：" + Style.RESET_ALL + f"{folder_name}")
                        print(Fore.GREEN + "修改后文件夹名：" + Style.RESET_ALL + f"{new_folder_name}")
                    except OSError as e:
                        print(Fore.RED + f"重命名文件夹时出错: {e}" + Style.RESET_ALL)
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



    # 根据库的类型确定目标文件夹
    def move_folder(self, library_type_index: int, config_manager: ConfigManager):
        if library_type_index == 1:
            target_folder = config_manager.movies_folder
        else:
            print(Fore.GREEN + "请选择要移动到的文件夹：" + Style.RESET_ALL)
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
    def match_mode_1(self):
        for folder_name in os.listdir(self.parent_folder_path):
            folder_path = os.path.join(self.parent_folder_path, folder_name)
            print(Fore.RED + "正在处理文件夹：" + Style.RESET_ALL + f"{folder_path}")
            if folder_path in self.processed_folders:
                continue

            title, year = self.extract_folder_info(folder_name)

            matched_content = None
            if self.library_type_index == 1:
                print(Fore.GREEN + "正在搜索电影中：" + Style.RESET_ALL + f"{title} ({year})")
                matched_content = self.plex_api.search_movie(title)
            elif self.library_type_index == 2:
                print(Fore.GREEN + "正在搜索剧集中：" + Style.RESET_ALL + f"{title} ({year})")
                matched_content = self.plex_api.search_tv(title, year)

            if matched_content:
                try:
                    print(Fore.BLUE + f"从库中获取内容: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}" + Style.RESET_ALL)
                    tmdb_id = matched_content['tmdbid']
                    new_folder_name = self.folder_title_format(matched_content['title'], matched_content['year'], tmdb_id)
                except KeyError:
                    print(Fore.RED + "无法从匹配的内容中获取年份。跳过此文件夹。" + Style.RESET_ALL)
                    continue  # 跳过此文件夹并继续处理下一个文件夹

                new_folder_path = os.path.join(self.parent_folder_path, new_folder_name)

                # 移动文件夹
                target_path = os.path.join(self.target_folder, new_folder_name) if self.target_folder else new_folder_path
                if not os.path.exists(target_path):
                    os.rename(folder_path, target_path)
                    print(Fore.GREEN + "文件夹已成功重命名并移动到：" + Style.RESET_ALL + f"{target_path}")
                else:
                    for filename in os.listdir(folder_path):
                        source = os.path.join(folder_path, filename)
                        destination = os.path.join(target_path, filename)
                        if not os.path.exists(destination):
                            shutil.move(source, destination)
                        else:
                            print(f"文件 {filename} 已存在，跳过移动。")

                    # 检查源文件夹是否为空，如果为空，则删除
                    if not os.listdir(folder_path):
                        os.rmdir(folder_path)
                        print(Fore.GREEN + "原始文件夹已清空并删除。")

                print(Fore.BLUE + "-" * 120)




    def match_mode_2(self):
        for folder_name in os.listdir(self.parent_folder_path):
            folder_path = os.path.join(self.parent_folder_path, folder_name)
            print(Fore.RED + "正在处理文件夹：" + Style.RESET_ALL + f"{folder_path}")
            if folder_path in self.processed_folders:
                continue

            title, year = self.extract_folder_info(folder_name)

            matched_content = None
            if self.library_type_index == 1:
                print(Fore.GREEN + "正在搜索电影中：" + Style.RESET_ALL + f"{title} ({year})")
                matched_content = self.tmdb_api.search_movie(title, year)
                # 如果搜索结果为空，提示用户手动输入
                if matched_content is None:
                    title = input("未找到匹配的电影。请手动输入标题（留空表示跳过）：")
                    year = input("请手动输入年份（留空表示跳过）：")
                    # 如果用户输入不为空，再次进行搜索
                    if title and year:
                        matched_content = self.tmdb_api.search_movie(title)
            elif self.library_type_index == 2:
                print(Fore.GREEN + "正在搜索剧集中：" + Style.RESET_ALL + f"{title} ({year})")
                matched_content = self.tmdb_api.search_tv(title, year)
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
                title = first_matched_content['title'] if self.library_type_index == 1 else first_matched_content['name']
                year = first_matched_content['release_date'][:4] if self.library_type_index == 1 else first_matched_content['first_air_date'][:4]
                tmdb_id = first_matched_content['id']

                print(Fore.BLUE + "从库中获取内容: " + Style.RESET_ALL + f"{title} ({year}) {{tmdbid-{tmdb_id}}}")
                new_folder_name = self.folder_title_format(title, year, tmdb_id)
                new_folder_name = self.clean_folder_name(new_folder_name)
                new_folder_path = os.path.join(self.parent_folder_path, new_folder_name)  # 新添加的代码行

                target_path = os.path.join(self.target_folder, new_folder_name)
                if os.path.exists(target_path):
                    for filename in os.listdir(folder_path):
                        source = os.path.join(folder_path, filename)
                        destination = os.path.join(target_path, filename)
                        if not os.path.exists(destination):
                            shutil.move(source, destination)

                else:
                    os.rename(folder_path, target_path)

                # 检查源文件夹是否存在，如果存在，再检查是否为空
                if os.path.exists(folder_path) and not os.listdir(folder_path):
                    os.rmdir(folder_path)
                print(Fore.GREEN + "所有内容移动到：" + Style.RESET_ALL + f"{target_path}")
                print(Fore.BLUE + "-" * 120)

    # 匹配模式3
    def match_mode_3(self):
        for folder_name in os.listdir(self.parent_folder_path):
            folder_path = os.path.join(self.parent_folder_path, folder_name)
            print(Fore.Red + "正在处理文件夹：" + Style.RESET_ALL + f"{folder_path}")
            if folder_path in self.processed_folders:
                continue

            title, year = self.extract_folder_info(folder_name)

            matched_content = None
            if self.library_type_index == 1:
                print(Fore.GREEN + f"正在搜索电影中：{title} ({year})" + Style.RESET_ALL)
                matched_content = self.plex_api.search_movie(title)
            elif self.library_type_index == 2:
                print(Fore.GREEN + f"正在搜索剧集中：{title} ({year})" + Style.RESET_ALL)
                matched_content = self.plex_api.search_tv(title, year)

            if matched_content:
                print(Fore.GREEN + f"从库中获取内容: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}" + Style.RESET_ALL)
                tmdb_id = matched_content['tmdbid']
                new_folder_name = self.folder_title_format(matched_content['title'], matched_content['year'], tmdb_id)
                self.process_folder(folder_path, new_folder_name, matched_content)

    # 匹配模式4
    def match_mode_4(self):
        for folder_name in os.listdir(self.parent_folder_path):
            folder_path = os.path.join(self.parent_folder_path, folder_name)
            print(Fore.Red + "正在处理文件夹：" + Style.RESET_ALL + f"{folder_path}")
            if folder_path in self.processed_folders:
                continue
            if not os.path.isdir(folder_path):
                continue

            title, year = self.extract_folder_info(folder_name)

            if not year:
                new_folder_name = title
            else:
                new_folder_name = self.folder_title_format(title, year, None)

            self.process_folder(folder_path, new_folder_name, None)

# 主函数
def main() -> None:
    # 创建MediaRenamer实例
    print(Fore.RED + '开始程序:注意输入的目录结构必须是【你的目录/剧集或电影文件夹/媒体文件或其他子目录】' + Style.RESET_ALL)
    media_renamer: MediaRenamer = MediaRenamer()
    

    # 根据匹配模式执行相应的函数
    if media_renamer.match_mode_index == 4:
        media_renamer.match_mode_4()
        exit()

    if media_renamer.match_mode_index == 1:
        media_renamer.match_mode_1()
    elif media_renamer.match_mode_index == 2:
        media_renamer.match_mode_2()
    elif media_renamer.match_mode_index == 3:
        media_renamer.match_mode_3()

# 如果这个脚本是直接运行的，而不是被导入的，那么就运行主函数
if __name__ == "__main__":
    main()
