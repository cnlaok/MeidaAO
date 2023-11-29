# -*- coding: utf-8 -*-
# @Time : 2023/11/21
# @File : config.py

import os
import json
from typing import Dict


class ConfigManager:
    def __init__(self, config_file: str):
        self.config_file: str = config_file
        self.config: Dict[str, str] = {}
        self.plex_url: str = None
        self.plex_token: str = None
        self.tmdb_api_key: str = None
        self.movies_folder: str = None
        self.shows_folder: str = None
        self.anime_folder: str = None
        self.chinese_drama_folder: str = None
        self.documentary_folder: str = None
        self.american_drama_folder: str = None
        self.japanese_korean_drama_folder: str = None
        self.sports_folder: str = None
        self.variety_show_folder: str = None
        self.load_config()

    def load_config(self) -> None:
        # 检查配置文件是否存在，如果存在则加载
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            # 直接从配置中读取预定义的键
            self.video_suffix_list = self.config.get('video_suffix_list', [])
            self.subtitle_suffix_list = self.config.get('subtitle_suffix_list', [])
            self.other_suffix_list = self.config.get('other_suffix_list', [])
            self.movie_title_format = self.config.get('movie_title_format', '')
            self.move_files = self.config.get('move_files', False)
            self.delete_other_files = self.config.get('delete_other_files', False)
        self.check_config()


    def check_config(self) -> None:
        # 配置文件中需要的键
        keys = ['PLEX_URL', 'PLEX_TOKEN', 'TMDB_API_KEY', 'MOVIES_FOLDER', 'SHOWS_FOLDER', 'ANIME_FOLDER', 'CHINESE_DRAMA_FOLDER', 'DOCUMENTARY_FOLDER', 'AMERICAN_DRAMA_FOLDER', 'JAPANESE_KOREAN_DRAMA_FOLDER', 'SPORTS_FOLDER', 'VARIETY_SHOW_FOLDER']
        # 对应每个键的提示信息
        prompts = {
            'PLEX_URL': '请输入Plex服务器的URL:',
            'PLEX_TOKEN': '请输入Plex的令牌:',
            'TMDB_API_KEY': '请输入TMDB的API密钥:',
            'MOVIES_FOLDER': '请输入电影文件夹的路径:',
            'SHOWS_FOLDER': '请输入剧集文件夹的路径:',
            'ANIME_FOLDER': '请输入动漫文件夹的路径:',
            'CHINESE_DRAMA_FOLDER': '请输入国剧文件夹的路径:',
            'DOCUMENTARY_FOLDER': '请输入纪录片文件夹的路径:',
            'AMERICAN_DRAMA_FOLDER': '请输入美剧文件夹的路径:',
            'JAPANESE_KOREAN_DRAMA_FOLDER': '请输入日韩剧文件夹的路径:',
            'SPORTS_FOLDER': '请输入体育文件夹的路径:',
            'VARIETY_SHOW_FOLDER': '请输入综艺文件夹的路径:'
        }
        # 检查每个键是否在配置中，如果不在则提示用户输入
        for key in keys:
            if key not in self.config or not self.config[key]:
                self.config[key] = input(prompts.get(key, f"请输入{key}："))
            if key == 'PLEX_URL':
                self.plex_url = self.config[key]
            elif key == 'PLEX_TOKEN':
                self.plex_token = self.config[key]
            elif key == 'TMDB_API_KEY':
                self.tmdb_api_key = self.config[key]
            elif key == 'MOVIES_FOLDER':
                self.movies_folder = self.config[key]
            elif key == 'SHOWS_FOLDER':
                self.shows_folder = self.config[key]
            elif key == 'ANIME_FOLDER':
                self.anime_folder = self.config[key]
            elif key == 'CHINESE_DRAMA_FOLDER':
                self.chinese_drama_folder = self.config[key]
            elif key == 'DOCUMENTARY_FOLDER':
                self.documentary_folder = self.config[key]
            elif key == 'AMERICAN_DRAMA_FOLDER':
                self.american_drama_folder = self.config[key]
            elif key == 'JAPANESE_KOREAN_DRAMA_FOLDER':
                self.japanese_korean_drama_folder = self.config[key]
            elif key == 'SPORTS_FOLDER':
                self.sports_folder = self.config[key]
            elif key == 'VARIETY_SHOW_FOLDER':
                self.variety_show_folder = self.config[key]
        self.save_config()


    def save_config(self) -> None:
        # 保存配置到文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4, separators=(',', ': '))



    def get_server_info_and_key(self) -> Dict[str, str]:
        # 获取服务器信息和密钥
        return {
            'plex_url': self.plex_url,
            'plex_token': self.plex_token,
            'tmdb_api_key': self.tmdb_api_key,
            'movies_folder': self.movies_folder,
            'shows_folder': self.shows_folder,
            'anime_folder': self.anime_folder,
            'chinese_drama_folder': self.chinese_drama_folder,
            'documentary_folder': self.documentary_folder,
            'american_drama_folder': self.american_drama_folder,
            'japanese_korean_drama_folder': self.japanese_korean_drama_folder,
            'sports_folder': self.sports_folder,
            'variety_show_folder': self.variety_show_folder
        }
        