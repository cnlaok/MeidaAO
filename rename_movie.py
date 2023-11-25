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
from typing import Dict, Tuple, List



CONFIG_FILE = 'config.json'

class MovieRenamer:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config_manager = ConfigManager(self.config_file)
        server_info_and_key = self.config_manager.get_server_info_and_key()
        self.plex_api = PlexApi(server_info_and_key['plex_url'], server_info_and_key['plex_token'])
        self.video_suffix_list = ['.mp4', '.mkv', '.flv', '.avi', '.mpg', '.mpeg', '.mov', '.ts', '.wmv', '.rm', '.rmvb', '.3gp', '.3g2', '.webm']
        self.subtitle_suffix_list = ['.srt', '.ass', '.stl', '.sub', '.smi', '.sami', '.ssa', '.vtt']
        self.other_suffix_list = ['.nfo', '.jpg', '.txt', '.png', '.log']
        self.movie_title_format = ['chinese_title', 'english_title', 'year', 'resolution', 'source', 'codec', 'audio_format', 'edit_version']

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


    def rename_files(self, rename_dict: Dict[str, str], template: list):
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
                print(Fore.GREEN + f"正在重命名：{os.path.basename(old_name)} -> {os.path.basename(new_name)}" + Style.RESET_ALL)
                os.rename(old_name, new_name)
            else:
                print(Fore.RED + f"文件已存在，跳过重命名：{os.path.basename(new_name)}" + Style.RESET_ALL)
        print(Fore.GREEN + "重命名完成" + Style.RESET_ALL)

    def get_file_info(self, file_path: str) -> Dict[str, str]:
        """
        从文件名提取信息。

        参数:
        file_path (str): 文件的路径。

        返回:
        Dict[str, str]: 一个字典，包含从文件名中提取的信息。
        """
        print(Fore.GREEN + f"正在处理的文件名: {os.path.basename(file_path)}" + Style.RESET_ALL)
        file_name_no_ext, file_ext = os.path.splitext(os.path.basename(file_path))
        file_name_no_ext = file_name_no_ext.replace('.', ' ')
        file_name_no_ext = file_name_no_ext.upper()
        elements_to_remove = ['%7C', '国语中字', '简英双字', '繁英雙字', '泰语中字', '3D', '国粤双语', r'\d+分钟版']
        for element in elements_to_remove:
            file_name_no_ext = re.sub(element, '', file_name_no_ext)
        file_name_no_ext = re.sub(r'\b(REMUX|BDREMUX|BD-REMUX)\b', 'REMUX', file_name_no_ext, flags=re.IGNORECASE)
        file_name_no_ext = re.sub(r'\b(BLURAY|BD|BLU-RAY|BD1080P)\b', 'BD', file_name_no_ext, flags=re.IGNORECASE)
        file_name_no_ext = re.sub(r'\b(HQCAM|HQ-CAM)\b', 'HQCAM', file_name_no_ext, flags=re.IGNORECASE)
        file_name_no_ext = re.sub(r'【.*?】', '', file_name_no_ext)
        file_name_no_ext = re.sub(r'\{.*?\}', '', file_name_no_ext)
        file_name_no_ext = re.sub(r'\[.*?\]', '', file_name_no_ext)

        elements_regex = {
            "year": r'\b(19[0-9]{2}|20[0-5][0-9])\b',
            "resolution": r'\b(?:HD)?(480P|540P|720P|1080P|2160P|4K|8K)\b',
            "source": r'\b(REMUX|BD|BDRIP|WEB-DL|WEBDL|WEBRIP|WEB|HR-HDTV|HRHDTV|HDTV|HDRIP|DVDRIP|DVDSCR|DVD|HDTC|TC|HQCAM|CAM|TS)\b',
            "codec": r'\b(X264|H264|H 264|H\.264|X265|H265|H 265|H\.265|HEVC|H265版|H264版|VP8|VP9|AV1|VC1|MPEG1|MPEG2|MPEG-4|Theora|ProRes)\b',
            "bit_depth": r'\b\d{1,2}BIT\b',
            "hdr_info": r'(HDR10\+|DV|SDR|HDR10|HDR|DOLBY VISION|HLG|DISPLAYHDR)',
            "audio_format": r'\b(MP3|AAC|WAV|FLAC|ALAC|APE|LPCM|DTS-HD MA|DTS-HD HR|DDP5 1|DTS:X|DTS-X|AC-3 EX|AC3EX|E-AC-3|DCA-MA|EAC3|TRUEHD|ATMOS|DTS|DD5 1|DD\+|AC3|DD|EX|DDL|7 1|5 1|DTS-HD\.MA\.TrueHD\.7\.1\.Atmos)\b',
            "edit_version": r'\b(PROPER|REPACK|LIMITED|IMAX|UNRATE|R-RATE|SE|DC|DIRECTOR\'S CUT|THEATRICAL CUT|ANNIVERSARY EDITION|REMASTERED|OPEN MATTE)\b'
        }

        elements = {key: None for key in elements_regex.keys()}
        for key, regex in elements_regex.items():
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
        print(Fore.GREEN + f"剩余的文件名: {file_name_no_ext}" + Style.RESET_ALL)
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
            chinese_title = re.search(r'[\u4e00-\u9fff0-9a-zA-Z½]+', file_name_no_ext)
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
            chinese_title = re.search(r'[\u4e00-\u9fffA-Za-z0-9：，]+', parent_folder_name)
            if chinese_title:
                elements['chinese_title'] = chinese_title.group(0)
                print(Fore.GREEN + f"提取的中文标题: {elements['chinese_title']}" + Style.RESET_ALL)
        english_title = re.search(r'[a-zA-Z0-9]+(\s[a-zA-Z0-9]+)*', file_name_no_ext)

        if english_title:
            elements['english_title'] = english_title.group(0)
            file_name_no_ext = file_name_no_ext.replace(english_title.group(0), '')
        else:
            elements['english_title'] = None

        if elements['chinese_title'] is None and elements['english_title'] is None:
            parent_folder_name = os.path.basename(os.path.dirname(file_path))
            chinese_title = re.search(r'[\u4e00-\u9fff]+', parent_folder_name)
            english_title = re.search(r'[a-zA-Z0-9_]+', parent_folder_name)
            if chinese_title:
                elements['chinese_title'] = chinese_title.group(0)
            if english_title:
                elements['english_title'] = english_title.group(0)
        print(elements)
        return elements


    def search_movie(self, plex_api: PlexApi, chinese_title: str = None, english_title: str = None, year: str = None) -> Dict[str, str]:
        """
        从 Plex 搜索电影。

        参数:
        plex_api (PlexApi): PlexApi 的实例。
        chinese_title (str): 电影的中文标题。
        english_title (str): 电影的英文标题。
        year (str): 电影的年份。

        返回:
        Dict[str, str]: 一个字典，包含从 Plex 中搜索到的电影信息。
        """
        if chinese_title == english_title:
            english_title = None
        try:
            if chinese_title is not None:
                print(Fore.GREEN + f"正在从 Plex 搜索: 中文标题={chinese_title}, 年份={year}" + Style.RESET_ALL)
                search_endpoint = f"/search?query={chinese_title}"
            else:
                print(Fore.GREEN + f"正在从 Plex 搜索: 英文标题={chinese_title}, 年份={year}" + Style.RESET_ALL)
                search_endpoint = f"/search?query={english_title}"
            
            search_url = plex_api.plex_url + search_endpoint
            response = requests.get(search_url, headers=plex_api.headers)
            movies = response.json()
            
            # 检查是否有匹配的媒体
            if 'Metadata' in movies['MediaContainer']:
                for media in movies['MediaContainer']['Metadata']:
                    #print("media 字典的内容：", media)  # 打印 media 字典的内容
                    try:
                        file_path = media['Media'][0]['Part'][0]['file']
                        #print("文件路径:", file_path)
                    except (IndexError, KeyError):
                        continue
                    
                    extracted_info = {}
                    extracted_info['chinese_title'] = media.get('title')
                    extracted_info['year'] = media.get('year')
                    resolution = media.get('Media')[0].get('videoResolution')
                    extracted_info['resolution'] = resolution + 'P' if resolution.lower() != '4k' else resolution
                    bitrate_mbps = media.get('Media')[0].get('bitrate') / 8000   # 将比特率转换为兆字节每秒
                    if bitrate_mbps <= 0.3:
                        extracted_info['source'] = 'TS'
                    elif 0.3 < bitrate_mbps <= 0.7:
                        extracted_info['source'] = 'HQCAM'
                    elif 0.7 < bitrate_mbps <= 1.5:
                        extracted_info['source'] = 'HDTC'
                    elif 1.5 < bitrate_mbps <= 3:
                        extracted_info['source'] = 'DVDRIP'
                    elif 3 < bitrate_mbps <= 5:
                        extracted_info['source'] = 'HDRIP'
                    elif 5 < bitrate_mbps <= 8:
                        extracted_info['source'] = 'HDTV'
                    elif 8 < bitrate_mbps <= 12:
                        extracted_info['source'] = 'WEBRIP'
                    elif 12 < bitrate_mbps <= 20:
                        extracted_info['source'] = 'WEB-DL'
                    elif 20 < bitrate_mbps <= 30:
                        extracted_info['source'] = 'BDRIP'
                    elif 30 < bitrate_mbps <= 50:
                        extracted_info['source'] = 'BD'
                    else:
                        extracted_info['source'] = 'REMUX'
                    extracted_info['codec'] = media.get('Media')[0].get('videoCodec').upper()
                    extracted_info['audio_format'] = media.get('Media')[0].get('audioCodec').upper()

                    return extracted_info  # 返回获取的媒体信息
            else:
                print(Fore.RED + "未找到匹配的媒体。尝试手动输入标题和年份进行搜索。" + Style.RESET_ALL)
                manual_title = input("请输入电影的标题（如果想跳过，请直接按回车）：")
                manual_year = input("请输入电影的年份（如果想跳过，请直接按回车）：")
                
                # 检查输入是否为空，如果为空则跳过
                if not manual_title.strip() and not manual_year.strip():
                    print("跳过当前文件的匹配。")
                    return None
                
                return self.search_movie(plex_api, chinese_title=manual_title, year=manual_year)

        except requests.exceptions.RequestException as e:
            print(Fore.RED + f"无法连接到 Plex: {e}" + Style.RESET_ALL)
            return None

    def process_directory(self, directory_path, move_files, delete_other_files):
        files_info = {}
        all_filenames = []

        for root, dirs, files in os.walk(directory_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                extension = os.path.splitext(filename)[1]

                # 检查文件是否已经移动，如果已移动则跳过
                if not os.path.exists(file_path):
                    continue

                # 移动文件
                if move_files and root != directory_path:
                    target_path = os.path.join(directory_path, filename)
                    if not os.path.exists(target_path):
                        shutil.move(file_path, target_path)
                        continue  # 移动文件后跳过后续处理

                # 删除指定扩展名的文件
                if delete_other_files and extension in self.other_suffix_list:
                    os.remove(file_path)
                    continue  # 删除文件后跳过后续处理

                # 处理媒体和字幕文件
                if extension in self.video_suffix_list or extension in self.subtitle_suffix_list:
                    file_info = self.get_file_info(file_path)
                    if file_info:
                        files_info[file_path] = file_info
                        all_filenames.append(filename)

        return files_info, all_filenames

    def collect_files_info(self, parent_folder_path, move_files=True, delete_other_files=False):
        print(Fore.GREEN + f"正在遍历文件夹: {parent_folder_path}" + Style.RESET_ALL)
        total_files_info = {}
        total_filenames = []

        for movie_folder in os.listdir(parent_folder_path):
            movie_folder_path = os.path.join(parent_folder_path, movie_folder)
            if not os.path.isdir(movie_folder_path):
                continue

            files_info, all_filenames = self.process_directory(movie_folder_path, move_files, delete_other_files)
            total_files_info.update(files_info)
            total_filenames.extend(all_filenames)

            # 清空旧信息并重新遍历目录，确保获取最新文件列表
            if move_files:
                total_files_info.clear()
                total_filenames.clear()
                updated_files_info, updated_filenames = self.process_directory(movie_folder_path, False, delete_other_files)
                total_files_info.update(updated_files_info)
                total_filenames.extend(updated_filenames)

        print(Fore.GREEN + "文件预处理完成" + Style.RESET_ALL)
        return total_files_info, total_filenames


    def process_file_info(self, file_path: str, plex_api: PlexApi) -> Dict[str, str]:
        """
        处理文件信息。

        参数:
        file_path (str): 文件的路径。

        返回:
        Dict[str, str]: 一个字典，包含处理后的文件信息。
        """
        elements_from_file = self.get_file_info(file_path)
        chinese_title = elements_from_file['chinese_title']
        english_title = elements_from_file['english_title']
        year = elements_from_file['year']
        plex_info = self.search_movie(self.plex_api, chinese_title, english_title, year)
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
            # 如果 Plex 有中文标题，并且标题中包含中文字符，则使用 Plex 的中文标题
            if 'chinese_title' in plex_info and plex_info['chinese_title'] and any('\u4e00' <= char <= '\u9fff' for char in plex_info['chinese_title']):
                final_elements['chinese_title'] = plex_info['chinese_title']
            # 如果 Plex 的中文标题实际为英文，则不使用这个中文标题
            elif 'chinese_title' in plex_info and plex_info['chinese_title'] and all('\u4e00' > char or char > '\u9fff' for char in plex_info['chinese_title']):
                final_elements['chinese_title'] = None
        else:
            final_elements = elements_from_file  # 如果 Plex 无法匹配到电影信息，返回从文件名中提取的元素

        # 处理从文件名中提取的信息
        for key, value in final_elements.items():
            if isinstance(value, str):
                if key == 'english_title':
                    # 英文标题转换为首字母大写的形式
                    final_elements[key] = value.title().replace(' ', '.')
                else:
                    # 其他元素全部转换为大写
                    final_elements[key] = value.upper().replace(' ', '.')

        return final_elements


    def main(self) -> None:
        """
        主函数。
        """
        parent_folder_path = input("请输入父文件夹的路径：")
        if not os.path.exists(parent_folder_path):
            print(Fore.RED + "输入的路径不存在，请检查后重新输入。" + Fore.RESET)
            return
        files_info, all_filenames = self.collect_files_info(parent_folder_path)
        rename_dict = {}
        for file_path, elements_from_file in files_info.items():
            final_elements = self.process_file_info(file_path, self.plex_api)
            if final_elements:
                new_name_elements = [str(final_elements[key]) for key in self.movie_title_format if final_elements[key] is not None]
                new_filename = '.'.join(new_name_elements) + os.path.splitext(file_path)[1]
                rename_dict[file_path] = os.path.join(os.path.dirname(file_path), new_filename)

        self.rename_files(rename_dict, self.movie_title_format)
        print(Fore.GREEN + "脚本执行完毕" + Style.RESET_ALL)


if __name__ == "__main__":
    movie_renamer = MovieRenamer('config.json')
    movie_renamer.main()
