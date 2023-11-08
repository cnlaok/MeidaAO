# -*- coding: utf-8 -*-
# @Time : 2023/11/03
# @File : config.py

import os
import json

class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = {}
        self.plex_url = None  # 添加这一行
        self.plex_token = None  # 添加这一行
        self.tmdb_api_key = None  # 添加这一行
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        self.check_config()

    def check_config(self):
        keys = ['PLEX_URL', 'PLEX_TOKEN', 'TMDB_API_KEY']
        for key in keys:
            if key not in self.config or not self.config[key]:
                self.config[key] = input(f"请输入{key}：")
            if key == 'PLEX_URL':  # 添加这一行
                self.plex_url = self.config[key]  # 添加这一行
            elif key == 'PLEX_TOKEN':  # 添加这一行
                self.plex_token = self.config[key]  # 添加这一行
            elif key == 'TMDB_API_KEY':  # 添加这一行
                self.tmdb_api_key = self.config[key]  # 添加这一行
        self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def get_server_info_and_key(self):
        return {
            'plex_url': self.plex_url,
            'plex_token': self.plex_token,
            'tmdb_api_key': self.tmdb_api_key
        }
