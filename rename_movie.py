# -*- coding: utf-8 -*-
# @Time : 2023/11/21
# @File : rename_movie.py

import os
import re
import json
import requests
import shutil
from api import PlexApi
from config import ConfigManager
from colorama import Fore, Style
from typing import Dict, Optional, Union, List, Tuple
from difflib import SequenceMatcher

CONFIG_FILE = 'config.json'

class MovieRenamer:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config_manager = ConfigManager(self.config_file)
        self.config = self.config_manager.config
        server_info_and_key = self.config_manager.get_server_info_and_key()
        self.plex_api = PlexApi(server_info_and_key['plex_url'], server_info_and_key['plex_token'])
        self.video_suffix_list = self.config['video_suffix_list'].split(',')
        self.subtitle_suffix_list = self.config['subtitle_suffix_list'].split(',')
        self.other_suffix_list = self.config['other_suffix_list'].split(',')
        self.movie_title_format = self.config['movie_title_format'].split(',')
        self.movie_move_files = self.config['move_files']
        self.movie_delete_files = self.config['movie_delete_files']
        

    def main(self) -> None:
        """
        主函数。
        """
        print(Fore.RED + '开始程序:注意输入的目录结构必须是【你的目录/剧集或电影文件夹/媒体文件或其他子目录】' + Style.RESET_ALL)
        parent_folder_path = input("请输入你的目录的路径：")
        if not os.path.exists(parent_folder_path):
            print(Fore.RED + "输入的路径不存在，请检查后重新输入。" + Fore.RESET)
            return
        print(Fore.GREEN + f"预处理所有文件名: {parent_folder_path}" + Style.RESET_ALL)
        # 在处理文件信息之前，先预处理文件

        if self.movie_delete_files:
            self.delete_files(parent_folder_path)

        if self.movie_move_files:
            self.move_files(parent_folder_path)

        rename_dict = self.process_movie_files(parent_folder_path)
        if rename_dict is not None:
            self.rename_files(rename_dict)
            print(Fore.RED + "媒体文件重命名执行完毕。" + Style.RESET_ALL)


        subtitle_rename_dict = self.process_subtitle_files(parent_folder_path)
        if subtitle_rename_dict is not None:
            self.rename_files(subtitle_rename_dict)
            print(Fore.RED + "字幕文件重命名执行完毕。" + Style.RESET_ALL)

    def move_files(self, parent_folder_path):
        for root, dirs, files in os.walk(parent_folder_path, topdown=False):
            # 跳过父文件夹和直接子目录
            if root == parent_folder_path or os.path.dirname(root) == parent_folder_path:
                continue

            for filename in files:
                file_path = os.path.join(root, filename)

                # 检查文件是否已经移动，如果已移动则跳过
                if not os.path.exists(file_path):
                    continue

                # 移动文件
                if self.move_files:
                    movie_folder_path = os.path.dirname(root)
                    target_path = os.path.join(movie_folder_path, filename)
                    if not os.path.exists(target_path):
                        shutil.move(file_path, target_path)

    def delete_files(self, parent_folder_path):
        for root, dirs, files in os.walk(parent_folder_path, topdown=False):
            # 跳过父文件夹和直接子目录
            if root == parent_folder_path:
                continue

            for filename in files:
                file_path = os.path.join(root, filename)
                extension = os.path.splitext(filename)[1][1:]

                # 删除指定扩展名的文件
                if self.movie_delete_files and extension in self.other_suffix_list:
                    if os.path.exists(file_path):
                        os.remove(file_path)

            # 检查并删除空目录
            if not os.listdir(root):
                os.rmdir(root)
        print(Fore.RED + "执行移动删除完成。" + Style.RESET_ALL)


    def process_movie_files(self, directory_path: str) -> Dict[str, str]:
        """
        遍历指定目录，处理所有媒体文件。

        参数:
        directory_path (str): 要处理的目录路径。

        返回:
        Dict[str, str]: 媒体文件路径到新文件名的映射。
        """
        files_info, all_filenames = self.collect_files_info(directory_path)
        rename_dict = {}
        for file_path, elements_from_file in files_info.items():
            final_elements = self.process_file_info(file_path, files_info, self.plex_api)
            if final_elements:
                new_name_elements = [str(final_elements[key]) for key in self.movie_title_format if final_elements[key] is not None]
                new_filename = '.'.join(new_name_elements) + os.path.splitext(file_path)[1]
                rename_dict[file_path] = os.path.join(os.path.dirname(file_path), new_filename)
        return rename_dict or {}


    # 定义一个函数来计算两个字符串的相似度
    def similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio()


    def process_subtitle_files(self, directory_path):
        print(f"支持的字幕文件格式: {self.subtitle_suffix_list}")
        subtitle_files = {}
        media_files = {}
        media_file_counts = {}

        for root, dirs, files in os.walk(directory_path):
            media_files_in_dir = [file for file in files if file.endswith(tuple('.' + ext for ext in self.video_suffix_list))]
            subtitles_in_dir = [file for file in files if file.endswith(tuple('.' + ext for ext in self.subtitle_suffix_list))]

            # 将媒体文件的路径和名称添加到media_files字典中，并初始化每个媒体文件的计数器
            for media_file in media_files_in_dir:
                media_files[os.path.join(root, media_file)] = media_file
                media_file_counts[os.path.join(root, media_file)] = 0

            for subtitle_file in subtitles_in_dir:
                max_similarity = 0
                best_match = None

                subtitle_name = os.path.splitext(subtitle_file)[0]

                for media_file in media_files_in_dir:
                    media_name = os.path.splitext(media_file)[0]
                    similarity = self.similar(media_name, subtitle_name)

                    # 只要相似度大于0，并且这个媒体文件的计数器值最小，就视为匹配
                    if similarity > 0 and (best_match is None or media_file_counts[os.path.join(root, media_file)] < media_file_counts[os.path.join(root, best_match)]):
                        max_similarity = similarity
                        best_match = media_file

                if best_match:  # 如果有媒体文件，则必定满足相似度
                    file_path = os.path.join(root, best_match)
                    new_name_base = os.path.splitext(media_files[file_path])[0]
                    subtitle_ext = os.path.splitext(subtitle_file)[1]
                    new_name = new_name_base + subtitle_ext

                    identifier = 1
                    while os.path.exists(os.path.join(root, new_name_base + f"_{identifier}" + subtitle_ext)) or new_name_base + f"_{identifier}" + subtitle_ext in subtitle_files.values():
                        identifier += 1
                    if identifier > 1:
                        new_name = new_name_base + f"_{identifier}" + subtitle_ext

                    # 增加这个媒体文件的计数器值
                    media_file_counts[file_path] += 1
                else:
                    # 如果没有找到满足相似度的媒体文件，可以选择保留原始名称或采用其他默认处理方式
                    new_name = subtitle_file
                    print(f"没有找到满足相似度的媒体文件: {os.path.join(root, subtitle_file)}")

                # 在新名称中包含完整的路径
                subtitle_files[os.path.join(root, subtitle_file)] = os.path.join(root, new_name)

        return subtitle_files


    def collect_files_info(self, parent_folder_path):
        total_files_info = {}
        total_filenames = []

        for movie_folder in os.listdir(parent_folder_path):
            movie_folder_path = os.path.join(parent_folder_path, movie_folder)
            if not os.path.isdir(movie_folder_path):
                continue

            files_info, all_filenames = self.process_directory(movie_folder_path)
            total_files_info.update(files_info)
            total_filenames.extend(all_filenames)

        print(Fore.RED + "文件名预处理完成。" + Style.RESET_ALL)
        return total_files_info, total_filenames

    def process_directory(self, directory_path: str) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
        """
        遍历指定目录，处理所有媒体文件。

        参数:
        directory_path (str): 要处理的目录路径。

        返回:
        Tuple[Dict[str, Dict[str, str]], List[str]]: 包含两个元素的元组，第一个是文件路径到文件信息的映射字典，第二个是所有文件名的列表。
        """
        files_info = {}  # type: Dict[str, Dict[str, str]]
        all_filenames = []  # type: List[str]

        for root, dirs, files in os.walk(directory_path):
            for filename in files:
                try:
                    file_path = os.path.join(root, filename)
                    extension = os.path.splitext(filename)[1].lower().lstrip('.')

                    # 处理媒体
                    if extension in self.video_suffix_list:
                        file_info = self.get_file_info(file_path)
                        if file_info:
                            files_info[file_path] = file_info
                            all_filenames.append(filename)
                except Exception as e:
                    print(f"处理文件 {filename} 时发生错误: {e}")

        return files_info, all_filenames

    def process_file_info(self, file_path: str, files_info: Dict[str, Dict[str, str]], plex_api: PlexApi) -> Dict[str, str]:
        """
        处理文件信息。

        参数:
        file_path (str): 文件的路径。

        返回:
        Dict[str, str]: 一个字典，包含处理后的文件信息。
        """
        elements_from_file = files_info[file_path]
        chinese_title = elements_from_file['chinese_title']
        english_title = elements_from_file['english_title']
        year = elements_from_file['year']
        plex_info = self.search_movie(file_path, chinese_title, english_title, year)
        if plex_info:
            final_elements = elements_from_file.copy() # 复制一份文件信息
            for key, value in plex_info.items():
                if value and final_elements.get(key) is None:
                    if isinstance(value, str):
                        if key == 'english_title':
                            # 英文标题转换为首字母大写的形式
                            final_elements[key] = value.title().replace(' ', '.')
                        else:
                            # 其他元素全部转换为大写
                            final_elements[key] = value.upper().replace(' ', '.')
                    elif isinstance(value, int):
                        # 将整数转换为字符串
                        final_elements[key] = str(value)

            # 使用 Plex 的中文标题（如果存在且包含中文字符）
            if 'chinese_title' in plex_info and plex_info['chinese_title'] and any('\u4e00' <= char <= '\u9fff' for char in plex_info['chinese_title']):
                final_elements['chinese_title'] = plex_info['chinese_title']

            # 使用 Plex 的 HDR 信息（如果存在）
            if 'hdr_info' in plex_info and plex_info['hdr_info']:
                final_elements['hdr_info'] = plex_info['hdr_info']

        else:
            final_elements = elements_from_file  # 如果 Plex 无法匹配到电影信息，返回从文件名中提取的元素

        # 处理最终元素大小写问题
        for key, value in final_elements.items():
            if isinstance(value, str):
                if key == 'english_title':
                    # 英文标题转换为首字母大写的形式
                    final_elements[key] = value.title().replace(' ', '.')
                elif key == 'bit_depth':
                    # 保持 bit_depth 的值为小写
                    final_elements[key] = value.lower()
                else:
                    # 其他元素全部转换为大写
                    final_elements[key] = value.upper().replace(' ', '.').replace(':', '：').replace('-', '：')

        #print("提取的信息：", final_elements)
        return final_elements

    def get_file_info(self, file_path: str) -> Dict[str, str]:
        """
        从文件名提取信息。

        参数:
        file_path (str): 文件的路径。

        返回:
        Dict[str, str]: 一个字典，包含从文件名中提取的信息。
        """
        print(Fore.GREEN + "文件正在提取元素: " + Style.RESET_ALL + f"{os.path.basename(file_path)}")
        file_name_no_ext, file_ext = os.path.splitext(os.path.basename(file_path))
        file_ext = file_ext[1:]  # 获取不包含点号的扩展名
        file_name_no_ext = file_name_no_ext.replace('.', ' ')
        file_name_no_ext = file_name_no_ext.upper()
        self.elements_to_remove = self.config['elements_to_remove'].split(',')
        for element in self.elements_to_remove:
            file_name_no_ext = re.sub(element, '', file_name_no_ext)
        file_name_no_ext = re.sub(r'\b(REMUX|BDREMUX|BD-REMUX)\b', 'REMUX', file_name_no_ext, flags=re.IGNORECASE)
        file_name_no_ext = re.sub(r'\b(BLURAY|BD|BLU-RAY|BD1080P)\b', 'BD', file_name_no_ext, flags=re.IGNORECASE)
        file_name_no_ext = re.sub(r'\b(HQCAM|HQ-CAM)\b', 'HQCAM', file_name_no_ext, flags=re.IGNORECASE)
        file_name_no_ext = re.sub(r'【.*?】', '', file_name_no_ext)
        file_name_no_ext = re.sub(r'\{.*?\}', '', file_name_no_ext)
        file_name_no_ext = re.sub(r'\[.*?\]', '', file_name_no_ext)

        self.elements_regex = self.config['elements_regex']
        elements = {key: None for key in self.elements_regex.keys()}
        for key, regex in self.elements_regex.items():
            if key == 'year':
                match = re.search(regex, file_name_no_ext, re.IGNORECASE)
                if match:
                    elements[key] = match.group(0)
                    file_name_no_ext = file_name_no_ext.replace(match.group(0), '')
            else:
                matches = re.findall(regex, file_name_no_ext, re.IGNORECASE)
                if matches:
                    elements[key] = ' '.join(matches)
                    for match in matches:
                        file_name_no_ext = file_name_no_ext.replace(match, '')
        file_name_no_ext = file_name_no_ext.split('-')[0]
        #print(Fore.GREEN + f"剩余的文件名: {file_name_no_ext}" + Style.RESET_ALL)
        series_number_arabic = re.search(r'\b[2-5]\b', file_name_no_ext)
        series_number_roman = re.search(r'\b(?:M{0,3})(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})\b', file_name_no_ext)
        if series_number_arabic:
            elements['series_number'] = series_number_arabic.group(0)
            file_name_no_ext = file_name_no_ext.replace(series_number_arabic.group(0), '')
        elif series_number_roman:
            elements['series_number'] = series_number_roman.group(0)
            file_name_no_ext = file_name_no_ext.replace(series_number_roman.group(0), '')

        chinese_title = re.search(r'《.*?》', file_name_no_ext)
        if chinese_title:
            elements['chinese_title'] = chinese_title.group(0)[1:-1]
            file_name_no_ext = file_name_no_ext.replace(chinese_title.group(0), '')
        else:
            chinese_title = re.search(r'[\u4e00-\u9fff]+[0-9a-zA-Z：，·]*', file_name_no_ext)
            if chinese_title:
                if re.search(r'[\u4e00-\u9fff]', chinese_title.group(0)):
                    elements['chinese_title'] = chinese_title.group(0)
                    file_name_no_ext = file_name_no_ext.replace(chinese_title.group(0), '')
                else:
                    elements['chinese_title'] = None
            else:
                elements['chinese_title'] = None
        if elements['chinese_title'] is None and file_path and len(os.listdir(os.path.dirname(file_path))) < 8:
            parent_folder_name = os.path.basename(os.path.dirname(file_path))
            chinese_title = re.search(r'[\u4e00-\u9fff]+[0-9a-zA-Z：，·]*', parent_folder_name)
            if chinese_title:
                elements['chinese_title'] = chinese_title.group(0)
                #print(Fore.GREEN + f"提取的中文标题: {elements['chinese_title']}" + Style.RESET_ALL)
        english_title = re.search(r'[a-zA-Z0-9]+(\s[a-zA-Z0-9]+)*', file_name_no_ext)

        if english_title:
            elements['english_title'] = english_title.group(0)
            file_name_no_ext = file_name_no_ext.replace(english_title.group(0), '')
        else:
            elements['english_title'] = None

        if elements['chinese_title'] is None and elements['english_title'] is None:
            parent_folder_name = os.path.basename(os.path.dirname(file_path))
            chinese_title = re.search(r'[\u4e00-\u9fff]+[0-9a-zA-Z：，·]*', parent_folder_name)
            english_title = re.search(r'[a-zA-Z0-9_]+', parent_folder_name)
            if chinese_title:
                elements['chinese_title'] = chinese_title.group(0)
            if english_title:
                elements['english_title'] = english_title.group(0)

        return elements

    def search_movie(self, file_path: str, chinese_title: str = None, english_title: str = None, year: str = None) -> str:
        file_name = os.path.basename(file_path)
        print(Fore.GREEN + "PLEX正在提取元素:" + Style.RESET_ALL, file_name)

        if chinese_title == english_title:
            english_title = None

        movie_info_found = False
        extracted_info = {}

        if chinese_title is not None:
            movies = self.plex_api.search_movie(chinese_title)
        else:
            movies = self.plex_api.search_movie(english_title)

        if movies:
            movie_info_found = True
            media_list = movies.get('Media', [])
            for media in media_list:
                part_list = media.get('Part', [])
                for part in part_list:
                    if 'file' in part:
                        file_path = part['file']
                        file_name_in_part = os.path.basename(file_path)
                        if file_name in file_name_in_part or file_name_in_part in file_name:
                            extracted_info = {
                                'chinese_title': movies.get('title', ''),
                                'year': movies.get('year', ''),
                                'resolution': self.resolve_resolution(media),
                                'source': self.determine_source(media),
                                'codec': media.get('videoCodec', '').upper(),
                                'bit_depth': str(media.get('bitDepth', '8')) + 'bit',
                                'hdr_info': self.get_hdr_info(media),
                                'audio_format': media.get('audioCodec', '').upper()
                            }
                            print("提取PLEX的信息：", extracted_info)
                            return extracted_info

        if not movie_info_found:
            # 只有当没有找到电影信息时，才请求手动输入
            print("未找到匹配的电影，请求手动输入")
            manual_title = input("请输入电影的标题（如果想跳过，请直接按回车）：")
            manual_year = input("请输入电影的年份（如果想跳过，请直接按回车）：")
            if not manual_title.strip() and not manual_year.strip():
                return {}  # 返回一个空字典，而不是原始的文件名
            return self.search_movie(file_path, chinese_title=manual_title, year=manual_year)

        return {}

    def resolve_resolution(self, media: Dict) -> str:
        resolution = media.get('videoResolution', '').lower()
        return resolution + 'P' if resolution != '4k' else resolution

    def determine_source(self, media: Dict) -> str:
        bitrate_mbps = media.get('bitrate', 0) / 8000
        if bitrate_mbps <= 0.3:
            return 'TS'
        elif 0.3 < bitrate_mbps <= 0.7:
            return 'HQCAM'
        elif 0.7 < bitrate_mbps <= 1.5:
            return 'HDTC'
        elif 1.5 < bitrate_mbps <= 3:
            return 'DVDRIP'
        elif 3 < bitrate_mbps <= 5:
            return 'HDRIP'
        elif 5 < bitrate_mbps <= 8:
            return 'HDTV'
        elif 8 < bitrate_mbps <= 12:
            return 'WEBRIP'
        elif 12 < bitrate_mbps <= 20:
            return 'WEB-DL'
        elif 20 < bitrate_mbps <= 30:
            return 'BDRIP'
        elif 30 < bitrate_mbps <= 50:
            return 'BD'
        else:
            return 'REMUX'


    def get_hdr_info(self, media: Dict) -> str:
        if 'Part' in media:
            for part in media['Part']:
                if 'Stream' in part:
                    for stream in part['Stream']:
                        display_title = stream.get('displayTitle', '')
                        if display_title:
                            display_title = display_title.upper()
                            hdr_info = re.search(r'(DOLBY VISION|DOVI|DV|HDR10\+|HDR10|HLG|DISPLAYHDR)', display_title)
                            if hdr_info:
                                return hdr_info.group(0)
        return 'SDR'


    def rename_files(self, rename_dict: Dict[str, str]):
        """
        重命名文件。

        参数:
        rename_dict (Dict[str, str]): 一个字典，包含旧文件名作为键，新文件名作为值。
        template (list): 一个列表，包含文件名的组成部分。

        返回:
        无
        """
        index = 1
        for old_name, new_name in rename_dict.items():
            print(self.format_file_info(index, old_name, new_name))
            index += 1

        choice = input("请输入你不想修改的文件序号，如果全部修改，请直接按回车：")
        if choice:
            choices = choice.split()  # 分割输入的字符串
            for choice in choices:
                try:
                    choice = int(choice)
                    if 1 <= choice <= len(rename_dict):
                        del rename_dict[list(rename_dict.keys())[choice - 1]]
                    else:
                        print(f"输入的序号 {choice} 不在有效范围内，请重新输入。")
                except ValueError:
                    print("输入的不是有效的数字，请重新输入。")

        for old_name, new_name in rename_dict.items():
            if not os.path.exists(new_name):     
                print(self.format_file_info(index, old_name, new_name))
                os.rename(old_name, new_name)
            else:
                print(Fore.RED + f"跳过重命名：{os.path.basename(new_name)}" + Style.RESET_ALL)



    def format_file_info(self, index: int, old_name: str, new_name: str) -> str:
        """
        格式化文件信息的输出。
        参数:
        index (int): 文件的索引。
        old_name (str): 文件的原始名称。
        new_name (str): 文件的新名称。
        返回:
        str: 格式化后的文件信息。
        """
        old_name = os.path.basename(old_name)
        new_name = os.path.basename(new_name)
        return f"{index}. 改前名: {Fore.BLUE}{old_name}{Style.RESET_ALL}\n{index}. 改后名: {Fore.GREEN}{new_name}{Style.RESET_ALL}"


    def process_single_folder(self, folder_path):
        # 检查路径是否存在并且是一个文件夹
        if not os.path.isdir(folder_path):
            print(f"路径 {folder_path} 不存在或者不是一个文件夹。")
            return

        # 提取文件夹名称
        folder_name = os.path.basename(folder_path)

        # 提取文件夹信息
        title, year = self.extract_folder_info(folder_name)

        # 根据库类型搜索匹配的内容
        matched_content = None
        if self.library_type_index == 1:
            print(f"正在搜索电影中：{title} ({year})")
            matched_content = self.tmdb_api.search_movie(title, year)
        elif self.library_type_index == 2:
            print(f"正在搜索剧集中：{title} ({year})")
            matched_content = self.tmdb_api.search_tv(title, year)

        # 如果找到匹配的内容，重命名文件夹
        if matched_content:
            print(f"从库中获取内容: {matched_content['title']} ({matched_content['year']}) {{tmdbid-{matched_content['tmdbid']}}}")
            tmdb_id = matched_content['tmdbid']
            new_folder_name = self.folder_title_format(matched_content['title'], matched_content['year'], tmdb_id)
            self.process_folder(folder_path, new_folder_name, matched_content)


if __name__ == "__main__":
    movie_renamer = MovieRenamer(CONFIG_FILE)
    movie_renamer.main()
