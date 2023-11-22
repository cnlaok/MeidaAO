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
        self.load_config()

    def load_config(self) -> None:
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        self.check_config()

    def check_config(self) -> None:
        keys = ['PLEX_URL', 'PLEX_TOKEN', 'TMDB_API_KEY', 'MOVIES_FOLDER', 'SHOWS_FOLDER', 'ANIME_FOLDER', 'CHINESE_DRAMA_FOLDER', 'DOCUMENTARY_FOLDER', 'AMERICAN_DRAMA_FOLDER', 'JAPANESE_KOREAN_DRAMA_FOLDER', 'SPORTS_FOLDER', 'VARIETY_SHOW_FOLDER']  # 新增
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
            elif key == 'ANIME_FOLDER':  # 新增
                self.anime_folder = self.config[key]  # 新增
            elif key == 'CHINESE_DRAMA_FOLDER':  # 新增
                self.chinese_drama_folder = self.config[key]  # 新增
            elif key == 'DOCUMENTARY_FOLDER':  # 新增
                self.documentary_folder = self.config[key]  # 新增
            elif key == 'AMERICAN_DRAMA_FOLDER':  # 新增
                self.american_drama_folder = self.config[key]  # 新增
            elif key == 'JAPANESE_KOREAN_DRAMA_FOLDER':  # 新增
                self.japanese_korean_drama_folder = self.config[key]  # 新增
            elif key == 'SPORTS_FOLDER':  # 新增
                self.sports_folder = self.config[key]  # 新增
            elif key == 'VARIETY_SHOW_FOLDER':  # 新增
                self.variety_show_folder = self.config[key]  # 新增
        self.save_config()


    def save_config(self) -> None:
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def get_server_info_and_key(self) -> Dict[str, str]:
        return {
            'plex_url': self.plex_url,
            'plex_token': self.plex_token,
            'tmdb_api_key': self.tmdb_api_key,
            'movies_folder': self.movies_folder,
            'shows_folder': self.shows_folder
        }
    