# -*- coding: utf-8 -*-
# @Time : 2023/11/25
# @File : rename_show.py

import re
import os
import time
import json
import colorama
from colorama import Fore, Style
from api import TMDBApi


class LocalMediaRename:
    def __init__(self, config_file: str):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.tmdb = TMDBApi(config['TMDB_API_KEY'])
        self.tmdb_language = self.select_language(config)
        self.tv_name_format = config['tv_name_format']
        self.video_suffix_list = config['video_suffix_list']
        self.subtitle_suffix_list = config['subtitle_suffix_list']
        self.rename_seasons = config['rename_seasons']
        self.delete_files = config['delete_files']
        self.debug = config['debug']
        self.other_suffix_list = config['other_suffix_list'].split(',')

    def select_language(self, config):
        if config['ask_language_change']:
            change_language = input("当前的语言选项是" + config['language_option'] + "。你想更改吗？（y/n）")
            if change_language.lower() == 'y':
                language_option = input("请选择语言：1. 中文 2. 英文 3. 日文\n")
                if language_option == '2':
                    return "en-US"
                elif language_option == '3':
                    return "ja-JP"
                else:
                    print(colorama.Fore.GREEN + "已默认设置为中文。" + colorama.Fore.RESET)
                    return "zh-CN"
        else:
            return config['language_option']

    def rename_files(self, folder_path: str):
        for folder_name in os.listdir(folder_path):
            sub_folder_path = os.path.join(folder_path, folder_name)
            if os.path.isdir(sub_folder_path):
                match = re.search(r'(.*) \((\d{4})\) {tmdb-(\d+)}', folder_name)
                title = folder_name  # 假设整个文件夹名就是标题
                if match:
                    title, year, tmdb_id = match.groups()
                    print(colorama.Fore.GREEN + f"正在处理的文件夹: {folder_name} 标题: {title}, 年份: {year}, TMDB ID: {tmdb_id}" + colorama.Fore.RESET)
                # 检查是否存在季文件夹
                season_folders = [name for name in os.listdir(sub_folder_path) if os.path.isdir(os.path.join(sub_folder_path, name)) and re.search(r'(S\d+|SEASON \d+|第\d+季)', name.upper())]
                if season_folders:
                    # 如果存在季文件夹，对每个季文件夹执行相同的操作
                    for season_folder in season_folders:
                        season_folder_path = os.path.join(sub_folder_path, season_folder)
                        print(f"正在处理的季文件夹: {season_folder}") 
                        if match:
                            # 根据TMDB ID重命名文件
                            self.tv_rename_id(tmdb_id, season_folder_path)
                        else:
                            # 如果没有TMDB ID，使用标题来重命名文件
                            self.tv_rename_keyword(title, season_folder_path)
                else:
                    # 如果不存在季文件夹，假设剧集只有一季，并对子文件夹中的文件执行重命名操作
                    if match:
                        # 根据TMDB ID重命名文件
                        self.tv_rename_id(tmdb_id, sub_folder_path)
                    else:
                        # 如果没有TMDB ID，使用标题来重命名文件
                        self.tv_rename_keyword(title, sub_folder_path)


    def tv_rename_id(self, tv_id: str, folder_path: str, first_number: int = 1) -> dict:
        folder_path = os.path.normpath(folder_path) + os.sep
        notice_msg = colorama.Fore.GREEN + '[提示!]' + colorama.Fore.RESET

        # 设置返回数据
        result = dict(success=False,
                    args=dict(tv_id=tv_id,
                                folder_path=folder_path,
                                first_number=first_number),
                    result=[])

        # 根据剧集id 查找TMDB剧集信息
        tv_info_result = self.tmdb.tv_info(tv_id, language=self.tmdb_language, silent=False)
        result['result'].append(tv_info_result)

        # 若查找失败则停止，并返回结果
        if tv_info_result['request_code'] != 200:
            return result

        episodes = []  # 给episodes一个默认值

        # 若查找结果只有一项，则无需选择，直接进行下一步
        if len(tv_info_result['seasons']) == 1:
            season_number = tv_info_result['seasons'][0]['season_number']
        else:
            # 获取到多项匹配结果，从文件夹名中提取季数
            season_folder_name = os.path.basename(os.path.normpath(folder_path)).upper()
            print(f"正在处理的文件夹: {season_folder_name}") 
            patterns = [r'S(\d+)', r'SEASON (\d+)', r'第(\d+)季']
            for pattern in patterns:
                match = re.search(pattern, season_folder_name, re.IGNORECASE)
                if match:
                    season_number = int(match.group(1))
                    break
            if not match:
                # 如果提取不到季数，请求用户手动输入
                season_number = input("无法从文件夹名中提取季数，请手动输入：")
                season_number = int(season_number)  # 将输入的字符串转换为整数

        # 获取剧集对应季每集信息
        tv_season_info = self.tmdb.tv_season_info(tv_id, season_number, language=self.tmdb_language, silent=self.debug)
        result['result'].append(tv_season_info)

        # 若获取失败则停止， 并返回结果
        if tv_season_info['request_code'] != 200:
            failure_msg = colorama.Fore.RED + '\n[TvInfo●失败]' + colorama.Fore.RESET
            print(f"{failure_msg} 剧集id: {tv_id}\t{tv_info_result['name']} 第 {season_number} 季\n{tv_season_info['status_message']}")
            return result

        # 保存剧集标题
        episodes = list(
            map(
                lambda x: self.tv_name_format.format(
                    name=tv_info_result['name'], season=tv_season_info['season_number'], episode=x[
                        'episode_number'], title=x['name']),
                tv_season_info['episodes']))
        episodes = episodes[first_number - 1:]

        # 创建包含源文件名以及目标文件名列表
        file_list = os.listdir(folder_path)
        video_list = list(
            filter(lambda x: x.split(".")[-1] in self.video_suffix_list, file_list))

        subtitle_list = list(
            filter(lambda x: x.split(".")[-1] in self.subtitle_suffix_list, file_list))
        video_rename_list = list(
            map(
                lambda x, y: dict(original_name=x,
                                target_name=y + '.' + x.split(".")[-1]),
                video_list, episodes))
        subtitle_rename_list = list(
            map(
                lambda x, y: dict(original_name=x,
                                target_name=y + '.' + x.split(".")[-1]),
                subtitle_list, episodes))

        # 检查TMDB的集数是否与媒体文件数量相同
        if len(tv_season_info['episodes']) == len(video_list):
            print(colorama.Fore.GREEN + "TMDB的集数与媒体文件数量相同，以下是将要重命名的文件列表：" + colorama.Fore.RESET)

            # 输出提醒消息
            print("以下视频文件将被重命名: ")
            for video in video_rename_list:
                print("{} -> {}".format(video['original_name'],
                                        video['target_name']))
            print("以下字幕文件将被重命名: ")
            for subtitle in subtitle_rename_list:
                print("{} -> {}".format(subtitle['original_name'],
                                        subtitle['target_name']))

            while True:
                signal = input("你确定要重命名吗？[Enter] 确认，[n] 取消\t")
                if signal.lower() == '':
                    break
                elif signal.lower() == 'n':
                    return
                else:
                    continue

            for file in video_rename_list + subtitle_rename_list:
                # 在重命名文件之前，清理文件名
                for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
                    file['target_name'] = file['target_name'].replace(char, '.')
                # 如果文件名以'.'结尾，删除这个字符
                if file['target_name'].endswith('.'):
                    file['target_name'] = file['target_name'][:-1]
                os.rename(folder_path + file['original_name'], folder_path + file['target_name'])
                if self.debug:
                    print(colorama.Fore.GREEN + "正在重命名: {} -> {}".format(file['original_name'], file['target_name']) + colorama.Fore.RESET)
                time.sleep(1)

            print(colorama.Fore.GREEN + "文件重命名操作完成" + colorama.Fore.RESET)
        else:
            tmdb_episodes = set(range(1, len(tv_season_info['episodes']) + 1))
            existing_episodes = []
            for file in video_rename_list:
                match = re.search(r'E(\d+)', file['original_name'])
                if match:
                    existing_episodes.append(int(match.group(1)))
                else:
                    match = re.search(r'(\d{2}-\d{2}|\d{4})', file['original_name'])
                    if match:
                        existing_episodes.append(match.group(1))

            # 如果existing_episodes包含日期，按日期排序并转换为集数
            if existing_episodes and isinstance(existing_episodes[0], str):
                existing_episodes.sort()
                existing_episodes = list(range(1, len(existing_episodes) + 1))
            else:
                existing_episodes = set(existing_episodes)

            missing_episodes = tmdb_episodes - set(existing_episodes)

            print(colorama.Fore.RED + f"警告：TMDB的集数与媒体文件数量不同，缺失的集数为：{len(missing_episodes)}，缺失的集为：{sorted(list(missing_episodes))}，已默认选择不重命名。" + colorama.Fore.RESET)

    def tv_rename_keyword(self,
                          keyword: str,
                          folder_path: str,
                          first_number: int = 1) -> dict:
        """
        根据TMDB剧集关键词获取剧集标题,并批量将指定文件夹中的视频文件及字幕文件重命名为剧集标题.

        :param keyword: 剧集关键词
        :param folder_path: 文件夹路径, 结尾必须加'/', 如/abc/test/
        :param first_number: 从指定集数开始命名, 如first_name=5, 则从第5集开始按顺序重命名
        :return: 重命名请求结果
        """

        notice_msg = colorama.Fore.GREEN + '[提示!]' + colorama.Fore.RESET

        # 创建返回数据
        result = dict(success=False,
                      args=dict(keyword=keyword,
                                folder_path=folder_path,
                                first_number=first_number),
                      result=[])
        # 使用关键词查找剧集
        search_result = self.tmdb.search_tv(keyword, language=self.tmdb_language)
        result['result'].append(search_result)
        # 查找失败则停止, 并返回结果
        if search_result['request_code'] != 200 or len(
                search_result['results']) == 0:
            return result

        # 若查找结果只有一项, 则继续进行, 无需选择
        if len(search_result['results']) == 1:
            rename_result = self.tv_rename_id(
                search_result['results'][0]['id'], folder_path, first_number)
            result['result'] += (rename_result['result'])
            return result

        # 若有多项, 则手动选择
        while True:
            tv_number = input(f"{notice_msg} 查找到多个结果, 请输入对应[序号], 输入[n]退出\t")
            active_number = list(range(len(search_result['results'])))
            active_number = list(map(lambda x: str(x), active_number))
            if tv_number == 'n':
                result['result'].append("用户输入[n], 已主动退出选择匹配剧集")
                return result
            elif tv_number in active_number:
                tv_id = search_result['results'][int(tv_number)]['id']
                break
            else:
                continue

        # 根据获取到的id进行重命名
        for season_number in range(1, len(search_result['results']) + 1):
            rename_result = self.tv_rename_id(search_result['results'][int(tv_number)]['id'], folder_path, first_number)
            result['result'] += (rename_result['result'])
        return result

    def rename_season_folders(self, folder_path: str, rename_seasons=False, delete_files=False):
        for folder_name in os.listdir(folder_path):
            sub_folder_path = os.path.join(folder_path, folder_name)
            if os.path.isdir(sub_folder_path):
                # 如果rename_seasons为True，则重命名季度文件夹
                if rename_seasons:
                    self.rename_season_folders(sub_folder_path)

                # 检查是否存在季文件夹
                season_folders = [name for name in os.listdir(sub_folder_path) if os.path.isdir(os.path.join(sub_folder_path, name)) and re.search(r'(S\d+|SEASON \d+|第\d+季)', name.upper())]

                # 遍历所有季文件夹
                for folder in season_folders:
                    folder_path = os.path.join(sub_folder_path, folder)
                    if os.path.isdir(folder_path):
                        print(f"正在处理的季文件夹: {folder}")
                        # 提取季数
                        season_number = re.search(r'\d+', folder).group()
                        # 创建新的文件夹名称
                        new_folder_name = f'Season {season_number}'
                        # 重命名文件夹
                        os.rename(folder_path, os.path.join(sub_folder_path, new_folder_name))

                # 如果delete_files为True，则删除指定格式的文件
                if delete_files:
                    file_list = os.listdir(sub_folder_path)
                    for file_name in file_list:
                        if file_name.endswith(tuple(self.other_suffix_list)):
                            os.remove(os.path.join(sub_folder_path, file_name))


if __name__ == '__main__':
    # 创建一个LocalMediaRename对象
    renamer = LocalMediaRename('config.json')
    # 让用户输入根目录
    print(Fore.RED + '开始程序:注意输入的目录结构必须是【你的目录/剧集或电影文件夹/媒体文件或其他子目录】' + Style.RESET_ALL)
    root_folder_path = input("请输入你的目录的路径：")
    # 使用LocalMediaRename对象来重命名文件
    renamer.rename_files(root_folder_path)
    renamer.rename_season_folders(root_folder_path, rename_seasons=renamer.rename_seasons, delete_files=renamer.delete_files)
