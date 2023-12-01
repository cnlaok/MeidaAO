# 导入所需的类型和模块
import os
import json
import shutil
import csv
from typing import Tuple, Union, List, Dict
from colorama import Fore, Style
from api import PlexApi, TMDBApi
from folder_api import FolderAPI


class MediaRenamer:
    def __init__(self):
        # 加载配置文件
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        # 从配置中获取服务器信息和密钥
        server_info_and_key = self.config
        self.folder_api = FolderAPI()
        # 创建TMDBApi和PlexApi实例
        self.tmdb_api = TMDBApi(server_info_and_key['TMDB_API_KEY'])
        self.plex_api = PlexApi(server_info_and_key['PLEX_URL'], server_info_and_key['PLEX_TOKEN'], execute_request=False)
        self.folder_api = FolderAPI()
        self.processed_folders = []
        self.append_data = self.config['append_data']
        if self.append_data:
            self.matched_contents = []
        else:
            pass

        # 获取用户输入
        self.match_mode_index, self.library_type_index, self.naming_rule_index, self.parent_folder_path = self.get_user_input()      
        # 根据库的类型确定目标文件夹
        user_input = input("你确定要移动吗？[Enter] 确认，[n] 取消\t").lower()
        if self.match_mode_index in [1, 2] and (not user_input or user_input == 'y'):
            self.target_folder = self.move_folder(self.library_type_index)
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


    # 根据库的类型确定目标文件夹
    def move_folder(self, library_type_index: int) -> str:
        if library_type_index is not None:
            target_folder = self.config['target_folders'][library_type_index]
        else:
            target_folder = self.parent_folder_path
        return target_folder



    # 根据库的类型确定目标文件夹
    def move_folder(self, library_type_index: int):
        if library_type_index == 1:
            target_folder = self.config['movies_folder']
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
                1: self.config['shows_folder'],
                2: self.config['anime_folder'],
                3: self.config['chinese_drama_folder'],
                4: self.config['documentary_folder'],
                5: self.config['american_drama_folder'],
                6: self.config['japanese_korean_drama_folder'],
                7: self.config['sports_folder'],
                8: self.config['variety_show_folder']
            }.get(folder_index, self.config['shows_folder'])
        return target_folder

  
    def write_to_file(self):
        if self.append_data and self.matched_contents is not None:
            print(self.matched_contents)
            if not os.path.exists('matched_content.csv'):
                with open('matched_content.csv', 'w', encoding='utf-8') as f:
                    pass
            with open('matched_content.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 检查文件是否为空或者文件是否存在
                if f.tell() == 0:
                    # 写入表头
                    writer.writerow(['标题', '年份', 'tmdbid', '类型'])
                for content in self.matched_contents:
                    # 在写入数据之前，先检查这些数据是否已经存在于内存中
                    if not self.is_content_in_file(*content):
                        writer.writerow(content)
                        # 将新写入的数据添加到内存中
                        self.csv_contents.append(content) 

    def is_content_in_file(self, title, year, tmdb_id, library_type):
        search_string = f"{title},{year},{tmdb_id},{library_type}"
        try:
            with open('matched_content.csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # 跳过标题行
                for row in reader:
                    if ','.join(row) == search_string:
                        return True
            return False
        except FileNotFoundError:
            return False


    def process_single_folder(self, folder_path, mode=1):
        print(Fore.RED + "正在处理文件夹：" + Style.RESET_ALL + f"{folder_path}")
        if folder_path in self.processed_folders:
            return

        folder_name = os.path.basename(folder_path)
        title, year = self.folder_api.extract_folder_info(folder_name)

        matched_content = None
        api = self.plex_api if mode == 1 else self.tmdb_api

        search_function = api.search_movie if self.library_type_index == 1 else api.search_tv
        print(Fore.GREEN + f"正在搜索{'电影' if self.library_type_index == 1 else '剧集'}中：" + Style.RESET_ALL + f"{title} ({year})")
        matched_content = search_function(title, year)

        if matched_content is None and mode == 2:
            title = input(f"未找到匹配的{'电影' if self.library_type_index == 1 else '剧集'}。请手动输入标题（留空表示跳过）：")
            year = input("请手动输入年份（留空表示跳过）：")
            if title and year:
                matched_content = search_function(title, year)

        if matched_content:
            try:
                if mode == 1:
                    # 处理模式1的特定情况
                    print(Fore.BLUE + f"从库中获取内容: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}" + Style.RESET_ALL)
                    tmdb_id = matched_content['tmdbid']
                    new_folder_name = self.folder_title_format(matched_content['title'], matched_content['year'], tmdb_id)
                    content_to_append = [matched_content['title'], matched_content['year'], matched_content['tmdbid'], str(self.library_type_index)]
                else:
                    # 处理模式2的情况
                    first_matched_content = matched_content['results'][0]
                    content_title = first_matched_content['title'] if self.library_type_index == 1 else first_matched_content['name']
                    content_year = first_matched_content['release_date'][:4] if self.library_type_index == 1 else first_matched_content['first_air_date'][:4]
                    tmdb_id = first_matched_content['id']
                    print(Fore.BLUE + f"从库中获取内容: {content_title} ({content_year}) {{tmdbid-{tmdb_id}}}" + Style.RESET_ALL)
                    new_folder_name = self.folder_title_format(content_title, content_year, tmdb_id)
                    new_folder_name = self.folder_api.clean_folder_name(new_folder_name)
                    content_to_append = [content_title, content_year, str(tmdb_id), str(self.library_type_index)]
            except KeyError:
                print(Fore.RED + "无法从匹配的内容中获取年份。跳过此文件夹。" + Style.RESET_ALL)
                return  # 跳过此文件夹并继续处理下一个文件夹
            # 如果 append_data 为 true，则将匹配的内容添加到 matched_contents 列表中
            if self.append_data:
                self.matched_contents.append(content_to_append)

            self.move_folder(folder_path, new_folder_name)
            print(Fore.BLUE + "-" * 120)


    def move_folder(self, folder_path, new_folder_name):
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

    def find_in_csv(self, title, year):
        with open('matched_content.csv', 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0] == title and row[1] == year:
                    return row
        return None
    
    # 匹配模式1
    def match_mode_1(self):
        for folder_name in os.listdir(self.parent_folder_path):
            folder_path = os.path.join(self.parent_folder_path, folder_name)
            self.process_single_folder(folder_path, mode=1)
        self.write_to_file()

    # 匹配模式2
    def match_mode_2(self):
        for folder_name in os.listdir(self.parent_folder_path):
            folder_path = os.path.join(self.parent_folder_path, folder_name)
            self.process_single_folder(folder_path, mode=2)
        self.write_to_file()
    # 匹配模式3
    def match_mode_3(self):
        for folder_name in os.listdir(self.parent_folder_path):
            folder_path = os.path.join(self.parent_folder_path, folder_name)
            print(Fore.RED + "正在处理文件夹：" + Style.RESET_ALL + f"{folder_path}")
            if folder_path in self.processed_folders:
                continue

            title, year = self.folder_api.extract_folder_info(folder_name)

            # 从 matched_content.csv 文件中获取匹配的数据
            matched_content = self.find_in_csv(title, year)
            if matched_content:
                print(Fore.GREEN + f"从库中获取内容: {matched_content[0]} ({matched_content[1]}) {{tmdbid-{matched_content[2]}}}" + Style.RESET_ALL)
                new_folder_name = self.folder_title_format(matched_content[0], matched_content[1], matched_content[2])
                self.folder_api.process_folder(folder_path, new_folder_name, matched_content)


    # 匹配模式4
    def match_mode_4(self):
        for folder_name in os.listdir(self.parent_folder_path):
            folder_path = os.path.join(self.parent_folder_path, folder_name)
            print(Fore.RED + "正在处理文件夹：" + Style.RESET_ALL + f"{folder_path}")
            if folder_path in self.processed_folders:
                continue
            if not os.path.isdir(folder_path):
                continue

            title, year = self.folder_api.extract_folder_info(folder_name)

            if not year:
                new_folder_name = title
            else:
                new_folder_name = self.folder_title_format(title, year, None)

            self.folder_api.process_folder(folder_path, new_folder_name, None)

    def process(self):
        if self.match_mode_index == 1:
            self.match_mode_1()
        elif self.match_mode_index == 2:
            self.match_mode_2()
        elif self.match_mode_index == 3:
            self.match_mode_3()
        elif self.match_mode_index == 4:
            self.match_mode_4()
            exit()

def main() -> None:
    print(Fore.RED + '开始程序:注意输入的目录结构必须是【你的目录/剧集或电影文件夹/媒体文件或其他子目录】' + Style.RESET_ALL)
    media_renamer: MediaRenamer = MediaRenamer()
    media_renamer.process()

if __name__ == "__main__":
    main()
