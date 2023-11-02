# @Time : 2023/10/30
# @File : MediaToolKit.py

import os
import re
import json
import logging
from TMDBApi import TMDBApi
from config_utils import ServerConfig  # 修改这里
from plexapi.server import PlexServer


class Utils:
    @staticmethod
    def load_matched_folders(file_name):
        if not os.path.exists(file_name):
            with open(file_name, 'w') as f:
                json.dump([], f)
        try:
            with open(file_name, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []  # 返回一个空列表

    @staticmethod
    def rename_folder(folder_path, new_folder_path, folder_name, new_folder_name):
        if folder_name != new_folder_name:
            if not os.path.exists(new_folder_path):
                if os.path.exists(folder_path):
                    os.rename(folder_path, new_folder_path)
                    print("\033[32m原文件夹名：\033[0m" + f"{folder_name}")
                    print("\033[32m修改后文件夹名：\033[0m" + f"{new_folder_name}")
                    print("-" * 50)


class MediaRenamer:
    def __init__(self, server_config):
        self.server_config = server_config
        self.plex_url, self.plex_token, self.tmdb_api_key = server_config.get_server_info_and_key()
        self.plex = PlexServer(self.plex_url, self.plex_token)  # 创建 Plex 服务器对象
        self.tmdb_api = TMDBApi(self.tmdb_api_key)
        self.request_counts = {}
        self.processed_folders = []

    def plex_search(self, folder_name, library_type_index):
        # 根据library_type_index选择搜索库的类型
        if library_type_index == 1:
            library_type = 'movie'
        elif library_type_index == 2:
            library_type = 'show'
        else:
            print("无效的库类型索引")
            return None

        # 获取所有同类型的库
        sections = [s for s in self.plex.library.sections() if s.type == library_type]

        # 在所有同类型的库中搜索内容
        for section in sections:
            # 首先进行精确匹配标题和年份
            results = section.search(title=folder_name)
            if results and 'year' in results[0] and str(results[0].year) in folder_name:
                return results[0]

            # 如果没有找到精确匹配，再进行模糊匹配标题
            results = section.search(title=folder_name)
            if results:
                # 如果找到了多个匹配项，显示前10个供用户选择
                if len(results) > 1:
                    print("找到多个匹配项：")
                    for i, result in enumerate(results[:10]):
                        print(f"{i+1}. {result.title} ({result.year})")
                    index = int(input("请输入你选择的匹配项编号，或输入0跳过："))
                    if index > 0 and index <= len(results):
                        return results[index-1]
                    else:
                        return None
                else:
                    return results[0]

        # 如果没有找到匹配的内容，就返回None
        return None

    def extract_folder_info(self, folder_name):
        # 移除 "{tmdb-xxxxxx}" 格式的字符串
        folder_name = re.sub(r'\{tmdb-\d+\}', '', folder_name)

        # 使用正则表达式匹配括号内的年份
        year = re.search(r'\((\d{4})\)', folder_name)
        if year:
            year = year.group().strip('()')

        # 移除年份后的文件夹名
        folder_without_year = re.sub(r'\('+year+r'\)', '', folder_name) if year else folder_name

        # 提取中文标题
        chinese_titles = re.findall(r'[\u4e00-\u9fff0-9：，]+(?![^\(]*\))', folder_without_year)

        # 提取英文标题
        english_title = ' '.join(re.findall(r'[a-zA-Z\s]+(?![^\(]*\))', folder_without_year))

        # 如果没有找到中文或英文标题，则将所有非年份的数字视为标题
        if not chinese_titles and not english_title:
            title = ''.join(re.findall(r'(?<!\()\d+(?!\))', folder_without_year))
        else:
            title = ' '.join(chinese_titles) if chinese_titles else english_title

        # 移除前后的空格
        title = title.strip()

        return title, year, chinese_titles

    def generate_new_folder_name(self, title, year, tmdb_id=None, naming_rule_index=1):
        naming_rules = {
            1: f"{title} ({year})",
            2: f"{title} ({year}) {{tmdb-{tmdb_id}}}" if tmdb_id else f"{title} ({year})",
            3: f"{title}.{year}.tmdb-{tmdb_id}" if tmdb_id else f"{title} ({year})"
        }
        return naming_rules.get(naming_rule_index, f"{title} ({year})")

    def process_folder(self, folder_path, search_function, title_key, date_key, naming_rule_index, library_type_index):
        # 根据库类型确定文件名
        if library_type_index == 1:
            matched_folders_file = 'matched_movie_folders.json'
        elif library_type_index == 2:
            matched_folders_file = 'matched_tv_folders.json'
        else:
            print("无效的库类型索引")
            return

        # 打印 matched_folders_file 的值
        print(f"matched_folders_file: {matched_folders_file}")
        for folder_name in os.listdir(folder_path):
            print(f"Processing folder: {folder_name}")  
            
            matched_folder = next((f for f in self.matched_folders if f['name'] == folder_name), None)
            
            if matched_folder:
                print(f"Folder '{folder_name}' has already been processed. Skipping...")  
                continue
            
            title, year, _ = self.extract_folder_info(folder_name)
            match_data = search_function(title)
            
            if match_data and 'id' in match_data:
                if library_type_index == 1:
                    match_data = self.api.movie_info(match_data['id'])
                elif library_type_index == 2:
                    match_data = self.api.tv_info(match_data['id'])
                    
                new_folder_name = self.generate_new_folder_name(
                    match_data[title_key], 
                    match_data[date_key][:4], 
                    match_data['id'], 
                    naming_rule_index
                )
                
                new_folder_path = os.path.join(os.path.dirname(folder_path), new_folder_name)
                
                Utils.rename_folder(folder_path, new_folder_path, folder_name, new_folder_name)  
                
                self.matched_folders.append({
                    'name': folder_name,
                    'match': (match_data[title_key], match_data['id'], match_data[date_key][:4])
                })

        with open(matched_folders_file, 'w') as f:  # 修改这里
            json.dump(self.matched_folders, f)
            print(f"Saved {len(self.matched_folders)} matched folders to {matched_folders_file}")
    def match_mode_1(self, parent_folder_path, library_type_index, naming_rule_index):
        filename = self.get_filename_by_library_type(library_type_index)
        if filename is None:
            return

        self.processed_folders = self.load_processed_folders(filename)

        for folder_name in os.listdir(parent_folder_path):
            folder_path = os.path.join(parent_folder_path, folder_name)
            if os.path.isdir(folder_path) and folder_name not in self.processed_folders:
                print("\033[31m正在处理的文件夹：\033[0m" + f"{folder_name}")
                title, year, _ = self.extract_folder_info(folder_name)
                match_data = self.plex_search(title, library_type_index)
                if match_data:
                    new_folder_name = self.generate_new_folder_name(match_data.title, match_data.year, match_data.ratingKey, naming_rule_index)
                else:
                    # 如果在Plex服务器上找不到匹配项，就在TMDB上进行搜索
                    if library_type_index == 1:
                        match_data = self.tmdb_api.search_movie(title)
                    elif library_type_index == 2:
                        match_data = self.tmdb_api.search_tv(title)

                    # 如果在TMDB上找到了匹配项，就获取更详细的信息
                    if match_data and 'id' in match_data:
                        if library_type_index == 1:
                            match_data = self.tmdb_api.movie_info(match_data['id'])
                        elif library_type_index == 2:
                            match_data = self.tmdb_api.tv_info(match_data['id'])

                        new_folder_name = self.generate_new_folder_name(
                            match_data['title'], 
                            match_data['release_date'][:4], 
                            match_data['id'], 
                            naming_rule_index
                        )

                       
                # 将处理过的文件夹添加到列表中
                self.processed_folders.append(folder_name)
                self.save_processed_folders(filename, self.processed_folders)
        all_folders = set(os.listdir(parent_folder_path))
        processed_folders = set(self.processed_folders)
        unprocessed_folders = all_folders - processed_folders
        print("处理完成后：")
        print("已处理的文件夹：", processed_folders)
        print("未处理的文件夹：", unprocessed_folders)
    def match_mode_2(self, parent_folder_path, library_type_index, naming_rule_index):
        # 匹配模式2的处理逻辑
        rename_list = []
        matched_folders = []
        if library_type_index == 1:
            search_function = self.api.search_movie
            title_key = 'title'
            date_key = 'release_date'
        elif library_type_index == 2:
            search_function = self.api.search_tv
            title_key = 'name'
            date_key = 'first_air_date'

        for folder_name in os.listdir(parent_folder_path):
            folder_path = os.path.join(parent_folder_path, folder_name)
            if os.path.isdir(folder_path):
                self.process_folder(
                    folder_path,
                    search_function,
                    title_key,
                    date_key,
                    naming_rule_index,
                    matched_folders)
        for i, (old_name, new_name) in enumerate(rename_list):
            if i not in indices_to_skip:
                folder_path = os.path.join(parent_folder_path, old_name)  # 获取当前文件夹的路径
                new_folder_path = os.path.join(parent_folder_path, self.generate_new_folder_name(old_name, new_name, naming_rule_index))
                self.rename_folder(folder_path, new_folder_path, old_name, new_name)   
       
    def match_mode_3(self, parent_folder_path, naming_rule_index):
         # 如果 matched_folders 是空的，打印一条消息并返回
        if not matched_folders:
            print("警告：没有找到已匹配的文件夹。")
            return
        rename_list = []
        # 匹配模式3的处理逻辑
        for folder_name in os.listdir(parent_folder_path):
            folder_path = os.path.join(parent_folder_path, folder_name)
            if os.path.isdir(folder_path):
                matched_folder = next(
                    (f for f in matched_folders if f['name'] == folder_name), None)
                if matched_folder:
                    title, tmdb_id, year = matched_folder['match']
                    new_folder_name = self.generate_new_folder_name(
                        title, year, tmdb_id, naming_rule_index)
                    new_folder_path = os.path.join(
                        os.path.dirname(folder_path), new_folder_name)
                    self.rename_folder(
                        folder_path, new_folder_path)
                    rename_list.append((folder_name, new_folder_name))  # 将旧的和新的文件夹名添加到列表中

        for old_name, new_name in rename_list:
            folder_path = os.path.join(parent_folder_path, old_name)  # 获取当前文件夹的路径
            new_folder_path = os.path.join(parent_folder_path, self.generate_new_folder_name(old_name, new_name, naming_rule_index))
            self.rename_folder(folder_path, new_folder_path, old_name, new_name)  # 使用 old_name 和 new_name 作为参数
       
       
    def match_mode_4(self, parent_folder_path):
        naming_rule_index = 1  # 固定使用命名规则1
        folder_names = [folder_name for folder_name in os.listdir(parent_folder_path) if os.path.isdir(os.path.join(parent_folder_path, folder_name))]

        rename_list = []
        for i, folder_name in enumerate(folder_names):
            # 提取标题和年份
            title, year, _ = self.extract_folder_info(folder_name)
            if title is None or year is None:
                print(f"无法从文件夹名 {folder_name} 中提取标题和年份，跳过此文件夹。")
                continue
            new_folder_name = f"{title} ({year})"
            rename_list.append((folder_name, new_folder_name))

        # 计算新名字的最大长度
        max_length_old = max(len(old_name) for old_name, _ in rename_list)
        max_length_new = max(len(new_name) for _, new_name in rename_list)

        print("{:<8}{:<{}}{:<{}}".format("序号", "原名", max_length_old, "修后名", max_length_new))
        print("{:<8}{:<{}}{:<{}}".format("----", "--------", max_length_old, "--------", max_length_new))
        for i, (old_name, new_name) in enumerate(rename_list):
            print("{:<8}{:<{}}{:<{}}".format(i+1, old_name, max_length_old, new_name, max_length_new))
        indices_to_skip = input("\033[32m请输入你不想处理的文件夹的序号，用逗号分隔（默认为空）:\033[0m ")
        indices_to_skip = set(
            int(idx) -
            1 for idx in indices_to_skip.split(",") if idx.strip().isdigit())
    
        for i, (old_name, new_name) in enumerate(rename_list):
            if i not in indices_to_skip:
                folder_path = os.path.join(parent_folder_path, old_name)  # 获取当前文件夹的路径
                new_folder_path = self.generate_new_folder_name(title, year)
                self.rename_folder(folder_path, new_folder_path, old_name, new_name)           
    def get_filename_by_library_type(self, library_type_index):
        # 根据库类型选择要读取的文件
        if library_type_index == 1:
            return 'matched_movie_folders.json'
        elif library_type_index == 2:
            return 'matched_tv_folders.json'
        else:
            print("无效的库类型索引")
            return None

    def load_processed_folders(self, filename):
        # 读取已处理的文件夹列表
        with open(filename, 'r') as f:
            return json.load(f)

    def save_processed_folders(self, filename, processed_folders):
        # 将更新后的列表写回到文件中
        with open(filename, 'w') as f:
            json.dump(processed_folders, f)