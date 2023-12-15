# -*- coding: utf-8 -*-
# @Time : 2023/11/25
# @File : rename_show.py

import re
import os
import time
import json
import shutil
import colorama
from natsort import natsorted
from colorama import Fore, Style
from api import TMDBApi


class LocalMediaRename:
    def __init__(self, config_file: str):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.tmdb = TMDBApi(config['TMDB_API_KEY'])
        self.tmdb_language = self.select_language(config)
        self.tv_name_format = config['tv_name_format']
        self.video_suffix_list = [suffix.lower() for suffix in config['video_suffix_list'].split(',')]
        self.video_suffix_list += [suffix.upper() for suffix in config['video_suffix_list'].split(',')]
        self.subtitle_suffix_list = config['subtitle_suffix_list'].split(',')
        self.other_suffix_list = config['other_suffix_list'].split(',')
        self.rename_seasons = config['rename_seasons']
        self.show_delete_files = config['show_delete_files']
        self.auto_rename = config['auto_rename']
        self.debug = config['debug']
        self.destination_folder = config['destination_folder']

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
                    print(Fore.RED + "-" * 120)
                    print(colorama.Fore.GREEN + f"正在处理的文件夹: {folder_name} 标题: {title}, 年份: {year}, TMDB ID: {tmdb_id}" + colorama.Fore.RESET)
                    time.sleep(1)
                season_folders = [name for name in os.listdir(sub_folder_path) if os.path.isdir(os.path.join(sub_folder_path, name)) and re.search(r'(S\d+|SEASON \d+|第\d+季)', name.upper())]
                if season_folders:
                    all_skipped_episodes = []
                    for season_folder in season_folders:
                        season_folder_path = os.path.join(sub_folder_path, season_folder)
                        #print(f"正在处理的季文件夹: {season_folder}") 
                        if match:
                            skipped_episodes = self.tv_rename_id(tmdb_id, season_folder_path)
                            all_skipped_episodes.extend(skipped_episodes)
                        else:
                            skipped_episodes = self.tv_rename_keyword(title, season_folder_path)
                            all_skipped_episodes.extend(skipped_episodes)

                    if not all_skipped_episodes:
                        new_folder_path = os.path.join(self.destination_folder, folder_name)
                        suffix = 2
                        while os.path.exists(new_folder_path):
                            new_folder_name = f'{folder_name} 版本-{suffix}'
                            new_folder_path = os.path.join(self.destination_folder, new_folder_name)
                            suffix += 1

                        try:
                            shutil.move(sub_folder_path, new_folder_path)
                            print(f"成功移动文件夹: {sub_folder_path} -> {new_folder_path}")
                        except Exception as e:
                            print(f"移动文件夹时发生错误: {e}")

                        if self.debug:
                            print(colorama.Fore.GREEN + "正在移动: {} -> {}".format(sub_folder_path, new_folder_path) + colorama.Fore.RESET)
                else:
                    if match:
                        skipped_episodes = self.tv_rename_id(tmdb_id, sub_folder_path)
                        if not skipped_episodes:
                            new_folder_path = os.path.join(self.destination_folder, folder_name)
                            suffix = 2
                            while os.path.exists(new_folder_path):
                                new_folder_name = f'{folder_name} 版本-{suffix}'
                                new_folder_path = os.path.join(self.destination_folder, new_folder_name)
                                suffix += 1

                            try:
                                shutil.move(sub_folder_path, new_folder_path)
                                print(f"成功移动文件夹: {sub_folder_path} -> {new_folder_path}")
                            except Exception as e:
                                print(f"移动文件夹时发生错误: {e}")

                            if self.debug:
                                print(colorama.Fore.GREEN + "正在移动: {} -> {}".format(sub_folder_path, new_folder_path) + colorama.Fore.RESET)
                    else:
                        skipped_episodes = self.tv_rename_keyword(title, sub_folder_path)
                        if not skipped_episodes:
                            new_folder_path = os.path.join(self.destination_folder, folder_name)
                            suffix = 2
                            while os.path.exists(new_folder_path):
                                new_folder_name = f'{folder_name} 版本-{suffix}'
                                new_folder_path = os.path.join(self.destination_folder, new_folder_name)
                                suffix += 1

                            try:
                                shutil.move(sub_folder_path, new_folder_path)
                                #print(f"成功移动文件夹: {sub_folder_path} -> {new_folder_path}")
                            except Exception as e:
                                print(f"移动文件夹时发生错误: {e}")

                            if self.debug:
                                print(colorama.Fore.GREEN + "正在移动: {} -> {}".format(sub_folder_path, new_folder_path) + colorama.Fore.RESET)


    def tv_rename_id(self, tv_id: str, folder_path: str, first_number: int = 1, auto_rename=False):
        skipped_episodes = []  # 在函数开始处初始化 skipped_episodes
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
                season_number = 1


        # 获取剧集对应季每集信息
        tv_season_info = self.tmdb.tv_season_info(tv_id, season_number, language=self.tmdb_language, silent=self.debug)
        result['result'].append(tv_season_info)

        # 若获取失败则停止， 并返回结果
        if tv_info_result['request_code'] != 200:
            failure_msg = colorama.Fore.RED + '\n[TvInfo●失败]' + colorama.Fore.RESET
            print(f"{failure_msg} 剧集id: {tv_id}\t{tv_info_result['name']} 第 {season_number} 季\n{tv_season_info['status_message']}")
            return result

        # 保存剧集标题
        if 'episodes' in tv_season_info:
            episodes = list(
                map(
                    lambda x: self.tv_name_format.format(
                        name=tv_info_result['name'], season=tv_season_info['season_number'], episode=x[
                            'episode_number'], title=x['name']),
                    tv_season_info['episodes']))
            episodes = episodes[first_number - 1:]

            # 创建包含源文件名以及目标文件名列表
            file_list = os.listdir(folder_path)
            sorted_file_list = natsorted(file_list)

            video_list = list(
                filter(lambda x: x.split(".")[-1] in self.video_suffix_list, sorted_file_list))

            subtitle_list = list(
                filter(lambda x: x.split(".")[-1] in self.subtitle_suffix_list, sorted_file_list))
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

        else:
            print(colorama.Fore.RED + f"警告：'episodes' 键不存在于 tv_season_info 字典中。跳过当前操作。" + colorama.Fore.RESET)
            return result  # 返回结果，跳过当前操作

        # 检查TMDB的集数是否与媒体文件数量相同
        if len(tv_season_info['episodes']) == len(video_list):
            print(colorama.Fore.GREEN + "TMDB的集数与媒体文件数量相同，以下是将要重命名的文件列表：" + colorama.Fore.RESET)

            # 输出提醒消息
            print("以下媒体文件将被重命名: ")
            for video in video_rename_list:
                continue
                #print("{} -> {}".format(video['original_name'], video['target_name']))
            
            # 只有当存在字幕文件时才输出提示
            if subtitle_rename_list:
                #print("以下字幕文件将被重命名: ")
                for subtitle in subtitle_rename_list:
                    continue
                    #print("{} -> {}".format(subtitle['original_name'], subtitle['target_name']))

            while not self.auto_rename:
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
                

            print(colorama.Fore.GREEN + f"文件重命名操作完成" + colorama.Fore.RESET)

        else:
            tmdb_episodes = set(range(1, len(tv_season_info['episodes']) + 1))
            existing_episodes = []
            skipped_episodes = []  # 新增：用于记录被跳过的剧集
            for file in video_rename_list:
                # 尝试匹配多种集数格式
                match = re.search(r'E(\d+)', file['original_name'])
                if match:
                    # 从匹配的结果中提取集数
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
            print(existing_episodes)
            print(missing_episodes)
            print(colorama.Fore.RED + f"警告：文件数为：{len(video_list)}，TMDB的集数为：{len(tv_season_info['episodes'])}，缺失的集数为：{len(missing_episodes)}，缺失的集为：{sorted(list(missing_episodes))}。" + colorama.Fore.RESET)           

            for i in range(len(tv_season_info['episodes'])):
                if (i + 1) in missing_episodes:
                    skipped_episodes.append(i + 1)  # 新增：记录被跳过的剧集
                    continue

            print(colorama.Fore.GREEN + "剧集因缺集被跳过重命名！" + colorama.Fore.RESET)
            skipped_episodes = ['default_value']
            return skipped_episodes
        return skipped_episodes  # 返回被跳过的剧集

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
        all_skipped_episodes = []
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
            skipped_episodes = self.tv_rename_id(search_result['results'][int(tv_number)]['id'], folder_path, first_number)
        return result

    def rename_season_folders(self, folder_path: str, rename_seasons: bool=False):
        # 首先确保传入的是一个目录
        if not os.path.isdir(folder_path):
            return

        for folder_name in os.listdir(folder_path):
            sub_folder_path = os.path.join(folder_path, folder_name)
            # 只处理目录
            if os.path.isdir(sub_folder_path):
                # 检查是否存在季文件夹
                season_match = re.search(r'\bS(\d+)\b|\bS (\d+)\b|\bSEASON(\d+)\b|\bSEASON (\d+)\b|\b第(\d+)季\b|S\d+', folder_name.upper())
                if season_match:
                    season_number = re.search(r'\d+', season_match.group()).group().strip()
                    season_number = str(int(season_number))
                    new_folder_name = f'Season {season_number}'
                    new_folder_path = os.path.join(folder_path, new_folder_name)
                    if folder_name == new_folder_name:
                        continue
                    # 检查新的文件夹名是否已经存在，如果存在，添加一个后缀
                    suffix = 2
                    while os.path.exists(new_folder_path):
                        new_folder_name = f'Season {season_number} 版本-{suffix}'
                        new_folder_path = os.path.join(folder_path, new_folder_name)
                        suffix += 1

                    print(f"季文件夹: {folder_name}  ->  {new_folder_name}")
                    os.rename(sub_folder_path, new_folder_path)

                # 递归处理子文件夹
                self.rename_season_folders(sub_folder_path)








    def delete_files(self, folder_path: str, show_delete_files=False):
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for file_name in filenames:
                if file_name.endswith(tuple(self.other_suffix_list)):
                    full_file_name = os.path.join(dirpath, file_name)
                    try:
                        os.remove(full_file_name)
                    except OSError as e:
                        print(f"Error: {e.filename} - {e.strerror}.")


if __name__ == '__main__':
    # 创建一个LocalMediaRename对象
    renamer = LocalMediaRename('config.json')
    # 让用户输入根目录
    print(Fore.RED + '开始程序:注意输入的目录结构必须是【你的目录/剧集或电影文件夹/媒体文件或其他子目录】' + Style.RESET_ALL)
    root_folder_path = input("请输入你的目录的路径：")

    # 重命名季度文件夹
    renamer.rename_season_folders(root_folder_path, rename_seasons=renamer.rename_seasons)

    # 删除指定格式的文件
    renamer.delete_files(root_folder_path, show_delete_files=renamer.show_delete_files)
    # 使用LocalMediaRename对象来重命名文件
    renamer.rename_files(root_folder_path)